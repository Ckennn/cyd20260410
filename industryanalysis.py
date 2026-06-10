"""
industryanalysis.py
qlsignalNew_20240808
Created by huanghx on 2024/8/9
Copyright © 2024 huanghx. All rights reserved.
"""
import os
import time
from decimal import Decimal, ROUND_HALF_UP
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
from pandas._typing import Suffixes

import dfutil
import logutil
import qldef
import qloption
import tradedateutil

is_clearance_state = False  # 当前是否在清盘状态


# 删除df中列名含有suffix后缀的列
def delete_df_suffix_column(df, suffix='_y'):
    # 删除所有列名中包含"_y"的列
    columns = df.columns
    new_columns = [col for col in columns if suffix not in col]
    df_result = df[new_columns]
    return df_result


# 从3个参数里，返回非空的list集合
def get_non_empty_list(param0, param1, param2):
    # 创建所有可能组合的列表
    combos = [param0, param1, param2]
    # 迭代所有组合，只保留非空的
    non_empty_combos = [combo for combo in combos if dfutil.not_empty(combo)]
    return non_empty_combos


# 获取指定日期的量化结果所在文件名（通过文件名中的日期范围来判断，避免不断读取文件来查找，提升效率）
def get_result_file_path(date: int):
    cache_dir = qldef.quantitative_result_directory
    filelist = dfutil.get_all_files(cache_dir, 'results')
    for file_path in filelist:
        # 使用os.path.basename获取文件名
        # prefix = os.path.dirname(file_path)
        suffix = os.path.basename(file_path)
        
        # Filter for trigger files only, to avoid picking up summary or trades files
        if 'trigger' not in suffix:
            continue
            
        segments = suffix.split('_')
        if len(segments) > 4:
            start_date_int = int(segments[2])
            end_date_int = int(segments[3])
            if (start_date_int <= date) and (date <= end_date_int):
                # Verify header has signal_key to avoid using stale files
                try:
                    # Read first line only
                    with open(file_path, 'r', encoding='utf-8') as f:
                        header = f.readline()
                        if qldef.signal_key in header:
                            return file_path
                except Exception:
                    continue


# 获取指定日期的量化股票列表
def get_selected_result_stocks(date: int, board_name: str = ''):
    file_path = get_result_file_path(date)
    if dfutil.len_safe(file_path) > 0:
        df = qloption.database.read_single_big_csv(file_path)
        if dfutil.not_empty(df):
            # Ensure required columns exist
            if 'date' not in df.columns or qldef.board_name_key not in df.columns:
                return pd.DataFrame()
                
            if len(board_name) == 0:
                # Use bracket notation for safer access and fix logic for checking non-empty board_name
                df_date = df[(df['date'] == date) & (df[qldef.board_name_key].astype(str).str.len() > 0)]
            else:
                df_date = df[(df['date'] == date) & (df[qldef.board_name_key] == board_name)]
            return df_date


def check_restore_clearance_state(date_list, selected_limit_count: int, is_buy: bool = True):
    """
    检查当前是否可恢复“清仓状态”，满足条件如下：
    当T0,T1个股数量上升，且超过400，则恢复交易机制
    优化：如果T0单日暴增（超过800或环比翻倍），也立即恢复
    @param date_list：日期列表
    @param selected_limit_count：指定日期选择股票数量参考值（比如400）
    @param is_buy: 是否买入业务
    """
    global is_clearance_state  # 声明全局变量

    # 如果当前没有在“清仓”状态 或者 不是买入业务，则直接返回
    if (not is_clearance_state) or (not is_buy):
        return

    i = 0
    df_date0 = None # T-2
    df_date1 = None # T-1
    df_date2 = None # T0 (最新)
    date_list.sort()  # 执行卖出策略时，按升序排序
    while i < dfutil.len_safe(date_list):
        date_int = date_list[i]
        if i == 0:
            df_date0 = get_selected_result_stocks(date_int)
        elif i == 1:
            df_date1 = get_selected_result_stocks(date_int)
        elif i == 2:
            df_date2 = get_selected_result_stocks(date_int)
        i += 1
    
    count0 = dfutil.len_safe(df_date0)
    count1 = dfutil.len_safe(df_date1)
    count2 = dfutil.len_safe(df_date2) # T0 (最新)

    # 原逻辑：T1 > 400 且 T2 > T1 (温和回升)
    condition_gentle = (count1 >= selected_limit_count) and (count2 > count1)
    
    # 新逻辑：T0 > 800 (暴力反转) 或 T0 > T1 * 2 (环比翻倍，且绝对值不低)
    condition_aggressive = (count2 >= selected_limit_count * 2) or (count2 > count1 * 2 and count2 > selected_limit_count)

    if condition_gentle or condition_aggressive:
        is_clearance_state = False
        logutil.log.critical(f"🟢 解除熔断 (Restore): T0={count2}, T1={count1}, T2={count0} (Aggressive={condition_aggressive})")


def check_set_clearance_state(date_list, selected_limit_count: float, rate: float) -> bool:
    """
    检查是否设置符合“清仓状态”
    当T0参数大于selected_limit_count（默认1000），T1和T2选出“个股”的数量小于1000，数量连续下降且T1或T2下降
    幅度较T0数量减少50%及以上则在T3开盘清仓
    @param date_list：日期列表
    @param selected_limit_count：指定日期选择股票数量参考值（比如1000）
    @param rate：选择个股数量的下降比率（比如下降一半为0.5）
    """
    global is_clearance_state  # 声明全局变量

    # delete by hhx 2024.09.03
    # if is_buy:
    #     return False

    i = 0
    df_date0 = None
    df_date1 = None
    df_date2 = None
    date_list.sort()  # 执行卖出策略时，按升序排序
    while i < dfutil.len_safe(date_list):
        date_int = date_list[i]
        if i == 0:
            df_date0 = get_selected_result_stocks(date_int)
        elif i == 1:
            df_date1 = get_selected_result_stocks(date_int)
        elif i == 2:
            df_date2 = get_selected_result_stocks(date_int)
        i += 1

    if ((dfutil.len_safe(df_date0) >= selected_limit_count)
            and (dfutil.len_safe(df_date1) < selected_limit_count)
            and (dfutil.len_safe(df_date2) < selected_limit_count)
            and ((dfutil.len_safe(df_date0) * rate >= dfutil.len_safe(df_date1))
                 or (dfutil.len_safe(df_date0) * rate >= dfutil.len_safe(df_date2)))):
        is_clearance_state = True
        logutil.log.critical(f"🔴 触发熔断 (Clearance): T0={dfutil.len_safe(df_date0)}, T1={dfutil.len_safe(df_date1)}, T2={dfutil.len_safe(df_date2)}")
        return True
    else:
        return False


