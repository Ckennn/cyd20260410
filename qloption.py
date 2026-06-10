"""
qloption.py
qlsignalNew
Created by huanghx on 2024/7/25
Copyright © 2024 huanghx. All rights reserved.
"""

import os
from typing import Optional
import pathlib

import pandas as pd

import dfutil
import logutil
import qldef


# 由于业务逻辑异常，无法回复，然后发送通知邮件或短信，然后退出程序（这里可以简化为直接退出程序）add by hhx 2024.07.22
def notify_unsupported_exit(*args, return_value: any = None) -> any:
    # 退出程序
    logutil.log.error(f"unsupported_exit: {args}")
    return dfutil.unsupported_exit(args, return_value)

    # if return_value:
    #     return return_value
    # else:
    #     return sys.exit()


def notify_fatal_exit(*args, return_value: any = None) -> any:
    # 退出程序
    logutil.log.error(f"fatal_exit: {args}")
    return dfutil.fatal_exit(args, return_value)
    # if return_value:
    #     return return_value
    # else:
    #     return sys.exit()


class database:
    # 获取market
    @staticmethod
    def to_market_of(df_indicator):
        return df_indicator['market']

    # 获取target
    @staticmethod
    def to_target_of(df_indicator):
        return df_indicator['target']

    # 获取market 和 target
    @staticmethod
    def get_market_and_target(path: str, split='_'):
        segments = path.split(split)
        market = "zh"
        target = ""
        if len(segments) > 1:
            market = segments[0]
            target = segments[1]

        return [market, target]

    @staticmethod
    def get_market(path: str, split='_'):
        market_target = database.get_market_and_target(path, split)
        market = "zh"
        if len(market_target) > 0:
            market = market_target[0]

        return market

    @staticmethod
    def get_target(path: str, split='_'):
        market_target = database.get_market_and_target(path, split)
        target = ""
        if len(market_target) > 1:
            target = market_target[1]

        return target

    # 获取工程目录下所有以“1d_ind.csv”为后缀的文件列表 add by hhx 2024.07.25
    @staticmethod
    def get_all_market_files(path='', filter_str="1d_ind.csv") -> list:
        filelist = dfutil.get_all_files(path, filter_str)
        return filelist

        # for root, dirs, files in os.walk(directory):
        #     for file in files:
        #         yield os.path.join(root, file)

    # 获取所有股票代码列表
    @staticmethod
    def get_code_list(target_path):
        stock_code_list = []
        filelist = database.get_all_market_files(target_path)
        for file_path in filelist:
            # 使用os.path.basename获取文件名
            # prefix = os.path.dirname(file_path)
            suffix = os.path.basename(file_path)
            stock_code = database.get_target(suffix)
            if len(stock_code) > 0:
                stock_code_list.append(stock_code)

        return stock_code_list

    # 获取对应股票/申万2级行业板块的日度行情数据
    @staticmethod
    def get_code_daily_quote_data(stock_code, start_date: int, end_date: int, target_path, filter_str="1d_ind.csv", allow_fallback=True):
        # 优化：直接构造可能的文件名，避免遍历所有文件
        # 常见的命名模式：zh_000001_1d_ind.csv
        possible_filenames = [
            f"zh_{stock_code}_1d_ind.csv",
            f"{stock_code}_1d_ind.csv",
            f"zh_{stock_code}.csv",
            f"{stock_code}.csv"
        ]
        
        found_file = None
        for filename in possible_filenames:
            filepath = os.path.join(target_path, filename)
            if os.path.exists(filepath):
                found_file = filepath
                break
        
        # 如果直接找不到，再尝试遍历（兼容旧逻辑，但尽量避免）
        if not found_file and allow_fallback:
            # 仅在找不到时遍历，且可以考虑是否真的需要遍历
            # 为了保持兼容性，还是保留遍历逻辑，但加上日志警告性能
            # logutil.log.debug(f"直接查找股票文件失败: {stock_code}, 尝试遍历目录...")
            filelist = database.get_all_market_files(target_path, filter_str)
            for file_path in filelist:
                if stock_code in os.path.basename(file_path):
                    found_file = file_path
                    break
        
        if found_file:
            prefix = os.path.dirname(found_file)
            suffix = os.path.basename(found_file)
            df_stock = database.read_file_csv(prefix, suffix, None, None, None)
            
            if dfutil.not_empty(df_stock):
                # Ensure date column is numeric before comparison
                if qldef.date_key in df_stock.columns:
                    df_stock[qldef.date_key] = pd.to_numeric(df_stock[qldef.date_key], errors='coerce').fillna(0).astype(int)
                
                df_stock = df_stock[(df_stock[qldef.date_key] >= start_date) & (df_stock[qldef.date_key] <= end_date)]
                
                if dfutil.not_empty(df_stock):
                    # 将字段名是date的int类型转datetime类型
                    df_stock[qldef.date_key] = pd.to_datetime(df_stock[qldef.date_key], format='%Y%m%d')

                    # 新datetime列作为索引列
                    df_stock.set_index([qldef.date_key], inplace=True)

                    # 按backtrader 格式要求，第7列openinterest ，也可以不用
                    df_stock['openinterest'] = 0

                    # 按日期索引递增排序
                    df_stock = df_stock.sort_index()

                    return df_stock
        
        return None

    # 读取csv文件 并 解析csv文件名中的market和target
    @staticmethod
    def read_file_csv(prefix, suffix, dtype, usecols, nrows) -> Optional[pd.DataFrame]:
        market = database.get_market(suffix)
        target = database.get_target(suffix)

        # logutil.log.debug(f'当前股票代码为：{target}')

        # prefix = prefix + '/'
        # df_indicator = dfutil.PandasFile.read_file_csv(dfutil.PandasFile(), prefix, suffix,
        #                                                None, usecols, nrows)
        file_path = str(os.path.join(prefix, suffix))
        df_indicator = database.read_single_big_csv(file_path, usecols, nrows)

        # 不为空 且 target为6为的股票代码
        if (dfutil.not_empty(df_indicator)) and (len(target) == 6) and (target.isdigit()):
            # 新增两列：market 和 target
            df_indicator['market'] = market
            df_indicator['target'] = target
            """
            新增列：“今日交易量 相对于 昨日的3日平均交易量 的倍数”（列名："mrvolmavol(3,1)"） volume
            mrvolmavol(3,1) = Multiply Ratio of Volume to Moving Average Volume（第一个数字表示ma时间长度，
            第二个数字表示cr时间长度（例如1表示"今日比昨日"））
            """
            # test_list = df_indicator.loc[1:3, ["volume"]]
            # average_volume_past3 = np.mean(test_list)
            # today_volume = df_indicator.loc[0, ["volume"]]
            # if average_volume_past3:
            #     volume_ratio = today_volume / average_volume_past3
            #     logutil.log.debug(f"今日交易量 相对于 昨日的3日平均交易量 的倍数: {volume_ratio}")

            volume_list_from1 = df_indicator.loc[1:, ["volume"]]  # 返回值为DataFrame类型
            # volume_list_from0 = df_indicator["volume"]  # 返回值为Series类型，与DataFrame类型求比率时格式不对
            volume_list_from0 = df_indicator.loc[0:, ["volume"]]  # 返回值为DataFrame类型
            average_volume_past3 = volume_list_from1.rolling(3).mean().shift(-2)
            average_volume_past3.loc[len(volume_list_from1) + 1] = None  # 增加一行是与volume_list行数一样，便于下面计算比率
            average_volume_past3.reset_index(drop=True, inplace=True)  # 重置索引，从0开始，设置了drop=True来丢弃原来的索引
            if not dfutil.empty(average_volume_past3):
                df_indicator["mrvolmavol(3,1)"] = volume_list_from0 / average_volume_past3

        return df_indicator

    @staticmethod
    def read_single_big_csv(filepath, usecols=None, nrows=None):
        """
        基于python将较大的文本文件读取为dataframe时（文本文件可能是csv或者xlsx类型）。直接用pandas对整个文件进行读取的话，会比较耗时。
        这里提供一个简单的加速方案：分批读取：
        实现方案
        需要首先将文件转为可以分批读取的数据类型:csv(’,‘分隔)或者tsv(’\t’分隔)。
        然后基于 pandas 的 read_csv函数的 chunksize参数实现分批读取（此参数用于设定每批读入多少行数据）。一般设置为一个稍大的整数即可
        明显提速。封装成以下的函数，可以直接调用：
        说明：此函数针对csv文件，如果文件不是基于逗号分隔，在read_csv函数中设置对应的sep参数（分隔符）。
        """
        is_exist = pathlib.Path(filepath).is_file()
        if not is_exist:
            return None

        # logutil.log.debug(f"读取的文件路径：{filepath}")

        # 1000 -> 5000 modify by hhx 2024.09.06
        try:
            df_chunk = pd.read_csv(filepath, chunksize=5000, usecols=usecols, nrows=nrows)
            res_chunk = []
            for chunk in df_chunk:
                res_chunk.append(chunk)
            
            if not res_chunk:  # 如果没有读取到任何块
                return None
                
            res_df = pd.concat(res_chunk)
            return res_df
        except pd.errors.EmptyDataError:
            # logutil.log.warning(f"读取 CSV 文件失败 (EmptyDataError): {filepath}")
            return None
        except Exception as e:
            logutil.log.error(f"读取 CSV 文件失败: {filepath}, 错误: {e}")
            return None

    # bool | list[str] 改为 bool Python3.9不支持这个 modify by hhx 2025.01.23
    @staticmethod
    # def write_single_big_csv(df: pd.DataFrame, filepath, mode='w', header: bool | list[str] = True):
    def write_single_big_csv(df: pd.DataFrame, filepath, mode='w', header: bool = True):
        """
        写入csv文件时，当DataFrame数据内容比较大时，需要分批写入csv文件
        添加mode参数：mode参数用于指定文件的打开模式 modify by hhx 2024.08.01
        ‌其中'a'表示追加模式，‌意味着如果文件已经存在，‌新的数据将被追加到文件的末尾，‌而不是覆盖原有的内容；
           'w'表示重新写入，会覆盖原来的内容
        """
        chunk_size = 5000  # 1000 -> 5000 modify by hhx 2024.09.06
        i = 0
        while i < dfutil.len_safe(df):
            chunk_end = min(i + chunk_size, len(df))  # 如果剩下的行数<chunk_size，则取剩下的
            chunk = df.iloc[i:chunk_end]
            if i == 0:
                # 首次按照入参mode来写入
                chunk.to_csv(filepath, index=False, header=header, mode=mode)
            else:
                # 由于是分批次写入，除了首次，后面都是追加写入（mode='a'） 且 去掉表头（header=False）
                chunk.to_csv(filepath, index=False, header=False, mode='a')
            i += chunk_size

    # 写入csv文件（去掉表头：header=False）- bool | list[str] 改为 bool Python3.9不支持这个 modify by hhx 2025.01.23
    @staticmethod
    # def write_file_csv(df: pd.DataFrame, prefix, suffix, mode='w', header: bool | list[str] = True):  # -> bool:
    def write_file_csv(df: pd.DataFrame, prefix, suffix, mode='w', header: bool = True):  # -> bool:
        dfutil.create_directory(prefix)  # 先判断目录是否存在，如果不存在，则创建
        # prefix = prefix + '/'
        # return dfutil.PandasFile.write_file_csv(dfutil.PandasFile(), df, prefix, suffix, True, False, True, False,
        #                                         mode=mode)
        file_path = os.path.join(prefix, suffix)
        database.write_single_big_csv(df, file_path, mode, header=header)

    # 写入csv文件（传入完整文件路径参数）- bool | list[str] 改为 bool Python3.9不支持这个 modify by hhx 2025.01.23
    @staticmethod
    # def write_to_file_csv(df: pd.DataFrame, file_path, mode='w', header: bool | list[str] = True):
    def write_to_file_csv(df: pd.DataFrame, file_path, mode='w', header: bool = True):
        # 使用os.path.basename获取文件名
        prefix = os.path.dirname(file_path)
        suffix = os.path.basename(file_path)
        database.write_file_csv(df, prefix, suffix, mode, header)

    # 获取行业板块数据
    @staticmethod
    def get_board_target_df():
        target_path = qldef.market_quotation_directory
        df_board_target = database.read_file_csv(target_path, qldef.dc_board_target_file_name,
                                                 None, None, None)
        return df_board_target

    # 获取申万二级行业板块数据
    @staticmethod
    def get_sw_second_industry_df():
        target_path = qldef.market_SYWGIndexQuote_directory
        board_target_df = database.read_file_csv(target_path, qldef.sw_second_industry_file_name,
                                                 None, None, None)
        return board_target_df

    # 获取行业交易参数
    @staticmethod
    def get_industry_params_df():
        industry_params_file_path = qldef.file_cache_path + '/industry_parameters_model.csv'
        df_industry_params = database.read_single_big_csv(industry_params_file_path)
        return df_industry_params

    # 获取行业交易参数2
    @staticmethod
    def get_industry_params_df2():
        # 尝试读取动态参数文件
        dynamic_file_path = os.path.join(qldef.file_cache_path, 'industry_parameters_dynamic.csv')
        base_file_path = os.path.join(qldef.file_cache_path, 'industry_parameters_model2.csv')
        
        df_base = database.read_single_big_csv(base_file_path)
        
        if os.path.exists(dynamic_file_path):
            try:
                df_dynamic = pd.read_csv(dynamic_file_path)
                # 确保日期列是字符串类型，以便匹配
                df_dynamic['date'] = df_dynamic['date'].astype(str)
                # 将动态参数合并到 df_base (这里需要一种机制让调用者知道是动态的)
                # 由于 df_base 是静态配置，而 df_dynamic 是每日变化的
                # 我们可以返回一个包含动态数据的特殊 DataFrame 或者修改调用逻辑
                # 方案：返回 df_base，但在其中附加一个 _dynamic_data 属性或列
                # 或者更简单：在 industryanalysis.py 中单独加载动态参数，这里只负责返回基础配置
                # 为了保持接口一致性，这里我们暂时只返回 df_base，
                # 但如果 df_base 为空，尝试返回动态数据的结构（虽然这不太可能）
                pass
            except Exception as e:
                pass
                
        return df_base

    # 获取动态行业交易参数
    @staticmethod
    def get_industry_dynamic_params_df():
        # 优先读取 XGBoost 预测结果
        xgboost_file_path = os.path.join(qldef.file_cache_path, 'industry_parameters_xgboost.csv')
        if os.path.exists(xgboost_file_path):
            try:
                df = pd.read_csv(xgboost_file_path)
                df['date'] = df['date'].astype(str)
                # 确保有 prob_up 列，如果没有则说明是旧文件
                if 'prob_up' in df.columns:
                    return df
            except Exception:
                pass
        
        # 回退到统计版动态阈值
        dynamic_file_path = os.path.join(qldef.file_cache_path, 'industry_parameters_dynamic.csv')
        if os.path.exists(dynamic_file_path):
            try:
                df = pd.read_csv(dynamic_file_path)
                df['date'] = df['date'].astype(str)
                return df
            except Exception:
                return None
        return None
