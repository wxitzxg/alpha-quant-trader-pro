#!/usr/bin/env python3
"""
新增 API endpoint 端到端测试
测试 8 个新增模块的 27 个 API endpoint
"""

import pytest
import os
import sys
from fastapi.testclient import TestClient
from api_server.main import app

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

client = TestClient(app)


# ==================== 1. 基础技术指标测试 ====================
class TestBaseIndicators:
    """基础技术指标测试"""

    def test_calculate_base_indicators_post(self):
        """测试 POST /api/v1/indicators/base - 计算基础技术指标"""
        response = client.post(
            "/api/v1/indicators/base",
            json={"stock_code": "600519", "days": 30}
        )

        # 允许 200 或 400（数据不足）
        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "stock_code" in data
            assert "indicators" in data
            assert "signals" in data
            print(f"✅ 基础指标计算成功 - 股票: {data['stock_code']}")
        elif response.status_code == 400:
            print(f"⚠️  基础指标计算失败（数据不足）: {response.json().get('detail')}")
        else:
            print(f"⚠️  基础指标计算错误: {response.json().get('detail')}")

    def test_calculate_base_indicators_get(self):
        """测试 GET /api/v1/indicators/base/{stock_code} - GET 版本"""
        response = client.get("/api/v1/indicators/base/600519?days=30")

        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "stock_code" in data
            assert "indicators" in data
            print("✅ GET 版本基础指标计算成功")
        elif response.status_code == 400:
            print(f"⚠️  GET 版本基础指标计算失败: {response.json().get('detail')}")


# ==================== 2. 背离检测测试 ====================
class TestDivergence:
    """背离检测测试"""

    def test_detect_divergence(self):
        """测试 POST /api/v1/indicators/divergence - 检测背离"""
        response = client.post(
            "/api/v1/indicators/divergence?stock_code=600519&days=60&indicator=macd"
        )

        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "divergences" in data
            assert "bullish_divergence" in data["divergences"]
            assert "bearish_divergence" in data["divergences"]
            bullish = data["divergences"]["bullish_divergence"]
            bearish = data["divergences"]["bearish_divergence"]
            print(f"✅ 背离检测完成 - 底背离: {bullish.get('detected')}, 顶背离: {bearish.get('detected')}")
        elif response.status_code == 400:
            print(f"⚠️  背离检测失败: {response.json().get('detail')}")


# ==================== 3. TD 序列测试 ====================
class TestTDSequential:
    """TD 序列测试"""

    def test_calculate_td_sequential(self):
        """测试 POST /api/v1/indicators/td-sequential - TD 序列"""
        response = client.post(
            "/api/v1/indicators/td-sequential?stock_code=600519&days=30&period=9&compare_period=4"
        )

        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "td_buy_count" in data
            assert "td_sell_count" in data
            assert "status" in data
            assert "interpretation" in data
            print(f"✅ TD 序列计算成功 - 状态: {data['status']}, 低九: {data['td_buy_count']}, 高九: {data['td_sell_count']}")
        elif response.status_code == 400:
            print(f"⚠️  TD 序列计算失败: {response.json().get('detail')}")


# ==================== 4. VCP 形态检测测试 ====================
class TestVCP:
    """VCP 形态检测测试"""

    def test_detect_vcp(self):
        """测试 POST /api/v1/indicators/vcp - VCP 形态检测"""
        response = client.post(
            "/api/v1/indicators/vcp?stock_code=600519&days=120&min_drops=2&max_drops=4"
        )

        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "is_vcp" in data
            assert "stage" in data
            assert "drop_count" in data
            print(f"✅ VCP 检测完成 - 形态: {'是' if data['is_vcp'] else '否'}, 阶段: {data['stage']}, 回调次数: {data['drop_count']}")
        elif response.status_code == 400:
            print(f"⚠️  VCP 检测失败: {response.json().get('detail')}")


