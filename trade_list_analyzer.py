"""
trade_list_analyzer.py
qlsignalNew_20240808
Created by huanghx on 2024/8/23
Copyright © 2024 huanghx. All rights reserved.
"""
try:
    import backtrader as bt
except ImportError:
    bt = None

import pandas as pd
import qldef


def get_trade_date(trade_list_df):
    """
    获取交易日期
    @return: 交易日期，获取某只股票的买卖日期，
    返回字典，key为股票名，value为(买入日期列表，卖出日期列表)
    """
    trade_dict = dict()
    if not trade_list_df.empty:
        # 分组，找出买卖日期
        grouped = trade_list_df.groupby('股票')
        for name, group in grouped:
            buy_date_list = list(group['买入日期'])
            sell_date_list = list(group['卖出日期'])
            # 判断是否有买卖日期
            if trade_dict.get(name) is None:
                trade_dict[name] = (buy_date_list, sell_date_list)
            else:
                trade_dict[name][0].extend(buy_date_list)
                trade_dict[name][1].extend(sell_date_list)
    return trade_dict


if bt is not None:
    class TradeListAnalyzer(bt.Analyzer):
        """
        交易列表分析器
        https://community.backtrader.com/topic/1274/closed-trade-list-including-mfe-mae-analyzer/2
        """

        def __init__(self):
            self.trades = []
            self.cum_profit = 0.0

        def get_analysis_data(self) -> tuple:
            """
            获取分析数据
            @return: 交易订单列表，交易日期
            """
            trade_list_df = pd.DataFrame(self.trades)
            return trade_list_df, get_trade_date(trade_list_df)

        def notify_trade(self, trade):
            if trade.isclosed:

                total_value = self.strategy.broker.getvalue()

                dir = 'short'
                if trade.history[0].event.size > 0: dir = 'long'

                pricein = trade.history[len(trade.history) - 1].status.price
                priceout = trade.history[len(trade.history) - 1].event.price
                datein = bt.num2date(trade.history[0].status.dt)
                dateout = bt.num2date(trade.history[len(trade.history) - 1].status.dt)
                if trade.data._timeframe >= bt.TimeFrame.Days:
                    datein = datein.date()
                    dateout = dateout.date()

                pcntchange = 100 * priceout / pricein - 100
                pnl = trade.history[len(trade.history) - 1].status.pnlcomm
                pnlpcnt = 100 * pnl / total_value
                barlen = trade.history[len(trade.history) - 1].status.barlen
                # 修复 ZeroDivisionError: float division by zero
                if barlen == 0:
                    pbar = 0.0
                else:
                    pbar = pnl / barlen
                self.cum_profit += pnl

                size = value = 0.0
                for record in trade.history:
                    if abs(size) < abs(record.status.size):
                        size = record.status.size
                        value = record.status.value

                highest_in_trade = max(trade.data.high.get(ago=0, size=barlen + 1))
                lowest_in_trade = min(trade.data.low.get(ago=0, size=barlen + 1))
                hp = 100 * (highest_in_trade - pricein) / pricein
                lp = 100 * (lowest_in_trade - pricein) / pricein
                if dir == 'long':
                    mfe = hp
                    mae = lp
                if dir == 'short':
                    mfe = -lp
                    mae = -hp

                self.trades.append(
                    {'订单': trade.ref,
                     '股票': trade.data._name,
                     # 'dir': dir,
                     '买入日期': datein,
                     '买价': round(pricein, 2),
                     '卖出日期': dateout,
                     '卖价': round(priceout, 2),
                     '收益率%': round(pcntchange, 2),
                     '利润': round(pnl, 2),
                     '利润%': round(pnlpcnt, 2),
                     '持仓期': barlen,
                     '单位利润': round(pbar, 2),
                     '累计利润': round(self.cum_profit, 2),
                     'MFE%': round(mfe, 2),
                     'MAE%': round(mae, 2)})

                exit_context = {}
                if hasattr(self.strategy, 'pending_exit_context'):
                    exit_context = self.strategy.pending_exit_context.pop(trade.data._name, {}) or {}

                if self.trades:
                    last_trade = self.trades[-1]
                    last_trade[qldef.sell_reason_key] = exit_context.get(qldef.sell_reason_key)
                    last_trade[qldef.sector_id_key] = exit_context.get(qldef.sector_id_key)
                    last_trade[qldef.industry_active_ratio_key] = exit_context.get(qldef.industry_active_ratio_key)
                    last_trade[qldef.industry_threshold_key] = exit_context.get(qldef.industry_threshold_key)
                    last_trade[qldef.industry_threshold_delta_key] = exit_context.get(qldef.industry_threshold_delta_key)
                    last_trade[qldef.industry_active_ratio_delta_1d_key] = exit_context.get(qldef.industry_active_ratio_delta_1d_key)
                    last_trade[qldef.regime_code_key] = exit_context.get(qldef.regime_code_key)
                    last_trade[qldef.dynamic_stop_ma_key] = exit_context.get(qldef.dynamic_stop_ma_key)
                    last_trade[qldef.price_key] = exit_context.get(qldef.price_key)
                    last_trade[qldef.ma_value_key] = exit_context.get(qldef.ma_value_key)
                    last_trade[qldef.signal_key] = exit_context.get(qldef.signal_key)
                    last_trade[qldef.strategy_name_key] = exit_context.get(qldef.strategy_name_key)
else:
    class TradeListAnalyzer:
        def __init__(self):
            pass
        def get_analysis_data(self) -> tuple:
            return pd.DataFrame(), {}
