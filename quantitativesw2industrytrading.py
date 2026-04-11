"""
quantitativesw2industrytrading.py
qlsignalNew_20240808
Created by huanghx on 2024/8/16
Copyright © 2024 huanghx. All rights reserved.
"""
import os
import time
from datetime import datetime

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


# 获取所有申万二级行业代码列表
def get_sw2_industry_code_list():
    target_path = qldef.market_SYWGIndexQuote_directory
    sw2_industry_code_list = qloption.database.get_code_list(target_path)
    return sw2_industry_code_list


# def get_board_target_df():
#     target_path = qldef.market_SYWGIndexQuote_directory
#     board_target_df = qloption.database.read_file_csv(target_path, qldef.sw_second_industry_file_name, None, None, None)
#     return board_target_df


# 根据行业代码获取对应所属行业板块名称
def get_board_name(board_code, board_target_df):
    board_name = ''
    if dfutil.not_empty(board_target_df):
        df_board_code = board_target_df[board_target_df[qldef.board_code_key] == int(board_code)]
        if dfutil.not_empty(df_board_code):
            df_board_code = df_board_code.reset_index(drop=True)  # 删除现有索引，并将其转换为默认的整数索引
            board_name = df_board_code.at[0, qldef.board_name_key]  # 获取第0行的board_name值

    return board_name


# 根据行业代码获取对应所属行业板块名称
def get_board_df(board_code, board_target_df):
    df_result = None
    if dfutil.not_empty(board_target_df):
        df_result = board_target_df[(board_target_df[qldef.sw_board_code_key] == int(board_code))
                                    & (board_target_df.board_type == qldef.industry_key)]
        if dfutil.not_empty(df_result):
            df_result = df_result.reset_index(drop=True)  # 删除现有索引，并将其转换为默认的整数索引

    return df_result


# 获取对应申万2级行业的日度行情数据
def get_industry_daily_quote_data(board_code, start_date: int, end_date: int, filter_str="1d_ind.csv"):
    target_path = qldef.market_SYWGIndexQuote_directory
    df = qloption.database.get_code_daily_quote_data(board_code, start_date, end_date, target_path, filter_str)
    return df


# 获取指定日期的待交易（含买入和卖出）的股票数据
def get_tobe_traded_stocks(date: datetime):
    df_result = None
    cache_dir = qldef.stocks_tobe_traded_directory
    filelist = dfutil.get_all_files(cache_dir, str(dfutil.date_by_datetime(date)))
    for file_path in filelist:
        df = qloption.database.read_single_big_csv(file_path)
        if dfutil.not_empty(df):
            if dfutil.empty(df_result):
                df_result = df
            else:
                df_result = pd.concat([df_result, df], ignore_index=True)

    return df_result


def get_trade_state(date: int, df_all, board_target_df, board_code, is_buy: bool = True) -> [bool, pd.DataFrame]:
    """
    判断该行业板块在指定日期是否可以买入/卖出（减少频繁读取文件，提高效率）
    @param date: 日期
    @param df_all: 待交易的股票列表
    @param board_target_df: 行业板块数据列表
    @param board_code: 行业板块代码
    @param is_buy: 买入/卖出
    返回值[bool, pd.DataFrame]：前面用于判断是否可以买入/卖出；后面用于判断买入股票数量，便于计算买入金额
    """
    board_name = get_board_name(board_code, board_target_df)
    df_date_trade = None  # 对应日期下全部需要交易（买入/卖出）的个股数据列表
    trade_type_key = qldef.trade_type_key
    if dfutil.not_empty(df_all):
        df = df_all[df_all[qldef.date_key] == date]
        if dfutil.not_empty(df):
            if is_buy:
                # 买入：判断某列是否包含特定的字符串数据 str.contains(board_code)
                df_date_trade = df[df[trade_type_key] == qldef.trade_buy_type]
                if dfutil.not_empty(df_date_trade):
                    df_date_code = df_date_trade[(df_date_trade[qldef.sw_board_code_key] == board_code)
                                                 | (df_date_trade[qldef.sw_board_name_key] == board_name)
                                                 | (df_date_trade[qldef.sw_board_name_key].str.contains(board_name))]
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
                if dfutil.not_empty(df_date_trade):
                    df_date_code = df_date_trade[(df_date_trade[qldef.sw_board_code_key] == board_code)
                                                 | (df_date_trade[qldef.sw_board_name_key] == board_name)
                                                 | (df_date_trade[qldef.sw_board_name_key].str.contains(board_name))]
                else:
                    df_date_code = None

                # if (dfutil.empty(df_date_code)) & (dfutil.not_empty(df_date_trade)):
                #     # 判断该个股所在行业板块是否需要卖出：只要确定某个行业板块需要卖出，则整个行业板块下的个股全部卖出
                #     board_name = get_board_name(board_code)
                #     df_date_code = df_date_trade[df_date_trade[qldef.board_name_key] == board_name]

            if dfutil.not_empty(df_date_code):
                return [True, df_date_trade]
            else:
                return [False, df_date_trade]

    return [False, df_date_trade]


