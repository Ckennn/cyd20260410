"""
databaseutil.py
qlsignalNew
Created by huanghx on 2024/7/30
Copyright © 2024 huanghx. All rights reserved.
"""
import os
import project_paths

DB_PATH = str(project_paths.get_db_path())

from multiprocessing import Lock
import multiprocessing
from datetime import datetime


# ---------------- SQLite fallback ----------------
# If your original code was designed for MSSQL (pymssql/pyodbc) but you now have a local sqlite db,
# keep QL_USE_SQLITE=1 (default) to force using sqlite.
# You can override the db path via STOCK_DB_PATH.
USE_SQLITE = os.environ.get('QL_USE_SQLITE', '1').strip().lower() not in ('0','false','off','no','n')

import pathlib
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# import pymssql  # delete by hhx 2025.01.24
# import pyodbc  # add by hhx 2025.01.24
import pandas as pd
import sqlite3

import numpy as np

import dfutil
import logutil
import qldef
import qloption
import tradedateutil


# 计算指数移动平均线（EMA）：例如11/22日EMA
def calculate_ema(target_df):
    # 以下三个方法都可以计算
    close_reverse_order_df = target_df['close'].iloc[::-1]  # 将收盘价按照日期反序（因为源数据是从现在到过去排序的），否测计算结果不对
    target_df['ema(11)'] = close_reverse_order_df.ewm(span=11, min_periods=0, adjust=False).mean()
    target_df['ema(22)'] = close_reverse_order_df.ewm(span=22, min_periods=0, adjust=False).mean()
    # target_df['EMA11'] = close_df.ewm(alpha=2 / 12, adjust=False).mean()
    # target_df['EMA22'] = close_df.ewm(alpha=2 / 23, adjust=False).mean()
    # target_df['ema(11)'] = calc_ema_reverse_order(target_df, 11)
    # target_df['ema(22)'] = calc_ema_reverse_order(target_df, 22)


# 计算DIFF、DEA、MACD、BBI
def calculate_diff_dea(target_df):
    # 以下三个方法都可以计算
    diff = 'macddif(12,26,9)'
    dea = 'macddea(12,26,9)'
    bar = 'macdbar(12,26,9)'
    bbi = 'bbi(3,6,12,24)'
    close_reverse_order_df = target_df['close'].iloc[::-1]  # 将收盘价按照日期反序（因为源数据是从现在到过去排序的），否测计算结果不对
    ema12 = close_reverse_order_df.ewm(span=12, min_periods=0, adjust=False).mean()
    ema26 = close_reverse_order_df.ewm(span=26, min_periods=0, adjust=False).mean()
    target_df[diff] = ema12 - ema26
    diff_reverse_order_df = target_df[diff].iloc[::-1]  # 将收盘价按照日期反序（因为源数据是从现在到过去排序的），否测计算结果不对
    target_df[dea] = diff_reverse_order_df.ewm(alpha=2 / 10, adjust=False).mean()
    target_df[bar] = 2 * (target_df[diff] - target_df[dea])
    target_df[bbi] = dfutil.Stock.calculate_bbi(target_df, 3, 6, 12, 24)


# 计算移动平均交易价格 和 移动平均交易量
def calculate_ma(target_df):
    # 计算移动平均交易价格(ma：5/10/20/30/60/120/250日均线)
    target_df['ma(5)'] = target_df['close'].rolling(5).mean().shift(-4)
    target_df['ma(10)'] = target_df['close'].rolling(10).mean().shift(-9)
    target_df['ma(20)'] = target_df['close'].rolling(20).mean().shift(-19)
    target_df['ma(30)'] = target_df['close'].rolling(30).mean().shift(-29)
    target_df['ma(60)'] = target_df['close'].rolling(60).mean().shift(-59)
    target_df['ma(120)'] = target_df['close'].rolling(120).mean().shift(-119)
    target_df['ma(250)'] = target_df['close'].rolling(250).mean().shift(-249)

    # 计算移动平均交易量（MAVOL）：3/5/10/20日均量
    target_df['mavol(3)'] = target_df[qldef.volume_key].rolling(3).mean().shift(-2)
    target_df['mavol(5)'] = target_df[qldef.volume_key].rolling(5).mean().shift(-4)
    target_df['mavol(10)'] = target_df[qldef.volume_key].rolling(10).mean().shift(-9)
    target_df['mavol(20)'] = target_df[qldef.volume_key].rolling(20).mean().shift(-19)


# 综合计算计算指数移动平均线、DIFF、DEA等
def calculate_all(target_df):
    # 计算开始时间
    calculate_start_time = time.time()

    # 计算指数移动平均线（EMA）：例如11/22日EMA
    calculate_ema(target_df)
    # 计算DIFF、DEA、MACD、BBI
    calculate_diff_dea(target_df)
    # 计算移动平均交易价格 和 计算移动平均交易量
    calculate_ma(target_df)

    # 保存指数移动平均线、DIFF、DEA等的结束时间
    calculate_end_time = time.time()
    execution_time = calculate_end_time - calculate_start_time
    logutil.log.debug(f"计算指数移动平均线、DIFF、DEA等耗时长：{execution_time} 秒")


# 将东方财富的一级行业板块 映射到 申万二级行业板块
def dc_map_to_sw2():
    cache_dir = qldef.market_quotation_directory  # 获取当前用户的临时文件夹路径
    dc_industry_filepath = os.path.join(cache_dir, qldef.dc_board_target_file_name)
    sw2_industry_filepath = os.path.join(cache_dir, qldef.sw2_board_target_file_name)
    df_dc_industry = qloption.database.read_single_big_csv(dc_industry_filepath)
    if dfutil.not_empty(df_dc_industry):
        df_sw2_industry = qloption.database.read_single_big_csv(sw2_industry_filepath)
        if dfutil.not_empty(df_sw2_industry):
            sw2_board_code_list = []
            sw2_board_name_list = []
            for index, row in df_dc_industry.iterrows():
                if dfutil.len_safe(row) > 0:
                    target = row[qldef.target_key]
                    df_target = df_sw2_industry[df_sw2_industry[qldef.target_key] == target]
                    if dfutil.not_empty(df_target):
                        df_target = df_target.reset_index(drop=True)  # 删除现有索引，并将其转换为默认的整数索引
                        board_code = df_target.loc[0, qldef.board_code_key]
                        if dfutil.not_none(board_code):
                            sw2_board_code_list.append(board_code)
                        else:
                            # 注意：这里不能设为None或空字符串，否则会导致dataFrame中的sw2_board_code值为str类型
                            sw2_board_code_list.append(0)

                        board_name = df_target.loc[0, qldef.board_name_key]
                        sw2_board_name_list.append(board_name)
                    else:
                        sw2_board_code_list.append(0)
                        sw2_board_name_list.append(None)

            sw_board_code_key = 'sw_board_code'
            sw_board_name_key = 'sw_board_name'
            if sw_board_code_key in df_dc_industry.columns:
                df_dc_industry[sw_board_code_key] = sw2_board_code_list
            else:
                # 将列表作为新的列插入到DataFrame中
                # 参数1（loc）表示插入列的位置，参数2（column）表示新列的名称，参数3（value）是要插入的列表
                df_dc_industry.insert(loc=dfutil.len_safe(df_dc_industry.columns), column=sw_board_code_key,
                                      value=sw2_board_code_list)

            if sw_board_name_key in df_dc_industry.columns:
                df_dc_industry[sw_board_name_key] = sw2_board_name_list
            else:
                # 将列表作为新的列插入到DataFrame中
                df_dc_industry.insert(loc=dfutil.len_safe(df_dc_industry.columns), column=sw_board_name_key,
                                      value=sw2_board_name_list)

            qloption.database.write_file_csv(df_dc_industry, cache_dir, qldef.dc_board_target_file_name)


