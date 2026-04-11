"""
key_indicator_analyzer.py
qlsignalNew_20240808
Created by huanghx on 2024/8/23
Copyright © 2024 huanghx. All rights reserved.
"""
try:
    import backtrader as bt
except ImportError:
    bt = None
    # 定义一个空的Analyzer类，避免继承报错
    class MockAnalyzer:
        pass
    if not hasattr(bt, 'Analyzer'):
        # 创建一个假的bt模块结构
        import types
        bt = types.ModuleType('backtrader')
        bt.Analyzer = MockAnalyzer

import numpy as np
import pandas as pd

import qldef

"""
该指标器主要分析策略：累计收益率,年化收益率, 最大回撤，胜率, 夏普率, 凯利比率,近7天收益率, 
近30天收益率,佣金占资产比, 开平仓总次数等，通过这些重要指标反映出策略是否可行。
"""


class KeyIndicatorAnalyzer(bt.Analyzer):
    """
    关键指标分析器
    """

    def __init__(self):
        super(KeyIndicatorAnalyzer, self).__init__()
        # 年 period
        self.year_period = 252
        # 月 period
        self.month_period = 21
        # 周 period
        self.week_period = 5

        # 每日详情
        self.daily_details = []
        # 佣金
        self.commission = 0

        # 盈利
        self.win_list = []
        # 亏损
        self.loss_list = []

        # 重要指标
        self.key_indicators_df = pd.DataFrame(
            columns=[
                '策略', '累计收益率',
                '年化收益率', '最大回撤',
                '胜率', '夏普率', '凯利比率',
                '近7天收益率', '近30天收益率',
                '佣金占资产比', '开平仓总次数'
            ])
        # 每日详情指标，用于画图，{本策略：DataFrame, 基准名：DataFrame}，其中基准名，是最后传进来的基准名
        self.daily_chart_dict = dict()

    def get_analysis_data(self, benchmark_df, benchmark_key, benchmark_name='沪深300'):
        """
        获取分析数据，传基准数据过来，对比使用的。
        @param benchmark_df: 基准数据
        @param benchmark_key: 基准数据key
        @param benchmark_name: 基准名称
        """
        self._calculate_benchmark_indicators(benchmark_df, benchmark_key, benchmark_name)

        # 数据对齐（Data Alignment）
        # 1. Inner Join: 使用 pd.concat([..., axis=1, join='inner']) 将策略收益率和基准收益率按照日期索引进行合并。
        # 2. 取交集: inner 模式会只保留两者都有数据的公共日期。这样可以确保绘图时，每一个时间点上都同时存在策略数据和基准数据，彻底解决曲线错位或断裂的问题。
        if qldef.this_strategy_ind_key in self.daily_chart_dict and benchmark_key in self.daily_chart_dict:
            strategy_df = self.daily_chart_dict[qldef.this_strategy_ind_key]
            benchmark_chart_df = self.daily_chart_dict[benchmark_key]

            # 统一索引类型为 DatetimeIndex，确保 pd.concat 能正确对齐
            if not isinstance(strategy_df.index, pd.DatetimeIndex):
                strategy_df.index = pd.to_datetime(strategy_df.index)
            
            if not isinstance(benchmark_chart_df.index, pd.DatetimeIndex):
                benchmark_chart_df.index = pd.to_datetime(benchmark_chart_df.index)

            # Ensure indices are unique
            strategy_df = strategy_df[~strategy_df.index.duplicated(keep='last')]
            benchmark_chart_df = benchmark_chart_df[~benchmark_chart_df.index.duplicated(keep='last')]

            # 按照日期索引进行合并，取交集
            # 注意：这里我们只需要对齐后的索引
            aligned_df = pd.concat([strategy_df, benchmark_chart_df], axis=1, join='inner')
            common_index = aligned_df.index

            # 更新回字典
            self.daily_chart_dict[qldef.this_strategy_ind_key] = strategy_df.loc[common_index]
            self.daily_chart_dict[benchmark_key] = benchmark_chart_df.loc[common_index]

        return self.key_indicators_df, self.daily_chart_dict

    def _calculate_benchmark_indicators(self, benchmark_df, benchmark_key, benchmark_name):
        """
        计算基准的重要指标
        """
        series = benchmark_df['close']
        total_return = self.total_return(series)
        annual_return = self.annual_return(series)
        period = self.week_period
        recent_7_days_return = self.recent_period_return(series, period)
        period = self.month_period
        recent_30_days_return = self.recent_period_return(series, period)
        max_drawdown = self.max_drawdown(series)
        sharp_ratio = self.sharp_ratio(series)
        self.key_indicators_df.loc[len(self.key_indicators_df)] = [
            benchmark_name,
            total_return,
            annual_return,
            max_drawdown,
            None,
            sharp_ratio,
            None,
            recent_7_days_return,
            recent_30_days_return,
            None,
            None
        ]
        # 收益率走势
        df = pd.DataFrame(index=benchmark_df.index)
        s = self.yield_curve(series)
        # 插入一列
        df.insert(0, '收益率', s)
        df.index.name = '日期'
        self.daily_chart_dict[benchmark_key] = df

    def next(self):
        super(KeyIndicatorAnalyzer, self).next()
        # 当前日期
        current_date = self.strategy.data.datetime.date(0)
        # 总资产
        total_value = self.strategy.broker.getvalue()
        # 现金
        cash = self.strategy.broker.getcash()
        self.daily_details.append({
            '日期': current_date,
            '总资产': total_value,
            '现金': cash
        })

    def notify_trade(self, trade):
        # 交易关闭
        if trade.isclosed:
            # 佣金
            self.commission += trade.commission
            # 盈利与亏损
            if trade.pnlcomm >= 0:
                # 盈利加入盈利列表，利润 0 算盈利
                self.win_list.append(trade.pnlcomm)
            else:
                # 亏损加入亏损列表
                self.loss_list.append(trade.pnlcomm)

    def stop(self):
        # 胜率
        if self._win_times() + self._loss_times() == 0:
            win_rate = 0
        else:
            win_percent = self._win_times() / (self._win_times() + self._loss_times())
            win_rate = f'{round(win_percent * 100, 2)}%'

        df = pd.DataFrame(self.daily_details)

        # 累计收益率
        total_return = self.total_return(df['总资产'])

        # 年化收益率
        annual_return = self.annual_return(df['总资产'])

        # 最近7天收益率
        period = self.week_period
        recent_7_days_return = self.recent_period_return(df['总资产'], period)

        # 最近30天收益率
        period = self.month_period
        recent_30_days_return = self.recent_period_return(df['总资产'], period)

        # 最大回撤
        max_drawdown = self.max_drawdown(df['总资产'])
        # 计算夏普率
        sharp_ratio = self.sharp_ratio(df['总资产'])

        # 计算凯利比率
        kelly_percent = self.kelly_percent()

        # 佣金占总资产比
        commission_percent = self.commission_percent(df['总资产'])

        # 交易次数
        trade_times = self._win_times() + self._loss_times()

        # 本策略的指标
        self.key_indicators_df.loc[len(self.key_indicators_df)] = [
            '本策略',
            total_return,
            annual_return,
            max_drawdown,
            win_rate,
            sharp_ratio,
            kelly_percent,
            recent_7_days_return,
            recent_30_days_return,
            commission_percent,
            trade_times
        ]

        # 收益率走势
        df['收益率'] = self.yield_curve(df['总资产'])
        df.set_index('日期', inplace=True)
        # 每日详情指标输出
        self.daily_chart_dict[qldef.this_strategy_ind_key] = df

    def commission_percent(self, series) -> str:
        """
        佣金比例
        """
        percent = self.commission / series.iloc[0]
        return f'{round(percent * 100, 2)}%'

    def yield_curve(self, series) -> pd.Series:
        """
        收益率曲线
        """
        percent = (series - series.iloc[0]) / series.iloc[0]
        return round(percent * 100, 2)

    def total_return(self, series) -> str:
        """
        累计收益率
        """
        percent = (series.iloc[-1] - series.iloc[0]) / series.iloc[0]
        return f'{round(percent * 100, 2)}%'

    def annual_return(self, series) -> str:
        """
        年化收益率
        """
        percent = (series.iloc[-1] - series.iloc[0]) / series.iloc[0] / len(series) * self.year_period
        return f'{round(percent * 100, 2)}%'

    def recent_period_return(self, series, period) -> str:
        """
        最近一段时间收益率
        """
        if len(series) < period:
            return '0.00%'
        percent = (series.iloc[-1] - series.iloc[-period]) / series.iloc[-period]
        return f'{round(percent * 100, 2)}%'

    def max_drawdown(self, series) -> str:
        """
        最大回撤
        """
        s = (series - series.expanding().max()) / series.expanding().max()
        percent = s.min()
        return f'{round(percent * 100, 2)}%'

    def sharp_ratio(self, series) -> float:
        """
        夏普率
        夏普率：它的定义是投资收益与无风险收益之差的期望值，再除以投资标准差（即其波动性）
        夏普率越高，代表每承受一单位的风险，会产生较多的超额报酬。
        夏普率越低，代表每承受一单位的风险，会产生较少的超额报酬。
        夏普率为正，代表该投资报酬率高于无风险收益率，反之则低于无风险收益率。
        夏普率为负，代表该投资报酬率为负，亦即投资损失。
        夏普率越高越好，一般来说，夏普率大于1.0就是很不错的了。
        夏普率的计算公式：(Rp-Rf)/σp
        其中，Rp为投资组合的预期收益率，Rf为无风险收益率，σp为投资组合的标准差。
        公认默认无风险收益率为年化3%
        公式：sharpe = (回报率均值 - 无风险利率) / 回报率标准差
        """
        ret_s = series.pct_change().fillna(0)
        avg_ret_s = ret_s.mean()
        avg_risk_free = 0.03 / self.year_period
        sd_ret_s = ret_s.std()
        if sd_ret_s == 0:
            return 0.0
        sharp = (avg_ret_s - avg_risk_free) / sd_ret_s
        sharp_year = round(np.sqrt(self.year_period) * sharp, 3)
        return sharp_year

    def kelly_percent(self) -> str:
        """
        凯利公式
        定义：计算每次交易，投入资金占总资金的最优比率的分析者，
        声称每次交易按此比例投入资金得到的回报最大，风险最小。
        公式：K = W - [(1 - W) / R]
        其中，K为凯利公式，W胜率，R为盈亏比，即平均盈利除以平均损失。
        解读：如果凯利比率为负，说明该投资策略不可行，应放弃；如果凯利比率为正，
        例如 kelly_percent = 0.2，说明每次交易投入资金占总资金的20%为最优比率。
        未必可靠，只是个参考
        """
        win_times = self._win_times()
        loss_times = self._loss_times()
        if win_times > 0 and loss_times > 0:
            avg_win = np.average(self.win_list)  # 平均盈利
            avg_loss = abs(np.average(self.loss_list))  # 平均亏损，取绝对值
            win_loss_ratio = avg_win / avg_loss  # 盈亏比
            if win_loss_ratio == 0:
                kelly_percent = None
            else:
                sum_trades = win_times + loss_times
                win_percent = win_times / sum_trades  # 胜率
                # 计算凯利比率
                # 即每次交易投入资金占总资金的最优比率
                kelly_percent = win_percent - ((1 - win_percent) / win_loss_ratio)
        else:
            kelly_percent = None  # 信息不足

        return f'{round(kelly_percent * 100, 2)}%' if kelly_percent else None

    def _win_times(self):
        """
        盈利次数
        """
        return len(self.win_list)

    def _loss_times(self):
        """
        亏损次数
        """
        return len(self.loss_list)