# 在3个df数据中出现2-3次的数据（比如买入交易策略）
# 修改逻辑：只要行业板块在3天内出现2-3次，则选取该板块在最新一天（或最近有效日）的个股
def get_2_or_3_result(dates, industry_params_df, merge_on, merge_suffixes=None, is_buy: bool = True):
    if merge_suffixes is None:
        merge_suffixes = ['_x', '_y']

    # 确保日期按升序排列 [T-2, T-1, T0]
    dates.sort()
    
    select_industry_tuple_list = []
    valid_boards_by_date = []
    
    for date_int in dates:
        # select_industry_stocks 返回 [df_result, df_fit_sell_low_policy]
        tuple_res = select_industry_stocks(date_int, industry_params_df, is_buy=is_buy)
        select_industry_tuple_list.append(tuple_res)
        
        df_res = tuple_res[0] if tuple_res and len(tuple_res) > 0 else None
        
        if dfutil.not_empty(df_res):
            boards = set(df_res[qldef.board_name_key].unique())
            valid_boards_by_date.append(boards)
        else:
            valid_boards_by_date.append(set())

    # 逻辑：板块必须在3天内至少出现2次
    # 优化：放宽条件，允许板块在5天内至少出现2次
    # 注意：dates 长度可能只有3，需要兼容
    all_boards = set()
    for s in valid_boards_by_date:
        all_boards.update(s)
        
    final_boards = set()
    for board in all_boards:
        count = 0
        for s in valid_boards_by_date:
            if board in s:
                count += 1
        
        # 优化：放宽筛选条件，如果板块在3天内至少有1天活跃，且该天活跃股数量较多，也可以纳入
        # 但为了保持逻辑一致性，这里先只放宽到 "3天内至少1次" 或者维持 "3天内2次" 但降低活跃阈值
        # 考虑到 Step 2 信号量巨大但 Step 3 过滤后极少，说明 "3天2热" 太严了
        # 尝试改为：3天内至少1次活跃
        if count >= 1: 
            final_boards.add(board)
    
    # DEBUG LOGGING
    # logutil.log.info(f"Date: {dates[-1]}, Valid Boards by date: {valid_boards_by_date}")
    # logutil.log.info(f"Final Boards: {final_boards}")
            
    if not final_boards:
        return None
        
    # 为这些板块选择股票
    # 策略：优先选择最新日期（T0）的股票，如果T0没有，则选择T-1，再T-2
    # dates是升序，所以索引2是最新
    
    df_result_list = []
    
    # 获取每一天的结果DataFrame
    df_list = [t[0] if t and len(t)>0 else None for t in select_industry_tuple_list]
    
    for board in final_boards:
        # 检查 T0 (dates[2])
        if dfutil.not_empty(df_list[2]) and board in valid_boards_by_date[2]:
            df_subset = df_list[2][df_list[2][qldef.board_name_key] == board]
            df_result_list.append(df_subset)
        # 检查 T-1 (dates[1])
        elif dfutil.not_empty(df_list[1]) and board in valid_boards_by_date[1]:
            df_subset = df_list[1][df_list[1][qldef.board_name_key] == board]
            df_result_list.append(df_subset)
        # 检查 T-2 (dates[0])
        elif dfutil.not_empty(df_list[0]) and board in valid_boards_by_date[0]:
            df_subset = df_list[0][df_list[0][qldef.board_name_key] == board]
            df_result_list.append(df_subset)
            
    df_result = None
    if df_result_list:
        # 合并结果并去重
        df_result = pd.concat(df_result_list, ignore_index=True).drop_duplicates(subset=merge_on)

    return df_result


# 根据行业板块名获取对应板块的个股总数量 - todo 暂时没有使用
# 返回值：size（如果为-1，则表示还未生成当日的日度行情数据，比如明天/后天等）
def get_board_size(date, board_name):
    size = -1
    """
    cache_dir = qldef.quantitative_result_directory
    filelist = dfutil.get_all_files(cache_dir, 'results')
    for file_path in filelist:
        df = qloption.database.read_single_big_csv(file_path)
        if dfutil.not_empty(df):
            df_date = df[(df.date == date) & (len(df.board_name) > 0)]
            if dfutil.not_empty(df_date):
                # 将行业板块数据分类并计算总数
                df_category = df_date.groupby(qldef.board_name_key, as_index=False).size()
                size_list = df_category.loc[df_category[qldef.board_name_key] == board_name]['size']
                if len(size_list) > 0:
                    size = size_list.iloc[0]  # Series取值方式
                break
    """

    df_result = get_selected_result_stocks(date, board_name)
    if dfutil.not_empty(df_result):
        size = len(df_result)

    return size


# 比较T1日比T0日的板块数量 - todo 暂时没有使用
# 返回值：如果下降，则为True；否则为False
def compare_board_size(date, board_name, board_size):
    size = get_board_size(date, board_name)
    if size < board_size:
        return True
    else:
        return False


# 根据行业板块名称获取符合对应条件的板块个股
# date：日期
# board_name：行业板块名称
# prev_size：上一天符合策略的行业板块的个股数量
# is_buy：交易业务类型(买入 or 卖出)
def get_date_board_df(date, board_name, prev_size, is_buy: bool = True):
    size = -1  # 如果为-1，则表示还未生成当日的日度行情数据，比如明天/后天等
    df_select_board = None
    df_date = get_selected_result_stocks(date)
    if dfutil.not_empty(df_date):
        # 计算对应行业板块个股数量

        # 方法1：将行业板块数据分类并计算总数
        # df_category = df_date.groupby(qldef.board_name_key, as_index=False).size()
        # size_list = df_category.loc[df_category[qldef.board_name_key] == board_name]['size']
        # if len(size_list) > 0:
        #     size = int(size_list.iloc[0])  # Series取值方式：使用int()函数将np.int64转换为int类型
        # 方法2
        df_date_board = df_date[(df_date[qldef.board_name_key] == board_name)]
        size = len(df_date_board)
        if is_buy:
            # 买入交易策略时
            if size >= prev_size:
                # 如果指定日期比上一日板块个股数量上涨，则返回对应板块的个股；否则返回空
                df_select_board = df_date_board
        else:
            # 卖出交易策略时
            if (size > 0) & (size < prev_size):  # 注意：两个判断条件都要加上()，否则会判断错误！！！
                # 如果指定日期比上一日板块个股数量下降，则返回对应板块的个股；否则返回空
                df_select_board = df_date_board

    return df_select_board


# 根据行业板块名称获取符合对应条件的板块个股
# df_date：指定日期的量化股票列表
# board_name：行业板块名称
# prev_size：上一天符合策略的行业板块的个股数量
# is_buy：交易业务类型(买入 or 卖出)
def get_board_df(df_date, board_name, prev_size, is_buy: bool = True):
    size = -1  # 如果为-1，则表示还未生成当日的日度行情数据，比如明天/后天等
    df_select_board = None
    # df_date = get_selected_result_stocks(date)
    if dfutil.not_empty(df_date):
        # 计算对应行业板块个股数量

        # 方法1：将行业板块数据分类并计算总数
        # df_category = df_date.groupby(qldef.board_name_key, as_index=False).size()
        # size_list = df_category.loc[df_category[qldef.board_name_key] == board_name]['size']
        # if len(size_list) > 0:
        #     size = int(size_list.iloc[0])  # Series取值方式：使用int()函数将np.int64转换为int类型
        # 方法2
        df_date_board = df_date[(df_date[qldef.board_name_key] == board_name)]
        size = len(df_date_board)
        if is_buy:
            # 买入交易策略时
            if size >= prev_size:
                # 如果指定日期比上一日板块个股数量上涨，则返回对应板块的个股；否则返回空
                df_select_board = df_date_board
        else:
            # 卖出交易策略时
            if (size > 0) & (size < prev_size):  # 注意：两个判断条件都要加上()，否则会判断错误！！！
                # 如果指定日期比上一日板块个股数量下降，则返回对应板块的个股；否则返回空
                df_select_board = df_date_board

    return df_select_board