def save_df_to_file_csv(prefix, suffix, df, subset, sort_key='', ascending=False, drop_duplicates=True):
    """
    保存dataFrame数据到csv文件并去重
    @param prefix: 文件目录
    @param suffix: 文件名
    @param df: dataFrame数据
    @param subset: 去重字段数组
    @param sort_key: 排序字段key
    @param ascending: 排序方式（默认降序）
    @param drop_duplicates: 是否需要去重（默认去重）
    """
    if dfutil.not_empty(df):
        pathfile = str(os.path.join(prefix, suffix))
        is_exist = pathlib.Path(pathfile).is_file()
        if is_exist:
            # 从先读取源文件内容，再顶部插入新行情数据，再覆盖方式写入文件
            temp_df = qloption.database.read_single_big_csv(pathfile)

            sort_start_time = time.time()
            if drop_duplicates:
                # 去重和排序耗时：0.002489秒，而且主要是去重比较耗时，排序仅0.0004左右
                # 当ignore_index=True时，新连接的数据将重新生成索引，忽略原始数据的索引，生成一个新的整数索引，方便后续操作
                df = pd.concat([df, temp_df], ignore_index=True).drop_duplicates(subset=subset)
            else:
                # 非去重和非排序：0.00055秒
                df = pd.concat([df, temp_df], ignore_index=True)

            # 注意：排序字段需要为int类型，不能为字符串类型，否则会报错！！！
            if dfutil.len_safe(sort_key) > 0:
                # 通过sort_key排序后，索引会错乱
                df = df.sort_values(sort_key, ascending=ascending)

            sort_end_time = time.time()
            execution_time = sort_end_time - sort_start_time
            logutil.log.debug(f'合并dataFrame数据耗时：{execution_time}秒')

            df = df.reset_index(drop=True)  # 删除现有索引，并将其转换为默认的整数索引
            qloption.database.write_file_csv(df, prefix, suffix)
        else:
            qloption.database.write_file_csv(df, prefix, suffix)


def save_daily_quote_to_csv(target_df, market, target, daily_quote_type: qldef.daily_quote_type, cache_dir):
    """
    保存日度行情数据到csv文件
    通过inner_code区分不同的证券产品，并保存到对应日期的csv文件中
    添加mode参数：mode参数用于指定文件的打开模式 modify by hhx 2024.08.01
    其中'a'表示追加模式，‌意味着如果文件已经存在，‌新的数据将被追加到文件的末尾，‌而不是覆盖原有的内容；
    'w'表示重新写入，会覆盖原来的内容。
    """
    suffix = f"{market}_{target}_1d_ind.csv"
    if daily_quote_type == qldef.daily_quote_type.hs300_type:  # 沪深300 指数
        suffix = f"{market}_{target}_hs300.csv"

    pathfile = cache_dir + '/' + suffix
    is_exist = pathlib.Path(pathfile).is_file()

    # todo test hhx
    # if __debug__:
    #     target_df = target_df.reset_index(drop=True)  # 删除现有索引，并将其转换为默认的整数索引
    #     open_price = target_df.at[0, 'open']  # 获取第0行open列表的值
    #     # open_price = target_df.loc[0, 'open']  # 获取第0行open列表的值
    #     if open_price == 0:
    #         logutil.log.debug(
    #             f'{target_name}({target})股票开盘价为0，可能正在停牌中，已过滤该非法数据')

    # 保存单个股票的日度行情数据到文件的开始时间
    save_start_time = time.time()
    # 改为仅判断文件是否存在 modify by hhx 2024.09.05
    # if is_first_query or (not is_exist):
    if not is_exist:
        # 如果首次查询 或者 文件不存在，则直接带列头和追加方式写入文件
        target_df = target_df.reset_index(drop=True)  # 删除现有索引，并将其转换为默认的整数索引

        if daily_quote_type == qldef.daily_quote_type.stock_type:
            # 个股类型：综合计算计算指数移动平均线、DIFF、DEA等
            calculate_all(target_df)

        qloption.database.write_file_csv(target_df, cache_dir, suffix, mode='a')
    else:
        # 如果非首次查询 且 文件存在，则从先读取源文件内容，再顶部插入新行情数据，再覆盖方式写入文件
        temp_df = qloption.database.read_single_big_csv(pathfile)

        # todo 去重合并 和 日期排序 耗时(仅查询历史数据需要，后期每日更新数据不需要) hhx
        sort_start_time = time.time()
        # 非去重和非排序：0.00055秒
        # target_df = pd.concat([target_df, temp_df], ignore_index=True)
        # 去重和排序耗时：0.002489秒，而且主要是去重比较耗时，排序仅0.0004左右
        target_df = (pd.concat([target_df, temp_df], ignore_index=True)
                     .drop_duplicates(subset=[qldef.inner_code_key, qldef.date_key]))
        # Ensure date field is integer type to avoid TypeError when sorting
        if qldef.date_key in target_df.columns:
            target_df[qldef.date_key] = pd.to_numeric(target_df[qldef.date_key], errors='coerce').fillna(0).astype(int)
        target_df = target_df.sort_values(qldef.date_key, ascending=False)  # 按日期的降序排序
        sort_end_time = time.time()
        execution_time = sort_end_time - sort_start_time
        logutil.log.debug(f'合并dataFrame数据耗时：{execution_time}秒')

        target_df = target_df.reset_index(drop=True)  # 删除现有索引，并将其转换为默认的整数索引

        if daily_quote_type == qldef.daily_quote_type.stock_type:
            # 综合计算计算指数移动平均线、DIFF、DEA等
            calculate_all(target_df)

        qloption.database.write_file_csv(target_df, cache_dir, suffix)

    # 保存单个股票的日度行情数据到文件的结束时间
    save_end_time = time.time()
    execution_time = save_end_time - save_start_time
    logutil.log.debug(
        f"保存个股{len(target_df)}条的日度行情数据到文件，耗时长：{execution_time} 秒")


# 保存日度行情数据到csv文件，添加进程锁
def save_daily_quote_to_csv_with_process_lock(target_df, market, target, daily_quote_type: qldef.daily_quote_type,
                                              cache_dir, process_lock=None):
    if process_lock is None:
        save_daily_quote_to_csv(target_df, market, target, daily_quote_type, cache_dir)
    else:
        # 添加多进程锁，避免多进程同时写入一个文件时，出现数据错乱或丢失的情况 add by hhx 2024.09.26
        with process_lock:
            save_daily_quote_to_csv(target_df, market, target, daily_quote_type, cache_dir)


