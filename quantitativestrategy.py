"""
quantitativestrategy.py
qlsignalNew_20240808
Created by huanghx on 2024/8/19
Copyright © 2024 huanghx. All rights reserved.
"""
import os
import pathlib
import time
import multiprocessing

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import dfutil
import logutil
import qldef
import qloption
import qlsignal0
import qlsignalcaochen  # 注意这个不能删除，否则会报错：FATAL-ERROR:  ("signal_symbol='sigcaochen'",), UNSUPPORTED
import tradedateutil


def _process_single_stock_strategy(args):
    """
    处理单只股票的量化策略（用于多进程）
    Args:
        args: (file_path, start_date, end_date, df_board_target_dict)
    Returns:
        df_result: 该股票的量化结果DataFrame
    """
    file_path, start_date, end_date, df_board_target_dict = args
    
    try:
        # 从字典重建df_board_target
        df_board_target = pd.DataFrame(df_board_target_dict) if df_board_target_dict else pd.DataFrame()
        
        # 读取股票数据
        prefix = os.path.dirname(file_path)
        suffix = os.path.basename(file_path)
        df_indicator = qloption.database.read_file_csv(prefix, suffix, None, None, None)
        
        if dfutil.empty(df_indicator):
            return None
        
        df_result = pd.DataFrame()
        dates = dfutil.get_date_list(start_date, end_date)
        
        for date_int in dates:
            if not tradedateutil.isTradeDay(str(date_int), "%Y%m%d"):
                continue
            
            # 按指定日期获取行索引
            row_begin_list = df_indicator.index[df_indicator.date == date_int].tolist()
            if dfutil.empty(row_begin_list):
                continue
            row_begin = row_begin_list[0]
            
            signal_name_list = qlsignal0.list_signal(qldef.signalsymbol_caochen)
            for signal_name in signal_name_list:
                if len(signal_name) > 0:
                    # 调用信号函数
                    result_info = qlsignal0.call_signal(qldef.signalsymbol_caochen, signal_name, df_indicator, row_begin)
                    is_signal = result_info[0]
                    
                    if is_signal:
                        market = df_indicator['market'][0]
                        target = df_indicator['target'][0]
                        
                        # 查找target_name
                        target_name = ''
                        if dfutil.not_empty(df_board_target):
                            cond = (df_board_target['target'].astype(str) == str(target))
                            if 'board_type' in df_board_target.columns:
                                cond = cond & (df_board_target.board_type == qldef.industry_key)
                            
                            target_name_list = df_board_target[cond]['target_name']
                            if len(target_name_list):
                                target_name = target_name_list.iloc[0]
                        
                        # 查找board_name
                        board_name = ''
                        if dfutil.not_empty(df_board_target):
                            cond = (df_board_target.target.astype(str) == str(target))
                            if 'board_type' in df_board_target.columns:
                                cond = cond & (df_board_target.board_type == qldef.industry_key)

                            board_name_list = df_board_target[cond][qldef.board_name_key]
                            if len(board_name_list):
                                board_name = board_name_list.iloc[0]
                        
                        mtn = f"{market}.{target}.{target_name}"
                        sm = result_info[1]
                        stock_info = {
                            qldef.date_key: date_int,
                            qldef.mtn_key: mtn,
                            qldef.sm_key: sm,
                            qldef.board_name_key: board_name,
                            qldef.signal_key: signal_name
                        }
                        
                        if dfutil.empty(df_result):
                            df_result = pd.DataFrame(stock_info, index=[0])
                        else:
                            df_result = pd.concat([df_result, pd.DataFrame([stock_info])], ignore_index=True)
        
        return df_result if dfutil.not_empty(df_result) else None
        
    except Exception as e:
        # 在子进程中打印错误
        print(f'处理股票文件 {file_path} 时出错: {e}')
        return None