# 卖出交易策略：T0行业板块数量超过设置参数时，T1,T2参数连续两天下降，则在T3天开盘卖出；若T0参数低于10则T1开盘卖出。
# 买入交易策略：T0行业板块数量超过设置参数时，T1,T2参数连续两天上涨，则在T3天开盘买入。
# def get_continue_n_result(dates, merge_on, select_policy: int, merge_suffixes=None, is_buy: bool = False):
def get_continue_n_result(dates, industry_params_df, merge_on, merge_suffixes=None, is_buy: bool = False,
                          is_merge=True):
    if merge_suffixes is None:
        merge_suffixes = ['_x', '_y']

    df_result = None
    df_fit_sell_low_policy = None
    is_has_init = False
    # t0_board_size_list = []
    t1_board_size_dic = {}
    # t2_board_size_list = []

    dates.sort()  # 执行卖出策略时，按升序排序
    i = 0
    while i < len(dates):
        date_int = dates[i]
        if i == 0:
            select_industry_tuple = select_industry_stocks(date_int, industry_params_df, is_buy)
            if len(select_industry_tuple) > 1:
                df_select_stocks = select_industry_tuple[0]
                if is_has_init:
                    if (df_select_stocks is not None) & (df_result is not None):
                        if is_merge:
                            # 计算两个df的交集，on=['mtn', 'board_name']表示这两列的会合并，而其他列表名会加上‘_y’后缀
                            df_result = pd.merge(df_result, df_select_stocks, on=merge_on,
                                                 suffixes=merge_suffixes)
                        else:
                            # 计算两个df的并集 并 去重
                            df_result = pd.concat([df_result, df_select_stocks],
                                                  ignore_index=True).drop_duplicates(subset=merge_on)
                    else:
                        df_result = None
                else:
                    df_result = df_select_stocks
                    is_has_init = True

        elif i == 1:  # 注意：两个判断条件都要加上()，否则会判断错误！！！
            # 当T0行业板块个股总数超出卖出参数时，当T1<T0时，则符合卖出条件，保留；否则剔除
            if dfutil.not_empty(df_result):
                # 获取指定日期的量化股票列表
                df_date = get_selected_result_stocks(date_int)
                # 将行业板块数据分类并计算总数
                df_category = df_result.groupby(qldef.board_name_key, as_index=False).size()
                for index, row in df_category.iterrows():
                    name = row[qldef.board_name_key]

                    # count = df_result[qldef.board_name_key].value_counts()[board_name] # 计算特定列中某个值的总行数
                    t0_board_size = row['size']
                    # t0_board_size_list.append(t0_board_size)
                    # t1_board_size = get_board_size(date_int, name)

                    # 根据行业板块名称获取符合对应条件的板块个股
                    df_board = get_board_df(df_date, name, t0_board_size, is_buy)
                    if dfutil.not_empty(df_board):
                        t1_board_size = len(df_board)
                        if t1_board_size >= 0:
                            # t1_board_size_list.append(t1_board_size)
                            t1_board_size_dic[name] = t1_board_size

                            df_result_board_name = df_result[df_result[qldef.board_name_key] == name]
                            if dfutil.not_empty(df_result_board_name):
                                if is_merge:
                                    # 计算两个df的交集，on=['mtn', 'board_name']表示这两列的会合并，而其他列表名会加上‘_y’后缀
                                    df_merge = pd.merge(df_result_board_name, df_board, on=merge_on,
                                                        suffixes=merge_suffixes)
                                    df_result = df_result[df_result[qldef.board_name_key] != name]
                                    if dfutil.not_empty(df_merge):
                                        df_result = pd.concat([df_result, df_merge],
                                                              ignore_index=True).drop_duplicates(subset=merge_on)
                                    df_result = delete_df_suffix_column(df_result)
                                else:
                                    # 计算两个df的并集 并 去重
                                    df_result = pd.concat([df_result, df_board],
                                                          ignore_index=True).drop_duplicates(subset=merge_on)

                        else:
                            df_result = df_result[df_result[qldef.board_name_key] != name]
                    else:
                        df_result = df_result[df_result[qldef.board_name_key] != name]

        elif i == 2:
            # 当T0行业板块个股总数超出卖出参数时，当T1<T0时，则符合卖出条件，保留；否则剔除
            if dfutil.not_empty(df_result):
                # 获取指定日期的量化股票列表
                df_date = get_selected_result_stocks(date_int)
                # 将行业板块数据分类并计算总数
                df_category = df_result.groupby(qldef.board_name_key, as_index=False).size()
                for index, row in df_category.iterrows():
                    name = row[qldef.board_name_key]

                    # count = df_result[qldef.board_name_key].value_counts()[board_name] # 计算特定列中某个值的总行数
                    # t1_board_size = t1_board_size_list[index]
                    # t2_board_size = get_board_size(date_int, name)
                    t1_board_size = t1_board_size_dic.get(name)
                    if t1_board_size is not None: # Ensure key exists
                        df_board = get_board_df(df_date, name, t1_board_size, is_buy)
                        if dfutil.not_empty(df_board):
                            t2_board_size = len(df_board)
                            if t2_board_size >= 0:
                                df_result_board_name = df_result[df_result[qldef.board_name_key] == name]
                                if dfutil.not_empty(df_result_board_name):
                                    if is_merge:
                                        # 计算两个df的交集，on=['mtn', 'board_name']表示这两列的会合并，而其他列表名会加上‘_y’后缀
                                        df_merge = pd.merge(df_board, df_result_board_name, on=merge_on,
                                                            suffixes=merge_suffixes)
                                        df_result = df_result[df_result[qldef.board_name_key] != name]
                                        if dfutil.not_empty(df_merge):
                                            df_result = pd.concat([df_result, df_merge],
                                                                  ignore_index=True).drop_duplicates(subset=merge_on)
                                        df_result = delete_df_suffix_column(df_result)
                                    else:
                                        # 计算两个df的并集 并 去重
                                        df_result = pd.concat([df_result, df_board],
                                                              ignore_index=True).drop_duplicates(subset=merge_on)
                            else:
                                df_result = df_result[df_result[qldef.board_name_key] != name]
                        else:
                            df_result = df_result[df_result[qldef.board_name_key] != name]
                    else: # Key not found, remove from result
                         df_result = df_result[df_result[qldef.board_name_key] != name]

            if not is_buy:
                # 判断：若T0参数低于10，则T1开盘卖出
                select_industry_tuple = select_industry_stocks(date_int, industry_params_df, is_buy)
                if len(select_industry_tuple) > 1:
                    df_low_policy = select_industry_tuple[1]
                    if dfutil.not_empty(df_low_policy):
                        if dfutil.empty(df_fit_sell_low_policy):
                            df_fit_sell_low_policy = df_low_policy
                        else:
                            # drop_duplicates表示去重，subset指定对应列的数据进行去重，ignore_index表示重新设置索引排序
                            df_fit_sell_low_policy = pd.concat([df_fit_sell_low_policy, df_low_policy],
                                                               ignore_index=True).drop_duplicates(subset=merge_on)

        i += 1

    if not is_buy:
        if (dfutil.not_empty(df_fit_sell_low_policy)) & (dfutil.not_empty(df_result)):
            # drop_duplicates表示去重，subset指定对应列的数据进行去重，ignore_index表示重新设置索引排序
            df_result = pd.concat([df_result, df_fit_sell_low_policy],
                                  ignore_index=True).drop_duplicates(subset=merge_on)
        elif dfutil.not_empty(df_fit_sell_low_policy):
            df_result = df_fit_sell_low_policy

    return df_result


