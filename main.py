"""
main.py
qlsignalNew
Created by huanghx on 2024/7/22
Copyright © 2024 huanghx. All rights reserved.

FIXED: 添加命令行参数支持 (--start, --end)
"""
import multiprocessing
import argparse
# import multiprocessing
# from multiprocessing import Process
from multiprocessing import Pool
# from multiprocessing import Lock
# from concurrent.futures import ProcessPoolExecutor
# This is a sample Python script.
import databaseutil
import datarepairutil
import dfutil
import industryanalysis
import qldef
import qloption
import quantitativedcindustrytrading
# import quantitativesw2industrytrading

import quantitativetrading
import quantitativestrategy
import generate_industry_config


# 多进程运行
def multi_process(target, *args):
    if target is not None:
        if dfutil.len_safe(args) > 0:
            no_none_args = dfutil.remove_none_from_tuple(args)
            if dfutil.len_safe(no_none_args) > 1:
                # 如果参数大于1，则使用多进程运行
                
                # 使用 os.cpu_count() 获取当前机器的 CPU 核心数，
                # 并预留 1-2 个核心给操作系统和其他后台任务，避免系统卡死
                cpu_count = multiprocessing.cpu_count()
                max_workers = max(1, cpu_count - 1)
                
                print(f"🚀 启动并发处理 (Workers: {max_workers})...")
                
                # 使用 ProcessPoolExecutor 替代 multiprocessing.Pool
                from concurrent.futures import ProcessPoolExecutor
                with ProcessPoolExecutor(max_workers=max_workers) as executor:
                    futures = []
                    for process_args in no_none_args:
                        if process_args is not None:
                            # 提交任务
                            # 注意：executor.submit 需要将参数拆包传入，这里假设 process_args 是一个元组
                            future = executor.submit(target, *process_args)
                            futures.append(future)
                    
                    # 等待所有任务完成
                    # wait(futures) 
                    # 上下文管理器退出时会自动调用 executor.shutdown(wait=True)，所以这里不需要显式 wait，
                    # 除非我们需要在任务完成时立即处理结果。但为了确保异常被捕获，我们可以在这里遍历结果。
                    for future in futures:
                        try:
                            future.result() # 如果任务抛出异常，这里会重新抛出
                        except Exception as e:
                            print(f"❌ 任务执行出错: {e}")

            elif dfutil.len_safe(no_none_args) == 1:
                # 如果参数小于等于1，则使用主进程
                no_none_arg0 = no_none_args[0]
                if dfutil.len_safe(no_none_arg0) >= 2:
                    target(no_none_arg0[0], no_none_arg0[1])


# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # ========== 添加命令行参数支持 ==========
    parser = argparse.ArgumentParser(description='量化交易系统 - SQLite版本')
    
    # 支持位置参数 (兼容 python main.py 4 20240101 20240131 格式)
    parser.add_argument('positional_args', nargs='*', 
                        help='位置参数兼容: [步骤号] [开始日期] [结束日期]')

    parser.add_argument('--start', type=int, default=20240101, 
                        help='开始日期 (格式: YYYYMMDD, 默认: 20240101)')
    parser.add_argument('--end', type=int, default=20240131, 
                        help='结束日期 (格式: YYYYMMDD, 默认: 20240131)')
    parser.add_argument('--skip-query', action='store_true', 
                        help='跳过数据库查询，直接使用已有CSV文件')
    parser.add_argument('--skip-strategy', action='store_true', 
                        help='跳过量化策略执行')
    parser.add_argument('--skip-analysis', action='store_true', 
                        help='跳过行业板块分析')
    
    args = parser.parse_args()
    
    # 默认值
    start_date1 = args.start
    end_date1 = args.end
    target_step = 0 # 0 表示运行所有默认步骤
    
    # 处理位置参数覆盖
    if args.positional_args:
        # 如果有位置参数，尝试解析
        if len(args.positional_args) >= 1:
            try:
                target_step = int(args.positional_args[0])
                print(f"🎯 指定运行步骤: {target_step}")
            except ValueError:
                pass
        
        if len(args.positional_args) >= 2:
            try:
                start_date1 = int(args.positional_args[1])
            except ValueError:
                pass
                
        if len(args.positional_args) >= 3:
            try:
                end_date1 = int(args.positional_args[2])
            except ValueError:
                pass
    
    print(f"=" * 80)
    print(f"量化交易系统 - SQLite版本")
    print(f"=" * 80)
    print(f"日期范围: {start_date1} - {end_date1}")
    print(f"运行模式: {'全部步骤' if target_step == 0 else f'仅运行步骤 {target_step}'}")
    if target_step == 0:
        print(f"跳过数据库查询: {args.skip_query}")
        print(f"跳过量化策略: {args.skip_strategy}")
        print(f"跳过行业分析: {args.skip_analysis}")
    print(f"=" * 80)
    print()

    # 步骤0: 更新行业配置 (总是执行)
    print("Step 0: 更新行业配置 (model2.csv)...")
    try:
        generate_industry_config.generate_config()
        print("Step 0 完成\n")
    except Exception as e:
        print(f"Step 0 失败 (非致命): {e}\n")

    # 必须放在 if __name__ == '__main__': 之后，否则多进程会报错
    # freeze_support()  # Windows下必须调用，但这里不是打包成exe，所以不需要
    
    # 批量修复异常数据
    # datarepairutil.fix_abnormal_data()
    # databaseutil.dc_map_to_sw2()
    # board_target_df = qloption.database.get_board_target_df()
    # industryanalysis.stocks_to_industry(20240328, 20240827, board_target_df)
    # datarepairutil.drop_duplicates_file(qldef.stocks_tobe_traded_directory, '2019')
    # datarepairutil.calculate_board_stock_count(20250101, 20251231)  # 每年1日需要执行一次
    # datarepairutil.merge_all_stocks_tobe_traded_to_one_file('2024')

    date_now = dfutil.date_now()
    
    # 保留原有的多进程配置（但默认禁用）
    start_date2 = 20140101
    end_date2 = 20241216
    start_date3 = 20190101
    end_date3 = 20191231
    start_date4 = 20160101
    end_date4 = 20161231

    # process_target = None

    """
    创建进程锁：解决多个进程同时读写统一文件，出现数据丢失或错乱的问题
    不同的进程之间通过队列或其他方式传递锁（Lock）对象，但是做法不正确。在Python的多处理模块中，
    Lock对象不能通过普通的队列传递，它们必须通过继承被共享。
    解决方法：
        确保在创建进程时，如果需要共享Lock对象，可以使用Manager对象中的Lock()方法来创建一个可以在不同进程之间共享的锁对象,
    而不能直接使用multiprocessing.Lock()。
    """
    # process_lock = Lock()
    process_lock = multiprocessing.Manager().Lock()
    process1_args = (start_date1, end_date1, process_lock)
    process2_args = (start_date2, end_date2, process_lock)
    process3_args = (start_date3, end_date3, process_lock)
    process4_args = (start_date4, end_date4, process_lock)
    
    # 默认只使用 process1（命令行参数指定的日期范围）
    process2_args = None
    process3_args = None
    process4_args = None

    # 是否查询数据库
    # 逻辑：如果没有指定特定步骤(0)，或者指定了步骤1，且没有跳过查询
    is_query_db = (target_step == 0 or target_step == 1) and (not args.skip_query)
    if is_query_db:
        print("Step 1: 从数据库查询日度行情数据...")
        process_target_stock = databaseutil.start_query_stock_daily_quote  # 查询个股日度行情数据（含沪深300指数日度行情）
        process_target_sw2 = databaseutil.start_query_sw2_industry_daily_quote  # 查询申万二级行业板块日度行情数据
        multi_process(process_target_stock, process1_args, process2_args, process3_args, process4_args)
        multi_process(process_target_sw2, process1_args, process2_args, process3_args, process4_args)
        print("Step 1 完成\n")
    else:
        print("Skip Step 1: 数据库查询\n")

    # 是否开始执行量化策略
    is_start_executing_strategy = (target_step == 0 or target_step == 2) and (not args.skip_strategy)
    if is_start_executing_strategy:
        print("Step 2: 执行量化策略...")
        process_target = quantitativestrategy.start_executing_strategy
        multi_process(process_target, process1_args, process2_args, process3_args, process4_args)
        print("Step 2 完成\n")
    else:
        print("Skip Step 2: 量化策略\n")

    # XGBoost 动态阈值模型训练 (Step 2.5)
    is_train_xgboost = (target_step == 0 or target_step == 3) and (not args.skip_analysis)
    if is_train_xgboost:
        print("Step 2.5: 训练 XGBoost 动态阈值模型...")
        try:
            import analyze_industry_heat
            import train_xgboost_threshold_model
            
            print("  -> 2.5.1 生成行业热度历史数据...")
            analyze_industry_heat.main()
            
            print("  -> 2.5.2 训练 XGBoost 模型并生成动态预测...")
            train_xgboost_threshold_model.main()
            
            print("Step 2.5 完成\n")
        except Exception as e:
            print(f"Step 2.5 失败: {e}\n")
    else:
        print("Skip Step 2.5: XGBoost 模型训练\n")

    # 对量化结果进行行业板块买入/卖出分析
    is_start_industry_sector_analysis = (target_step == 0 or target_step == 3) and (not args.skip_analysis)
    is_merge = True  # 是否取交集（默认为True，表示取交集，否则取并集）
    if is_start_industry_sector_analysis:
        print("Step 3: 行业板块分析...")
        process_target = industryanalysis.start_industry_sector_analysis
        # process1_args = (start_date1, end_date1, is_merge)
        multi_process(process_target, process1_args, process2_args, process3_args, process4_args)
        print("Step 3 完成\n")
    else:
        print("Skip Step 3: 行业板块分析\n")

    # 开始进行股票交易回测（注意：交易回测的可交易日期总天数不能低于21天，因为self.month_period = 21，否则会出现越界）
    # 逻辑：如果指定了步骤4，则强制运行；否则如果步骤为0，则跟随 skip_strategy 设置
    if target_step == 4:
        is_start_stock_back_trade = True
    elif target_step == 0:
        is_start_stock_back_trade = not args.skip_strategy
    else:
        is_start_stock_back_trade = False
        
    if is_start_stock_back_trade:
        print("Step 4: 股票交易回测...")
        process_target = quantitativetrading.run_strategy
        # 使用命令行参数的时间范围，而不是默认的 process1_args (20240101-20240131)
        # 如果需要测试特定时间段，可以在命令行指定 --start 20240101 --end 20240131
        current_args = (start_date1, end_date1, process_lock)
        multi_process(process_target, current_args, None, None, None)
        print("Step 4 完成\n")
    else:
        print("Skip Step 4: 股票交易回测\n")

    # 开始进行行业板块交易回测
    # 逻辑：如果指定了步骤5，则强制运行；否则如果步骤为0，则跟随 skip_analysis 设置
    if target_step == 5:
        is_start_board_back_trade = True
    elif target_step == 0:
        is_start_board_back_trade = not args.skip_analysis
    else:
        is_start_board_back_trade = False
        
    if is_start_board_back_trade:
        print("Step 5: 行业板块交易回测...")
        process_target = quantitativedcindustrytrading.run_strategy
        current_args = (start_date1, end_date1, process_lock)
        multi_process(process_target, current_args, None, None, None)
        print("Step 5 完成\n")
    
    print("=" * 80)
    print("Run Completed!")
    print("=" * 80)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