# 查询日度行情数据
# skip_days：跳过天数（比如想获取20200101-20201231的数据，则需要跳过20210101-当前日期的天数）
# daily_quote_type：日度行情类型（默认为个股日度行情类型）
def query_qt_daily_quote(server, database, user, password, total_days, per_query_days, skip_days=0,
                         daily_quote_type=qldef.daily_quote_type.stock_type, process_lock=None):
    """
    建立连接（port默认为"1433"，charset默认为utf8）
    charset='CP936'：可以解决查询数据库时，中文返回乱码的问题。出现乱码原因是字符串字段类型为：varchar，
    造成读取数据乱码。
    """
    # 开始计时
    start_time = time.time()

    # 这里可以切换数据库查询方式 modify by hhx 2025.01.24
    if qldef.is_use_pymssql:
        # 方法1（搭建pymssql环境比较麻烦） delete by hhx 2025.01.24
        # dbtool = pymssql
        dbtool = None
        pass
        # 使用集合定义连接参数（要使用字典格式）
        conn_params = {
            'server': server,
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8',
        }
    else:
        # 方法2 add by hhx 2025.01.24
        # dbtool = pyodbc
        dbtool = None
        pass
        driver = '{ODBC Driver 17 for SQL Server}'  # 根据实际安装的驱动进行调整
        conn_params = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={user};PWD={password}'
    try:
        if qldef.is_use_pymssql:
            conn = dbtool.connect(**conn_params)  # 入参为字典格式
        else:
            conn = dbtool.connect(conn_params)

    except dbtool.Error as e:
        logutil.log.critical(f"数据库连接失败: {e.args[0]}")
        return
    else:
        # 连接数据库结束时间
        connect_end_time = time.time()
        execution_time = connect_end_time - start_time
        logutil.log.debug(f"连接数据库成功，耗时长：{execution_time} 秒")  # 大概5秒左右
    # finally:
    #     logutil.log.debug("无论发生什么事情，此处一定会执行")

    # 创建cursor对象
    if conn is not None:
        cursor = conn.cursor()
    else:
        logutil.log.error('连接数据库成功，但是数据库返回的conn为空')
        return

    i = 1
    while i <= total_days / per_query_days:
        # 开始计时
        start_time = time.time()

        df = None
        # row_count = 0  # 记录日度行情表总行数
        # start_date = dfutil.past_date(total_days - per_query_days * i + 1)  # 默认从指定开始日期的前一天开始向前查询
        start_date = dfutil.past_date(total_days + skip_days - per_query_days * i)  # 为了便于理解，默认从指定开始日期开始向前查询
        date_list = dfutil.loop_dates(days_back=per_query_days, start_date=start_date)  # 默认查询3年的数据 3*365
        # date_list = dfutil.get_date_list(20200101, 20210101)
        # logutil.log.debug(f'总共查询{len(date_list)}天的日度行情数据')

        # past_date_str = start_date.strftime("%Y%m%d")
        # cache_dir = qldef.file_cache_path + f"/market_{past_date_str}_1d"  # 获取当前用户的临时文件夹路径
        if daily_quote_type == qldef.daily_quote_type.stock_type:
            # 保存个股日度行情数据文件 目录
            cache_dir = qldef.market_quotation_directory
        else:
            # 保存申万行业板块日度行情数据文件 目录
            cache_dir = qldef.market_SYWGIndexQuote_directory

        # is_first_query = True  # 默认为第一次查询
        # filelist = qloption.database.get_all_market_files(cache_dir)
        # if len(filelist) > 1000:
        #     is_first_query = False

        for date in date_list:
            # 判断是否交易日，如果非交易日，直接continue add by hhx 2024.09.13
            if not tradedateutil.isTradeDay(str(date), "%Y%m%d"):
                continue

            if daily_quote_type == qldef.daily_quote_type.stock_type:
                # 执行SQL查询（QT_DailyQuote为日度行情表名，LC_STIBDailyQuote为科创板日度行情表名）
                sql0 = (
                    f"SELECT InnerCode, TradingDay, PrevClosePrice, OpenPrice, HighPrice, LowPrice, ClosePrice, "
                    f"TurnoverVolume, TurnoverValue, TurnoverDeals, XGRQ  FROM QT_DailyQuote "
                    f"WHERE TradingDay = '{date}'")
                sql1 = (
                    f"SELECT InnerCode, TradingDay, PrevClosePrice, OpenPrice, HighPrice, LowPrice, ClosePrice, "
                    f"TurnoverVolume, TurnoverValue, TurnoverDeals, UpdateTime  FROM LC_STIBDailyQuote "
                    f"WHERE TradingDay = '{date}'")
                # sql = "SELECT * FROM QT_StockPerformance"
                try:
                    cursor.execute(sql0)
                except dbtool.Error as e:
                    logutil.log.critical(f"查询A股日度行情表（QT_DailyQuote）失败: {e.args[0]}")
                    continue
                rows0 = cursor.fetchall()

                try:
                    cursor.execute(sql1)
                except dbtool.Error as e:
                    logutil.log.critical(f"查询科创板日度行情表（LC_STIBDailyQuote）失败: {e.args[0]}")
                    continue
                rows1 = cursor.fetchall()

                rows = rows0 + rows1  # 两个list相加

                # 初始化列名
                columns = [qldef.inner_code_key, qldef.date_key, 'prev_close_price', 'open', 'high', 'low',
                           'close', qldef.volume_key, 'amount', 'turnover_deals', 'update_time']

            else:
                # 查询申万行业板块日度行情表
                sql = (
                    f"SELECT InnerCode, TradingDay, PrevClosePrice, OpenPrice, HighPrice, LowPrice, ClosePrice, "
                    f"TurnoverVolume, TurnoverValue, IndexPE, IndexPB, TotalMarketValue, AShareTotalMV, ChangePCT, "
                    f"UpdateTime  FROM QT_SYWGIndexQuote WHERE TradingDay = '{date}'")
                try:
                    cursor.execute(sql)
                except dbtool.Error as e:
                    logutil.log.critical(f"查询申万行业板块日度行情表（QT_SYWGIndexQuote）失败: {e.args[0]}")
                    continue
                rows = cursor.fetchall()

                # 初始化列名
                columns = [qldef.inner_code_key, qldef.date_key, 'prev_close_price', 'open', 'high', 'low',
                           'close', qldef.volume_key, 'amount', 'index_pe', 'index_pb', 'total_market_value',
                           'aShare_total_mv', 'change_pct', 'update_time']

            # 由于取最新日期获取的所有日度行情数据 不一定包括全部的数据，因为有些个股比较早或比较晚上市，改为去重方式 modify by hhx 2024.09.13
            # if row_count == 0:
            #     row_count = dfutil.len_safe(rows)

            if dfutil.len_safe(rows) > 0:
                # logutil.log.debug(np.shape(rows))

                """
                使用pyodbc查询数据库时，会报错：ValueError: Shape of passed values is (42316, 1), indices imply (42316, 11) 
                add by hhx 2025.01.24
                """
                # 方法1：通过np.reshape修改数据的shape
                # if not qldef.is_use_pymssql:
                #     rows = np.reshape(rows, newshape=(dfutil.len_safe(rows), dfutil.len_safe(columns)))
                # 方法2：pd.DataFrame 改为 pd.DataFrame.from_records
                if dfutil.empty(df):
                    # 将查询结果转化为 dataframe对象
                    # df = pd.DataFrame(rows, columns=columns)
                    df = pd.DataFrame.from_records(rows, columns=columns)
                else:
                    # 将新行添加到DataFrame中（由于pandas库的更新，2.0及以后得版本把append()这个方法给删除了，取而代之的是concat()方法）
                    # df = pd.concat([df, pd.DataFrame(rows, columns=df.columns)], ignore_index=True)
                    df = pd.concat([df, pd.DataFrame.from_records(rows, columns=df.columns)], ignore_index=True)
            else:
                continue

            # 修改DataFrame的列标题（InnerCode：证券内部编码，具有唯一性）
            # df.columns = [qldef.inner_code_key, qldef.date_key, 'prev_close_price', 'open',
            # 'high', 'low', 'close', qldef.volume_key, 'amount', 'turnover_deals', 'UpdateTime']

            # # 分割依据的列名（可以按照指定列的唯一性进行分类）
            # split_column = qldef.inner_code_key
            # # 获取唯一值并创建字典存储分割后的DataFrame
            # unique_values = df[split_column].unique()
            # dataframes = {value: df[df[split_column] == value] for value in unique_values}  # 以inner_code为key的字典

        """
        if is_stock_daily_quote:
            # 修复指定日期范围内没有日度行情数据 add by hhx 2024.08.29
            inner_codes = datarepairutil.get_repair_inner_codes(20201231, 20201231)
            df_code_list = [df[df.inner_code == code] for code in inner_codes]  # list数组
            if len(df_code_list) > 0:
                df = pd.concat(df_code_list)
                df = df.reset_index(drop=True)  # 删除现有索引，并将其转换为默认的整数索引
                row_count = len(df)
        """

        # 查询指定天数的日度行情数据 结束时间
        query_end_time = time.time()
        execution_time = query_end_time - start_time
        logutil.log.debug(f"查询{len(date_list)}天的日度行情数据耗时长：{execution_time} 秒")

        if dfutil.not_empty(df):
            # 将日期(数据库为timestamp类型)转为int类型
            df[qldef.date_key] = df[qldef.date_key].apply(lambda x: x.strftime("%Y%m%d")).astype(int)
            if daily_quote_type == qldef.daily_quote_type.stock_type:
                # 由于从数据库获取的日交易量为正常交易量的100倍，所以需要除以100 add by hhx 2024.08.30
                df[qldef.volume_key] = df[qldef.volume_key] / 100

            # 由于取最新日期获取的所有日度行情数据 不一定包括全部的数据，因为有些个股比较早或比较晚上市，改为去重方式 modify by hhx 2024.09.13
            # first_row_df = df.loc[0:row_count - 1]  # loc：结束索引（包括），iloc：不包括结束索引
            first_row_df = df.drop_duplicates(subset=[qldef.inner_code_key])

            inner_code_key = qldef.inner_code_key
            logutil.log.debug(f'日度行情数据保存目录：{cache_dir}')
            dfutil.create_directory(cache_dir)
            target = ''  # 股票代码
            company_code_df = None  # 保存证券内部编码、公司代码和证券代码等信息
            industry_df = None  # 保存申万二级行业板块信息

            """
            使用ThreadPoolExecutor线程池可以提高多线程处理任务的效率
            （1）max_workers：设置最大线程数量（默认无上限）
            （2）控制线程池大小为8（因为当前设备系统为8 核）
            （3）as_completed(fs, timeout=None)
                as_completed()方法用于获取已完成的Future对象。fs是一组Future对象，timeout是超时时间。
                as_completed()方法返回一个迭代器，每次迭代都会返回一个已完成的Future对象。
            （4）Future 对象可以用来获取任务的执行结果。可以使用 Future 对象的 result() 方法来等待任务执行完成并
                获取其结果。result() 方法会阻塞当前线程，直到任务执行完成并返回结果。
            （5）使用线程池对象的 executor.shutdown() 方法可以关闭线程池
            （6）wait(fs, timeout=None, return_when=ALL_COMPLETED)
                wait()方法用于等待一组Future对象执行完毕。fs是一组Future对象，timeout是超时时间，return_when
                指定何时返回。如果指定return_when为FIRST_COMPLETED，则在第一个Future对象完成后就会返回。
            """
            # 使用动态线程数，IO密集型任务可以设置较高的并发数
            # 获取CPU核心数，默认为4（防止获取失败）
            cpu_count = os.cpu_count() or 4
            # 设置最大工作线程数：CPU核心数 * 4，但不超过 64
            max_workers = min(64, cpu_count * 4)
            
            # executor = ThreadPoolExecutor(max_workers=8)         # 方法1
            # futures = []
            with (ThreadPoolExecutor(max_workers=max_workers) as executor):  # 方法2
                for index, row in first_row_df.iterrows():
                    if dfutil.len_safe(row) > 0:
                        inner_code = row[inner_code_key]
                        market = "zh"
                        industry_row = None
                        quote_type = daily_quote_type
                        if ((quote_type == qldef.daily_quote_type.stock_type)
                                or (quote_type == qldef.daily_quote_type.hs300_type)):
                            # 通过InnerCode从SecuMain表查找对应的股票代码和股票名称
                            sql2 = (f"SELECT InnerCode, CompanyCode, SecuCode, ChiNameAbbr FROM SecuMain "
                                    f"WHERE InnerCode = '{inner_code}'")
                            cursor.execute(sql2)
                            company_code_row = cursor.fetchmany()  # 默认获取一条数据（可指定查询数量）
                            company_code = company_code_row[0][1]
                            target = company_code_row[0][2]  # 股票代码
                            # target_name = company_code_row[0][3] # 股票名称

                            # 如果是无效的量化股票，则不处理，直接continue - modify by hhx 2024.09.02
                            if dfutil.is_invalid_quantization_stock(target):
                                continue

                            # quote_type = daily_quote_type
                            # is_hs300 = False
                            if dfutil.is_hs300(target):
                                # is_hs300 = True
                                quote_type = qldef.daily_quote_type.hs300_type
                            elif daily_quote_type == qldef.daily_quote_type.hs300_type:
                                # 只获取沪深300 指数的日度行情数据
                                continue

                            # 通过CompanyCode从DZ_ExgIndustry 或 LC_ExgIndustry 表查找二级行业代码和名称
                            # industry_row = None
                            if dfutil.not_empty(company_code):
                                # if not is_hs300:  # 沪深300指数不保存到行业板块csv
                                if quote_type != qldef.daily_quote_type.hs300_type:
                                    # 38-申万行业分类(新)
                                    # sql3 = (f"SELECT FirstIndustryCode, FirstIndustryName, SecondIndustryCode, "
                                    #         f"SecondIndustryName FROM DZ_ExgIndustry WHERE CompanyCode = "
                                    #         f"'{company_code}' AND Standard = '{qldef.sw_industry_standard}'")
                                    sql3 = (f"SELECT SecondIndustryCode, SecondIndustryName FROM DZ_ExgIndustry WHERE "
                                            f"CompanyCode = '{company_code}' AND Standard = '{qldef.sw_industry_standard}'")
                                    try:
                                        cursor.execute(sql3)
                                    except dbtool.Error as e:
                                        logutil.log.critical(f"查询申万行业分类表（DZ_ExgIndustry）失败: {e.args[0]}")
                                        continue

                                    industry_row = cursor.fetchmany()  # 可能存在多条，但只取其中一条

                            # 必须两个都有值，以排除“上证指数”、“工业指数”等指数行情
                            # if (dfutil.not_empty(company_code_row) and dfutil.not_empty(industry_row)) or is_hs300:
                            if ((dfutil.not_empty(company_code_row) and dfutil.not_empty(industry_row))
                                    or (quote_type == qldef.daily_quote_type.hs300_type)):
                                # 过滤开盘价为0的非法数据（一般开盘价都不为0，为0的可能是停牌股票）
                                target_df = df[(df[inner_code_key] == inner_code) & (df['open'] > 0)]
                                # 新增两列：market 和 target
                                # target_df['market'] = market
                                # target_df['target'] = target

                                if dfutil.not_empty(target_df):
                                    # save_daily_quote_to_csv(target_df, market, target, target_name, is_first_query,
                                    #                         is_hs300, cache_dir)
                                    logutil.log.debug(f"保存第{i}遍第{index}个{market}_{target}文件")
                                    future = executor.submit(save_daily_quote_to_csv_with_process_lock, target_df,
                                                             market, target, quote_type, cache_dir, process_lock)
                                    # futures.append(future)
                                    # 获取任务执行结果（result() 方法会阻塞当前线程，直到任务执行完成并返回结果）
                                    # print(future.result())

                                    if i == 1:  # modify by hhx 2024.09.02
                                        # if not is_hs300:
                                        if quote_type != qldef.daily_quote_type.hs300_type:
                                            # 初始化列名
                                            columns = [qldef.inner_code_key, 'company_code', 'target',
                                                       'target_name']
                                            """
                                            使用pyodbc查询数据库时，会报错：ValueError: Shape of passed values is (42316, 1)
                                            , indices imply (42316, 11)  add by hhx 2025.01.24
                                            """
                                            if dfutil.empty(company_code_df):
                                                # company_code_df = pd.DataFrame(company_code_row, columns=columns)
                                                company_code_df = pd.DataFrame.from_records(company_code_row,
                                                                                            columns=columns)
                                            else:
                                                # 将新行添加到DataFrame中（由于pandas库的更新，2.0及以后得版本把append()这个方法给删除了，取而代之的是concat()方法）
                                                # company_code_df = pd.concat(
                                                #     [company_code_df,
                                                #      pd.DataFrame(company_code_row, columns=company_code_df.columns)],
                                                #     ignore_index=True)
                                                company_code_df = pd.concat(
                                                    [company_code_df,
                                                     pd.DataFrame.from_records(company_code_row,
                                                                               columns=company_code_df.columns)],
                                                    ignore_index=True)

                        else:
                            # 通过InnerCode从LC_IndexBasicInfo表查找对应的行业类别
                            # sql2 = f"SELECT * FROM LC_IndexBasicInfo WHERE IndexCode = '{inner_code}'"
                            # 通过IndexCode和IndustryStandard从LC_CorrIndexIndustry表查找对应的IndustryCode
                            sql2 = (f"SELECT IndustryStandard, IndustryCode FROM LC_CorrIndexIndustry "
                                    f"WHERE IndustryStandard = '{qldef.sw_industry_standard}' "
                                    f"AND IndexCode = '{inner_code}'")
                            cursor.execute(sql2)
                            index_industry_row = cursor.fetchmany()  # 默认获取一条数据（可指定查询数量）
                            if dfutil.not_empty(index_industry_row):
                                industry_standard = index_industry_row[0][0]
                                industry_code = index_industry_row[0][1]
                                # 查询申万二级行业（Classification = '2'代表查询申万二级，如果为'1'，则查询申万一级）
                                sql3 = (f"SELECT IndustryCode, IndustryName, FirstIndustryCode, FirstIndustryName, "
                                        f"SecondIndustryCode, SecondIndustryName FROM CT_IndustryType WHERE "
                                        f"IndustryCode = '{industry_code}' AND Standard = '{industry_standard}' "
                                        f"AND Classification = '2'")
                                cursor.execute(sql3)
                                industry_row = cursor.fetchmany()  # 默认获取一条数据（可指定查询数量）
                                if dfutil.not_empty(industry_row):
                                    industry_code = industry_row[0][0]  # 申万二级行业代码
                                    industry_name = industry_row[0][1]  # 申万二级行业名称
                                    # 过滤开盘价为0的非法数据（一般开盘价都不为0，为0的可能是停牌股票）
                                    target_df = df[(df[inner_code_key] == inner_code) & (df['open'] > 0)]
                                    if dfutil.not_empty(target_df):
                                        # with ThreadPoolExecutor(max_workers=8) as executor:
                                        logutil.log.debug(f"保存第{i}遍第{index}个文件")
                                        # name = multiprocessing.current_process().name  # 获取当前进程的名字
                                        future = executor.submit(save_daily_quote_to_csv_with_process_lock, target_df,
                                                                 market, industry_code, quote_type, cache_dir,
                                                                 process_lock)
                                        # 获取任务执行结果（result() 方法会阻塞当前线程，直到任务执行完成并返回结果）
                                        # print(future.result())

                        if i == 1:  # modify by hhx 2024.09.02 -> 改为quote_type判断 2024.09.12
                            # if not is_hs300:
                            if quote_type != qldef.daily_quote_type.hs300_type:
                                if dfutil.not_empty(industry_row):
                                    # 初始化列名
                                    industry_columns = [qldef.board_code_key, qldef.board_name_key]
                                    if quote_type == qldef.daily_quote_type.sw2_industry_type:
                                        industry_columns = [qldef.board_code_key, qldef.board_name_key,
                                                            'FirstIndustryCode',
                                                            'FirstIndustryName', 'SecondIndustryCode',
                                                            'SecondIndustryName']

                                    """
                                    使用pyodbc查询数据库时，会报错：ValueError: Shape of passed values is (42316, 1), indices imply (42316, 11) 
                                    add by hhx 2025.01.24
                                    """
                                    if dfutil.empty(industry_df):
                                        # 初始化列名
                                        # industry_columns = [qldef.board_code_key, qldef.board_name_key]
                                        # industry_df = pd.DataFrame(industry_row, columns=industry_columns)
                                        industry_df = pd.DataFrame.from_records(industry_row, columns=industry_columns)
                                    else:
                                        # 将新行添加到DataFrame中（由于pandas库的更新，2.0及以后得版本把append()这个方法给删除了，取而代之的是concat()方法）
                                        # industry_df = pd.concat(
                                        #     [industry_df, pd.DataFrame(industry_row, columns=industry_df.columns)],
                                        #     ignore_index=True)
                                        industry_df = pd.concat(
                                            [industry_df, pd.DataFrame.from_records(industry_row,
                                                                                    columns=industry_df.columns)],
                                            ignore_index=True)
                                # else:
                                #     if dfutil.not_empty(company_code_row):
                                #         # 如果company_code_row不为空，则插入一行含列名的空DataFrame（注意：需要加上index=[0]，否则不会生成nan空行）
                                #         if dfutil.empty(industry_df):
                                #             industry_df = pd.DataFrame(index=[0], columns=industry_columns)
                                #         else:
                                #             industry_df = pd.concat(
                                #                 [industry_df, pd.DataFrame(index=[0], columns=industry_df.columns)],
                                #                 ignore_index=True)
                # 关闭线程池
                executor.shutdown()

            # 保存 全部个股/申万二级行业板块 日度行情数据到csv文件的结束时间
            save_end_time = time.time()
            execution_time = save_end_time - query_end_time
            if daily_quote_type == qldef.daily_quote_type.stock_type:
                logutil.log.debug(f"保存{len(date_list)}天的全部股票日度行情数据到csv文件耗时长：{execution_time} 秒")

                if (dfutil.not_empty(company_code_df)) & (dfutil.not_empty(industry_df)):
                    # 从0行开始取board_code列的值
                    company_code_df[qldef.board_code_key] = industry_df.loc[0:, qldef.board_code_key]
                    # 从0行开始取board_name列的值
                    company_code_df[qldef.board_name_key] = industry_df.loc[0:, qldef.board_name_key]

                if dfutil.not_empty(company_code_df):
                    suffix = qldef.sw2_board_target_file_name  # 该行情板块文件为申万二级行业板块，用于与东财行业板块进行映射
                    subset = [qldef.inner_code_key, 'company_code']
                    sort_key = qldef.inner_code_key
                    # todo 去重合并 和 日期排序 耗时(仅查询历史数据需要，后期每日更新数据不需要) hhx
                    if process_lock is None:
                        save_df_to_file_csv(cache_dir, suffix, company_code_df, subset, sort_key, True, True)
                        dc_map_to_sw2()
                    else:
                        with process_lock:
                            save_df_to_file_csv(cache_dir, suffix, company_code_df, subset, sort_key, True, True)
                            dc_map_to_sw2()

            elif daily_quote_type == qldef.daily_quote_type.sw2_industry_type:
                # 查询申万二级行业板块指数时
                logutil.log.debug(
                    f"保存{len(date_list)}天的申万二级行业板块日度行情数据到csv文件耗时长：{execution_time} 秒")
                if dfutil.not_empty(industry_df):
                    # 将board_code(数据库为dtype('O')字符串类型)转为int类型，因为保存到csv文件时 转为int类型了
                    industry_df[qldef.board_code_key] = industry_df[qldef.board_code_key].astype(int)

                    suffix = 'zh_sw_second_industry.csv'  # 该行情板块文件为申万二级行业板块
                    subset = [qldef.board_code_key, qldef.board_name_key]
                    sort_key = qldef.board_code_key
                    if process_lock is None:
                        save_df_to_file_csv(cache_dir, suffix, industry_df, subset, sort_key, True, True)
                    else:
                        with process_lock:
                            save_df_to_file_csv(cache_dir, suffix, company_code_df, subset, sort_key, True, True)

        i += 1

    # 关闭cursor和连接
    cursor.close()
    conn.close()