# 选择符合指定策略的行业股票
# date 指定日期
# select_policy 选择策略，比如60
# is_buy 是否选择待买入的股票（默认为True，传False，则选择待卖出的股票）
# 返回符合策略的行业板块列表
# def select_industry_stocks(date: int, select_policy: int = 0, is_buy: bool = True):
def select_industry_stocks(date: int, industry_params_df, is_buy: bool = True):
    """
    df_result = None
    df_fit_sell_low_policy = None
    # industry_params_file_path = qldef.file_cache_path + '/industry_parameters_model.csv'
    # industry_params_df = qloption.database.read_single_big_csv(industry_params_file_path)
    if dfutil.not_empty(industry_params_df):
        df_date = get_selected_result_stocks(date)
        if dfutil.not_empty(df_date):
            # 将行业板块数据分类并计算总数
            df_category = df_date.groupby(qldef.board_name_key, as_index=False).size()
            for index, row in df_category.iterrows():
                size = row['size']
                board_name = row[qldef.board_name_key]
                is_fit_strategy = False
                is_fit_sell_low_policy = False
                board_row_index = -1
                if dfutil.not_empty(board_name):
                    # 获取对应行业板块名的行索引
                    # df_param = df_industry_params[df_industry_params[qldef.board_name_key] == board_name]
                    board_row_list = industry_params_df.index[
                        industry_params_df[qldef.board_name_key] == board_name].tolist()
                    if len(board_row_list) > 0:
                        board_row_index = board_row_list[0]
                    if board_row_index >= 0:
                        if is_buy:
                            # buy_policy = select_policy
                            buy_param = industry_params_df.loc[board_row_index, 'buy_param']
                            if dfutil.not_empty(buy_param):
                                try:
                                    if isinstance(buy_param, str) and '%' in buy_param:
                                        percent = float(buy_param.replace('%', '')) / 100.0
                                        # Find stock count column (e.g. stock_count_2024)
                                        stock_count_col = next((col for col in industry_params_df.columns if col.startswith('stock_count_')), None)
                                        if stock_count_col:
                                            total_count = float(industry_params_df.loc[board_row_index, stock_count_col])
                                            buy_policy = total_count * percent
                                        else:
                                            buy_policy = 99999 # Fail safely
                                    else:
                                         buy_policy = float(buy_param)
                                         
                                     is_fit_strategy = size >= buy_policy
                                     if is_fit_strategy:
                                          logutil.log.debug(f"Buy strategy fit: board={board_name}, size={size}, policy={buy_policy}")
                                      else:
                                          logutil.log.debug(f"Buy strategy mismatch: board={board_name}, size={size}, policy={buy_policy}")
                                          pass
                                 except Exception as e:
                                    logutil.log.error(f"Error parsing buy_param '{buy_param}' for board '{board_name}': {e}")
                                    is_fit_strategy = False
                                    
                            # is_fit_strategy = size >= buy_policy  # 考虑默认初始值select_policy
                        else:
                            # sell_high_policy = select_policy
                            # sell_low_policy = 10  # 初始化值
                            sell_policy = industry_params_df.loc[board_row_index, 'sell_param']
                            if dfutil.not_empty(sell_policy):
                                segments = sell_policy.split("/")
                                if len(segments) > 1:
                                    sell_high_policy = segments[0]
                                    sell_low_policy = segments[1]
                                    # 不考虑默认初始值select_policy
                                    if size >= int(sell_high_policy):
                                        is_fit_strategy = True
                                    elif size < int(sell_low_policy):
                                        is_fit_sell_low_policy = True

                            # 考虑默认初始值select_policy
                            # if size >= int(sell_high_policy):
                            #     is_fit_strategy = True
                            # elif size < int(sell_low_policy):
                            #     is_fit_sell_low_policy = True

                if is_fit_sell_low_policy or is_fit_strategy:
                    df_select_board = df_date[(df_date[qldef.board_name_key] == board_name)]
                    if dfutil.not_empty(df_select_board):
                        if is_fit_sell_low_policy:
                            if dfutil.empty(df_fit_sell_low_policy):
                                # 初始化列名
                                df_fit_sell_low_policy = pd.DataFrame(df_select_board, columns=df_date.columns)
                            else:
                                # 将新行添加到DataFrame中（由于pandas库的更新，2.0及以后得版本把append()这个方法给删除了，取而代之的是concat()方法）
                                df_fit_sell_low_policy = pd.concat(
                                    [df_fit_sell_low_policy, pd.DataFrame(df_select_board, columns=df_date.columns)],
                                    ignore_index=True)
                        elif is_fit_strategy:
                            if dfutil.empty(df_result):
                                # 初始化列名
                                df_result = pd.DataFrame(df_select_board, columns=df_date.columns)
                            else:
                                # 将新行添加到DataFrame中（由于pandas库的更新，2.0及以后得版本把append()这个方法给删除了，取而代之的是concat()方法）
                                df_result = pd.concat(
                                    [df_result, pd.DataFrame(df_select_board, columns=df_date.columns)],
                                    ignore_index=True)

    if dfutil.not_empty(df_result):
        df_result = df_result.reset_index(drop=True)  # 删除现有索引，并将其转换为默认的整数索引

    if dfutil.not_empty(df_fit_sell_low_policy):
        df_fit_sell_low_policy = df_fit_sell_low_policy.reset_index(drop=True)  # 删除现有索引，并将其转换为默认的整数索引

    return [df_result, df_fit_sell_low_policy]
    """
    return select_industry_stocks2(date, industry_params_df, is_buy)


