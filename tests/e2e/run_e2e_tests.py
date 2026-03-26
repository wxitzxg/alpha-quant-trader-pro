#!/usr/bin/env python
"""E2E 测试运行器

Usage:
    python tests/e2e/run_e2e_tests.py              # Run all tests
    python tests/e2e/run_e2e_tests.py -v           # Verbose output
    python tests/e2e/run_e2e_tests.py -k "health"  # Run only health tests
    python tests/e2e/run_e2e_tests.py --status     # Check status only
    python tests/e2e/run_e2e_tests.py --setup      # Check Docker services
    python tests/e2e/run_e2e_tests.py --skip-setup # Skip Docker check
    python tests/e2e/run_e2e_tests.py --cov        # Coverage report
"""

import argparse
import subprocess
import sys
from pathlib import Path

import httpx


# Configuration
API_BASE_URL = "http://localhost:8000"
HEALTH_ENDPOINT = "/health"
E2E_TESTS_DIR = Path(__file__).parent
PROJECT_ROOT = E2E_TESTS_DIR.parent.parent


def run_command(cmd: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        cwd=PROJECT_ROOT,
    )


def check_docker_services() -> tuple[bool, str]:
    """Check if Docker containers are running.

    Returns:
        Tuple of (is_healthy, status_message)
    """
    result = run_command(["docker", "compose", "ps"])

    if result.returncode != 0:
        return False, f"Docker compose command failed: {result.stderr}"

    output = result.stdout
    if not output.strip():
        return False, "No Docker containers found. Run 'docker compose up -d' first."

    # Check for "Up" status in output
    lines = output.strip().split("\n")
    services_up = 0
    services_total = 0

    for line in lines[1:]:  # Skip header line
        if line.strip():
            services_total += 1
            if "Up" in line:
                services_up += 1

    if services_up == services_total and services_total > 0:
        return True, f"All {services_up} Docker services are running"
    elif services_up > 0:
        return False, f"Only {services_up}/{services_total} services are running"
    else:
        return False, "No services are running. Run 'docker compose up -d' first."


def check_api_health() -> tuple[bool, str]:
    """Check if API server is healthy.

    Returns:
        Tuple of (is_healthy, status_message)
    """
    try:
        with httpx.Client(base_url=API_BASE_URL, timeout=10.0) as client:
            response = client.get(HEALTH_ENDPOINT)

            if response.status_code == 200:
                data = response.json()
                return True, f"API server is healthy: {data}"
            else:
                return False, f"API returned status {response.status_code}"
    except httpx.ConnectError:
        return False, f"Cannot connect to API at {API_BASE_URL}"
    except Exception as e:
        return False, f"Health check failed: {e}"


def print_service_status() -> None:
    """Print detailed service status."""
    print("=" * 60)
    print("Service Status")
    print("=" * 60)

    # Docker status
    docker_healthy, docker_msg = check_docker_services()
    status_icon = "[OK]" if docker_healthy else "[FAIL]"
    print(f"\n{status_icon} Docker Services: {docker_msg}")

    # Show docker compose ps output
    result = run_command(["docker", "compose", "ps"])
    if result.returncode == 0 and result.stdout.strip():
        print("\nDocker Containers:")
        for line in result.stdout.strip().split("\n"):
            print(f"  {line}")

    # API health
    api_healthy, api_msg = check_api_health()
    status_icon = "[OK]" if api_healthy else "[FAIL]"
    print(f"\n{status_icon} API Server: {api_msg}")

    print("\n" + "=" * 60)


def run_e2e_tests(
    verbose: bool = False,
    test_filter: str | None = None,
    coverage: bool = False,
) -> int:
    """Run E2E tests with pytest.

    Args:
        verbose: Enable verbose output
        test_filter: pytest -k filter expression
        coverage: Enable coverage report

    Returns:
        Exit code from pytest
    """
    cmd = [sys.executable, "-m", "pytest", str(E2E_TESTS_DIR)]

    if verbose:
        cmd.append("-v")

    if test_filter:
        cmd.extend(["-k", test_filter])

    if coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
        ])

    print(f"\nRunning: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="E2E test runner for Alpha Quant Trader Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python tests/e2e/run_e2e_tests.py              # Run all tests
    python tests/e2e/run_e2e_tests.py -v           # Verbose output
    python tests/e2e/run_e2e_tests.py -k "health"  # Run only health tests
    python tests/e2e/run_e2e_tests.py --status     # Check status only
    python tests/e2e/run_e2e_tests.py --skip-setup # Skip Docker check
        """,
    )

    # Action arguments
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--setup",
        action="store_true",
        help="Check Docker service status only",
    )
    action_group.add_argument(
        "--status",
        action="store_true",
        help="Display detailed service status",
    )

    # Test options
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip environment checks (Docker, API health)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose test output",
    )
    parser.add_argument(
        "-k",
        "--test-filter",
        type=str,
        metavar="EXPR",
        help="Filter tests by expression (passed to pytest -k)",
    )
    parser.add_argument(
        "--cov",
        action="store_true",
        help="Generate coverage report",
    )

    args = parser.parse_args()

    # Handle --status
    if args.status:
        print_service_status()
        return 0

    # Handle --setup
    if args.setup:
        docker_healthy, docker_msg = check_docker_services()
        print(f"Docker Services: {docker_msg}")
        return 0 if docker_healthy else 1

    # Run tests (default action)
    if not args.skip_setup:
        print("Checking environment...")

        # Check Docker
        docker_healthy, docker_msg = check_docker_services()
        if not docker_healthy:
            print(f"Error: {docker_msg}")
            print("\nRun 'docker compose up -d' to start services.")
            return 1
        print(f"  [OK] {docker_msg}")

        # Check API health
        api_healthy, api_msg = check_api_health()
        if not api_healthy:
            print(f"Error: {api_msg}")
            print("\nWait for API server to start or check logs.")
            return 1
        print(f"  [OK] {api_msg}")

        print()

    # Run tests
    exit_code = run_e2e_tests(
        verbose=args.verbose,
        test_filter=args.test_filter,
        coverage=args.cov,
    )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