# 开始从数据库查询 日度行情 和 板块行情
# skip_days：跳过天数（比如想获取20200101-20201231的数据，则需要跳过20210101-当前日期的天数）
# daily_quote_type：日度行情类型（默认为个股日度行情类型）


# ---------------- sqlite query helpers ----------------
def _sqlite_connect():
    return sqlite3.connect(DB_PATH)

def _clean_trade_date(series):
    # Handles both 'YYYYMMDD' and 'YYYY-MM-DD'
    # Convert to int to ensure consistent type for sorting
    cleaned = series.astype(str).str.replace('-', '', regex=False)
    return pd.to_numeric(cleaned, errors='coerce').fillna(0).astype(int)

def _process_single_stock(args):
    """
    处理单只股票的数据（用于多进程）
    Args:
        args: (stock_code, stock_data_dict, market, cache_dir)
            stock_data_dict: 包含stock_name和records的字典
    Returns:
        stock_code: 处理完成的股票代码
    """
    stock_code, stock_data_dict, market, cache_dir = args
    
    try:
        # 从字典重建DataFrame
        target_df = pd.DataFrame(stock_data_dict['records'])
        target_name = stock_data_dict.get('stock_name', '')
        
        target_df = target_df.sort_values('trade_date')
        
        # Rename to project-standard keys
        target_df = target_df.rename(columns={
            'stock_code': qldef.inner_code_key,
            'trade_date': qldef.date_key,
            'open_price': qldef.open_key,
            'high_price': qldef.high_key,
            'low_price': qldef.low_key,
            'close_price': qldef.close_key,
            'volume': qldef.turnover_vol_key,
            'turnover': qldef.turnover_value_key,
        })
        
        # Fill required columns
        if qldef.trade_status_key not in target_df.columns:
            target_df[qldef.trade_status_key] = 1
        if qldef.prev_close_key not in target_df.columns:
            target_df[qldef.prev_close_key] = target_df[qldef.close_key].shift(1)
            target_df[qldef.prev_close_key] = target_df[qldef.prev_close_key].fillna(target_df[qldef.close_key])
        
        # Add 'amount' field as alias for 'turnover'
        if 'amount' not in target_df.columns and qldef.turnover_value_key in target_df.columns:
            target_df['amount'] = target_df[qldef.turnover_value_key]
        
        # Save to CSV (without process_lock in worker process)
        save_daily_quote_to_csv(
            target_df,
            market,
            str(stock_code),
            qldef.daily_quote_type.stock_type,
            cache_dir
        )
        
        return stock_code
    except Exception as e:
        # 在子进程中打印错误（因为logutil可能不支持多进程）
        print(f'处理股票 {stock_code} 时出错: {e}')
        return None

