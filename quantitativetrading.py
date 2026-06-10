"""
quantitativetrading.py
qlsignalNew_20240808
Created by huanghx on 2024/8/16
Copyright © 2024 huanghx. All rights reserved.
"""
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

try:
    import backtrader as bt
except ImportError:
    bt = None

import pandas as pd

import dfutil
import drawingutil
import key_indicator_analyzer
import logutil
import qldef
import qloption
import trade_list_analyzer
import attribution_report
from strategy_config import StrategyConfig
from market_regime import get_market_regime, MarketRegime

# 获取所有股票代码列表
def get_stock_code_list():
    target_path = qldef.market_quotation_directory
    stock_code_list = qloption.database.get_code_list(target_path)
    return stock_code_list


# 获取指定行业板块下的所有股票代码列表
def get_board_stock_list(board_name):
    df_result = None
    target_path = qldef.market_quotation_directory
    df_board_target = qloption.database.read_file_csv(target_path, qldef.dc_board_target_file_name, None, None, None)
    if dfutil.not_empty(df_board_target):
        df_result = df_board_target[df_board_target[qldef.board_name_key] == board_name]
    return df_result


# 根据股票代码获取对应所属行业板块名称
def get_board_name(stock_code, df_board_target):
    board_name = None
    # 改为传参数，避免频繁读取文件耗时
    # target_path = qldef.market_quotation_directory
    # df_board_target = qloption.database.read_file_csv(target_path, qldef.dc_board_target_file_name, None, None, None)
    if dfutil.not_empty(df_board_target):
        # zh_0_board_target.csv 中没有 board_type 列，且该文件仅包含行业板块数据，故移除 board_type 过滤
        df_result = df_board_target[(df_board_target[qldef.target_key] == int(stock_code))]
        if dfutil.not_empty(df_result):
            df_result = df_result.reset_index(drop=True)  # 删除现有索引，并将其转换为默认的整数索引
            board_name = df_result.loc[0, qldef.board_name_key]  # 获取第0行'board_name'列表的值

    return board_name


# 获取指定日期的待交易（含买入和卖出）的股票数据
def get_tobe_traded_stocks(date: datetime):
    df_result = None
    cache_dir = qldef.stocks_tobe_traded_directory
    filter_str = str(dfutil.date_by_datetime(date))
    filelist = dfutil.get_all_files(cache_dir, filter_str)
    for file_path in filelist:
        df = qloption.database.read_single_big_csv(file_path)
        if dfutil.not_empty(df):
            if dfutil.empty(df_result):
                df_result = df
            else:
                df_result = pd.concat([df_result, df], ignore_index=True)

    return df_result


# 获取所有待交易的股票数据
# def get_all_tobe_traded_stocks(start_date, end_date):
#     df_result = None
#     cache_dir = qldef.stocks_tobe_traded_directory
#     date_list = dfutil.get_date_list(start_date, end_date)
#     for date in date_list:
#         filelist = dfutil.get_all_files(cache_dir, date)
#         for file_path in filelist:
#             df = qloption.database.read_single_big_csv(file_path)
#             if dfutil.not_empty(df):
#                 if dfutil.empty(df_result):
#                     df_result = df
#                 else:
#                     df_result = pd.concat([df_result, df], ignore_index=True)
#
#     return df_result


# 获取指定日期范围内的所有待交易（含买入和卖出）的股票代码列表
def get_active_stock_code_list(start_date: int, end_date: int):
    active_stocks = set()
    cache_dir = qldef.stocks_tobe_traded_directory
    
    # 简单的日期遍历
    date_list = dfutil.get_date_list(start_date, end_date)
    
    logutil.log.info(f"正在扫描交易信号 ({start_date}-{end_date}) 以优化加载股票数量...")
    
    for date in date_list:
        filter_str = str(date)
        filelist = dfutil.get_all_files(cache_dir, filter_str)
        
        for file_path in filelist:
            try:
                # 只读取 mtn 列以提高速度
                # 注意：如果文件为空或格式不对，pd.read_csv 可能会报错，这里做简单的异常处理
                df = pd.read_csv(file_path, usecols=[qldef.mtn_key])
                if dfutil.not_empty(df):
                    # 获取去重后的股票代码
                    stocks = df[qldef.mtn_key].dropna().unique()
                    for s in stocks:
                        # 确保转换为字符串并补齐6位（假设是A股代码）
                        # 注意：mtn列里可能混有非数字的字符串，如果只是股票代码应该没问题
                        s_str = str(s).strip()
                        if s_str:
                             # 简单清洗：如果是纯数字且长度小于6，补0；如果是6位或更长，保持原样
                             # 这里主要为了匹配 get_stock_code_list 返回的格式
                             if s_str.isdigit():
                                 s_str = s_str.zfill(6)
                             active_stocks.add(s_str)
            except Exception as e:
                # 忽略读取错误或列不存在的错误
                logutil.log.warning(f"读取交易信号文件失败: {file_path}, 错误: {e}")
                continue
                
    return sorted(list(active_stocks))