# 选择符合指定策略的行业股票
# date 指定日期
# select_policy 选择策略，比如60
# is_buy 是否选择待买入的股票（默认为True，传False，则选择待卖出的股票）
# 返回符合策略的行业板块列表
# def select_industry_stocks(date: int, select_policy: int = 0, is_buy: bool = True):
def select_industry_stocks2(date: int, industry_params_df, is_buy: bool = True):
    df_result = None
    df_fit_sell_low_policy = None
    if dfutil.not_empty(industry_params_df):
        df_date = get_selected_result_stocks(date)
        if dfutil.not_empty(df_date):
            date_four_digits = str(date)[:4]  # 取整型数字前4位（即取年份）
            stock_count_key = 'stock_count' + '_' + date_four_digits

            # 将行业板块数据分类并计算总数
            df_category = df_date.groupby(qldef.board_name_key, as_index=False).size()
            for index, row in df_category.iterrows():
                size = row['size']
                board_name = row[qldef.board_name_key]
                is_fit_strategy = False
                is_fit_sell_low_policy = False
                board_row_index = -1
                if dfutil.not_empty(board_name):
                    # 获取对应行业板块名的行索引
                    # df_param = df_industry_params[df_industry_params[qldef.board_name_key] == board_name]
                    board_row_list = industry_params_df.index[
                        industry_params_df[qldef.board_name_key] == board_name].tolist()
                    if dfutil.len_safe(board_row_list) > 0:
                        board_row_index = board_row_list[0]
                    if board_row_index >= 0:
                        # 对应行业板块的个股总数
                        stock_count = industry_params_df.loc[board_row_index, stock_count_key]

                        if is_buy:
                            # buy_policy = select_policy
                            buy_param = industry_params_df.loc[board_row_index, 'buy_param']
                            if (dfutil.not_empty(buy_param)) and (dfutil.of_str(buy_param)):
                                buy_param_float = dfutil.percent_string_to_float(buy_param)
                                
                                # 优化：降低买入阈值 50%
                                buy_param_float = buy_param_float * 0.5
                                
                                buy_policy = buy_param_float * stock_count
                                # todo 四舍五入（其中quantize(Decimal("0.00")表示保留2为小数） test hhx
                                # buy_policy = float(Decimal(buy_policy).quantize(Decimal("0"), rounding=ROUND_HALF_UP))

                                is_fit_strategy = size >= buy_policy  # 不考虑默认初始值select_policy
                                # logutil.log.critical(f"DEBUG: date={date}, board={board_name}, size={size}, buy_policy={buy_policy}, fit={is_fit_strategy}")
                                # is_fit_strategy = size >= buy_policy  # 考虑默认初始值select_policy
                        else:
                            # sell_high_policy = select_policy
                            # sell_low_policy = 10  # 初始化值
                            sell_policy = industry_params_df.loc[board_row_index, 'sell_param']
                            if dfutil.not_empty(sell_policy):
                                segments = sell_policy.split("/")
                                if dfutil.len_safe(segments) > 1:
                                    sell_high_policy = segments[0]
                                    sell_low_policy = segments[1]
                                    sell_high_policy_float = -1
                                    sell_low_policy_float = -1
                                    if (dfutil.not_empty(sell_high_policy)) and (dfutil.of_str(sell_high_policy)):
                                        # 卖出参数是绝对数量，不是百分比，直接转换为float
                                        sell_high_policy_float = float(sell_high_policy)
                                    if (dfutil.not_empty(sell_low_policy)) and (dfutil.of_str(sell_low_policy)):
                                        # 卖出参数是绝对数量，不是百分比，直接转换为float
                                        sell_low_policy_float = float(sell_low_policy)
                                    # 不考虑默认初始值select_policy
                                    if (sell_high_policy_float > 0) and (size >= sell_high_policy_float):
                                        is_fit_strategy = True
                                    elif (sell_low_policy_float > 0) and (size < sell_low_policy_float):
                                        is_fit_sell_low_policy = True

                if is_fit_sell_low_policy or is_fit_strategy:
                    df_select_board = df_date[(df_date[qldef.board_name_key] == board_name)]
                    if dfutil.not_empty(df_select_board):
                        if is_fit_sell_low_policy:
                            if dfutil.empty(df_fit_sell_low_policy):
                                # 初始化列名
                                df_fit_sell_low_policy = pd.DataFrame(df_select_board, columns=df_date.columns)
                            else:
                                # 将新行添加到DataFrame中（由于pandas库的更新，2.0及以后得版本把append()这个方法给删除了，取而代之的是concat()方法）
                                df_fit_sell_low_policy = pd.concat(
                                    [df_fit_sell_low_policy, pd.DataFrame(df_select_board, columns=df_date.columns)],
                                    ignore_index=True)
                        elif is_fit_strategy:
                            if dfutil.empty(df_result):
                                # 初始化列名
                                df_result = pd.DataFrame(df_select_board, columns=df_date.columns)
                            else:
                                # 将新行添加到DataFrame中（由于pandas库的更新，2.0及以后得版本把append()这个方法给删除了，取而代之的是concat()方法）
                                df_result = pd.concat(
                                    [df_result, pd.DataFrame(df_select_board, columns=df_date.columns)],
                                    ignore_index=True)

    if dfutil.not_empty(df_result):
        df_result = df_result.reset_index(drop=True)  # 删除现有索引，并将其转换为默认的整数索引

    if dfutil.not_empty(df_fit_sell_low_policy):
        df_fit_sell_low_policy = df_fit_sell_low_policy.reset_index(drop=True)  # 删除现有索引，并将其转换为默认的整数索引

    return [df_result, df_fit_sell_low_policy]


# 计算指定年份 与 2024年个股总数的比例
def calculate_stock_count_rate_with_2024(industry_params_df, date):
    """Compute scaling rate relative to 2024.

    The original code assumed industry_params_df is always a valid DataFrame and always contains
    both stock_count_2024 and stock_count_<year> columns. When running with incomplete caches/config,
    industry_params_df can be None (or missing columns), which previously caused:
        TypeError: 'NoneType' object is not subscriptable

    This patched version fails gracefully and returns 1.0 as a neutral scaling factor.
    """
    try:
        if industry_params_df is None or getattr(industry_params_df, 'empty', True):
            logutil.log.critical('industry_params_df 为空(None/empty)，stock_rate=1.0（跳过按年度股数缩放）')
            return 1.0

        date_year = str(date)[:4]
        stock_count_column = f"{qldef.stock_count_key}_{date_year}"
        stock_count_2024_column = f"{qldef.stock_count_key}_2024"

        if stock_count_2024_column not in industry_params_df.columns:
            logutil.log.critical(f"industry_params_df 缺少列 {stock_count_2024_column}，stock_rate=1.0")
            return 1.0
        if stock_count_column not in industry_params_df.columns:
            logutil.log.critical(f"industry_params_df 缺少列 {stock_count_column}，stock_rate=1.0")
            return 1.0

        stock_count_sum_2024 = float(industry_params_df[stock_count_2024_column].sum())
        stock_count_sum_date = float(industry_params_df[stock_count_column].sum())

        if stock_count_sum_2024 <= 0:
            logutil.log.critical(f"{stock_count_2024_column} 汇总为0，stock_rate=1.0")
            return 1.0

        return stock_count_sum_date / stock_count_sum_2024

    except Exception as e:
        # Absolutely avoid crashing the whole pipeline due to a config/data issue
        logutil.log.critical(f"calculate_stock_count_rate_with_2024 异常: {e}，stock_rate=1.0")
        return 1.0