def query_sqlite_daily_quote(start_date, end_date, market, cache_dir=None, process_lock=None):
    'Read daily_quote from sqlite and write the same csv artifacts as query_qt_daily_quote.'
    # Backward-compatible default: allow callers that don't pass cache_dir.
    if cache_dir is None:
        cache_dir = getattr(qldef, 'market_quotation_directory', os.path.join(os.path.dirname(__file__), 'cache_files', 'debug'))

    if not os.path.exists(DB_PATH):
        logutil.log.critical(f'SQLite DB 不存在: {DB_PATH}')
        return False

    # SQLite dates are stored as TEXT (e.g., '20260114'). Force params to str.
    start_date = str(start_date)
    end_date = str(end_date)

    with _sqlite_connect() as conn:
        sql = (
            "SELECT stock_code, stock_name, trade_date, open_price, high_price, low_price, close_price, volume, turnover"
            " FROM daily_quote"
            " WHERE REPLACE(trade_date,'-','') >= ? AND REPLACE(trade_date,'-','') <= ?"
        )
        df = pd.read_sql_query(sql, conn, params=(start_date, end_date))
        if df is None or df.empty:
            logutil.log.critical(f'SQLite daily_quote 无数据: {start_date} - {end_date}')
            return False

        # Build SW2 mapping file from stock_info + stock_industry
        try:
            map_sql = (
                "SELECT si.stock_code, si.stock_name, st.second_industry_code, st.second_industry_name"
                " FROM stock_info si LEFT JOIN stock_industry st ON si.stock_code = st.stock_code"
            )
            map_df = pd.read_sql_query(map_sql, conn)
            if map_df is not None and not map_df.empty:
                sw2_df = pd.DataFrame({
                    qldef.inner_code_key: map_df['stock_code'],
                    qldef.company_code_key: map_df['stock_code'],
                    qldef.target_key: map_df['stock_code'],
                    qldef.target_name_key: map_df['stock_name'],
                    qldef.board_code_key: map_df['second_industry_code'],
                    qldef.board_name_key: map_df['second_industry_name'],
                })
                qloption.database.write_file_csv(sw2_df, cache_dir, qldef.sw2_board_target_file_name, dfutil.index_false, process_lock)
        except Exception as e:
            logutil.log.debug(f'SQLite SW2 mapping 生成失败(可忽略): {e}')

    # Save per-stock daily quote files with multiprocessing
    df['trade_date'] = _clean_trade_date(df['trade_date'])
    
    # 准备任务列表：将DataFrame转为字典以便进程间传递
    tasks = []
    for stock_code, g in df.groupby('stock_code'):
        stock_data_dict = {
            'stock_name': g['stock_name'].iloc[0] if 'stock_name' in g.columns and len(g) > 0 else '',
            'records': g.to_dict('records')  # 转为字典列表
        }
        tasks.append((stock_code, stock_data_dict, market, cache_dir))
    
    # 使用多进程处理
    max_workers = min(multiprocessing.cpu_count(), 12)  # 最多12个进程
    logutil.log.info(f'使用 {max_workers} 个进程处理 {len(tasks)} 只股票的CSV文件生成...')
    
    process_start_time = time.time()
    
    cpu_count = multiprocessing.cpu_count()
    max_workers = max(1, cpu_count - 1)
    
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # results = list(executor.map(_process_single_stock, tasks))
        future_to_task = {executor.submit(_process_single_stock, task): task for task in tasks}
        
        from concurrent.futures import as_completed
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                res = future.result()
                results.append(res)
            except Exception as e:
                # task 是一个元组，通常第一个元素是股票代码或相关信息
                info = task[0] if len(task) > 0 else "unknown"
                logutil.log.error(f"处理股票数据失败: {info} - {e}")
                results.append(None) # 保持结果列表长度或逻辑一致性，视后续统计需要而定
    
    process_end_time = time.time()
    execution_time = process_end_time - process_start_time
    
    success_count = sum(1 for r in results if r is not None)
    logutil.log.info(f'完成处理 {success_count}/{len(tasks)} 只股票，耗时：{execution_time:.2f} 秒')
    
    return True

