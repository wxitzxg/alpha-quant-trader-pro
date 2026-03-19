# 🤝 Contribution Guide

> How to contribute to Alpha Quant Trader Pro

---

## 📋 Table of Contents

1. [Ways to Contribute](#ways-to-contribute)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Submission Guidelines](#code-submission-guidelines)
5. [Pull Request Process](#pull-request-process)
6. [Code Review Process](#code-review-process)
7. [Community Guidelines](#community-guidelines)
8. [FAQ](#faq)

---

## 🌟 Ways to Contribute

We welcome contributions in many forms:

### Code Contributions
- **Bug fixes** - Fix issues in the codebase
- **New features** - Add functionality that aligns with project goals
- **Performance improvements** - Optimize existing code
- **Code refactoring** - Improve code quality and maintainability
- **Tests** - Add missing tests or improve test coverage

### Documentation Contributions
- **User guides** - Improve end-user documentation
- **Developer guides** - Enhance developer documentation
- **API documentation** - Update and expand API docs
- **Tutorials** - Create step-by-step guides
- **Examples** - Add code examples and use cases

### Other Contributions
- **Issue triage** - Help identify and categorize issues
- **Bug reports** - Report bugs with clear reproduction steps
- **Feature requests** - Suggest new features with use cases
- **Code reviews** - Review pull requests from other contributors
- **Community support** - Help answer questions from other users

---

## 🚀 Getting Started

### 1. Fork the Repository

Click the "Fork" button on the GitHub repository page to create your own copy.

### 2. Clone Your Fork

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/alpha-quant-trader-pro.git
cd alpha-quant-trader-pro

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/alpha-quant-trader-pro.git

# Verify remotes
git remote -v
# origin    https://github.com/YOUR_USERNAME/alpha-quant-trader-pro.git
# upstream  https://github.com/ORIGINAL_OWNER/alpha-quant-trader-pro.git
```

### 3. Set Up Development Environment

Follow the [Development Setup Guide](./05-development-setup.md) to configure your environment.

### 4. Find an Issue to Work On

- **Good first issues**: Look for issues labeled `good first issue`
- **Help wanted**: Issues labeled `help wanted` need contributors
- **Bugs**: Fix reported bugs
- **Features**: Implement new features from the roadmap

Browse issues at: https://github.com/ORIGINAL_OWNER/alpha-quant-trader-pro/issues

### 5. Discuss Before Starting

For significant changes or new features:

1. **Check if an issue exists** - Search existing issues
2. **Create an issue if needed** - Describe your proposed change
3. **Discuss with maintainers** - Get feedback before coding
4. **Get approval** - Wait for maintainer approval before starting work

This prevents duplicate work and ensures your contribution aligns with project goals.

---

## 🔁 Development Workflow

### 1. Create a Branch

**Naming conventions:**
- `feature/descriptive-name` - New features
- `fix/issue-description` - Bug fixes
- `docs/document-name` - Documentation changes
- `refactor/component-name` - Refactoring

```bash
# Sync with upstream
git fetch upstream
git checkout upstream/main
git pull upstream main

# Create new branch
git checkout -b feature/add-portfolio-analytics

# Or for bug fixes
git checkout -b fix/fix-data-sync-error
```

### 2. Make Your Changes

**Follow best practices:**
- Write tests first (TDD approach)
- Keep commits atomic and focused
- Follow coding standards
- Update documentation
- Run linters and formatters

```bash
# Make changes to code
# ...

# Run tests
pytest tests/ -v

# Format code
black .
isort .

# Run linters
flake8 .
mypy .

# Run pre-commit hooks
pre-commit run --all-files
```

### 3. Commit Your Changes

**Commit message format:**
```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting)
- `refactor` - Code refactoring
- `test` - Test additions or changes
- `chore` - Build process or auxiliary tool changes

**Examples:**
```bash
# Good commit messages
git commit -m "feat: add portfolio analytics dashboard"

git commit -m "fix: handle null values in KLine data"

git commit -m "docs: update API documentation for v2.0"

git commit -m "test: add unit tests for StockService"

# With body and footer
git commit -m "feat: add backtest optimization parameter

Add configurable optimization parameters to backtest engine.
Supports walk-forward analysis and Monte Carlo simulation.

Closes #123
Co-authored-by: Your Name <your.email@example.com>"
```

### 4. Push to Your Fork

```bash
# Push branch to your fork
git push origin feature/add-portfolio-analytics

# If branch already exists
git push -u origin feature/add-portfolio-analytics
```

### 5. Keep Your Branch Updated

```bash
# Rebase onto latest upstream changes
git fetch upstream
git rebase upstream/main

# Or merge upstream changes
git merge upstream/main

# Push updated branch (may need --force-with-lease)
git push --force-with-lease origin feature/add-portfolio-analytics
```

---

## 📝 Code Submission Guidelines

### Code Quality

**All submissions must:**
- [ ] Follow [coding standards](./06-coding-standards.md)
- [ ] Have 80%+ test coverage
- [ ] Pass all existing tests
- [ ] Include new tests for new code
- [ ] Be properly documented
- [ ] Use type hints where appropriate
- [ ] Handle errors appropriately
- [ ] Follow security best practices

### Testing Requirements

**Test coverage:**
```python
# Example: Test a new feature
# tests/test_portfolio_manager/test_services/test_portfolio_analytics.py

import pytest
from unittest.mock import Mock

from portfolio_manager.services import PortfolioAnalyticsService
from portfolio_manager.models import Portfolio


class TestPortfolioAnalyticsService:
    """Test portfolio analytics service."""

    @pytest.fixture
    def analytics_service(self):
        repository = Mock()
        return PortfolioAnalyticsService(repository)

    def test_calculate_returns(self, analytics_service):
        """Test return calculation."""
        portfolio = Portfolio(id=1, user_id=1)
        returns = analytics_service.calculate_returns(portfolio, days=30)
        assert returns is not None
        assert isinstance(returns, dict)

    def test_calculate_risk_metrics(self, analytics_service):
        """Test risk metrics calculation."""
        portfolio = Portfolio(id=1, user_id=1)
        metrics = analytics_service.calculate_risk_metrics(portfolio)
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
```

**Run tests before submitting:**
```bash
# Run all tests
pytest tests/ -v --cov=. --cov-report=term

# Run specific test file
pytest tests/test_portfolio_manager/ -v

# Check coverage
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

### Documentation Requirements

**Update documentation when:**
- Adding new features
- Changing existing APIs
- Fixing bugs that affect behavior
- Adding configuration options

**Documentation files:**
```
docs/
├── user-guide/          # User-facing documentation
├── admin-guide/         # Admin/ops documentation
├── developer-guide/     # Developer documentation
└── project-docs/        # Project documentation
```

### Commit Best Practices

**DO:**
- ✅ Make atomic commits (one logical change per commit)
- ✅ Write clear, descriptive commit messages
- ✅ Reference related issues (e.g., "Closes #123")
- ✅ Use conventional commit format
- ✅ Keep commits small and focused

**DON'T:**
- ❌ Make huge commits with many unrelated changes
- ❌ Use vague commit messages ("fix stuff", "update code")
- ❌ Commit commented-out code
- ❌ Commit debugging code or print statements
- ❌ Commit secrets or credentials

---

## 🔄 Pull Request Process

### 1. Create a Pull Request

**PR title format:**
- `feat: Add portfolio analytics dashboard`
- `fix: Handle null values in KLine data`
- `docs: Update API documentation for v2.0`

**PR description template:**
```markdown
## Description

[Provide a clear description of the changes]

## Related Issue

Closes #123
Related to #456

## Type of Change

- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Other (specify): _______

## Testing

- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Test coverage is 80%+
- [ ] Manual testing performed

## Checklist

- [ ] Code follows project coding standards
- [ ] Documentation updated
- [ ] Type hints added
- [ ] Error handling implemented
- [ ] Security considerations addressed
- [ ] Performance optimized
```

### 2. PR Review Process

**Typical timeline:**
1. **Initial review** - Within 2-3 business days
2. **Feedback** - Reviewers provide comments
3. **Updates** - Contributor addresses feedback
4. **Re-review** - Reviewers verify changes
5. **Approval** - PR is approved and merged

**What reviewers look for:**
- ✅ Code quality and readability
- ✅ Test coverage and quality
- ✅ Documentation completeness
- ✅ Adherence to coding standards
- ✅ Security considerations
- ✅ Performance implications
- ✅ Backward compatibility

### 3. Addressing Review Feedback

**When you receive feedback:**
```bash
# Make changes to address feedback
# ...

# Commit changes
git add .
git commit -m "fixup: address review feedback"

# Or amend previous commit
git add .
git commit --amend --no-edit

# Push changes
git push origin feature/add-portfolio-analytics
```

**Respond to comments:**
- Acknowledge feedback
- Ask clarifying questions if needed
- Explain your reasoning for changes
- Thank reviewers for their time

### 4. Merging Criteria

A PR will be merged when:
- ✅ All tests pass
- ✅ Code coverage requirement met (80%+)
- ✅ All review comments addressed
- ✅ CI/CD checks pass
- ✅ At least 2 approvals from maintainers (for significant changes)
- ✅ No unresolved conflicts

---

## 👥 Code Review Process

### As a Reviewer

**Review checklist:**
```
Code Quality
- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines)
- [ ] No deep nesting (>4 levels)
- [ ] Proper error handling
- [ ] No hardcoded values

Testing
- [ ] New code has tests
- [ ] Test coverage is adequate (80%+)
- [ ] Edge cases tested
- [ ] Test names are descriptive

Documentation
- [ ] Public functions have docstrings
- [ ] Complex logic is explained
- [ ] Type hints are complete

Security
- [ ] No hardcoded secrets
- [ ] User inputs validated
- [ ] SQL injection prevented
- [ ] Authentication/authorization correct

Performance
- [ ] Database queries optimized
- [ ] Appropriate caching used
- [ ] No unnecessary computations
```

**Provide constructive feedback:**
```markdown
# Good feedback
✅ "Consider using `with` statement for file handling to ensure proper cleanup."

✅ "This function is quite long (80 lines). Consider extracting the validation logic into a separate function."

✅ "Great job adding comprehensive tests! The edge cases are well covered."

# Avoid
❌ "This code is bad."
❌ "Why did you do it this way?"
❌ "Fix this."
```

### As a Contributor

**Responding to feedback:**
1. **Thank the reviewer** - Appreciate their time
2. **Acknowledge comments** - Confirm understanding
3. **Ask questions** - If feedback is unclear
4. **Make changes** - Address all feedback
5. **Push updates** - Notify reviewers

**Example responses:**
```markdown
Thank you for the review!

I've addressed all your comments:
- ✅ Extracted validation logic into separate function
- ✅ Added docstrings to public methods
- ✅ Improved error handling in the API endpoint

The changes are pushed to the branch. Please let me know if there's anything else!
```

---

## 🤝 Community Guidelines

### Our Values

**Respect**
- Treat everyone with respect and kindness
- Be considerate of different perspectives
- Avoid personal attacks or inflammatory language

**Inclusivity**
- Welcome contributors of all backgrounds
- Be patient with newcomers
- Use inclusive language

**Collaboration**
- Share knowledge openly
- Help others when you can
- Give credit where it's due

**Quality**
- Strive for excellence in your work
- Take pride in your contributions
- Learn from mistakes and feedback

### Code of Conduct

**Expected behavior:**
- ✅ Be respectful and professional
- ✅ Be welcoming to newcomers
- ✅ Provide constructive feedback
- ✅ Respect different viewpoints
- ✅ Focus on what's best for the project

**Unacceptable behavior:**
- ❌ Harassment or discrimination
- ❌ Personal attacks or insults
- ❌ Trolling or inflammatory comments
- ❌ Publishing others' private information
- ❌ Other conduct that would be reasonably considered inappropriate

### Reporting Issues

If you experience or witness unacceptable behavior:

1. **Contact maintainers** - Email: maintainers@alphaquant.com
2. **Provide details** - What happened, when, who was involved
3. **Confidentiality** - Reports will be handled confidentially
4. **Follow-up** - We'll investigate and take appropriate action

---

## ❓ FAQ

### How do I know what to work on?

**Look for:**
- Issues labeled `good first issue` - Great for beginners
- Issues labeled `help wanted` - Need contributors
- Issues with clear descriptions and acceptance criteria
- Features from the roadmap that interest you

**Ask:**
- Comment on an issue to express interest
- Ask for clarification if needed
- Discuss your approach before starting

### What if my PR is rejected?

**Possible reasons:**
- Doesn't align with project goals
- Implementation approach differs from project standards
- Already being worked on by someone else
- Better solution exists

**What to do:**
- Don't take it personally - it's about the code, not you
- Ask for feedback on how to improve
- Consider alternative approaches
- Look for other issues to work on

### How long does review take?

**Typical timeline:**
- Initial review: 2-3 business days
- Addressing feedback: Depends on changes needed
- Final approval: 1-2 business days after all feedback addressed

**Factors affecting review time:**
- Complexity of changes
- Reviewer availability
- Number of open PRs
- Quality of submission

### Can I work on multiple issues at once?

**Recommended:**
- Focus on one issue at a time
- Complete and merge before starting another
- This prevents conflicts and keeps context clear

**If working on multiple:**
- Use separate branches for each issue
- Keep branches up to date with main
- Clearly communicate progress on each

### What if I need help?

**Resources:**
- **GitHub Discussions** - Ask questions and get help
- **Issue comments** - Discuss specific issues
- **Documentation** - Check guides and examples
- **Codebase** - Study existing implementations

**Asking for help:**
```markdown
I'm working on issue #123 (Add portfolio analytics) and need help with:

1. I'm not sure how to calculate the Sharpe ratio correctly
2. The test is failing with this error: [error message]
3. Should this go in the service or the manager layer?

Here's what I've tried so far: [description]

Any guidance would be appreciated!
```

---

## 📚 Additional Resources

- 📖 [Development Setup](./05-development-setup.md) - Set up your environment
- 📏 [Coding Standards](./06-coding-standards.md) - Follow code style guidelines
- 🧪 [Testing Guide](./07-testing.md) - Write effective tests
- 🐛 [Debugging Guide](./09-debugging.md) - Debugging techniques
- 📖 [Project Structure](./02-project-structure.md) - Understand the codebase

---

## 🙏 Thank You!

Thank you for considering contributing to Alpha Quant Trader Pro! Your contributions help make this project better for everyone.

**Every contribution matters:**
- 🐛 Fixing a bug
- 📝 Improving documentation
- ✨ Adding a new feature
- 🧪 Writing tests
- 💬 Answering questions
- 🎨 Improving UI/UX

**We appreciate:**
- Your time and effort
- Your unique perspective
- Your willingness to learn and grow
- Your commitment to quality

**Happy coding! 🚀**

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
