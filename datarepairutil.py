"""
datarepairutil.py
qlsignalNew
Created by huanghx on 2024/8/29
Copyright © 2024 huanghx. All rights reserved.
"""
import os

import numpy as np
import pandas as pd

import dfutil
import logutil
import qldef
import qloption
import databaseutil


# 获取指定日期范围内没有日度行情数据的innerCode列表
def get_repair_inner_codes(start_date: int, end_date: int):
    # fix_files = []
    inner_codes = []
    target_path = qldef.market_quotation_directory
    filelist = qloption.database.get_all_market_files(target_path)
    for file_path in filelist:
        df_indicator = qloption.database.read_single_big_csv(file_path)
        if dfutil.not_empty(df_indicator):
            df_date = df_indicator[(df_indicator[qldef.date_key] >= start_date)
                                   & (df_indicator[qldef.date_key] <= end_date)]
            if dfutil.empty(df_date):
                inner_code = df_indicator[qldef.inner_code_key].iloc[0]
                inner_codes.append(inner_code)
                # fix_files.append(file_path)

    return inner_codes


# 将dataFrame中两列值（series类型）合并 并将一列的nan值替换为另一列的非nan值
def replace_nan_with_value(series1, series2):
    # 创建一个新的Series来保存结果
    result = pd.Series(np.nan, index=series1.index)
    # 遍历两个序列，按照规则填充结果
    for i in series1.index:
        if pd.isna(series1.loc[i]):
            result.loc[i] = series2.loc[i]
        else:
            result.loc[i] = series1.loc[i]

    return result


# 将文件中的数据去重
def drop_duplicates_file(direct_path, filter_str):
    # df_result = pd.concat(df_list, ignore_index=True).drop_duplicates(subset=merge_on)
    filelist = qloption.database.get_all_market_files(direct_path, filter_str)
    for file in filelist:
        # 使用os.path.basename获取文件名
        prefix = os.path.dirname(file)
        suffix = os.path.basename(file)
        df_indicator = qloption.database.read_single_big_csv(file)
        if dfutil.not_empty(df_indicator):
            df_indicator = df_indicator.drop_duplicates(subset=[qldef.mtn_key, qldef.board_name_key])
            if dfutil.not_empty(df_indicator):
                qloption.database.write_file_csv(df_indicator, prefix, suffix)


# 批量修复异常数据
def fix_abnormal_data():
    target_path = qldef.market_quotation_directory
    filelist = qloption.database.get_all_market_files(target_path)
    for file_path in filelist:
        # 使用os.path.basename获取文件名
        prefix = os.path.dirname(file_path)
        suffix = os.path.basename(file_path)
        # # 将列名为'low  ' 和 'low'两列值合并为列'low'，并重新计算指数移动平均线、DIFF、DEA等
        # df_indicator = qloption.database.read_single_big_csv(file_path)
        # if dfutil.not_empty(df_indicator):
        #     low_bank_key = 'low  '
        #     low_key = 'low'
        #     ma_vol_key = 'mrvolmavol(3,1)'
        #     # 判断列名是否存在df的列中
        #     if (low_bank_key in df_indicator.columns) and (low_key in df_indicator.columns):
        #         # df_low = df_indicator['low  '] + df_indicator['low']  # 这个不行，合并值全为nan
        #         merge_low_series = replace_nan_with_value(df_indicator[low_bank_key], df_indicator[low_key])
        #         df_indicator[low_bank_key] = merge_low_series
        #         # 删除列
        #         df_indicator = df_indicator.drop(low_key, axis=1)
        #         # 修改列名，将 'low  '改为 'low'
        #         df_indicator.rename(columns={low_bank_key: low_key}, inplace=True)
        #         if ma_vol_key in df_indicator.columns:
        #             ma_vol_series = df_indicator[ma_vol_key]
        #             if len(ma_vol_series) > 0:
        #                 df_indicator = df_indicator.drop(ma_vol_key, axis=1)
        #
        #         # 综合计算指数移动平均线、DIFF、DEA等
        #         databaseutil.calculate_all(df_indicator)
        #         qloption.database.write_file_csv(df_indicator, prefix, suffix)

        # 判断列 'bbi(3,6,12,24)' 是否存在
        # column_exists = 'bbi(3,6,12,24)' in df_indicator.columns
        # if not column_exists:
        #     # 综合计算指数移动平均线、DIFF、DEA等
        #     databaseutil.calculate_all(df_indicator)
        #     qloption.database.write_file_csv(df_indicator, prefix, suffix)

        # 删除没用的个股行情数据文件
        # segments = suffix.split("_")
        # target = ""
        # if len(segments) > 1:
        #     target = segments[1]
        #
        # if dfutil.is_invalid_quantization_stock(target):
        #     os.remove(file_path)

        # # 由于从数据库获取的日交易量为正常交易量的100倍，所以需要除以100
        df_indicator = qloption.database.read_single_big_csv(file_path)
        if dfutil.not_empty(df_indicator):
            df_indicator[qldef.volume_key] = df_indicator[qldef.volume_key] / 100
            # 综合计算指数移动平均线、DIFF、DEA等
            databaseutil.calculate_all(df_indicator)
            qloption.database.write_file_csv(df_indicator, prefix, suffix)