# 判断该股票在指定日期是否可以买入/卖出（减少频繁读取文件，提高效率）
# 返回值[bool, pd.DataFrame]：前面用于判断是否可以买入/卖出；后面用于判断买入股票数量，便于计算买入金额
def get_trade_state(date: int, df_all, board_target_df, stock_code, is_buy: bool = True) -> [bool, pd.DataFrame]:
    df_date_trade = None  # 对应日期下全部需要交易（买入/卖出）的个股数据列表
    trade_type_key = qldef.trade_type_key
    if dfutil.not_empty(df_all):
        df = df_all[df_all[qldef.date_key] == date]
        if dfutil.not_empty(df):
            if is_buy:
                # 买入：判断某列是否包含特定的字符串数据 str.contains(stock_code)
                df_date_trade = df[df[trade_type_key] == qldef.trade_buy_type]
                if dfutil.not_empty(df_date_trade):
                    df_date_code = df[(df[qldef.mtn_key].str.contains(stock_code))
                                      & (df[trade_type_key] == qldef.trade_buy_type)]
                else:
                    df_date_code = None
            else:
                # 卖出 - 先查找对应个股是否需要卖出，如果没有查找到，再判断该个股所在行业板块是否需要卖出

                # 查询“清仓”数据
                df_clear_trade = df[df[trade_type_key] == qldef.trade_clear_type]
                if dfutil.not_empty(df_clear_trade):
                    # 如果存在“清仓”数据，则直接返回
                    return [True, None]

                df_date_trade = df[df[trade_type_key] == qldef.trade_sell_type]
                df_date_code = df[(df[qldef.mtn_key].str.contains(stock_code))
                                  & (df[trade_type_key] == qldef.trade_sell_type)]
                if (dfutil.empty(df_date_code)) & (dfutil.not_empty(df_date_trade)):
                    # 判断该个股所在行业板块是否需要卖出：只要确定某个行业板块需要卖出，则整个行业板块下的个股全部卖出
                    board_name = get_board_name(stock_code, board_target_df)
                    # logutil.log.debug(f'{stock_code}所属“{board_name}”行业板块的个股都需要卖出')
                    df_date_code = df_date_trade[df_date_trade[qldef.board_name_key] == board_name]

            if dfutil.not_empty(df_date_code):
                return [True, df_date_trade]
            else:
                return [False, df_date_trade]

    return [False, df_date_trade]