def get_trade_state2(date: int, df_all, board_target_df, board_code, is_buy: bool = True) -> [bool, pd.DataFrame]:
    """
    判断该行业板块在指定日期是否可以买入/卖出（减少频繁读取文件，提高效率）
    @param date: 日期
    @param df_all: 待交易的股票列表
    @param board_target_df: 行业板块数据列表
    @param board_code: 行业板块代码
    @param is_buy: 买入/卖出
    返回值[bool, pd.DataFrame]：前面用于判断是否可以买入/卖出；后面用于判断买入股票数量，便于计算买入金额
    """
    df_date_trade = None  # 对应日期下全部需要交易（买入/卖出）的个股数据列表
    trade_type_key = qldef.trade_type_key
    if dfutil.not_empty(df_all):
        df = df_all[df_all[qldef.date_key] == date]
        if dfutil.not_empty(df):
            if is_buy:
                # 买入：判断某列是否包含特定的字符串数据 str.contains(board_code)
                df_date_trade = df[df[trade_type_key] == qldef.trade_buy_type]
            else:
                # 查询“清仓”数据
                df_clear_trade = df[df[trade_type_key] == qldef.trade_clear_type]
                if dfutil.not_empty(df_clear_trade):
                    # 如果存在“清仓”数据，则直接返回
                    return [True, None]

                df_date_trade = df[df[trade_type_key] == qldef.trade_sell_type]

            df_date_code = None
            if dfutil.not_empty(df_date_trade):
                board_df = get_board_df(board_code, board_target_df)
                for index, row in board_df.iterrows():
                    if dfutil.len_safe(row) > 0:
                        stock_code = str(row[qldef.target_key])
                        board_name = row[qldef.board_name_key]
                        df_date_code = df_date_trade[(df_date_trade[qldef.board_name_key] == board_name)
                                                     & (df_date_trade[qldef.mtn_key].str.contains(stock_code))]
                        if dfutil.not_empty(df_date_code):
                            break

            # 将行业板块数据分类并计算总数
            df_date_trade = df_date_trade.groupby(qldef.board_name_key, as_index=False).size()
            if dfutil.not_empty(df_date_code):
                return [True, df_date_trade]
            else:
                return [False, df_date_trade]

    return [False, df_date_trade]