# 计算每年各行业板块的个股总数
def calculate_board_stock_count(start_date: int, end_date: int):
    # fix_files = []
    board_df = qloption.database.get_board_target_df()
    target_path = qldef.market_quotation_directory
    filelist = qloption.database.get_all_market_files(target_path)
    my_dict = {}
    for file_path in filelist:
        # 使用os.path.basename获取文件名
        board_name = 'empty'
        prefix = os.path.dirname(file_path)
        suffix = os.path.basename(file_path)
        target = qloption.database.get_target(suffix)
        target_df = board_df[board_df[qldef.target_key] == int(target)]
        if dfutil.not_empty(target_df):
            target_df = target_df.reset_index(drop=True)  # 删除现有索引，并将其转换为默认的整数索引
            board_name = target_df.at[0, qldef.board_name_key]  # 获取第0行的board_name值
            board_code = target_df.at[0, qldef.board_code_key]  # 获取第0行的board_name值
        else:
            logutil.log.debug(f"{target}找不到{start_date}-{end_date}日期间的行情板块名")

        df_indicator = qloption.database.read_single_big_csv(file_path)
        if dfutil.not_empty(df_indicator):
            df_date = df_indicator[(df_indicator[qldef.date_key] >= start_date)
                                   & (df_indicator[qldef.date_key] <= end_date)]
            if dfutil.not_empty(df_date):
                count = my_dict.get(board_name, 0)
                count += 1
                my_dict[board_name] = count
            else:
                logutil.log.debug(f"{target}找不到{start_date}-{end_date}日期间的日度行情数据")
        else:
            logutil.log.debug(f"{file_path} 文件内容为空")

    logutil.log.debug(f"{my_dict}")
    industry_params_df = qloption.database.get_industry_params_df2()
    if dfutil.not_empty(industry_params_df):
        board_name_list = industry_params_df[qldef.board_name_key]
        stock_count_list = []
        for name in board_name_list:
            stock_count = my_dict[name]
            stock_count_list.append(stock_count)

        logutil.log.debug(f"{board_name_list}, {stock_count_list}")

        # 插入列
        four_digits = str(start_date)[:4]  # 取整型数字前4位（即取年份）
        key = 'stock_count' + '_' + four_digits
        industry_params_df[key] = stock_count_list

        # 写入文件
        qloption.database.write_file_csv(industry_params_df, qldef.file_cache_path, 'industry_parameters_model2.csv')


# 将指定日期的待交易策略文件合并到一个文件中
def merge_all_stocks_tobe_traded_to_one_file(year: str):
    target_path = qldef.stocks_tobe_traded_directory
    filter_str = year
    filelist = qloption.database.get_all_market_files(target_path, filter_str)
    df_result = None
    for file_path in filelist:
        # 使用os.path.basename获取文件名
        # board_name = 'empty'
        # prefix = os.path.dirname(file_path)
        # suffix = os.path.basename(file_path)
        df_indicator = qloption.database.read_single_big_csv(file_path)
        if dfutil.not_empty(df_indicator):
            if dfutil.empty(df_result):
                df_result = df_indicator
            else:
                # 将新行添加到DataFrame中（由于pandas库的更新，2.0及以后得版本把append()这个方法给删除了，取而代之的是concat()方法）
                df_result = pd.concat([df_result, df_indicator], ignore_index=True)

    if dfutil.not_empty(df_result):
        # 通过sort_key排序后，索引会错乱
        df_result = df_result.sort_values(qldef.date_key, ascending=False)
        df_result = df_result.reset_index(drop=True)  # 删除现有索引，并将其转换为默认的整数索引
        prefix = qldef.stocks_tobe_traded_per_year_directory
        suffix = "stocks_tobe_traded" + '_' + year
        qloption.database.write_file_csv(df_result, prefix, suffix)




