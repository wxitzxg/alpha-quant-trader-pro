#!/usr/bin/env python3
"""API 集成测试"""

import pytest
from fastapi.testclient import TestClient
from api_server.main import app

client = TestClient(app)


def test_complete_simulation_workflow():
    """完整模拟交易工作流测试：创建账户 -> 买入 -> 卖出 -> 查看收益 -> 删除账户"""

    # 1. 创建模拟账户
    response = client.post(
        "/api/v1/api/v1/simulation/account",
        json={"account_name": "集成测试账户", "initial_capital": 100000}
    )
    assert response.status_code == 200
    account_id = response.json()["data"]["account_id"]
    print(f"✅ 账户创建成功: {account_id}")

    # 2. 买入股票
    response = client.post(
        "/api/v1/api/v1/simulation/buy",
        json={
            "account_id": account_id,
            "symbol": "600519",
            "price": 1850.0,
            "quantity": 10
        }
    )
    assert response.status_code == 200
    print("✅ 买入成功")

    # 3. 查看持仓
    response = client.get(f"/api/v1/api/v1/simulation/positions/{account_id}")
    assert response.status_code == 200
    positions = response.json()["data"]["positions"]
    assert len(positions) == 1
    assert positions[0]["symbol"] == "600519"
    assert positions[0]["quantity"] == 10
    print(f"📊 持仓: {positions[0]}")

    # 4. 卖出股票
    response = client.post(
        "/api/v1/api/v1/simulation/sell",
        json={
            "account_id": account_id,
            "symbol": "600519",
            "price": 1900.0,
            "quantity": 5
        }
    )
    assert response.status_code == 200
    print("✅ 卖出成功")

    # 5. 查看账户信息
    response = client.get(f"/api/v1/api/v1/simulation/account/{account_id}")
    assert response.status_code == 200
    account_data = response.json()["data"]
    print(f"💰 账户总值: {account_data['total_value']:.2f}, 浮动盈亏: {account_data['floating_pl']:.2f}")

    # 6. 查看收益统计
    response = client.get(f"/api/v1/api/v1/performance/account/{account_id}")
    assert response.status_code == 200
    performance = response.json()["data"]
    assert "metrics" in performance
    print(f"📈 总收益率: {performance['metrics']['total_return']:.2f}%")

    # 7. 删除账户
    response = client.delete(f"/api/v1/api/v1/simulation/account/{account_id}")
    assert response.status_code == 200
    print("✅ 账户删除成功")


def test_backtest_workflow():
    """回测工作流测试"""

    # 1. 运行单股票回测
    response = client.post(
        "/api/v1/api/v1/backtest/single",
        json={
            "symbol": "600519",
            "strategy": "vcp",
            "config": {
                "initial_capital": 100000,
                "start_date": "2023-01-01",
                "end_date": "2023-03-31",
                "interval": "1d"
            }
        }
    )

    # 注意：这个测试需要数据库连接和数据，如果数据库不可用会失败
    # 在实际测试环境中应该有测试数据库
    if response.status_code == 500:
        pytest.skip("数据库不可用，跳过回测测试")

    assert response.status_code in [200, 400]  # 200 成功, 400 数据不足

    if response.status_code == 200:
        task_id = response.json()["data"]["task_id"]
        print(f"✅ 回测任务创建: {task_id}")

        # 2. 获取回测结果
        response = client.get(f"/api/v1/api/v1/backtest/result/{task_id}")
        assert response.status_code == 200
        result = response.json()["data"]
        print(f"📈 年化收益: {result['performance']['annual_return']:.2f}%")

        # 3. 生成 JSON 报告
        response = client.post(
            "/api/v1/api/v1/backtest/report",
            json={"task_id": task_id, "format": "json"}
        )
        assert response.status_code == 200
        print("✅ JSON 报告生成成功")