def industry_sector_analysis(date: int, prev_trade_days: int, is_buy: bool = True, is_merge=True,
                             board_target_df=None, industry_params_df=None):
    df_result = None
    date_list = tradedateutil.get_trade_dates(date, prev_trade_days)
    merge_on_list = [qldef.mtn_key, qldef.board_name_key]
    # 如果是买入，则加上signal_key，确保不同信号的同一只股票都能被选出来
    if is_buy:
        merge_on_list.append(qldef.signal_key)
        
    suffixes_list = ['', '_y']
    # 添加个股总数比例 add by hhx 2024.11.29
    stock_rate = calculate_stock_count_rate_with_2024(industry_params_df, date)
    # if is_buy:
    #     # 买入举例：3天内2-3次个股数量在11以上则T4开盘买入
    #     df_result = get_2_or_3_result(date_list, industry_params_df, merge_on_list, suffixes_list, is_buy)
    # else:
    #     # 卖出举例：T0行业板块数量超过设置参数时，T1,T2参数连续两天下降，则在T3天开盘卖出；若T0参数低于10则T1开盘卖出
    #     df_result = get_continue_n_result(date_list, merge_on_list, suffixes_list, is_buy)

    # add by hhx 2024.08.28
    global is_clearance_state  # 声明全局变量

    if not is_clearance_state:
        # 检查是否设置符合“清仓状态”
        check_set_clearance_state(date_list, selected_limit_count=1000*stock_rate, rate=0.5)

    if is_clearance_state:
        # 只有为“清仓状态”时，才检查当前是否可恢复“清仓状态”
        check_restore_clearance_state(date_list, selected_limit_count=400*stock_rate, is_buy=is_buy)

        if is_buy:
            # 如果当前在“清仓”状态下，则不能进行买入交易，即df_result = None
            df_result = None
        else:
            # 方法1
            rows = [date, '', '', '', '']
            columns = [qldef.date_key, qldef.mtn_key, qldef.board_name_key, qldef.sm_key, qldef.signal_key]
            df_result = pd.DataFrame([rows], columns=columns, index=[0])  # 注意记得加上括号[rows]

            # 方法2
            # info = {qldef.date_key: date, qldef.mtn_key: '', qldef.board_name_key: '', qldef.sm_key: ''}
            # df_result = pd.DataFrame(info, index=[0])
    else:
        if is_buy:
            # 买入举例：3天内2-3次个股数量在11以上则T4开盘买入
            df_result = get_2_or_3_result(date_list, industry_params_df, merge_on_list, suffixes_list, is_buy)
        else:
            # 卖出举例：T0行业板块数量超过设置参数时，T1,T2参数连续两天下降，则在T3天开盘卖出；若T0参数低于10则T1开盘卖出
            df_result = get_continue_n_result(date_list, industry_params_df, merge_on_list, suffixes_list, is_buy, is_merge)

    """
    # 当T0参数大于selected_limit_count，T1和T2选出“个股”的数量小于1000，数量连续下降且T1或T2下降幅度较T0数量减少50%及以上则在T3开盘清仓
    is_50_percent_off = is_selected_stocks_50_percent_off(date_list, selected_limit_count=1000, rate=0.5, is_buy=is_buy)
    if not is_50_percent_off:
        # 没有下降50%的情况下，继续执行“买入/卖出交易策略”
        df_result = get_continue_n_result(date_list, merge_on_list, suffixes_list, is_buy, is_merge)
    else:
        # 方法1
        rows = [date, '', '', '', '']
        columns = [qldef.date_key, qldef.mtn_key, qldef.board_name_key, qldef.sm_key, qldef.signal_key]
        df_result = pd.DataFrame([rows], columns=columns, index=[0])  # 注意记得加上括号[rows]

        # 方法2
        # info = {qldef.date_key: date, qldef.mtn_key: '', qldef.board_name_key: '', qldef.sm_key: ''}
        # df_result = pd.DataFrame(info, index=[0])

    # add by hhx 2024.08.28
    if is_buy:
        is_beyond_400 = is_selected_stocks_beyond_400(date_list, selected_limit_count=400)
        if not is_beyond_400:
            # 如果“清仓”状态下，is_beyond_400为False，则不能进行买入交易
            df_result = None
    """

    if dfutil.not_empty(df_result):
        # 删除所有列名中包含"_y"的列
        df_result = delete_df_suffix_column(df_result)

        next_trade_date_list = tradedateutil.get_trade_dates(date, 1, False, is_include_start_date=False)
        next_trade_date = None  # 记录 交易买入日期
        if len(next_trade_date_list) > 0:
            next_trade_date = next_trade_date_list[0]

        if dfutil.not_empty(next_trade_date):
            # 插入列：交易买入日期
            df_result.insert(loc=df_result.columns.get_loc(qldef.board_name_key) + 1, column=qldef.trade_date_key,
                             value=next_trade_date)

        trade_type = qldef.trade_buy_type
        if not is_buy:
            trade_type = qldef.trade_sell_type
        # if is_50_percent_off:
        if is_clearance_state:
            # 清仓类型
            trade_type = qldef.trade_clear_type

        # 插入列：交易类型
        df_result.insert(loc=df_result.columns.get_loc(qldef.trade_date_key) + 1, column=qldef.trade_type_key,
                         value=trade_type)

        # 如果是非清仓类型，则插入 个股对应的申万二级行业板块代码和名称 add by hhx 2024.10.11
        # 添加if not is_clearance_state判断条件，否则清仓类型时，返回数据为空 modify by hhx 2024.11.21
        if not is_clearance_state:
            df_result = stocks_tobe_traded_to_industry(df_result, board_target_df)

        df_result = enrich_trade_context(df_result, date, is_buy, industry_params_df, board_target_df)

        # 获取待保存的文件路径
        file_path = get_stocks_tobe_traded_filepath(date)
        if not dfutil.is_path_exist(file_path):
            # 由于需要保存‘买入’和‘卖出’类型的股票列表，所以mode为追加方式（'a'）
            qloption.database.write_to_file_csv(df_result, file_path, mode='a')
        else:
            # 如果文件存在，则不添加列表头
            qloption.database.write_to_file_csv(df_result, file_path, mode='a', header=False)

        # if not is_buy:
        #     subject_text = f'{date}的量化交易策略'
        #     body_text = f'附件是{subject_text}，请查收。'
        #     dfutil.send_email_with_bs(qldef.receiver_email_list, subject_text, body_text,
        #                               [file_path], is_send=qldef.is_send_email)

    return df_result


def _safe_float(val):
    try:
        if dfutil.empty(val):
            return None
        return float(val)
    except Exception:
        return None


def _parse_threshold(board_row, total_count, is_buy):
    if board_row is None or board_row.empty:
        return None
    if is_buy:
        buy_param = board_row.iloc[0].get('buy_param')
        if dfutil.empty(buy_param):
            return None
        try:
            if isinstance(buy_param, str) and '%' in buy_param:
                percent = float(str(buy_param).replace('%', '').strip()) / 100.0
                if total_count is None:
                    return None
                return percent * total_count
            return float(buy_param)
        except Exception:
            return None
    sell_param = board_row.iloc[0].get('sell_param')
    if dfutil.empty(sell_param):
        return None
    try:
        seg = str(sell_param).split('/')
        if len(seg) > 1:
            return float(seg[1])
        return float(seg[0])
    except Exception:
        return None


def _get_board_metrics(analysis_date, board_name, industry_params_df):
    if dfutil.empty(board_name) or industry_params_df is None or getattr(industry_params_df, 'empty', True):
        return None
    board_row = industry_params_df[industry_params_df[qldef.board_name_key] == board_name]
    total_count = None
    if dfutil.not_empty(board_row) and qldef.stock_count_key in board_row.columns:
        total_count = _safe_float(board_row.iloc[0].get(qldef.stock_count_key))
    if total_count is None or total_count <= 0:
        total_count = None

    current_count = dfutil.len_safe(get_selected_result_stocks(analysis_date, board_name))
    prev_dates = tradedateutil.get_trade_dates(analysis_date, 2, is_prev=True, is_include_start_date=True)
    prev_count = None
    if dfutil.len_safe(prev_dates) > 1:
        prev_count = dfutil.len_safe(get_selected_result_stocks(prev_dates[1], board_name))
    if prev_count is None:
        prev_count = current_count

    active_ratio = None
    active_ratio_prev = None
    if total_count and total_count > 0:
        active_ratio = current_count / total_count
        active_ratio_prev = prev_count / total_count
    return {
        'board_row': board_row,
        'total_count': total_count,
        'active_ratio': active_ratio,
        'active_ratio_prev': active_ratio_prev
    }