# Backtrader框架的订单观察者：主要用于跟踪并可视化交易策略中的买单的创建和过期状态
if bt is not None:
    class OrderObserver(bt.Observer):
        lines = ('created', 'expired',)

        plotinfo = dict(plot=True, subplot=True, plotlinelabels=True)

        plotlines = dict(
            created=dict(marker='*', markersize=8.0, color='lime', fillstyle='full'),
            expired=dict(marker='s', markersize=8.0, color='red', fillstyle='full')
        )

        def next(self):
            for order in self._owner._orderspending:
                if order.data is not self.data:
                    continue

                if not order.isbuy():
                    continue

                # Only interested in "buy" orders, because the sell orders
                # in the strategy are Market orders and will be immediately
                # executed

                if order.status in [bt.Order.Accepted, bt.Order.Submitted]:
                    self.lines.created[0] = order.created.price

                elif order.status in [bt.Order.Expired]:
                    self.lines.expired[0] = order.created.price


    class my_strategy(bt.Strategy):
        params = (
            # ('smaperiod', 15),
            # ('limitperc', 1.0),
            # ('valid', 7),
            ('print', True),
        )

        stock_code_list = []  # 交易股票列表
        end_date_time = None  # 交易结束日期
        tobe_traded_stocks_dic = {}  # 以日期为key保存待交易的股票列表
        board_target_df = qloption.database.get_board_target_df()  # 行业板块数据
        disable_sector_cooldown = qldef.enable_ab_disable_sector_cooldown
        disable_dynamic_stop = qldef.enable_ab_disable_dynamic_stop
        disable_sig_specific = qldef.enable_ab_disable_sig_specific

        def log(self, txt, dt=None, is_save_log: bool = False):
            # Logging function fot this strategy
            dt = dt or self.data.datetime[0]
            if isinstance(dt, float):
                dt = bt.num2date(dt).date()  # no Hour mintue second
            if self.params.print:
                log_txt = f'{dt.isoformat()}, {txt}'
                if is_save_log:
                    # 保存到日志文件中
                    logutil.log.critical(log_txt)
                else:
                    # 不保存到日志文件中
                    logutil.log.debug(log_txt)

        @staticmethod
        def downcast(amount, lot):
            # 其中// 为整除，abs为求绝对值
            return abs(amount // lot * lot)

        @staticmethod
        def get_buy_cash(all_cash, stock_count, ratio=1.0, max_ratio=0.98):
            """
            获取单只股票买入金额 todo test ratio待确定方案 hhx
            注意：本策略是以日为单位运行，以第二日开盘价作为交割价。backtrader的运行机制是以购买的资金/今日收盘价，
            得到购买数量后第二日开盘买入。所以买卖时为避免第二日开盘价与今日收盘价的差价，不能以全仓买入。
            @param all_cash: 可以总现金
            @param stock_count: 待买入股票总数量
            @param ratio: 每次买入总金额占总可用现金的比率（比如0.5，即一半）
            @param max_ratio: 每次买入总金额占总可用现金的最大比率（即不能超过总金额的0.98）
            """
            buy_cash = all_cash * max_ratio
            if stock_count > 0:
                buy_cash = all_cash // stock_count  # ‘//’ 表示整除

            # 个股购买最大金额不能超过总结的30%
            # if buy_cash > all_cash * 0.3:
            #     buy_cash = all_cash * 0.3

            return buy_cash

        def _extract_signal_row_context(self, df_context):
            if dfutil.empty(df_context):
                return {}
            row = df_context.iloc[0]
            return {
                qldef.sector_id_key: row.get(qldef.sector_id_key),
                qldef.industry_active_ratio_key: row.get(qldef.industry_active_ratio_key),
                qldef.industry_threshold_key: row.get(qldef.industry_threshold_key),
                qldef.industry_threshold_delta_key: row.get(qldef.industry_threshold_delta_key),
                qldef.industry_active_ratio_delta_1d_key: row.get(qldef.industry_active_ratio_delta_1d_key),
                qldef.signal_key: row.get(qldef.signal_key)
            }

        def _set_exit_context(self, stock_code, context):
            self.pending_exit_context[stock_code] = context

        # 购入/卖出交易股票
        def trade_stock(self, current_datetime, df_tobe_traded_stocks, board_target_df, stock_code, data, is_buy=True):
            all_cash = 0
            if is_buy:
                # 查询全部资产 - 永远不要满仓买入某只股票
                # all_value = self.broker.getvalue()
                # 查询全部可用资产
                all_cash = self.broker.getcash()
                if all_cash <= 0:
                    return

            current_date_int = dfutil.date_by_datetime(current_datetime)
            trade_state = get_trade_state(current_date_int, df_tobe_traded_stocks, board_target_df,
                                          stock_code, is_buy=is_buy)
            if len(trade_state) > 1:
                is_can_trade = trade_state[0]
                df_date_trade = trade_state[1]
                if is_buy:
                    if all_cash > 0:
                        # todo test hhx
                        # if (((stock_code == '300111') or (stock_code == '300254') or (stock_code == '000908')
                        #      or (stock_code == '301168') or (stock_code == '002459'))
                        #         and (current_date_int == 20230105)):
                        #     logutil.log.debug('符合买入条件')

                        stock_count = 0
                        if dfutil.not_empty(df_date_trade):
                            stock_count = len(df_date_trade)
                        if is_can_trade:
                            # order_value = self.get_buy_cash(all_cash, stock_count)
                            order_value = 50000  # 1. 确认修改为: 5万
                            
                            # 检查资金是否充足 (Step 4.1 Debug)
                            if self.broker.getcash() < order_value:
                                self.log(f"⚠️ 资金不足，跳过买入: {stock_code} (需 {order_value}, 余 {self.broker.getcash():.2f})", is_save_log=True)
                                return # use return instead of continue
                                
                            close = data.close[0]
                            # 防止收盘价为0导致除零错误
                            if close > 0:
                                order_amount = self.downcast(order_value / close, 100)
                                if order_amount > 0:
                                    self.order = self.buy(data, size=order_amount)
                                    
                                    # 记录信号名称 (Phase 2 Add)
                                    if dfutil.not_empty(df_date_trade) and qldef.signal_key in df_date_trade.columns:
                                        try:
                                            # 取第一行信号（如果有多个，暂时取第一个）
                                            signal_name = df_date_trade.iloc[0][qldef.signal_key]
                                            if signal_name:
                                                self.position_signals[stock_code] = signal_name
                                                # self.log(f"记录信号: {stock_code} -> {signal_name}")
                                        except Exception as e:
                                            self.log(f"Error extracting signal name: {e}", is_save_log=True)

                            else:
                                self.log(f"警告: {stock_code} 收盘价为 {close}，跳过买入", is_save_log=True)

                else:
                    # 优先执行板块/清仓卖出逻辑
                    if is_can_trade and (not self.disable_sector_cooldown):
                        signal_ctx = self._extract_signal_row_context(df_date_trade)
                        signal_name = self.position_signals.get(stock_code) or signal_ctx.get(qldef.signal_key)
                        if df_date_trade is None:
                            # is_can_trade为True 且 df_date_trade == None，则表示触发了下降50%的条件，需要清仓
                            self.log(f"触发板块清仓策略: {stock_code}", is_save_log=True)
                        else:
                            self.log(f"触发板块轮动卖出: {stock_code}", is_save_log=True)
                        self._set_exit_context(stock_code, {
                            qldef.sell_reason_key: qldef.sell_reason_sector_cooldown,
                            qldef.regime_code_key: self.current_regime.name if hasattr(self, 'current_regime') else None,
                            qldef.dynamic_stop_ma_key: None,
                            qldef.price_key: data.close[0],
                            qldef.ma_value_key: None,
                            qldef.signal_key: signal_name,
                            qldef.strategy_name_key: signal_name,
                            qldef.sector_id_key: signal_ctx.get(qldef.sector_id_key),
                            qldef.industry_active_ratio_key: signal_ctx.get(qldef.industry_active_ratio_key),
                            qldef.industry_threshold_key: signal_ctx.get(qldef.industry_threshold_key),
                            qldef.industry_threshold_delta_key: signal_ctx.get(qldef.industry_threshold_delta_key),
                            qldef.industry_active_ratio_delta_1d_key: signal_ctx.get(qldef.industry_active_ratio_delta_1d_key)
                        })
                            
                        self.order = self.close(data)  # 清仓
                        if stock_code in self.position_signals:
                            del self.position_signals[stock_code]
                        return
                    
                    # Phase 2: 技术指标止盈止损逻辑 (Technical Exit)
                    # 仅当持有仓位时检查
                    position = self.broker.getposition(data)
                    if position.size > 0:
                        signal_name = self.position_signals.get(stock_code)
                        
                        # Phase 5: 动态获取策略规则
                        regime_name = self.current_regime.name if hasattr(self, 'current_regime') else None
                        rules = StrategyConfig.get_rule(signal_name, regime_name)
                        
                        # 计算盈亏比例
                        # position.price 是持仓均价
                        # data.close[0] 是当前收盘价
                        current_price = data.close[0]
                        cost_price = position.price
                        
                        if cost_price > 0:
                            pnl_pct = (current_price - cost_price) / cost_price
                            
                            # DEBUG: Visualize rule lookup (Phase 3)
                            self.log(f"Checking rules for {stock_code}: Signal={signal_name}, Rules={rules}, PnL={pnl_pct:.2%}", is_save_log=False)
                            
                            exit_reason = None
                            
                            # 1. 止损检查
                            if (not self.disable_sig_specific) and (pnl_pct <= rules['stop_loss']):
                                exit_reason = f"止损触发 (当前盈亏: {pnl_pct:.2%}, 阈值: {rules['stop_loss']:.2%})"
                            
                            # 2. 止盈检查
                            elif (not self.disable_sig_specific) and (pnl_pct >= rules['take_profit']):
                                exit_reason = f"止盈触发 (当前盈亏: {pnl_pct:.2%}, 阈值: {rules['take_profit']:.2%})"
                                
                            # 3. 均线离场检查 (MA Exit)
                            elif (not self.disable_dynamic_stop) and rules.get('ma_exit'):
                                ma_period = rules['ma_exit']
                                if ma_period > 0 and len(data) >= ma_period:
                                    # 手动计算SMA (Simple Moving Average)
                                    # data.close.get(size=N) 返回最近N个数据（包含当前）
                                    closes = data.close.get(size=ma_period)
                                    sma = sum(closes) / ma_period
                                    
                                    if current_price < sma:
                                        exit_reason = f"跌破MA{ma_period} (现价: {current_price:.2f} < MA: {sma:.2f})"
                            
                            if exit_reason:
                                reason_type = qldef.sell_reason_sig_specific
                                dynamic_stop_ma = None
                                ma_value = None
                                if "跌破MA" in exit_reason:
                                    reason_type = qldef.sell_reason_dynamic_stop
                                    dynamic_stop_ma = rules.get('ma_exit')
                                    if dynamic_stop_ma and len(data) >= dynamic_stop_ma:
                                        closes = data.close.get(size=dynamic_stop_ma)
                                        ma_value = sum(closes) / dynamic_stop_ma

                                self._set_exit_context(stock_code, {
                                    qldef.sell_reason_key: reason_type,
                                    qldef.regime_code_key: self.current_regime.name if hasattr(self, 'current_regime') else None,
                                    qldef.dynamic_stop_ma_key: dynamic_stop_ma,
                                    qldef.price_key: current_price,
                                    qldef.ma_value_key: ma_value,
                                    qldef.signal_key: signal_name,
                                    qldef.strategy_name_key: signal_name
                                })
                                self.log(f"技术指标离场 - {stock_code} ({signal_name or 'Default'}): {exit_reason}", is_save_log=True)
                                self.order = self.close(data)
                                if stock_code in self.position_signals:
                                    del self.position_signals[stock_code]
                                return

        def notify_order(self, order):
            stock_code = order.data.params.dataname['target'].iloc[0]
            trade_type = '买入'
            if order.issell():  # order.isbuy() 是否买入
                trade_type = '卖出'

            if order.status in [order.Submitted, order.Accepted]:
                # Buy/Sell order submitted/accepted to/by broker - Nothing to do
                # if order.status == order.Submitted:
                #     self.log(f'{trade_type}{stock_code}订单已提交', dt=order.created.dt)
                # else:
                #     self.log(f'{trade_type}{stock_code}订单已接受', dt=order.created.dt)

                self.order = order
                return

            if order.status in [order.Expired]:
                self.log(f'买入{stock_code}过期', is_save_log=True)

            elif order.status in [order.Completed]:
                # order.info['name'] 值为 AutoOrderedDict({'shape': AutoOrderedDict()})
                self.log(f"{trade_type}{stock_code}, 成交量：{order.executed.size}，成交价：{order.executed.price:.2f}，"
                         f"成交总额：{order.executed.value:.2f}, 交易佣金：{order.executed.comm:.2f}", is_save_log=True)

            elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                self.log(f'{trade_type}{stock_code}失败', is_save_log=True)

            # Sentinel to None: new orders allowed
            self.order = None

        # 记录交易收益情况（可省略，默认不输出结果）
        def notify_trade(self, trade):
            if trade.isclosed:
                # 注意：这里是个股的毛收益和净收益，不是所有股票的累计毛收益和累计净收益哦，但是市值和现金是累计的
                self.log(f'策略收益：毛收益：{trade.pnl:.2f}，净收益：{trade.pnlcomm:.2f}，市值：{self.broker.getvalue():.2f}，'
                         f'现金：{self.broker.getcash():.2f}', is_save_log=True)

        def __init__(self):
            self.position_signals = {}  # {stock_code: signal_name}
            self.pending_exit_context = {}
            # 计算简单移动平均线，如5/10/20日均线
            # Equivalent to -> sma = btind.SMA(self.data, period=self.p.smaperiod)
            # sma = btind.SMA(period=self.p.smaperiod)
            # CrossOver (1: up, -1: down) close / sma：计算 收盘价和smaperiod日移动均线的交叉点
            # self.buysell = btind.CrossOver(self.data.close, sma, plot=True)

            # 在 Strategy 中添加资金或获取当前资金
            # self.broker.add_cash(10000)  # 正数表示增加资金
            # self.broker.add_cash(-10000)  # 负数表示减少资金

            logutil.log.debug(f'当前可用资金：{self.broker.getcash()}')
            logutil.log.debug(f'当前总资产：{self.broker.getvalue()}')
            logutil.log.debug(f'当前持仓量：{self.broker.getposition(self.data).size}')
            logutil.log.debug(f'当前持仓成本：{self.broker.getposition(self.data).price}')

            # name = self.datas[0]._name  # 取值cerebro.adddata(data, name=stock_code)设置的name
            # 使用self.getdatabyname(股票name).datetime.date(0)，可知给定name的股票数据的起始日期
            # date_test = self.getdatabyname('301168').datetime.date(0)

            # Sentinel to None: new ordersa allowed
            self.order = None

        def prenext(self):
            """
            股票的上市日期各不相同，有些也退市了。在回测时，Backtrader会遍历所有的数据，选择有效期的交集开始执行next()。
            这时我们的选股策略就会因为数据的问题出现一段时间的空窗期，所以我们不要用next()来执行，而是用prenext()来执行，
            Backtrader会循环所有的数据，选择最小的那个日期作为开始日，执行prenext()，但是此时衍生出两个问题：
            1、这只股票的开始日，未必是另一支股票的开始日，这回导致另一只股票没数据
            2、一直股票可能在某一天退市了就没有数据了，但是有持仓，这就很尴尬了
            """
            self.next()

        """
        next方法：固定的函数，框架执行过程中会不断循环next()，过一个K线，执行一次next()，即会从开始日期到结束日期 按天回调
        
        注意：本策略是以日为单位运行，以第二日开盘价作为交割价。backtrader的运行机制是以购买的资金/今日收盘价，
        得到购买数量后第二日开盘买入。所以买卖时为避免第二日开盘价与今日收盘价的差价，不能以全仓买入。 且在最后
        一天不做任何下单买卖。

        注意：股票剔除是当下bar做出的决定，但是在后一根bar，也就是end_date进行的买卖。所以一定要放入后一根bar的
        开盘数据作为交割价，不然有未来函数。在策略购买卖中，需要规范在股票剔除日（end_date）必须卖出。
        """

        def next(self):
            # 获取当前日期 (YYYYMMDD integer format)
            current_date = self.datas[0].datetime.date(0)
            current_date_int = dfutil.date_by_datetime(current_date)
            
            # Phase 5: 获取市场状态 (Market Regime)
            # 默认使用沪深300指数进行判断
            self.current_regime = get_market_regime(current_date_int)
            regime_name = self.current_regime.name
            
            # 仅在状态变化时打印日志，避免刷屏
            if not hasattr(self, 'last_regime') or self.last_regime != self.current_regime:
                self.log(f"🌍 市场状态切换: {self.last_regime.name if hasattr(self, 'last_regime') else 'INIT'} -> {regime_name}", is_save_log=True)
                self.last_regime = self.current_regime

            # 判断是否有交易指令正在进行，如果正在进行，则直接返回
            if self.order:
                return

            i = 0
            while i < len(self.datas):
                data = self.datas[i]
                # logutil.log.debug(f'data[{i}]数据长度为{len(data.params.dataname)}')

                # 获取当前日期
                current_datetime = data.datetime.date(0)

                """
                回测最后一日不进行买卖
                因为该策略是以收盘价下单，以下单后的下一日开盘价作为交割价。最后一日不做任何的买卖。所以在回测的最后一日的
                前一天必须下单卖出股票，以便在最后一根 bar 的开盘价做为交割价卖出，不然出现未来函数

                如果 len(data) >= data.buflen()，则表示 已经遍历全部数据点，即是否回测最后一日。
                """
                # 判断是否回测最后一日的前一日，如果是则全部卖出
                # logutil.log.debug(
                #     f'已经遍历全部数据点（当前执行日期为：{current_datetime}，总共{len(data)} - {data.buflen()}日），即为回测最后一日')
                if len(data) == data.buflen() - 1:
                    self.order = self.close(data)  # 清仓卖出
                    i += 1
                    continue

                # todo 688593 从20230601开始有数据，导致每次取到的日期为最后一天 hhx
                if current_datetime == self.end_date_time:
                    i += 1
                    continue

                # 获取当前股票代码
                # stock_code = self.stock_code_list[i]
                stock_code = data.params.dataname['target'].iloc[0]

                current_date_int = dfutil.date_by_datetime(current_datetime)
                # logutil.log.debug(f'data[{i}]数据长度为{len(data.params.dataname)}，日期：{current_date_int}')
                df_tobe_traded_stocks = None
                
                # 直接从内存字典中获取 (已在运行前预加载)
                if current_date_int in self.tobe_traded_stocks_dic:
                    df_tobe_traded_stocks = self.tobe_traded_stocks_dic[current_date_int]
                
                # 下面的懒加载逻辑保留作为备份，但在预加载模式下通常不会触发
                if dfutil.empty(df_tobe_traded_stocks):
                    # 如果内存中没有（可能是预加载未覆盖到的边缘日期），尝试现场读取
                    # df_tobe_traded_stocks = get_tobe_traded_stocks(current_datetime)
                    # self.tobe_traded_stocks_dic[current_date_int] = df_tobe_traded_stocks
                    pass # 优化：预加载已覆盖所有日期，无需再次读取

                # 检查是否有持仓
                position = self.getposition(data).size  # position = self.position
                if position > 0:
                    # 有持仓
                    # 卖出
                    self.trade_stock(current_datetime, df_tobe_traded_stocks, self.board_target_df,
                                     stock_code, data, is_buy=False)
                    # 买入
                    self.trade_stock(current_datetime, df_tobe_traded_stocks, self.board_target_df,
                                     stock_code, data, is_buy=True)
                else:
                    # 空仓 - 买入
                    self.trade_stock(current_datetime, df_tobe_traded_stocks, self.board_target_df,
                                     stock_code, data, is_buy=True)

                i += 1
else:
    class OrderObserver:
        pass
    class my_strategy:
        pass


# 开始进行交易回测
def run_strategy(start_date: int, end_date: int, process_lock=None):
    if bt is None:
        logutil.log.warning("Backtrader not installed, skipping strategy run.")
        return

    logutil.log.debug(f'开始进行交易回测，回测日期：{start_date} - {end_date}')
    # 开始计时
    start_time = time.time()

    """
    对于 Broker、Trades、BuySell 3个观测器，默认是自动添加给 cerebro 的，可以在实例化大脑时，
    通过 stdstats 来控制：bt.Cerebro(stdstats=False) 表示可视化时，不展示 Broker、Trades、BuySell 观测器；
    反之，自动展示；默认情况下是自动展示。
    # stdstats=False表示不展示 Broker、Trades、BuySell 观测器
    cerebro = bt.Cerebro(stdstats=False)
    # 手动添加Broker、Trades和BuySell观测器
    cerebro.addobserver(bt.observers.Broker) # 手动添加Broker观测器
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell)
    """
    # 在进行大规模回测时，禁用默认观察者，也不要启用自定义观察者，提高运行速度
    # cerebro = bt.Cerebro()
    cerebro = bt.Cerebro(stdstats=False, maxcpus=None)
    # cerebro.broker.set_coo(True)  # 以次日开盘价成交（默认这个）
    # cerebro.broker.set_coc(True)  # 以订单创建日的收盘价成交
    # 设置初始资金和佣金
    cerebro.broker.setcash(100000000.0) # 2. 确认修改为: 1亿本金
    cerebro.broker.setcommission(commission=0.0005)  # 万五手续费
    # 滑点：双边各 0.0001（防止真实交易中，设定的交易价格不一定能交易，系统会自动按照滑点进行动态调整价格，以接近真实交易）
    cerebro.broker.set_slippage_perc(perc=0.0001)

    # stock_code_list = get_stock_code_list()
    
    # 优化：仅加载在此期间有交易信号的股票
    stock_code_list = get_active_stock_code_list(start_date, end_date)
    if stock_code_list:
        logutil.log.critical(f"🚀 优化模式：仅加载 {len(stock_code_list)} 只活跃股票 (总共 5000+)")
    else:
        logutil.log.warning("⚠️ 未找到任何交易信号文件 (stocks_tobe_traded)。回测将不执行任何交易。请确保已运行步骤3 (Industry Analysis)。")
        # 也可以选择回退到全量加载，但通常没信号加载了也没用
        # stock_code_list = get_stock_code_list() 

    # ---------------------------------------------------------
    # 性能优化：预加载所有交易信号数据到内存
    # 避免在 next() 循环中频繁进行文件 I/O
    # ---------------------------------------------------------
    logutil.log.info("正在预加载所有交易信号数据...")
    preload_start_time = time.time()
    date_list = dfutil.get_date_list(start_date, end_date)
    preloaded_signals = {}
    
    def load_signal(date_int):
        # 将整数日期转换为 datetime 对象用于 get_tobe_traded_stocks
        dt = dfutil.datetime_by_date(date_int)
        # 获取当天的数据
        df_signals = get_tobe_traded_stocks(dt)
        return date_int, df_signals

    # 自动检测 CPU 核心数，并针对 I/O 密集型任务适当调整，同时设置上限防止资源耗尽
    cpu_count = os.cpu_count() or 1
    # 建议设置为 cpu_count + 4，但不超过 20 (之前的 32 导致了崩溃)
    worker_limit = min(cpu_count + 4, 20)
    max_workers = min(worker_limit, len(date_list)) if len(date_list) > 0 else 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for date_int, df_signals in executor.map(load_signal, date_list):
            if dfutil.not_empty(df_signals):
                preloaded_signals[date_int] = df_signals
            
    # 将预加载的数据赋值给策略类变量
    my_strategy.tobe_traded_stocks_dic = preloaded_signals
    logutil.log.critical(f"✅ 交易信号预加载完成，耗时: {time.time() - preload_start_time:.2f}秒，覆盖 {len(preloaded_signals)} 个交易日")
    # ---------------------------------------------------------

    total_stocks = len(stock_code_list)
    print(f"📊 共加载 {total_stocks} 只股票，开始添加数据到回测引擎...")
    
    # 尝试导入 tqdm，如果不可用则使用简单计数
    try:
        from tqdm import tqdm
        pbar = tqdm(stock_code_list, desc="添加回测数据", unit="stock")
        iterator = pbar
    except ImportError:
        iterator = stock_code_list
        pbar = None

    loaded_datas = []

    def load_stock_data(stock_code):
        # 提取真实的股票代码 (例如从 "zh.000028.国药一致" 提取 "000028")
        real_stock_code = stock_code
        if not str(stock_code).isdigit() and '.' in str(stock_code):
            parts = str(stock_code).split('.')
            for part in parts:
                if len(part) == 6 and part.isdigit():
                    real_stock_code = part
                    break

        try:
            # 显式禁用 fallback，提高性能
            stock_df = qloption.database.get_code_daily_quote_data(real_stock_code, start_date,
                                                                   end_date, qldef.market_quotation_directory,
                                                                   allow_fallback=False)
        except Exception as e:
            # logutil.log.critical(f"获取股票 {stock_code} 数据失败: {e}")
            return None

        if dfutil.not_empty(stock_df):
            # 确保 stock_df 索引是 DatetimeIndex
            if not isinstance(stock_df.index, pd.DatetimeIndex):
                try:
                    stock_df.index = pd.to_datetime(stock_df.index)
                except Exception as e:
                    return None
            
            start_date_time = dfutil.datetime_by_date(start_date)
            end_date_time = dfutil.datetime_by_date(end_date)
            
            # 确保数据包含回测所需的时间段
            if stock_df.index[-1] < pd.Timestamp(start_date_time) or stock_df.index[0] > pd.Timestamp(end_date_time):
                return None
                
            # 检查列名
            if 'open' not in stock_df.columns and 'Open' in stock_df.columns:
                stock_df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume', 'OpenInterest': 'openinterest'}, inplace=True)
            
            return stock_code, stock_df
        return None

    # 并行加载股票数据
    # 自动检测 CPU 核心数，并针对 I/O 密集型任务适当调整，同时设置上限防止资源耗尽
    cpu_count = os.cpu_count() or 1
    # 建议设置为 cpu_count + 4，但不超过 20 (之前的 32 导致了崩溃)
    worker_limit = min(cpu_count + 4, 20)
    max_workers = min(worker_limit, len(stock_code_list)) if len(stock_code_list) > 0 else 1
    logutil.log.info(f"正在并行加载 {len(stock_code_list)} 只股票数据 (使用 {max_workers} 个线程)...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for result in executor.map(load_stock_data, stock_code_list):
            if pbar:
                pbar.update(1)
            if result is not None:
                loaded_datas.append(result)

    if pbar:
        pbar.close()

    loaded_count = 0
    for stock_code, stock_df in loaded_datas:
        start_date_time = dfutil.datetime_by_date(start_date)
        end_date_time = dfutil.datetime_by_date(end_date)
        try:
            data = bt.feeds.PandasData(dataname=stock_df, fromdate=start_date_time, todate=end_date_time)
            cerebro.adddata(data, name=stock_code)
            my_strategy.stock_code_list.append(stock_code)
            loaded_count += 1
            
            # 更新最晚结束日期
            end_date_time = datetime.date(stock_df.index[-1])
            if (my_strategy.end_date_time is None) or (end_date_time > my_strategy.end_date_time):
                my_strategy.end_date_time = end_date_time
        except Exception as e:
            logutil.log.critical(f"Backtrader 加载数据失败 {stock_code}: {e}")
            continue

        if pbar is None and (loaded_count % 100 == 0):
             print(f"\r进度: {loaded_count}/{total_stocks}", end="")
    
    print(f"\n✅ 数据添加完成，共加载 {loaded_count}/{total_stocks} 只有效股票")

    # data = cerebro.datas[0]      # 可以取值
    # data1 = cerebro.datas[1]     # 可以取值
    # data = my_strategy.datas[0]  #  报错
    # dat1 = my_strategy.datas[1]

    # cerebro.addobserver(bt.observers.TimeReturn)  # 添加观察者
    cerebro.addobserver(OrderObserver)  # 添加观察者
    cerebro.addstrategy(my_strategy)  # 添加策略

    """
    1、bt.analyzers.Returns：主要用于计算和记录资产的收益率，它通过分析数据来计算资产的回报情况，提供关于资产收益的详细分析。
    这种分析器适合用于评估策略的盈利能力，帮助用户了解策略在不同时间段的收益情况。
    2、bt.observers.TimeReturn 则更侧重于实时监控和绘图，它不仅能够计算指标，还能在策略中调用并绘制图表，
    从而更好地进行实时监控。
    3、bt.analyzers.TimeReturn 返回业绩基准的收益率,在此之前,需要确保已经将业绩基准的行情数据adddata给大脑
    """
    # tframes = dict(
    #     days=bt.TimeFrame.Days,
    #     weeks=bt.TimeFrame.Weeks,
    #     months=bt.TimeFrame.Months,
    #     years=bt.TimeFrame.Years)
    # cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='mysharpe')
    # cerebro.addanalyzer(bt.analyzers.DrawDown, _name='mydrown')
    # cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='myannualreturn')
    # cerebro.addanalyzer(bt.analyzers.SQN, _name='mysqn')
    # cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='mytradeanalyzer')
    # cerebro.addanalyzer(bt.analyzers.PositionsValue, _name='mypositionvalue')
    # cerebro.addanalyzer(bt.analyzers.Returns, _name='myreturns')
    # cerebro.addanalyzer(bt.analyzers.LogReturnsRolling, timeframe=tframes['years'], _name='mylogreturnsrolling')
    # cerebro.addanalyzer(bt.analyzers.Transactions, _name='mytransactions')
    # cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='_TimeReturn')  # 累计收益曲线

    cerebro.addanalyzer(key_indicator_analyzer.KeyIndicatorAnalyzer, _name='key_indicator')
    cerebro.addanalyzer(trade_list_analyzer.TradeListAnalyzer, _name='trade_list')

    # 增加进度日志：每隔一定天数打印一次
    class ProgressObserver(bt.Observer):
        lines = ('count',)  # 必须定义 lines，否则会报错 ValueError: max() arg is an empty sequence
        plotinfo = dict(plot=False)
        params = (('interval', 30),)  # 每30天打印一次
        
        def next(self):
            if len(self) % self.params.interval == 0:
                dt = self.data.datetime.date(0)
                logutil.log.info(f"回测进度: 当前日期 {dt}")

    cerebro.addobserver(ProgressObserver)

    logutil.log.critical(f"初始总资金：{qldef.start_total_cash}，回测时间:{start_date}-{end_date}")
    results = cerebro.run(tradehistory=True)  # 注意：一定要打开，记录交易历史，用于生成自定义订单列表
    balance = cerebro.broker.getvalue()
    logutil.log.critical(f"剩余总资金：{balance}，回测时间:{start_date}-{end_date}")

    # 得到分析指标数据
    if not results:
        logutil.log.critical("回测未生成任何结果，可能是因为没有加载任何有效数据。")
        return

    result = results[0]
    
    # ---------------------------------------------------------
    # 性能优化：优化基准数据加载，减少不必要的文件读取
    # ---------------------------------------------------------
    benchmark_df = None
    try:
        benchmark_df = qloption.database.get_code_daily_quote_data(
            qldef.hs300_code1, 
            start_date, 
            end_date,
            qldef.market_quotation_directory,
            filter_str='hs300.csv'
        )
    except Exception as e:
        logutil.log.warning(f"加载基准数据(沪深300)失败: {e}")
        
    # 如果没有基准数据，创建一个空的DataFrame以避免报错
    if dfutil.empty(benchmark_df):
        # import pandas as pd
        logutil.log.warning("未找到基准数据，将使用空数据进行对比")
        # 创建一个带有必要列的空DataFrame
        benchmark_df = pd.DataFrame(columns=['close'])
        # 填充与策略相同的日期索引
        dates = result.data.datetime.get(ago=0, size=len(result.data))
        if dates:
            dt_index = [bt.num2date(d).date() for d in dates]
            benchmark_df = pd.DataFrame(index=pd.to_datetime(dt_index), columns=['close'])
            benchmark_df['close'] = 0.0 # 填充默认值
            
    key_indicators_df, daily_details_dict = result.analyzers.key_indicator.get_analysis_data(
        benchmark_df, qldef.reference_ind_key, '沪深300')
    # 得到交易列表
    trade_list_df, trade_dict = result.analyzers.trade_list.get_analysis_data()
    logutil.log.critical(f"关键指标：{key_indicators_df}")

    # Save key indicators and trade list to CSV
    try:
        if not os.path.exists(qldef.quantitative_result_directory):
            os.makedirs(qldef.quantitative_result_directory)

        summary_file_name = f"results_zh_{start_date}_{end_date}_summary.csv"
        summary_file_path = os.path.join(qldef.quantitative_result_directory, summary_file_name)
        key_indicators_df.to_csv(summary_file_path, index=False, encoding='utf-8-sig')
        logutil.log.critical(f"关键指标已保存至: {summary_file_path}")

        trades_file_name = f"results_zh_{start_date}_{end_date}_trades.csv"
        trades_file_path = os.path.join(qldef.quantitative_result_directory, trades_file_name)
        trade_list_df.to_csv(trades_file_path, index=False, encoding='utf-8-sig')
        logutil.log.critical(f"交易列表已保存至: {trades_file_path}")
        attribution_report.generate_attribution_reports(trades_file_path, qldef.quantitative_result_directory, start_date, end_date)

    except Exception as e:
        logutil.log.error(f"保存回测结果CSV失败: {e}")
    # logutil.log.debug(f"收益走势：{daily_details_dict}")
    # 参考指数
    # logutil.log.debug(f"交易订单列表：{trade_list_df}")
    # logutil.log.debug(f"交易股票以及对应的买卖点：{trade_dict}")

    this_strategy_df = daily_details_dict[qldef.this_strategy_ind_key]
    reference_df = daily_details_dict[qldef.reference_ind_key]

    # 绘制收益率曲线 并 插入关键指标的表格
    chart_file_name = f"results_zh_{start_date}_{end_date}_chart.png"
    chart_file_path = os.path.join(qldef.quantitative_result_directory, chart_file_name)
    
    drawingutil.draw_yield_curve_chart(this_strategy_df, reference_df, key_indicators_df, save_path=chart_file_path)
    logutil.log.critical(f"收益率曲线图已保存至: {chart_file_path}")

    # thestrat = results[0]
    # logutil.log.debug(f'Sharpe Ratio: {thestrat.analyzers.mysharpe.get_analysis()}')
    # logutil.log.debug(f'DrawDown: {thestrat.analyzers.mydrown.get_analysis()}')
    # logutil.log.debug(f'AnnualReturn: {thestrat.analyzers.myannualreturn.get_analysis()}')
    # logutil.log.debug(f'SQN: {thestrat.analyzers.mysqn.get_analysis()}')
    # logutil.log.debug(f'TradeAnalyzer: {thestrat.analyzers.mytradeanalyzer.get_analysis()}')
    # logutil.log.debug(f'PositionsValue: {thestrat.analyzers.mypositionvalue.get_analysis()}')
    # logutil.log.debug(f'Returns: {thestrat.analyzers.myreturns.get_analysis()}')
    # logutil.log.debug(f'LogReturnsRolling: {thestrat.analyzers.mylogreturnsrolling.get_analysis()}')
    # logutil.log.debug(f'Transactions: {thestrat.analyzers.mytransactions.get_analysis()}')
    # logutil.log.debug(f'TimeReturn: {thestrat.analyzers._TimeReturn.get_analysis()}')
    # cerebro.plot()

    # # 清除交易记录
    # cerebro.strategies[0].order.trades.clear()
    # # 打印清除记录后的状态
    # for trade in cerebro.strategies[0].order.trades:
    #     cerebro.strategies[0].log('Trade after clear: %.2f' % trade.pnl)

    # 结束计时
    end_time = time.time()
    execution_time = end_time - start_time
    logutil.log.critical(f'交易回测完成，回测日期：{start_date} - {end_date}，总耗时长：{execution_time} 秒')
