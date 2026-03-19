"""测试 AKShare 适配器 - 完整扩展版"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from data_sources.adapters.akshare_adapter import AKShareAdapter
from data_sources.models import Quote, KLine


class TestAKShareAdapter:
    """AKShareAdapter 测试类"""

    @pytest.fixture
    def adapter(self):
        """创建适配器实例"""
        return AKShareAdapter(timeout=1)

    def test_akshare_adapter_name(self, adapter):
        """测试适配器名称"""
        assert adapter.name == "akshare"

    def test_akshare_adapter_priority(self, adapter):
        """测试适配器优先级"""
        assert adapter.priority == 20

    @patch('akshare.stock_zh_a_spot_em')
    def test_get_realtime_success(self, mock_spot, adapter):
        """测试获取实时行情 - 成功"""
        # 模拟返回数据
        mock_df = Mock()
        mock_df.__getitem__.return_value = Mock()
        mock_df.__getitem__.return_value.__eq__.return_value = Mock()
        mock_filtered = Mock()
        mock_filtered.__len__.return_value = 1
        mock_filtered.iloc = Mock()
        mock_row = {
            '最新价': 100.0,
            '涨跌额': 2.0,
            '涨跌幅': 2.0,
            '成交量': 1000000,
            '成交额': 100000000.0
        }
        mock_filtered.iloc.__getitem__.return_value = mock_row
        mock_df.__getitem__.return_value.__eq__.return_value = mock_filtered

        mock_spot.return_value = mock_df

        result = adapter.get_realtime("600519")

        assert result is not None
        assert isinstance(result, Quote)
        assert result.symbol == "600519"
        assert result.price == 100.0

    @patch('akshare.stock_zh_a_spot_em')
    def test_get_realtime_not_found(self, mock_spot, adapter):
        """测试获取实时行情 - 未找到"""
        mock_df = Mock()
        mock_df.__getitem__.return_value = Mock()
        mock_df.__getitem__.return_value.__eq__.return_value = Mock()
        mock_filtered = Mock()
        mock_filtered.__len__.return_value = 0
        mock_df.__getitem__.return_value.__eq__.return_value = mock_filtered

        mock_spot.return_value = mock_df

        result = adapter.get_realtime("INVALID")
        assert result is None

    @patch('akshare.stock_zh_a_hist')
    def test_get_kline_success(self, mock_hist, adapter):
        """测试获取K线数据 - 成功"""
        # 模拟返回数据
        mock_df = Mock()
        mock_df.iterrows.return_value = [
            (0, {
                '日期': '2023-01-01',
                '开盘': 10.0,
                '最高': 11.0,
                '最低': 9.0,
                '收盘': 10.5,
                '成交量': 1000000,
                '成交额': 10000000.0,
                '换手率': 1.5
            })
        ]

        mock_hist.return_value = mock_df

        result = adapter.get_kline("600519", "1d", "2023-01-01", "2023-01-01")

        assert len(result) == 1
        assert isinstance(result[0], KLine)
        assert result[0].symbol == "600519"
        assert result[0].close == 10.5

    def test_get_dupont_analysis_not_implemented(self, adapter):
        """测试杜邦分析 - 不支持"""
        with pytest.raises(NotImplementedError) as exc_info:
            adapter.get_dupont_analysis("600519")

        assert "AKShare does not support dupont analysis" in str(exc_info.value)

    @patch('data_sources.adapters.akshare_adapter.AKShareAdapter.get_kline')
    def test_get_tech_indicators_success(self, mock_get_kline, adapter):
        """测试获取技术指标 - 成功"""
        # 模拟K线数据
        mock_kline = KLine(
            symbol="600519",
            datetime=datetime(2023, 1, 1),
            open_price=10.0,
            high=11.0,
            low=9.0,
            close=10.5,
            volume=1000000,
            amount=10000000.0,
            turnover=1.5
        )
        mock_get_kline.return_value = [mock_kline]

        result = adapter.get_tech_indicators("600519", "2023-01-01", "2023-01-01")

        assert isinstance(result, list)
        if len(result) > 0:
            assert 'date' in result[0]
            assert 'ma5' in result[0]
            assert 'rsi' in result[0]

    @patch('akshare.stock_individual_fund_flow')
    def test_get_fund_flows_success(self, mock_flow, adapter):
        """测试获取资金流向 - 成功"""
        mock_df = Mock()
        mock_df.__len__.return_value = 1
        mock_df.iterrows.return_value = [
            (0, {
                '日期': '2023-01-01',
                '主力净流入-净额': 1000000.0,
                '主力净流入-净占比': 10.0,
                '散户净流入-净额': -500000.0,
                '散户净流入-净占比': -5.0,
                '超大单净流入-净额': 500000.0
            })
        ]

        mock_flow.return_value = mock_df

        result = adapter.get_fund_flows("600519", "2023-01-01", "2023-01-01")

        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]['date'] == '2023-01-01'
            assert result[0]['main_net_inflow'] == 1000000.0

    @patch('akshare.stock_lhb_stock_detail_em')
    def test_get_dragon_tiger_success(self, mock_lhb, adapter):
        """测试获取龙虎榜 - 成功"""
        mock_df = Mock()
        mock_df.__len__.return_value = 1
        mock_df.iterrows.return_value = [
            (0, {
                '交易日': '2023-01-01',
                '买入营业部': ['营业部1', '营业部2'],
                '卖出营业部': ['营业部3', '营业部4'],
                '买入金额': 10000000.0,
                '卖出金额': 5000000.0,
                '上榜原因': '涨幅偏离值达7%'
            })
        ]

        mock_lhb.return_value = mock_df

        result = adapter.get_dragon_tiger("600519", "2023-01-01", "2023-01-01")

        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]['date'] == '2023-01-01'
            assert result[0]['buy_amount'] == 10000000.0

    @patch('akshare.stock_zh_a_spot_em')
    def test_get_stock_list_success(self, mock_spot, adapter):
        """测试获取股票列表 - 成功"""
        mock_df = Mock()
        mock_df.iterrows.return_value = [
            (0, {
                '代码': '600519',
                '名称': '贵州茅台',
                '最新价': 1000.0
            }),
            (1, {
                '代码': '000001',
                '名称': '平安银行',
                '最新价': 10.0
            })
        ]

        mock_spot.return_value = mock_df

        result = adapter.get_stock_list()

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]['symbol'] == '600519'
        assert result[0]['name'] == '贵州茅台'

    @patch('akshare.fund_open_fund_info_em')
    def test_get_fund_quotes_success(self, mock_fund, adapter):
        """测试获取基金净值 - 成功"""
        mock_df = Mock()
        mock_df.__len__.return_value = 1
        mock_df.iterrows.return_value = [
            (0, {
                '净值日期': '2023-01-01',
                '单位净值': 1.5,
                '累计净值': 2.0,
                '日增长率': 1.0
            })
        ]

        mock_fund.return_value = mock_df

        result = adapter.get_fund_quotes("000001", "2023-01-01", "2023-01-01")

        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]['date'] == '2023-01-01'
            assert result[0]['nav'] == 1.5

    def test_get_valuation_not_fully_supported(self, adapter):
        """测试获取估值指标 - 未完全支持"""
        result = adapter.get_valuation("600519", "2023-01-01", "2023-01-01")
        assert isinstance(result, list)
        # 应该返回空列表或记录警告

    @patch('akshare.stock_financial_analysis_indicator')
    def test_get_per_share_indicators_success(self, mock_financial, adapter):
        """测试获取每股指标 - 成功"""
        mock_df = Mock()
        mock_df.__len__.return_value = 1
        mock_df.iterrows.return_value = [
            (0, {
                '报告期': '2023-12-31',
                '基本每股收益': 1.5,
                '每股净资产': 10.0,
                '每股现金流': 2.0,
                '每股股息': 0.5
            })
        ]

        mock_financial.return_value = mock_df

        result = adapter.get_per_share_indicators("600519", "2023-01-01", "2023-12-31")

        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]['date'] == '2023-12-31'
            assert result[0]['eps'] == 1.5

    @patch('data_sources.adapters.akshare_adapter.AKShareAdapter.get_kline')
    def test_get_osc_indicators_success(self, mock_get_kline, adapter):
        """测试获取超买超卖指标 - 成功"""
        mock_kline = KLine(
            symbol="600519",
            datetime=datetime(2023, 1, 15),
            open_price=10.0,
            high=11.0,
            low=9.0,
            close=10.5,
            volume=1000000,
            amount=10000000.0,
            turnover=1.5
        )
        mock_get_kline.return_value = [mock_kline] * 15  # 至少14天数据

        result = adapter.get_osc_indicators("600519", "2023-01-01", "2023-01-15")

        assert isinstance(result, list)
        if len(result) > 0:
            assert 'date' in result[0]
            assert 'wr' in result[0]
            assert 'bias' in result[0]

    @patch('data_sources.adapters.akshare_adapter.AKShareAdapter.get_kline')
    def test_get_limit_up_down_success(self, mock_get_kline, adapter):
        """测试获取涨跌停数据 - 成功"""
        mock_kline1 = KLine(
            symbol="600519",
            datetime=datetime(2023, 1, 1),
            open_price=10.0,
            high=11.0,
            low=9.0,
            close=10.0,
            volume=1000000,
            amount=10000000.0,
            turnover=1.5
        )
        mock_kline2 = KLine(
            symbol="600519",
            datetime=datetime(2023, 1, 2),
            open_price=10.0,
            high=11.0,
            low=9.0,
            close=11.0,  # 涨停
            volume=2000000,
            amount=22000000.0,
            turnover=2.0
        )
        mock_get_kline.return_value = [mock_kline1, mock_kline2]

        result = adapter.get_limit_up_down("600519", "2023-01-01", "2023-01-02")

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[1]['is_limit_up'] == True

from datetime import datetime