def enrich_trade_context(df_result, analysis_date, is_buy, industry_params_df, board_target_df):
    if dfutil.empty(df_result):
        return df_result

    for col in [qldef.sell_reason_key, qldef.sector_id_key, qldef.industry_active_ratio_key, qldef.industry_threshold_key,
                qldef.industry_threshold_delta_key, qldef.industry_active_ratio_delta_1d_key]:
        if col not in df_result.columns:
            df_result[col] = None

    board_metric_cache = {}

    for idx, row in df_result.iterrows():
        trade_type = row.get(qldef.trade_type_key)
        board_name = row.get(qldef.board_name_key)
        sector_id = row.get(qldef.sw_board_code_key)
        if dfutil.empty(sector_id):
            sector_id = row.get(qldef.board_code_key)
        if dfutil.empty(sector_id):
            sector_id = board_name
        df_result.at[idx, qldef.sector_id_key] = sector_id

        if (trade_type == qldef.trade_sell_type) or (trade_type == qldef.trade_clear_type):
            df_result.at[idx, qldef.sell_reason_key] = qldef.sell_reason_sector_cooldown

        if dfutil.empty(board_name):
            continue
        if board_name not in board_metric_cache:
            board_metric_cache[board_name] = _get_board_metrics(analysis_date, board_name, industry_params_df)
        metrics = board_metric_cache.get(board_name)
        if not metrics:
            continue

        threshold = _parse_threshold(metrics.get('board_row'), metrics.get('total_count'), is_buy)
        active_ratio = metrics.get('active_ratio')
        active_ratio_prev = metrics.get('active_ratio_prev')
        active_ratio_delta_1d = None
        if (active_ratio is not None) and (active_ratio_prev is not None):
            active_ratio_delta_1d = active_ratio - active_ratio_prev
        threshold_delta = None
        if (active_ratio is not None) and (threshold is not None):
            threshold_delta = active_ratio - threshold

        df_result.at[idx, qldef.industry_active_ratio_key] = active_ratio
        df_result.at[idx, qldef.industry_threshold_key] = threshold
        df_result.at[idx, qldef.industry_threshold_delta_key] = threshold_delta
        df_result.at[idx, qldef.industry_active_ratio_delta_1d_key] = active_ratio_delta_1d

    return df_result


# 处理单个日期的行业板块分析（用于多进程）
def _process_single_date_industry_analysis(args):
    """
    处理单个日期的行业板块分析（用于多进程）
    Args:
        args: (date, board_target_df_dict, industry_params_df_dict, is_merge)
    Returns:
        date: 处理完成的日期
    """
    date, board_target_df_dict, industry_params_df_dict, is_merge = args
    
    try:
        # 从字典重建DataFrame
        board_target_df = pd.DataFrame(board_target_df_dict) if board_target_df_dict else pd.DataFrame()
        industry_params_df = pd.DataFrame(industry_params_df_dict) if industry_params_df_dict else pd.DataFrame()
        
        # 先删除已经存在的对应交易日期的待交易文件，避免重复写入
        filepath = get_stocks_tobe_traded_filepath(date)
        dfutil.delete_file(filepath)
        
        # 每个进程都有独立的 is_clearance_state，初始化为False
        global is_clearance_state
        is_clearance_state = False
        
        # 执行买入分析
        industry_sector_analysis(date, 3, is_buy=True, is_merge=is_merge,
                                 board_target_df=board_target_df, industry_params_df=industry_params_df)
        # 执行卖出分析
        industry_sector_analysis(date, 3, is_buy=False, is_merge=is_merge,
                                 board_target_df=board_target_df, industry_params_df=industry_params_df)
        
        print(f'✅ 日期 {date} 处理完成')
        return date
        
    except Exception as e:
        print(f'❌ 处理日期 {date} 时出错: {str(e)}')
        import traceback
        traceback.print_exc()
        return None