def query_sqlite_industry_quote(start_date, end_date, market, cache_dir=None, process_lock=None):
    'Read industry_quote from sqlite and write the same csv artifacts as query_sqlite_daily_quote.'
    # Backward-compatible default: allow callers that don't pass cache_dir.
    if cache_dir is None:
        cache_dir = getattr(qldef, 'market_quotation_directory', os.path.join(os.path.dirname(__file__), 'cache_files', 'debug'))

    if not os.path.exists(DB_PATH):
        logutil.log.critical(f'SQLite DB 不存在: {DB_PATH}')
        return False

    # SQLite dates are stored as TEXT (e.g., '20260114' or '2015-12-09'). Force params to str.
    start_date = str(start_date)
    end_date = str(end_date)

    with _sqlite_connect() as conn:
        # 1. Generate DC board target mapping file (zh_0_board_target.csv)
        try:
            # We need columns: inner_code, company_code, target, target_name, board_code, board_name
            # stock_industry has: stock_code, stock_name, second_industry_code, second_industry_name
            map_sql = (
                "SELECT stock_code, stock_name, second_industry_code, second_industry_name"
                " FROM stock_industry"
            )
            map_df = pd.read_sql_query(map_sql, conn)
            
            if map_df is not None and not map_df.empty:
                dc_board_df = pd.DataFrame({
                    qldef.inner_code_key: map_df['stock_code'],
                    qldef.company_code_key: map_df['stock_code'],
                    qldef.target_key: map_df['stock_code'],
                    qldef.target_name_key: map_df['stock_name'],
                    qldef.board_code_key: map_df['second_industry_code'],
                    qldef.board_name_key: map_df['second_industry_name'],
                    'board_type': qldef.industry_key, # Explicitly add board_type for compatibility
                })
                # Use default mode='w' and header=True. Ignore process_lock as it's not used by write_file_csv currently.
                qloption.database.write_file_csv(dc_board_df, cache_dir, qldef.dc_board_target_file_name)
                logutil.log.info(f"Generated DC board mapping file: {qldef.dc_board_target_file_name}")
        except Exception as e:
            logutil.log.error(f'SQLite DC board mapping generation failed: {e}')

        # 2. Query industry quotes
        sql = (
            "SELECT industry_code as stock_code, industry_name as stock_name, trade_date, open_price, high_price, low_price, close_price, volume, turnover"
            " FROM industry_quote"
            " WHERE REPLACE(trade_date,'-','') >= ? AND REPLACE(trade_date,'-','') <= ?"
        )
        df_db = pd.read_sql_query(sql, conn, params=(start_date, end_date))
        
        # 3. Check for missing industries and aggregate if necessary
        # Get total expected industries
        expected_industries_sql = "SELECT COUNT(DISTINCT second_industry_code) FROM stock_industry WHERE second_industry_code IS NOT NULL"
        expected_count = pd.read_sql_query(expected_industries_sql, conn).iloc[0, 0]
        
        db_industry_count = 0
        if df_db is not None and not df_db.empty:
            db_industry_count = df_db['stock_code'].nunique()
            
        # Check date coverage
        daily_quote_dates_sql = "SELECT count(DISTINCT trade_date) FROM daily_quote WHERE REPLACE(trade_date,'-','') >= ? AND REPLACE(trade_date,'-','') <= ?"
        daily_days = pd.read_sql_query(daily_quote_dates_sql, conn, params=(start_date, end_date)).iloc[0, 0]
        
        industry_days = 0
        min_industry_days = 0
        if df_db is not None and not df_db.empty:
            # Normalize trade_date to count unique days correctly (handle mixed 'YYYY-MM-DD' and 'YYYYMMDD')
            df_db_norm = df_db.copy()
            df_db_norm['norm_date'] = df_db_norm['trade_date'].astype(str).str.replace('-', '')
            industry_days = df_db_norm['norm_date'].nunique()
            
            # Check minimum coverage per industry to detect specific industry gaps (e.g. BK0465)
            industry_counts = df_db_norm.groupby('stock_code')['norm_date'].nunique()
            min_industry_days = industry_counts.min() if not industry_counts.empty else 0

        logutil.log.critical(f"DEBUG: daily_days={daily_days}, industry_days={industry_days}, min_industry_days={min_industry_days}, db_industry_count={db_industry_count}, expected_count={expected_count}")
        with open("debug_log.txt", "a") as f:
            f.write(f"DEBUG: daily_days={daily_days}, industry_days={industry_days}, min_industry_days={min_industry_days}, db_industry_count={db_industry_count}, expected_count={expected_count}\n")
            
        # If DB coverage is low (< 50% of expected) OR date coverage is low (< 95%) OR any industry has significant gaps, use aggregation
        df_agg = None
        if db_industry_count < (expected_count * 0.5) or (daily_days > 0 and industry_days < (daily_days * 0.95)) or (daily_days > 0 and min_industry_days < (daily_days * 0.95)):
            logutil.log.critical(f"DEBUG: Aggregation triggered!")
            with open("debug_log.txt", "a") as f:
                f.write("DEBUG: Aggregation triggered!\n")
            logutil.log.warning(f"Industry quote coverage low ({db_industry_count}/{expected_count}). Aggregating from daily_quote...")
            sql2 = (
                "SELECT "
                "  si.second_industry_code AS stock_code,"
                "  si.second_industry_name AS stock_name,"
                "  dq.trade_date,"
                "  AVG(dq.open_price) AS open_price,"
                "  MAX(dq.high_price) AS high_price,"
                "  MIN(dq.low_price) AS low_price,"
                "  AVG(dq.close_price) AS close_price,"
                "  SUM(dq.volume) AS volume,"
                "  SUM(dq.turnover) AS turnover"
                " FROM daily_quote dq"
                " JOIN stock_industry si ON dq.stock_code = si.stock_code"
                " WHERE REPLACE(dq.trade_date,'-','') >= ? AND REPLACE(dq.trade_date,'-','') <= ?"
                " GROUP BY si.second_industry_code, dq.trade_date"
            )
            df_agg = pd.read_sql_query(sql2, conn, params=(start_date, end_date))
            logutil.log.critical(f"DEBUG: df_agg size: {len(df_agg) if df_agg is not None else 0}")
            with open("debug_log.txt", "a") as f:
                f.write(f"DEBUG: df_agg size: {len(df_agg) if df_agg is not None else 0}\n")
        
        # Merge results (prefer DB data over aggregated data)
        if df_agg is not None and not df_agg.empty:
            # OPTIONAL: Write aggregated data back to DB to speed up future queries
            try:
                # Prepare data for insertion
                df_to_insert = df_agg.copy()
                df_to_insert = df_to_insert.rename(columns={
                    'stock_code': 'industry_code',
                    'stock_name': 'industry_name'
                })
                # Ensure columns match table structure (id, created_at handled by DB defaults if omitted)
                # But here we use 'to_sql' which might need alignment.
                # Actually, simpler to just insert main columns.
                
                # Check if we should insert. Only insert if we are sure it's new data.
                # Since we filtered out existing codes, these are new industries for this date range.
                
                # Add timestamp
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                df_to_insert['created_at'] = current_time
                
                # We need to ensure we don't insert duplicates if run multiple times in parallel.
                # SQLite INSERT OR IGNORE is useful here but pandas to_sql doesn't support it directly without tricks.
                # For now, let's just log that we *could* insert, or implement a safe insert.
                
                # Let's implement a safe row-by-row or batch insert with "INSERT OR IGNORE"
                # But to keep it simple and safe for now: 
                # We will perform the insert using SQL directly for better control.
                
                records_to_insert = df_to_insert[['industry_code', 'industry_name', 'trade_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume', 'turnover', 'created_at']].to_dict('records')
                
                if records_to_insert:
                    logutil.log.info(f"Persisting {len(records_to_insert)} aggregated industry records to SQLite...")
                    
                    insert_sql = """
                    INSERT OR IGNORE INTO industry_quote 
                    (industry_code, industry_name, trade_date, open_price, high_price, low_price, close_price, volume, turnover, created_at)
                    VALUES (:industry_code, :industry_name, :trade_date, :open_price, :high_price, :low_price, :close_price, :volume, :turnover, :created_at)
                    """
                    conn.executemany(insert_sql, records_to_insert)
                    conn.commit()
                    logutil.log.info("Persist complete.")
                    
            except Exception as e:
                logutil.log.error(f"Failed to persist aggregated industry data: {e}")

            # If aggregation occurred, use aggregated data as it is more complete/current for the requested range
            if df_agg is not None and not df_agg.empty:
                df = df_agg
                logutil.log.critical(f"DEBUG: Using aggregated data (size: {len(df)}) instead of DB data.")
            elif df_db is not None and not df_db.empty:
                df = df_db
            else:
                df = None
        else:
            df = df_db

        if df is None or df.empty:
            logutil.log.warning(f'SQLite industry_quote No Data: {start_date} - {end_date}')
            return False

    # Save per-industry daily quote files with multiprocessing
    df['trade_date'] = _clean_trade_date(df['trade_date'])
    
    # Prepare task list
    tasks = []
    for stock_code, g in df.groupby('stock_code'):
        stock_data_dict = {
            'stock_name': g['stock_name'].iloc[0] if 'stock_name' in g.columns and len(g) > 0 else '',
            'records': g.to_dict('records')
        }
        tasks.append((stock_code, stock_data_dict, market, cache_dir))
    
    # Multiprocessing
    cpu_count = multiprocessing.cpu_count()
    max_workers = max(1, cpu_count - 1)
    
    logutil.log.info(f'Processing {len(tasks)} industry quotes with {max_workers} processes...')
    
    process_start_time = time.time()
    
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {executor.submit(_process_single_stock, task): task for task in tasks}
        
        from concurrent.futures import as_completed
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                res = future.result()
                results.append(res)
            except Exception as e:
                info = task[0] if len(task) > 0 else "unknown"
                logutil.log.error(f"Failed to process industry quote: {info} - {e}")
                results.append(None)
    
    process_end_time = time.time()
    execution_time = process_end_time - process_start_time
    
    success_count = sum(1 for r in results if r is not None)
    logutil.log.info(f'Completed {success_count}/{len(tasks)} industry quotes in {execution_time:.2f} seconds')
    
    return True