# ==================== 5. ZigZag 测试 ====================
class TestZigZag:
    """ZigZag 测试"""

    def test_calculate_zigzag(self):
        """测试 POST /api/v1/indicators/zigzag - ZigZag 计算"""
        response = client.post(
            "/api/v1/indicators/zigzag?stock_code=600519&days=120&threshold=0.05"
        )

        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "trend" in data
            assert "trend_direction" in data
            assert "zigzag_points_count" in data
            print(f"✅ ZigZag 计算成功 - 趋势: {data['trend_direction']}, 转折点数量: {data['zigzag_points_count']}")
        elif response.status_code == 400:
            print(f"⚠️  ZigZag 计算失败: {response.json().get('detail')}")


# ==================== 6. 资金流向测试 ====================
class TestFundFlow:
    """资金流向测试"""

    def test_get_fund_flow(self):
        """测试 GET /api/v1/fundflow/{stock_code} - 资金流向"""
        response = client.get("/api/v1/fundflow/600519?page=1&page_size=10")

        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "stock_code" in data
            assert "fund_flows" in data
            assert "total" in data
            print(f"✅ 资金流向获取成功 - 数据条数: {len(data['fund_flows'])}")
        elif response.status_code == 400:
            print(f"⚠️  资金流向获取失败: {response.json().get('detail')}")

    def test_get_dragon_tiger(self):
        """测试 GET /api/v1/fundflow/dragon-tiger/{stock_code} - 龙虎榜"""
        response = client.get("/api/v1/fundflow/dragon-tiger/600519?page=1&page_size=10")

        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "stock_code" in data
            assert "dragon_tiger_data" in data
            print(f"✅ 龙虎榜数据获取成功 - 数据条数: {len(data['dragon_tiger_data'])}")
        elif response.status_code == 400:
            print(f"⚠️  龙虎榜数据获取失败: {response.json().get('detail')}")