def executing_strategy_task(start_date: int, end_date: int, target_path, df_board_target) -> pd.DataFrame:
    df_result = None
    filelist = qloption.database.get_all_market_files(target_path)
    for file_path in filelist:
        # 使用os.path.basename获取文件名
        prefix = os.path.dirname(file_path)
        suffix = os.path.basename(file_path)
        df_indicator = qloption.database.read_file_csv(prefix, suffix, None, None, None)

        if dfutil.not_empty(df_indicator):
            dates = dfutil.get_date_list(start_date, end_date)
            for date_int in dates:
                if not tradedateutil.isTradeDay(str(date_int), "%Y%m%d"):
                    continue

                # 按指定日期获取行索引
                # row_begin = 0
                row_begin_list = df_indicator.index[df_indicator.date == date_int].tolist()
                if dfutil.not_empty(row_begin_list):
                    row_begin = row_begin_list[0]
                else:
                    continue

                signal_name_list = qlsignal0.list_signal(qldef.signalsymbol_caochen)
                for signal_name in signal_name_list:
                    if len(signal_name) > 0:
                        # 0->row_begin
                        result_info = qlsignal0.call_signal(qldef.signalsymbol_caochen, signal_name, df_indicator,
                                                            row_begin)
                        is_signal = result_info[0]
                        if is_signal:
                            market = df_indicator['market'][0]
                            target = df_indicator['target'][0]
                            target_name = ''
                            if dfutil.not_empty(df_board_target):
                                cond = (df_board_target['target'].astype(str) == str(target))
                                if 'board_type' in df_board_target.columns:
                                    cond = cond & (df_board_target.board_type == qldef.industry_key)
                                
                                target_name_list = df_board_target[cond]['target_name']
                                if len(target_name_list):
                                    target_name = target_name_list.iloc[0]

                            board_name = ''
                            if dfutil.not_empty(df_board_target):
                                cond = (df_board_target.target.astype(str) == str(target))
                                if 'board_type' in df_board_target.columns:
                                    cond = cond & (df_board_target.board_type == qldef.industry_key)
                                
                                board_name_list = df_board_target[cond][qldef.board_name_key]
                                if len(board_name_list):
                                    board_name = board_name_list.iloc[0]

                            mtn = f"{market}.{target}.{target_name}"
                            sm = result_info[1]
                            stock_info = {qldef.date_key: date_int, qldef.mtn_key: mtn, qldef.sm_key: sm,
                                          qldef.board_name_key: board_name, qldef.signal_key: signal_name}
                            # logutil.log.debug(f'符合量化策略：{stock_info}')
                            if dfutil.empty(df_result):
                                df_result = pd.DataFrame(stock_info, index=[0])
                            else:
                                # 将新行添加到DataFrame中（由于pandas库的更新，2.0及以后得版本把append()这个方法给删除了，取而代之的是concat()方法）
                                df_result = pd.concat([df_result, pd.DataFrame([stock_info])], ignore_index=True)
        else:
            continue

    return df_result


# 获取待交易文件的路径
def get_results_zh_trigger_filepath(start_date_int: int, end_date_int: int):
    cache_dir = qldef.quantitative_result_directory
    # 使用os.path.basename获取最后一个目录名
    last_dir_name = os.path.basename(cache_dir)
    suffix = f"results_zh_{start_date_int}_{end_date_int}_trigger.csv"
    file_path = os.path.join(cache_dir, suffix)
    return file_path