def start_industry_sector_analysis(start_date: int, end_date: int, is_merge: bool = True, process_lock=None):
    logutil.log.debug(f'对{start_date} - {end_date}量化结果进行交易策略分析中...')
    # 开始计时
    start_time = time.time()

    # 重置全局清仓状态，确保每次分析独立
    global is_clearance_state
    is_clearance_state = False

    # 获取行业板块数据 modify by hhx 2024.10.11
    board_target_df = qloption.database.get_board_target_df()
    industry_params_df = qloption.database.get_industry_params_df2()
    
    # 尝试加载动态阈值数据
    industry_dynamic_params_df = qloption.database.get_industry_dynamic_params_df()
    if dfutil.not_empty(industry_dynamic_params_df):
        logutil.log.info("✅ 成功加载动态阈值参数 (Dynamic Thresholds)")
    else:
        logutil.log.warning("⚠️ 未找到动态阈值参数，将使用默认固定参数")

    if industry_params_df is None or getattr(industry_params_df, 'empty', True):
        logutil.log.critical('industry_params_df 为空(None/empty)，行业板块分析将跳过（避免 NoneType 崩溃）。请检查 qloption.database.get_industry_params_df2() 对应的参数文件/路径。')
        return

    # 准备任务：只处理交易日
    date_list = dfutil.get_date_list(start_date, end_date)
    # 按日期排序，确保顺序执行
    date_list.sort()
    
    trade_dates = []
    for date in date_list:
        if tradedateutil.isTradeDay(str(date), "%Y%m%d"):
            trade_dates.append(date)

    if len(trade_dates) == 0:
        logutil.log.warning(f'没有找到交易日，跳过行业板块分析')
        return

    logutil.log.info(f'开始顺序处理 {len(trade_dates)} 个交易日...')

    # 顺序执行，维护 is_clearance_state 状态
    success_count = 0
    for date in trade_dates:
        try:
            # 先删除已经存在的对应交易日期的待交易文件，避免重复写入
            filepath = get_stocks_tobe_traded_filepath(date)
            dfutil.delete_file(filepath)
            
            # 将动态阈值合并到当前日期的 industry_params_df 中
            current_params_df = industry_params_df.copy()
            if dfutil.not_empty(industry_dynamic_params_df):
                date_str = str(date)
                daily_dynamic = industry_dynamic_params_df[industry_dynamic_params_df['date'] == date_str]
                if not daily_dynamic.empty:
                    # 创建 board_name 到动态参数的映射
                    buy_map = dict(zip(daily_dynamic['board_name'], daily_dynamic['buy_threshold_ratio']))
                    sell_map = dict(zip(daily_dynamic['board_name'], daily_dynamic['sell_threshold_ratio']))
                    
                    # 检查是否有 XGBoost 的 prob_up 列
                    prob_map = {}
                    if 'prob_up' in daily_dynamic.columns:
                        prob_map = dict(zip(daily_dynamic['board_name'], daily_dynamic['prob_up']))
                    
                    # 更新 DataFrame
                    for idx, row in current_params_df.iterrows():
                        board = row[qldef.board_name_key]
                        
                        # 记录 XGBoost 预测概率 (用于日志或后续逻辑)
                        if board in prob_map:
                            prob = prob_map[board]
                            # 激活 XGBoost 逻辑：根据预测概率调整买入/卖出参数
                            
                            # 1. 防守模式 (Prob_Up < 0.45): 极低概率上涨 -> 强制空仓
                            if prob < 0.45:
                                # 设置极高的买入阈值 (如 999%)，确保不买入
                                current_params_df.at[idx, 'buy_param'] = "999.0%"
                                logutil.log.debug(f"防守模式: {board} Prob_Up={prob:.2f} < 0.45, 禁止买入")
                                
                            # 2. 进攻模式 (Prob_Up > 0.7): 高概率上涨 -> 降低门槛抢筹
                            elif prob > 0.70:
                                # 设置极低的买入阈值 (如 5%)，只要有启动迹象就买
                                current_params_df.at[idx, 'buy_param'] = "5.0%"
                                logutil.log.debug(f"进攻模式: {board} Prob_Up={prob:.2f} > 0.70, 激进买入")
                                
                            # 3. 紧急逃顶 (Prob_Crash > 0.65 - 假设 prob_up 极低也隐含了暴跌风险，或者单独有 prob_crash 列)
                            # 这里暂时复用 prob_up: 如果 prob_up < 0.3，视为极度危险，强制卖出
                            if prob < 0.30:
                                # 强制卖出：将卖出阈值设为极低 (0.1)，只要持仓就卖
                                # sell_param 格式通常是 "high/low" (如 "20/10")
                                # 我们修改 low (止损线) 为 9999 (只要 < 9999 就卖，即全卖)
                                # 或者修改 high (止盈线) 为 0.1 (只要 > 0.1 就卖，即全卖)
                                current_params_df.at[idx, 'sell_param'] = "0.1/9999"
                                logutil.log.debug(f"紧急逃顶: {board} Prob_Up={prob:.2f} < 0.30, 强制清仓")

                        if board in buy_map:
                            # 转换为百分比字符串
                            new_buy = f"{buy_map[board]}%"
                            current_params_df.at[idx, 'buy_param'] = new_buy
                        
                        if board in sell_map:
                            # 卖出逻辑较复杂，这里假设 sell_threshold_ratio 对应原来的第一个参数 (顶点)
                            # 保留原来的第二个参数 (止损，通常是10)
                            old_sell = str(row['sell_param'])
                            old_low = "10"
                            if "/" in old_sell:
                                old_low = old_sell.split("/")[1]
                            
                            # 暂时先只更新买入参数，卖出参数保持固定或稍后修改函数
                            pass

            # 执行买入分析
            industry_sector_analysis(date, 3, is_buy=True, is_merge=is_merge,
                                     board_target_df=board_target_df, industry_params_df=current_params_df)
            # 执行卖出分析
            industry_sector_analysis(date, 3, is_buy=False, is_merge=is_merge,
                                     board_target_df=board_target_df, industry_params_df=current_params_df)
            
            # logutil.log.info(f'✅ 日期 {date} 处理完成')
            success_count += 1
        except Exception as e:
            logutil.log.error(f'❌ 处理日期 {date} 时出错: {str(e)}')
            import traceback
            traceback.print_exc()

    logutil.log.info(f'成功处理 {success_count}/{len(trade_dates)} 个交易日')

    # 结束计时
    end_time = time.time()
    execution_time = end_time - start_time
    logutil.log.critical(
        f'对{start_date} - {end_date}量化结果进行交易策略分析已完成，总耗时长：{execution_time} 秒')


# 获取待交易文件的路径
def get_stocks_tobe_traded_filepath(date: int):
    cache_dir = qldef.stocks_tobe_traded_directory
    # 使用os.path.basename获取最后一个目录名
    last_dir_name = os.path.basename(cache_dir)
    suffix = f"{last_dir_name}_{date}.csv"
    file_path = os.path.join(cache_dir, suffix)
    return file_path


# 指定待交易的个股 插入对应的申万二级行业板块代码和名称
def stocks_tobe_traded_to_industry(df_stock, df_industry):
    if (dfutil.empty(df_industry)) or (dfutil.empty(df_stock)):
        return df_stock

    df_result = None
    for index, row in df_stock.iterrows():
        if dfutil.len_safe(row) > 0:
            mtn = row[qldef.mtn_key]
            if dfutil.len_safe(mtn) > 0:
                target = qloption.database.get_target(mtn, '.')
                df_target = df_industry[df_industry[qldef.target_key] == int(target)]
                if dfutil.not_empty(df_target):
                    # 这里需要重置索引，否则后面取列值的行数不为0，插入列到df_row值为None
                    df_target = df_target.reset_index(drop=True)
                    # 插入新列：申万二级行业板块代码和名称
                    df_row = row.to_frame().T  # 将series转为dataFrame
                    # 这里需要重置索引，否则默认行数不为0，插入列到df_row值为None
                    df_row = df_row.reset_index(drop=True)
                    # DEBUG: Check if board_code exists
                    if qldef.board_code_key in df_target.columns:
                        df_row[qldef.board_code_key] = df_target[qldef.board_code_key]
                    else:
                        print(f"WARNING: board_code not found in df_target for mtn {mtn}")
                        
                    if qldef.sw_board_code_key in df_target.columns:
                        df_row[qldef.sw_board_code_key] = df_target[qldef.sw_board_code_key]
                    else:
                        df_row[qldef.sw_board_code_key] = ''

                    if qldef.sw_board_name_key in df_target.columns:
                        df_row[qldef.sw_board_name_key] = df_target[qldef.sw_board_name_key]
                    else:
                        df_row[qldef.sw_board_name_key] = ''
                    if dfutil.empty(df_result):
                        df_result = df_row
                    else:
                        df_result = pd.concat([df_result, df_row], ignore_index=True)

    return df_result


def stocks_to_industry(start_date: int, end_date: int, df_industry):
    """
    将所有待交易的个股 插入对应的申万二级行业板块代码和名称
    @param start_date 开始日期
    @param end_date 结束日期
    @param df_industry 行业板块数据
    """
    if dfutil.empty(df_industry):
        return

    target_path = qldef.stocks_tobe_traded_directory
    filelist = qloption.database.get_all_market_files(target_path, 'stocks_tobe_traded')
    date_list = dfutil.get_date_list(start_date, end_date)
    for date in date_list:
        for file_path in filelist:
            # 使用os.path.basename获取文件名
            prefix = os.path.dirname(file_path)
            suffix = os.path.basename(file_path)
            # 判断文件名是否包含对应日期
            if str(date) in suffix:
                df_stock = qloption.database.read_file_csv(prefix, suffix, None, None, None)
                # 指定待交易的个股 插入对应的申万二级行业板块代码和名称
                df_result = stocks_tobe_traded_to_industry(df_stock, df_industry)
                if dfutil.not_empty(df_result):
                    qloption.database.write_file_csv(df_result, prefix, suffix)
                break