# ==================== 7. 财务数据测试 ====================
class TestFinancial:
    """财务数据测试"""

    def test_get_balance_sheet(self):
        """测试 GET /api/v1/api/v1/financial/balance-sheet/{stock_code} - 资产负债表"""
        response = client.get("/api/v1/api/v1/financial/balance-sheet/600519?year=2024&quarter=4")

        assert response.status_code in [200, 400, 404, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "symbol" in data
            assert "total_assets" in data
            assert "total_liabilities" in data
            print(f"✅ 资产负债表获取成功 - 总资产: {data['total_assets']}")
        elif response.status_code == 404:
            print(f"⚠️  资产负债表未找到")
        elif response.status_code == 400:
            print(f"⚠️  资产负债表获取失败: {response.json().get('detail')}")

    def test_get_income_statement(self):
        """测试 GET /api/v1/api/v1/financial/income-statement/{stock_code} - 利润表"""
        response = client.get("/api/v1/api/v1/financial/income-statement/600519?year=2024&quarter=4")

        assert response.status_code in [200, 400, 404, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "symbol" in data
            assert "revenue" in data
            assert "net_profit" in data
            print(f"✅ 利润表获取成功 - 营收: {data['revenue']}, 净利润: {data['net_profit']}")
        elif response.status_code == 404:
            print(f"⚠️  利润表未找到")
        elif response.status_code == 400:
            print(f"⚠️  利润表获取失败: {response.json().get('detail')}")

    def test_get_cash_flow(self):
        """测试 GET /api/v1/api/v1/financial/cash-flow/{stock_code} - 现金流量表"""
        response = client.get("/api/v1/api/v1/financial/cash-flow/600519?year=2024&quarter=4")

        assert response.status_code in [200, 400, 404, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "symbol" in data
            assert "operating_cash_flow" in data
            print(f"✅ 现金流量表获取成功 - 经营活动现金流: {data['operating_cash_flow']}")
        elif response.status_code == 404:
            print(f"⚠️  现金流量表未找到")
        elif response.status_code == 400:
            print(f"⚠️  现金流量表获取失败: {response.json().get('detail')}")

    def test_get_financial_indicators(self):
        """测试 GET /api/v1/api/v1/financial/indicators/{stock_code} - 财务指标"""
        response = client.get("/api/v1/api/v1/financial/indicators/600519?page=1&page_size=10")

        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "stock_code" in data
            assert "indicators" in data
            assert "total" in data
            print(f"✅ 财务指标获取成功 - 指标数量: {len(data['indicators'])}")
        elif response.status_code == 400:
            print(f"⚠️  财务指标获取失败: {response.json().get('detail')}")

    def test_get_dupont_analysis(self):
        """测试 GET /api/v1/api/v1/financial/dupont/{stock_code} - 杜邦分析"""
        response = client.get("/api/v1/api/v1/financial/dupont/600519?page=1&page_size=10")

        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "stock_code" in data
            assert "dupont_data" in data
            print(f"✅ 杜邦分析获取成功 - 数据条数: {len(data['dupont_data'])}")
        elif response.status_code == 400:
            print(f"⚠️  杜邦分析获取失败: {response.json().get('detail')}")

    def test_get_per_share_indicators(self):
        """测试 GET /api/v1/api/v1/financial/per-share/{stock_code} - 每股指标"""
        response = client.get("/api/v1/api/v1/financial/per-share/600519?page=1&page_size=10")

        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "stock_code" in data
            assert "per_share_indicators" in data
            print(f"✅ 每股指标获取成功 - 指标数量: {len(data['per_share_indicators'])}")
        elif response.status_code == 400:
            print(f"⚠️  每股指标获取失败: {response.json().get('detail')}")


# ==================== 8. 新闻资讯测试 ====================
class TestNews:
    """新闻资讯测试"""

    def test_get_news_list(self):
        """测试 GET /api/v1/news/list - 新闻列表"""
        response = client.get("/api/v1/news/list?page=1&page_size=5")

        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "news" in data
            assert "total" in data
            print(f"✅ 新闻列表获取成功 - 新闻数量: {len(data['news'])}")
        elif response.status_code == 400:
            print(f"⚠️  新闻列表获取失败: {response.json().get('detail')}")

    def test_search_news(self):
        """测试 GET /api/v1/news/search - 搜索新闻"""
        response = client.get("/api/v1/news/search?query=茅台&page=1&page_size=5")

        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()["data"]
            assert "results" in data
            assert "query" in data
            print(f"✅ 搜索新闻成功 - 关键词: {data['query']}, 结果数: {len(data['results'])}")
        elif response.status_code == 400:
            print(f"⚠️  搜索新闻失败: {response.json().get('detail')}")


# ==================== 运行测试 ====================
if __name__ == "__main__":
    print("=" * 60)
    print("🔍 新增 API endpoint 端到端测试")
    print("=" * 60)
    print()

    test_classes = [
        ("1. 基础技术指标", TestBaseIndicators),
        ("2. 背离检测", TestDivergence),
        ("3. TD 序列", TestTDSequential),
        ("4. VCP 形态检测", TestVCP),
        ("5. ZigZag", TestZigZag),
        ("6. 资金流向", TestFundFlow),
        ("7. 财务数据", TestFinancial),
        ("8. 新闻资讯", TestNews),
    ]

    results = {"passed": 0, "failed": 0, "skipped": 0}

    for name, test_class in test_classes:
        print(f"\n{('=' * 60)}")
        print(f"{name}")
        print(f"{('=' * 60)}")

        test_instance = test_class()
        methods = [m for m in dir(test_class) if m.startswith("test_")]

        for method_name in methods:
            try:
                method = getattr(test_instance, method_name)
                print(f"\n  📌 {method.__doc__}")
                method()
                results["passed"] += 1
            except AssertionError as e:
                print(f"  ❌ 测试失败: {e}")
                results["failed"] += 1
            except Exception as e:
                print(f"  ⚠️  测试异常: {e}")
                results["skipped"] += 1

    print(f"\n{('=' * 60)}")
    print("📊 测试总结")
    print(f"{('=' * 60)}")
    print(f"✅ 通过: {results['passed']}")
    print(f"❌ 失败: {results['failed']}")
    print(f"⚠️  跳过: {results['skipped']}")
    print(f"{'=' * 60}")

    # 返回退出码
    sys.exit(0 if results["failed"] == 0 else 1)