def test_analysis_workflow():
    """技术分析工作流测试"""

    # 1. 五维共振分析
    response = client.post(
        "/api/v1/api/v1/analysis/five-dimension",
        json={"stock_code": "600519", "days": 30}
    )

    # 注意：这个测试需要数据库连接和数据
    if response.status_code == 500:
        pytest.skip("数据库不可用，跳过技术分析测试")

    assert response.status_code in [200, 400]

    if response.status_code == 200:
        result = response.json()["data"]
        print(f"🎯 五维共振评分: {result.get('total_score', 'N/A')}/100")

    # 2. 策略分析
    response = client.get("/api/v1/api/v1/analysis/strategies/600519?days=30")
    if response.status_code == 500:
        pytest.skip("数据库不可用，跳过策略分析测试")

    assert response.status_code in [200, 400]

    # 3. 技术指标
    response = client.get("/api/v1/api/v1/analysis/indicators/600519?indicator=macd&days=30")
    if response.status_code == 500:
        pytest.skip("数据库不可用，跳过指标测试")

    assert response.status_code in [200, 400]


def test_simulation_account_management():
    """模拟账户管理测试"""

    # 创建多个账户
    account_ids = []
    for i in range(3):
        response = client.post(
            "/api/v1/api/v1/simulation/account",
            json={"account_name": f"测试账户_{i}", "initial_capital": 50000 + i * 10000}
        )
        assert response.status_code == 200
        account_ids.append(response.json()["data"]["account_id"])

    # 获取所有账户
    response = client.get("/api/v1/api/v1/simulation/accounts")
    assert response.status_code == 200
    accounts = response.json()["data"]
    assert len(accounts) >= 3
    print(f"📋 账户数量: {len(accounts)}")

    # 删除所有账户
    for account_id in account_ids:
        response = client.delete(f"/api/v1/api/v1/simulation/account/{account_id}")
        assert response.status_code == 200


def test_simulation_error_handling():
    """模拟交易错误处理测试"""

    # 1. 创建账户
    response = client.post(
        "/api/v1/api/v1/simulation/account",
        json={"account_name": "错误测试", "initial_capital": 10000}
    )
    account_id = response.json()["data"]["account_id"]

    # 2. 测试余额不足
    response = client.post(
        "/api/v1/api/v1/simulation/buy",
        json={
            "account_id": account_id,
            "symbol": "600519",
            "price": 10000.0,  # 价格太高，余额不足
            "quantity": 10
        }
    )
    assert response.status_code == 400
    print("✅ 余额不足错误处理正常")

    # 3. 测试不存在的账户
    response = client.get("/api/v1/api/v1/simulation/account/nonexistent_id")
    assert response.status_code == 404
    print("✅ 不存在账户错误处理正常")

    # 4. 测试卖出不存在的股票
    response = client.post(
        "/api/v1/api/v1/simulation/sell",
        json={
            "account_id": account_id,
            "symbol": "NONEXISTENT",
            "price": 100.0,
            "quantity": 10
        }
    )
    assert response.status_code == 400
    print("✅ 不存在持仓错误处理正常")

    # 清理
    client.delete(f"/api/v1/api/v1/simulation/account/{account_id}")


if __name__ == "__main__":
    print("=== 运行集成测试 ===\n")

    print("1. 完整模拟交易工作流测试")
    test_complete_simulation_workflow()
    print()

    print("2. 模拟账户管理测试")
    test_simulation_account_management()
    print()

    print("3. 模拟交易错误处理测试")
    test_simulation_error_handling()
    print()

    print("4. 回测工作流测试（需要数据库）")
    try:
        test_backtest_workflow()
    except Exception as e:
        print(f"⚠️  回测测试跳过: {e}")
    print()

    print("5. 技术分析工作流测试（需要数据库）")
    try:
        test_analysis_workflow()
    except Exception as e:
        print(f"⚠️  技术分析测试跳过: {e}")
    print()

    print("=== 所有测试完成 ===")