# 开始执行量化策略 add by hhx 2024.07.26
def start_executing_strategy(start_date_int: int, end_date_int: int, process_lock=None):
    logutil.log.debug(f'开始执行{start_date_int} - {end_date_int}的量化策略中...')
    # 开始计时
    start_time = time.time()

    # 先删除已经存在的量化策略分析结果文件，避免重复写入 add by hhx 2024.12.05
    file_path = get_results_zh_trigger_filepath(start_date_int, end_date_int)
    dfutil.delete_file(file_path)

    # current_date = dfutil.str_date(dfutil.date_now(), "%Y%m%d")  # 策略执行日期
    df_result = pd.DataFrame()  # 初始化

    target_path = qldef.market_quotation_directory
    df_board_target = qloption.database.read_file_csv(target_path, qldef.dc_board_target_file_name, None, None, None)

    # 转为字典以便进程间传递
    df_board_target_dict = df_board_target.to_dict('records') if dfutil.not_empty(df_board_target) else []
    
    # 获取所有股票文件
    filelist = qloption.database.get_all_market_files(target_path)
    
    # 过滤掉非数字的股票代码 (如 BKxxxx)
    # 准备任务列表
    tasks = []
    for file_path in filelist:
        suffix = os.path.basename(file_path)
        target = qloption.database.get_target(suffix)
        if len(target) == 6 and target.isdigit():
            tasks.append((file_path, start_date_int, end_date_int, df_board_target_dict))
    
    # tasks = [(file_path, start_date_int, end_date_int, df_board_target_dict) for file_path in filelist]
    
    # 使用多进程处理
    # max_workers = min(multiprocessing.cpu_count(), 12)  # 最多12个进程
    cpu_count = multiprocessing.cpu_count()
    max_workers = max(1, cpu_count - 1)
    logutil.log.info(f'使用 {max_workers} 个进程处理 {len(tasks)} 只股票的量化策略...')
    
    process_start_time = time.time()
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # results = executor.map(_process_single_stock_strategy, tasks)
        # 
        # for df_temp in results:
        #     if dfutil.not_empty(df_temp):
        #         if dfutil.empty(df_result):
        #             df_result = df_temp
        #         else:
        #             df_result = pd.concat([df_result, df_temp], ignore_index=True)

        # 改用 submit + as_completed 模式
        future_to_task = {executor.submit(_process_single_stock_strategy, task): task for task in tasks}
        
        from concurrent.futures import as_completed
        # 注意：这里使用 tqdm 可能需要额外处理，暂时先简单遍历
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                df_temp = future.result()
                if dfutil.not_empty(df_temp):
                    if dfutil.empty(df_result):
                        df_result = df_temp
                    else:
                        df_result = pd.concat([df_result, df_temp], ignore_index=True)
            except Exception as e:
                # 记录具体哪只股票出错
                stock_file = task[0] if len(task) > 0 else "Unknown"
                logutil.log.error(f"股票策略执行失败: {stock_file} - {e}")
                continue
    
    process_end_time = time.time()
    execution_time = process_end_time - process_start_time
    logutil.log.info(f'多进程处理完成，耗时：{execution_time:.2f} 秒')

    # ========================================================
    # 🛠️ 【修复】重新定义正确的保存路径
    # ========================================================
    # 必须重新获取一次路径，因为之前的变量被 for 循环覆盖了！
    save_file_path = get_results_zh_trigger_filepath(start_date_int, end_date_int)
    
    # 打印确认一下路径对不对
    print(f"📂 [INFO] 最终结果将保存至: {save_file_path}")

    if dfutil.not_empty(df_result):
        df_result = df_result.sort_values(qldef.date_key, ascending=False)
        
        # ... (groupby 逻辑不变) ...
        df_result_grouped = df_result.groupby(
            [qldef.date_key, qldef.mtn_key, qldef.board_name_key],
            as_index=False
        ).agg(lambda x: '，'.join(x.astype(str)))
        
        if dfutil.not_empty(df_result_grouped):
            # ⚠️ 注意：这里把 file_path 改成 save_file_path
            is_exist = pathlib.Path(save_file_path).is_file()
            
            if is_exist:
                qloption.database.write_to_file_csv(df_result_grouped, save_file_path, mode='a', header=False)
            else:
                qloption.database.write_to_file_csv(df_result_grouped, save_file_path)
            
            print(f"✅ [SUCCESS] 文件已成功生成！")

    # ... (结束计时代码) ...

    ## =======================================================
    ## 🕵️‍♂️ [DEBUG START] 现场取证代码
    ## =======================================================
    #print("-" * 50)
    #print(f"🕵️‍♂️ [Step 2] 正在诊断文件生成问题...")
    
    # 1. 打印程序原本计划保存的路径 (这很重要！)
    #print(f"📂 [DEBUG] 程序认为的目标保存路径是: {file_path}")
    #print(f"❓ [DEBUG] 请检查这个路径下的文件夹是否存在？")

    ## 2. 检查内存中的原始数据
    #if dfutil.not_empty(df_result):
    #    count = len(df_result)
    #    print(f"✅ [DEBUG] 内存中持有 {count} 条原始策略数据。")
    #    
    #    # 3. 强行保存原始数据的备份 (绕过后面的 groupby 逻辑)
    #    # 这样我们可以区分是“没数据”还是“分组逻辑写坏了数据”
    #    try:
    #        # 存到桌面，文件名为 debug_raw_data.csv
    #        debug_path = os.path.join(os.path.expanduser("~"), 'Desktop', 'debug_raw_data.csv')
    #        df_result.to_csv(debug_path, encoding='utf-8-sig', index=False)
    #        print(f"💾 [DEBUG] 已强行备份原始数据到桌面: {debug_path}")
    #    except Exception as e:
    #        print(f"❌ [DEBUG] 备份失败 (可能是路径问题): {e}")
    #        # 尝试存到 C 盘根目录
    #        try:
    #            df_result.to_csv(r"C:\debug_raw_data.csv", encoding='utf-8-sig')
    #            print(f"💾 [DEBUG] 已强行备份到 C盘根目录: C:\\debug_raw_data.csv")
    #        except:
    #            pass
    #else:
    #    print("❌ [DEBUG] 严重问题：df_result 是空的！前面的日志是在骗人吗？")
    #
    #print("-" * 50)
    # =======================================================
    # [DEBUG END] 
    # =======================================================

    # cache_dir = qldef.quantitative_result_directory
    # suffix = f"results_zh_{start_date_int}_{end_date_int}_trigger.csv"
    if dfutil.not_empty(df_result):
        df_result = df_result.sort_values(qldef.date_key, ascending=False)  # 按日期的降序排序
        # 将数据列表中date、mtn和board_name都相同的列通过“，”合并，注意：不在by参数中的列的值才会合并，否则保持原值（agg函数则用于对每个分组进行聚合操作）
        df_result_grouped = df_result.groupby([qldef.date_key, qldef.mtn_key, qldef.board_name_key],
                                              as_index=False).agg(lambda x: '，'.join(x.astype(str)))
        if dfutil.not_empty(df_result_grouped):
            # file_path = os.path.join(cache_dir, suffix)
            is_exist = pathlib.Path(file_path).is_file()
            if is_exist:
                qloption.database.write_to_file_csv(df_result_grouped, file_path, mode='a', header=False)
            else:
                qloption.database.write_to_file_csv(df_result_grouped, file_path)

            # subject_text = f'{start_date_int}-{end_date_int}的量化策略分析结果'
            # body_text = f'附件是{subject_text}，请查收。'
            # dfutil.send_email_with_bs(qldef.receiver_email_list, subject_text, body_text,
            #                           [file_path], is_send=qldef.is_send_email)

    # 结束计时
    end_time = time.time()
    execution_time = end_time - start_time
    logutil.log.critical(f"执行{start_date_int} - {end_date_int}的量化策略已完成，"
                         f"总耗时长：{execution_time} 秒，量化结果数量：{dfutil.len_safe(df_result)}")