def query_database(total_day_count, per_query_day_count, skip_days=0,
                   daily_quote_type=qldef.daily_quote_type.stock_type, process_lock=None):
    # SQLite fast-path (mirror the date range computed in query_qt_daily_quote/query_qt_industry_quote)
    if globals().get('USE_SQLITE', False) and os.path.exists(DB_PATH):
        market = qldef.china_market_key
        cache_dir = qldef.market_quotation_directory
        date_now = dfutil.date_now()
        end_date = date_now
        start_date = dfutil.get_date_from_now(total_day_count + skip_days, end_date)
        if daily_quote_type == qldef.daily_quote_type.stock_type:
            return query_sqlite_daily_quote(start_date, end_date, market, cache_dir, process_lock)
        if daily_quote_type == qldef.daily_quote_type.sw2_industry_type:
            return query_sqlite_industry_quote(start_date, end_date, market, cache_dir, process_lock)


    # 设置数据库连接参数
    server = ''
    database = ''
    user = ''
    password = ''
    query_qt_daily_quote(server, database, user, password, total_day_count, per_query_day_count,
                         skip_days, daily_quote_type, process_lock)


# 开始查询日度行情数据
def start_query_database(start_date: int, end_date: int, daily_quote_type=qldef.daily_quote_type.stock_type,
                         process_lock=None):
    logutil.log.debug(f"开始从数据库查询{start_date} - {end_date}日度行情 和 板块行情...")
    # 开始计时
    start_time = time.time()

    # SQLite shortcut: use the caller-provided date window directly.
    # The original workflow calculates "skip_days" from end_date to today and may
    # expand the query window unexpectedly. When we already have a local sqlite DB,
    # it is safer and faster to export exactly the requested range.
    if globals().get('USE_SQLITE', False) and os.path.exists(DB_PATH) and daily_quote_type in (
            qldef.daily_quote_type.stock_type, qldef.daily_quote_type.sw2_industry_type):
        market = getattr(qldef, 'china_market_key', 'zh')
        cache_dir = getattr(qldef, 'market_quotation_directory', os.path.join(os.path.dirname(__file__), 'cache_files'))
        if daily_quote_type == qldef.daily_quote_type.stock_type:
            ok = query_sqlite_daily_quote(start_date, end_date, market, cache_dir, process_lock)
        else:
            ok = query_sqlite_industry_quote(start_date, end_date, market, cache_dir, process_lock)
        end_time = time.time()
        logutil.log.critical(
            f"从数据库查询{start_date} - {end_date}{'个股' if daily_quote_type == qldef.daily_quote_type.stock_type else '行业'}日度行情 并保存csv文件，总耗时长：{end_time - start_time} 秒"
        )
        return ok
    # 执行代码
    date_now = dfutil.date_now()
    skip_days_list = dfutil.get_date_list(end_date, date_now)
    skip_days = len(skip_days_list) - 1

    date_list = dfutil.get_date_list(start_date, end_date)
    total_days = len(date_list)  # 3 * 365  # 总查询天数
    per_query_days = 73  # 每次查询的天数
    if total_days < per_query_days:
        per_query_days = total_days

    query_database(total_days, per_query_days, skip_days, daily_quote_type, process_lock)

    if daily_quote_type == qldef.daily_quote_type.hs300_type:
        label = '沪深300指数日度行情'
    elif daily_quote_type == qldef.daily_quote_type.sw2_industry_type:
        label = '申万二级行业板块'
    else:
        label = '个股日度行情'

    # 结束计时
    end_time = time.time()
    execution_time = end_time - start_time
    logutil.log.critical(f"从数据库查询{start_date} - {end_date}{label} 并保存csv文件，"
                         f"总耗时长：{execution_time} 秒")


# 开始查询个股日度行情数据（默认包含沪深300指数日度行情数据）
def start_query_stock_daily_quote(start_date: int, end_date: int, process_lock: Lock = None):
    start_query_database(start_date, end_date, qldef.daily_quote_type.stock_type, process_lock)


# 开始查询沪深300指数日度行情数据
def start_query_hs300_daily_quote(start_date: int, end_date: int, process_lock: Lock = None):
    start_query_database(start_date, end_date, qldef.daily_quote_type.hs300_type, process_lock)


# 开始查询申万二级行业板块日度行情数据
def start_query_sw2_industry_daily_quote(start_date: int, end_date: int, process_lock: Lock = None):
    start_query_database(start_date, end_date, qldef.daily_quote_type.sw2_industry_type, process_lock)