# Backtrader框架的订单观察者：主要用于跟踪并可视化交易策略中的买单的创建和过期状态
if bt is not None:
    class OrderObserver(bt.observer.Observer):
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

        board_code_list = []  # 交易股票列表
        end_date_time = None  # 交易结束日期
        tobe_traded_stocks_dic = {}  # 以日期为key保存待交易的股票列表
        board_target_df = qloption.database.get_sw_second_industry_df()  # 申万二级行情板块数据

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
        def get_buy_cash(all_cash, board_count, ratio=1.0, max_ratio=0.98):
            """
            获取单只股票买入金额 todo test ratio待确定方案 hhx
            注意：本策略是以日为单位运行，以第二日开盘价作为交割价。backtrader的运行机制是以购买的资金/今日收盘价，
            得到购买数量后第二日开盘买入。所以买卖时为避免第二日开盘价与今日收盘价的差价，不能以全仓买入。
            @param all_cash: 可以总现金
            @param board_count: 待买入股票总数量
            @param ratio: 每次买入总金额占总可用现金的比率（比如0.5，即一半）
            @param max_ratio: 每次买入总金额占总可用现金的最大比率（即不能超过总金额的0.98）
            """
            buy_cash = all_cash * max_ratio
            if board_count > 0:
                buy_cash = all_cash // board_count  # ‘//’ 表示整除

            # 个股购买最大金额不能超过总结的30%
            # if buy_cash > all_cash * 0.3:
            #     buy_cash = all_cash * 0.3

            return buy_cash

        # 购入/卖出交易股票
        def trade_board(self, current_datetime, df_tobe_traded_stocks, board_target_df, board_code, data, is_buy=True):
            all_cash = 0
            if is_buy:
                # 查询全部资产 - 永远不要满仓买入某只股票
                # all_value = self.broker.getvalue()
                # 查询全部可用资产
                all_cash = self.broker.getcash()
                if all_cash <= 0:
                    return

            current_date_int = dfutil.date_by_datetime(current_datetime)
            trade_state = get_trade_state(current_date_int, df_tobe_traded_stocks, board_target_df, board_code,
                                          is_buy=is_buy)
            if len(trade_state) > 1:
                is_can_trade = trade_state[0]
                df_date_trade = trade_state[1]
                if is_buy:
                    if all_cash > 0:
                        # todo test hhx
                        # if (((board_code == '300111') or (board_code == '300254') or (board_code == '000908')
                        #      or (board_code == '301168') or (board_code == '002459'))
                        #         and (current_date_int == 20230105)):
                        #     logutil.log.debug('符合买入条件')

                        board_count = 0
                        if dfutil.not_empty(df_date_trade):
                            board_count = len(df_date_trade)
                        if is_can_trade:
                            # order_value = self.get_buy_cash(all_cash, board_count)
                            order_value = 50000  # 固定每次交易金额为 50,000
                            close = data.close[0]
                            order_amount = self.downcast(order_value / close, 100)
                            if order_amount > 0:
                                self.order = self.buy(data, size=order_amount)

                else:
                    if is_can_trade and (df_date_trade is None):
                        # is_can_trade为True 且 df_date_trade == None，则表示触发了下降50%的条件，需要清仓
                        self.order = self.close(data)  # 清仓
                        return
                    elif is_can_trade:
                        """
                        data （默认：None）：用于制定给哪个数据集（即哪个证券）创建订单，默认为None，表示给第1个数据集（
                                            self.datas[0]、self.data0对应的证券）创建订单。
                        size（默认：None）：订单委托数量（正数），默认为None，表示会自动通过getsizer获取sizer。
                        price（默认：None）：订单委托价，None表示不指定具体的委托价，而是由市场决定最终的成交价。
                        """
                        # self.order = self.sell(data, size=position)
                        self.order = self.close(data)  # 清仓

        def notify_order(self, order):
            board_code = order.data.params.dataname['target'].iloc[0]
            trade_type = '买入'
            if order.issell():  # order.isbuy() 是否买入
                trade_type = '卖出'

            if order.status in [order.Submitted, order.Accepted]:
                # Buy/Sell order submitted/accepted to/by broker - Nothing to do
                # if order.status == order.Submitted:
                #     self.log(f'{trade_type}{board_code}订单已提交', dt=order.created.dt)
                # else:
                #     self.log(f'{trade_type}{board_code}订单已接受', dt=order.created.dt)

                self.order = order
                return

            if order.status in [order.Expired]:
                self.log(f'买入{board_code}过期', is_save_log=True)

            elif order.status in [order.Completed]:
                # order.info['name'] 值为 AutoOrderedDict({'shape': AutoOrderedDict()})
                self.log(f"{trade_type}{board_code}, 成交量：{order.executed.size}，成交价：{order.executed.price:.2f}，"
                         f"成交总额：{order.executed.value:.2f}, 交易佣金：{order.executed.comm:.2f}", is_save_log=True)

            elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                self.log(f'{trade_type}{board_code}失败', is_save_log=True)

            # Sentinel to None: new orders allowed
            self.order = None

        # 记录交易收益情况（可省略，默认不输出结果）
        def notify_trade(self, trade):
            if trade.isclosed:
                # 注意：这里是个股的毛收益和净收益，不是所有股票的累计毛收益和累计净收益哦，但是市值和现金是累计的
                self.log(f'策略收益：毛收益：{trade.pnl:.2f}，净收益：{trade.pnlcomm:.2f}，市值：{self.broker.getvalue():.2f}，'
                         f'现金：{self.broker.getcash():.2f}', is_save_log=True)

        def __init__(self):
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

            # name = self.datas[0]._name  # 取值cerebro.adddata(data, name=board_code)设置的name
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
                # board_code = self.board_code_list[i]
                board_code = data.params.dataname['target'].iloc[0]

                current_date_int = dfutil.date_by_datetime(current_datetime)
                # logutil.log.debug(f'data[{i}]数据长度为{len(data.params.dataname)}，日期：{current_date_int}')
                df_tobe_traded_stocks = None
                
                # 直接从内存字典中获取
                if current_date_int in self.tobe_traded_stocks_dic:
                    df_tobe_traded_stocks = self.tobe_traded_stocks_dic[current_date_int]
                
                # 下面的懒加载逻辑仅作为备份
                if dfutil.empty(df_tobe_traded_stocks):
                    # df_tobe_traded_stocks = get_tobe_traded_stocks(current_datetime)
                    # self.tobe_traded_stocks_dic[current_date_int] = df_tobe_traded_stocks
                    pass

                # 检查是否有持仓
                position = self.getposition(data).size  # position = self.position
                if position > 0:
                    # 有持仓
                    # 卖出
                    self.trade_board(current_datetime, df_tobe_traded_stocks, self.board_target_df,
                                     board_code, data, is_buy=False)
                    # 买入
                    self.trade_board(current_datetime, df_tobe_traded_stocks, self.board_target_df,
                                     board_code, data, is_buy=True)
                else:
                    # 空仓 - 买入
                    self.trade_board(current_datetime, df_tobe_traded_stocks, self.board_target_df,
                                     board_code, data, is_buy=True)

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
    # 初始资金
    cerebro.broker.setcash(qldef.start_total_cash)
    # 防止下单时现金不够被拒绝。只在执行时检查现金够不够 - 暂时不清楚具体出现场景
    # cerebro.broker.set_checksubmit(False)
    # 交易佣金，双边各 0.0002
    cerebro.broker.setcommission(commission=0.0002)
    # 滑点：双边各 0.0001（防止真实交易中，设定的交易价格不一定能交易，系统会自动按照滑点进行动态调整价格，以接近真实交易）
    cerebro.broker.set_slippage_perc(perc=0.0001)

    # ---------------------------------------------------------
    # 性能优化：预加载所有交易信号数据到内存
    # ---------------------------------------------------------
    logutil.log.info("正在预加载所有行业交易信号数据...")
    preload_start_time = time.time()
    date_list = dfutil.get_date_list(start_date, end_date)
    preloaded_signals = {}
    
    for date_int in date_list:
        dt = dfutil.datetime_by_date(date_int)
        df_signals = get_tobe_traded_stocks(dt)
        if dfutil.not_empty(df_signals):
            preloaded_signals[date_int] = df_signals
            
    my_strategy.tobe_traded_stocks_dic = preloaded_signals
    logutil.log.critical(f"✅ 行业信号预加载完成，耗时: {time.time() - preload_start_time:.2f}秒")
    # ---------------------------------------------------------

    board_code_list = get_sw2_industry_code_list()
    # todo test hhx
    # board_code_list = board_code_list[:5]
    # if '002459' not in board_code_list:
    #     board_code_list.append('002459')

    for board_code in board_code_list:
        # 获取数据
        board_df = get_industry_daily_quote_data(board_code, start_date, end_date)
        if dfutil.not_empty(board_df):
            start_date_time = dfutil.datetime_by_date(start_date)  # 回测开始时间
            end_date_time = dfutil.datetime_by_date(end_date)  # 回测结束时间
            data = bt.feeds.PandasData(dataname=board_df, fromdate=start_date_time, todate=end_date_time)  # 加载数据
            cerebro.adddata(data, name=board_code)
            my_strategy.board_code_list.append(board_code)  # 股票代码

            """
            以下方法将时间戳Timestamp对象转换为 datetime.datetime对象，而datetime.datetime对象
            与datetime.date对象不同，前者包括包含日期和时间信息，后者只包含日期信息（年、月、日）
            不能直接使用前面的end_date_time，该日期不一定是最后的交易日期
            """
            # timestamp = board_df.index[-1].timestamp()
            # end_date_time = datetime.fromtimestamp(timestamp)

            # 将时间戳Timestamp对象转换为datetime.date对象
            end_date_time = datetime.date(board_df.index[-1])
            # 注意逻辑运算使用 and 和 or，不用使用 & 和 |，这个两个为位运算
            if (my_strategy.end_date_time is None) or (end_date_time > my_strategy.end_date_time):
                my_strategy.end_date_time = end_date_time  # 结束交易日期
    
    if not my_strategy.board_code_list:
        logutil.log.warning("没有加载到任何行业板块数据，跳过行业回测")
        return

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

    cerebro.addanalyzer(key_indicator_analyzer.KeyIndicatorAnalyzer, _name='key_indicator')
    cerebro.addanalyzer(trade_list_analyzer.TradeListAnalyzer, _name='trade_list')

    logutil.log.critical(f"初始总资金：{qldef.start_total_cash}，回测时间:{start_date}-{end_date}")
    results = cerebro.run(tradehistory=True)  # 注意：一定要打开，记录交易历史，用于生成自定义订单列表
    balance = cerebro.broker.getvalue()
    logutil.log.critical(f"剩余总资金：{balance}，回测时间:{start_date}-{end_date}")

    # 得到分析指标数据
    if not results:
        logutil.log.critical("回测未生成任何结果，可能是因为没有加载任何有效数据。")
        return

    result = results[0]
    benchmark_df = qloption.database.get_code_daily_quote_data(qldef.hs300_code1, start_date, end_date,
                                                               target_path=qldef.market_quotation_directory,
                                                               filter_str='hs300.csv')  # 参考沪深300 数据
    key_indicators_df, daily_details_dict = result.analyzers.key_indicator.get_analysis_data(
        benchmark_df, qldef.reference_ind_key, '沪深300')
    # 得到交易列表
    trade_list_df, trade_dict = result.analyzers.trade_list.get_analysis_data()
    logutil.log.critical(f"关键指标：{key_indicators_df}")
    # logutil.log.debug(f"收益走势：{daily_details_dict}")
    # 参考指数
    # logutil.log.debug(f"交易订单列表：{trade_list_df}")
    # logutil.log.debug(f"交易股票以及对应的买卖点：{trade_dict}")

    this_strategy_df = daily_details_dict[qldef.this_strategy_ind_key]
    reference_df = daily_details_dict[qldef.reference_ind_key]

    # 绘制收益率曲线 并 插入关键指标的表格
    chart_file_name = f"results_industry_{start_date}_{end_date}_chart.png"
    chart_file_path = os.path.join(qldef.quantitative_result_directory, chart_file_name)
    
    drawingutil.draw_yield_curve_chart(this_strategy_df, reference_df, key_indicators_df, save_path=chart_file_path)
    logutil.log.critical(f"收益率曲线图已保存至: {chart_file_path}")

    # 结束计时
    end_time = time.time()
    execution_time = end_time - start_time
    logutil.log.critical(f'交易回测完成，回测日期：{start_date} - {end_date}，总耗时长：{execution_time} 秒')
