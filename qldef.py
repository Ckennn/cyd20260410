# coding=utf-8
"""
常量（被import的最底层）
"""

import sys
from enum import Enum
from typing import Callable, Optional
import pandas as pd
import os

import dfutil
import project_paths

# note: 不能 import ql 任何包

# note: 这里的定义不会在程序中动态改变，但是可以通过 env.custom.csv 在启动时设置

# note: 需要被外部访问的 def 或 lambda 名称不要以 "__" 开头，从其它文件中访问它们正常，但是从class中访问它们时会报错：
#       AttributeError: module 'qldef' has no attribute '_[class]__[attribute]'


#############################################
# todo: impl: 回调变量（防止循环import而设置，不好，需要重构）
#############################################

# note: 检查错误（ None会让使用时报错，防止代码错误 ）
check_the_value_defined = lambda: dfutil.is_var_defined_or_exit(__name__, var_prefix="the_")

# noinspection PyTypeChecker
the_signal_struct_stats_pk_list: list[str] = None
# noinspection PyTypeChecker
the_struct_partition_default_list: list[str] = None
# noinspection PyTypeChecker
the_stats_partition_default_list: list[str] = None
# noinspection PyTypeChecker
the_trigger_adjust_default_func: Callable[[pd.DataFrame], pd.DataFrame] = None
# noinspection PyTypeChecker
the_goodmerge_adjust_default_func: Callable[[pd.DataFrame], pd.DataFrame] = None
# # noinspection PyTypeChecker
# the_transaction_adjust_default_func: Callable[[pd.DataFrame], pd.DataFrame] = None
# noinspection PyTypeChecker
the_strip_adjust_default_func: Callable[[pd.DataFrame], pd.DataFrame] = None

#############################################
# 功能定义
#############################################
# todo: 目前代码上并没有删除超过时长的数据（signal/struct/stats），会计算越来越慢，需要改进
# note：可以在 env.custom.csv 中设置

#
# trigger model
# noinspection PyTypeChecker
model_type: str = None  # david | caochen
#
model_type_david: str = "david"
model_type_caochen: str = "caochen"

#
# noinspection PyTypeChecker
model_signal_symbol: str = None  # sigdef | sigdavid | sigcaochen
#
model_signal_group_list: list[str] = ["full"]  # full | core

# note: 配置时，uall 应该 放到最后，为了先执行其它sector逻辑，提高性能。同时，其它sector在 create trigger 时优先判断
# noinspection PyTypeChecker
model_sector_list: list[str] = None
# 用于集群的cluster配置
# noinspection PyTypeChecker
model_cluster_sector_list: list[str] = None
# noinspection PyTypeChecker
# model_cluster_autotag_list: list[str] = None

# 主模型目前计算的天数（交易日）(signal, struct, stats)
model_sss_date_count: int = 250
# 主模型可以计算的天数列表（交易日）(signal, struct, stats)
model_sss_date_count_list: list[int] = [250]
#
to_model_sss_duration_symbol = lambda: to_duration_symbol(model_sss_date_count)
to_model_sss_duration_symbol_list = lambda: [to_duration_symbol(x) for x in model_sss_date_count_list]

#
# 次模型目前使用的计算天数（交易日）(good filter, good merge, good out)
# note：大小只与参数训练有关，空间结构bintype和时间结构signal都与此无关(stats决定)
# note: 3个月，因为 goodmerge 后到 history 不再变化之间需要间隔 category 时长，
#       如果我们考虑 next20d 和 bin0.col.trend_40_20 结构，则需要 20+40 = 60 日
model_good_date_count: int = 20
# 次模型可以计算的天数列表（交易日）(good filter, good merge, good out)
model_good_date_count_list: list[int] = [20]
#
to_model_good_duration_symbol = lambda: to_duration_symbol(model_good_date_count)
to_model_good_duration_symbol_list = lambda: [to_duration_symbol(x) for x in model_good_date_count_list]

#
model_when_list: list[str] = [
    "close1n",
    "open2n", "close2n", "open3n", "close3n"
]
#
model_trade_when_list: list[str] = [
    "open2n", "close2n", "open3n", "close3n"
]
#
to_enable_model_when_by = lambda __when: \
    None if False \
        else True if dfutil.empty(model_when_list) \
        else (__when in model_when_list)
to_enable_model_trade_when_by = lambda __when: \
    None if False \
        else True if dfutil.empty(model_trade_when_list) \
        else (__when in model_trade_when_list)

#
model_category_list: list[str] = [
    "next02d",
    "next03d", "next04d", "next05d", "next06d", "next07d", "next08d", "next09d", "next10d",
    "next15d", "next20d"
]
#
model_trade_category_list: list[str] = [
    "next03d", "next04d", "next05d", "next06d", "next07d"
]
#
to_enable_model_category_by = lambda __category: \
    None if False \
        else True if dfutil.empty(model_category_list) \
        else (__category in model_category_list)
to_enable_model_trade_category_by = lambda __category: \
    None if False \
        else True if dfutil.empty(model_trade_category_list) \
        else (__category in model_trade_category_list)

#
# noinspection PyTypeChecker
model_bintype_list: list[str] = None  # 20220925增加
#
to_enable_model_bintype_by = lambda __bintype: \
    None if False \
        else True if dfutil.empty(model_bintype_list) \
        else (__bintype in model_bintype_list)

#
# noinspection PyTypeChecker
model_goodmerge_list: list[str] = None  # 1,2,11,12,20,99  # 20220925增加
#
to_enable_model_goodmerge_by = lambda __goodmerge: \
    None if False \
        else True if dfutil.empty(model_goodmerge_list) \
        else (__goodmerge in model_goodmerge_list)

#
# noinspection PyTypeChecker
model_goodout_list: list[str] = None  # 0,1122,20,99  # 20220925增加
#
to_enable_model_goodout_by = lambda __goodout: \
    None if False \
        else True if dfutil.empty(model_goodout_list) \
        else (__goodout in model_goodout_list)

#
model_transid_prefix: str = ""
model_transid_length: int = 9  # note: 目前支持10亿条

#
is_model_duration_symbol_support_year: bool = False  # 与us旧系统兼容（他们使用了 1y 字符串）
#
to_duration_datecount = lambda __symbol: \
    None if False \
        else int(__symbol[0:-1]) * 1 if __symbol.endswith("d") \
        else int(__symbol[0:-1]) * 250 if __symbol.endswith("y") \
        else dfutil.error(f"{__symbol=}, use {durationdatecount_all=}", return_value=durationdatecount_all)
#
to_duration_symbol = lambda __datecount: \
    None if False \
        else f"{int(__datecount)}d" if (__datecount <= 250 * 5) and (not is_model_duration_symbol_support_year) \
        else f"{int(__datecount)}d" if (__datecount < 250) and is_model_duration_symbol_support_year \
        else f"{int(__datecount / 250)}y" if (__datecount <= 250 * 5) and is_model_duration_symbol_support_year \
        else dfutil.error(f"{__datecount=}, use {durationsymbol_all=}", return_value=durationsymbol_all)
# #
# to_model_sss_duration_symbol = lambda: to_duration_symbol(model_sss_date_count)
# to_model_sss_duration_symbol_list = lambda: [to_duration_symbol(x) for x in model_sss_date_count_list]
# #
# to_model_good_duration_symbol = lambda: to_duration_symbol(model_good_date_count)
# to_model_good_duration_symbol_list = lambda: [to_duration_symbol(x) for x in model_good_date_count_list]


#############################################
# 功能定义
#############################################

#
#
enable_bintype_vary_close: bool = True  # 2021
#
enable_bintype_bin0_col_trend_03_01: bool = True  # 20211203增加
enable_bintype_bin0_col_trend_02_01: bool = True  # 20211203增加
enable_bintype_bin0_col_trend_01_01: bool = True  # 20220102增加
#
enable_bintype_bin10_col_trend_04_01: bool = True  # 20220102增加
enable_bintype_bin10_col_trend_03_01: bool = True  # 20220102增加
enable_bintype_bin10_col_trend_02_01: bool = True  # 20220102增加
enable_bintype_bin10_col_trend_01_01: bool = True  # 20220102增加
enable_bintype_bin10_col_closeema: bool = True  # 20220215增加
enable_bintype_bin10_col_ema: bool = True  # 20220215增加
enable_bintype_bin10_col_macd: bool = True  # 20220215增加
#
to_enable_bintype_bin10 = lambda: all([
    to_enable_model_bintype_by("bin10"),
    enable_bintype_bin10_col_trend_04_01,
    enable_bintype_bin10_col_trend_03_01,
    enable_bintype_bin10_col_trend_02_01,
    enable_bintype_bin10_col_trend_01_01,
    enable_bintype_bin10_col_closeema,
    enable_bintype_bin10_col_ema,
    enable_bintype_bin10_col_macd,
])

#
# enable_category_next03d: bool = True  # 20220110增加
# enable_category_next04d: bool = True  # 20220110增加
# enable_category_next02d: bool = True  # 20220312增加

#
enable_measure_moment_open: bool = True  # 20220312增加
enable_measure_moment_high: bool = True  # 20220402增加
enable_measure_moment_low: bool = True  # 20220402增加

#
# def
enable_signal_non: bool = True  # 20220312增加
#
enable_signal_ema_slow_above_fast: bool = True  # 20220312增加
enable_signal_ema_slow_below_fast: bool = True  # 20220312增加
enable_signal_low_below_days_20: bool = True  # 20220312增加
enable_signal_low_below_days_50: bool = True  # 20220312增加
enable_signal_low_below_days_100: bool = True  # 20220312增加
enable_signal_low_below_days_250: bool = True  # 20220312增加
enable_signal_high_above_days_20: bool = True  # 20220312增加
enable_signal_high_above_days_50: bool = True  # 20220312增加
enable_signal_high_above_days_100: bool = True  # 20220312增加
enable_signal_high_above_days_250: bool = True  # 20220312增加
enable_signal_cont_rise_cross_ema: bool = True  # 20220312增加
enable_signal_cont_rise_turn_down: bool = True  # 20220312增加
enable_signal_cont_rise_for_times: bool = True  # 20220312增加
enable_signal_cont_rise_for_times_2: bool = True  # 20220312增加
enable_signal_cont_down_turn_rise: bool = True  # 20220312增加
enable_signal_cont_flat_sudden_rise: bool = True  # 20220312增加
enable_signal_cont_flat_sudden_down: bool = True  # 20220312增加
enable_signal_down_fast_turn_slow: bool = True  # 20220312增加
enable_signal_down_fast_turn_slow_3: bool = True  # 20220312增加
enable_signal_rise_good_one_day: bool = True  # 20220312增加
enable_signal_rise_good_after_days: bool = True  # 20220312增加
enable_signal_down_good_one_day: bool = True  # 20220427增加
enable_signal_down_good_after_days: bool = True  # 20220427增加
#
# caochen
# 底部上破
enable_signal_caochen_volume_bloom_above_bottom_x_20220915: bool = False  # 20221021增加 # david: 100日pos太低
enable_signal_caochen_volume_bloom_above_bottom_x_20221011: bool = False  # 20221021增加 # david: 60日pos太低
enable_signal_caochen_volume_bloom_above_bottom_x_20230110: bool = False  # 20230110增加 # caochen: 20230110 去除
enable_signal_caochen_volume_bloom_above_bottom_x_20230111: bool = True  # 20230111增加 # caochen: 20230214 去除 # david: 20230302 恢复
enable_signal_caochen_volume_bloom_above_bottom_x_20230112: bool = True  # 20230112增加 # caochen: 20230214 去除 # david: 20230302 恢复
# 上升趋势
enable_signal_caochen_price_rise_predict_rise_x_20220914: bool = True  # 20221021增加
enable_signal_caochen_price_rise_predict_rise_x_20220915: bool = False  # 20221021增加 # caochen: 20221021 调整
# 上涨中继1
enable_signal_caochen_price_down_predict_rise_1_x_20220915: bool = False  # 20221021增加
enable_signal_caochen_price_down_predict_rise_1_x_20221020: bool = False  # 20221021增加
enable_signal_caochen_price_down_predict_rise_1_x_20221129: bool = True  # 20221129增加 # 增加ma上涨限制 # 增加了斜率概念 # caochen: 20230213: 停掉 # david: 20230302 恢复
# 上涨中继2
enable_signal_caochen_price_down_predict_rise_2_1_x_20220915: bool = False  # 20221021增加
enable_signal_caochen_price_down_predict_rise_2_2_x_20220915: bool = False  # 20221021增加
enable_signal_caochen_price_down_predict_rise_2_x_20221011: bool = False  # 20221021增加
enable_signal_caochen_price_down_predict_rise_2_x_20221020: bool = True  # 20221021增加 # 增加ma上涨限制
# 上涨中继3
enable_signal_caochen_price_down_predict_rise_3_x_20221011: bool = False  # 20221021增加
enable_signal_caochen_price_down_predict_rise_3_x_20221020: bool = True  # 20221021增加 # 增加ma上涨限制
# 单阳不破
enable_signal_caochen_price_rise_keep_close_1_x_20221121: bool = False  # 20221201增加 # caochen: 20221205停止
# 年线企稳
enable_signal_caochen_price_reach_year_rise_x_20230203: bool = False  # 20230203增加 # david: 20230210 caochen 更新
enable_signal_caochen_price_reach_year_rise_3_x_20230208: bool = False  # 20230208增加 # david: 20230210 caochen 更新
enable_signal_caochen_price_reach_year_rise_4_x_20230208: bool = False  # 20230208增加 # david: 20230210 caochen 更新
enable_signal_caochen_price_reach_year_rise_5_x_20230208: bool = False  # 20230208增加 # david: 20230210 caochen 更新
# 年线稳涨
enable_signal_caochen_price_reach_year_rise_1_x_20230210: bool = False  # 20230210增加 # david:  缺少价格下降的定义
enable_signal_caochen_price_reach_year_rise_1_x_20230212: bool = True  # 20230212增加
enable_signal_caochen_price_reach_year_rise_2_x_20230210: bool = True  # 20230210增加
enable_signal_caochen_price_reach_year_rise_3_x_20230210: bool = False  # 20230210增加 # caochen: 20230213: 去掉条件4
enable_signal_caochen_price_reach_year_rise_3_x_20230213: bool = True  # 20230210增加
# 低点上移
enable_signal_caochen_price_low_above_previous_x_20230203: bool = False  # 20230203增加 # david: trigger太多了（20230207有1300条）
enable_signal_caochen_price_low_above_previous_10_x_20230208: bool = True  # 20230208增加 # caochen: 20230214 去除 # david: 20230302 恢复
# 量增价涨
enable_signal_caochen_volume_enlarge_price_rise_4_x_20230310: bool = True  # 20230310增加

#
# enable_stats_partition_sub: bool = True  # 20220405增加
# enable_stats_sector: bool = True  # 20220417增加
# enable_sector_more: bool = True  # 20220429增加

#
# note: 提高性能：屏蔽目前不需要用到的计算
enable_stats_dist_std: bool = False  # 20220505增加
enable_stats_dist_skew: bool = False  # 20220505增加
enable_stats_dist_kurt: bool = False  # 20220505增加

#
# enable_goodout_result_sort_weight: bool = True  # False  # 20220524增加
#
# todo: impl: 调整参数重新生成trigger后，需要先清除 dqteall 文件 和 transaction 文件中该 date 的旧记录，目前不会自动清除
enable_goodout_ratio_close: bool = True  # 20220515增加
enable_goodout_ratio_close_multiply: bool = True  # 20220913增加
enable_goodout_ratio_high_low: bool = True  # 20220515增加
enable_goodout_ratio_high_low_multiply: bool = True  # 20220913增加
enable_goodout_ratio_high: bool = True  # 20220515增加
enable_goodout_ratio_high_multiply: bool = True  # 20220913增加
enable_goodout_ratio_low: bool = True  # 20220515增加
enable_goodout_ratio_low_multiply: bool = True  # 20220913增加
#
enable_goodout_datecount_close: bool = True  # 20220515增加
enable_goodout_datecount_close_multiply: bool = True  # 20220913增加
enable_goodout_datecount_high_low: bool = True  # 20220515增加
enable_goodout_datecount_high_low_multiply: bool = True  # 20220913增加
enable_goodout_datecount_high: bool = True  # 20220515增加
enable_goodout_datecount_high_multiply: bool = True  # 20220913增加
enable_goodout_datecount_low: bool = True  # 20220515增加
enable_goodout_datecount_low_multiply: bool = True  # 20220913增加

#
# enable_joblib_memory_cache: bool = True

#
enable_gen_bin_str_cache: bool = False  # 测试发现cache对于性能提升很不明显，参见exec_test.__test_bins_calc_bin_str
enable_calc_bin_str_cache: bool = False  # todo: impl: 这个cache没有用到，因为__calc_struct_bin_str中已经进行了cache。需要比较哪种更快

#
enable_create_indicator_multitask: bool = False
create_indicator_task_count: int = 2

#
enable_detect_signal_multitask: bool = False
detect_signal_task_count: int = 2

#
enable_find_struct_multitask: bool = False  # note: cache init很慢，除非数据很多，否则单进程更快
find_struct_task_count: int = 2  # note: 4 core mac机器执行时间长度：1(比2慢20%) > 4(比2慢5%) > 3~2

#
enable_calc_stats_signal_dist_multitask: bool = False
enable_calc_stats_bin_dist_multitask: bool = False
enable_calc_stats_bin_rank_multitask: bool = False
calc_stats_task_count: int = 2
calc_stats_signal_dist_task_count: int = 2
calc_stats_bin_dist_task_count: int = 2
calc_stats_bin_rank_task_count: int = 2
calc_stats_result_merge_method: str = "once"  # "many"
calc_stats_adjust_dist_col_of_count_as_int: bool = False  # date_count保持小数吧，更加精确
# calc_stats_duration_symbol: str = durationsymbol_latest_1_year  # 20220315增加
enable_calc_stats_bin_rank: bool = True  # 20220315增加，note：新版本计算rank很慢，原因未知。目前rank只用于rpt显示quote，先停止
enable_file_stats_save_csvzip: bool = False  # 20220315增加 note: 保存csv.zip很慢（20万行2千列的stats保存csv.zip需要20m）

#
enable_probe_goodfilter_expect_multitask: bool = False
probe_goodfilter_expect_task_count: int = 2
enable_probe_goodfilter_confid_multitask: bool = False
probe_goodfilter_confid_task_count: int = 2
# 数据多时内存可能不足，减少goodfilter的数据范围（goodfilter的时长只与train param有关，其dist取值的时长则由stats决定）
enable_probe_goodfilter_duration_min: bool = True  # 20220315增加

#
enable_probe_goodmerge_multitask: bool = False
probe_goodmerge_task_count: int = 2

#
enable_train_param_multitask: bool = False
train_param_task_count: int = 2

#
enable_sum_trade_multitask: bool = False
sum_trade_task_count: int = 2

#
enable_traverse_reduce_space_multitask: bool = False
traverse_reduce_space_task_count: int = 2
#
enable_traverse_plot_multitask: bool = False
traverse_plot_task_count: int = 2
#
enable_traverse_agg_multitask: bool = False
traverse_agg_task_count: int = 2
#
enable_traverse_plot_show: bool = True
#
enable_traverse_plot_scatter: bool = True
enable_traverse_plot_bar: bool = True
#
traverse_space_create_method: str = "trigger"  # trigger | dimension

#
enable_temp_cache_large_unzip: bool = False

#
recent_create_probe_good_date_count: int = 5
# recent_create_train_param_date_count: int = 1  # 5 # note: 参数训练不需要考虑以前未执行的日期吧，只考虑最新执行日期
recent_create_trigger_date_count: int = 5
recent_goodout_search_param_prev_date_count: int = 3  # 天数不能太长（保持最新状态）
recent_delete_temp_date_count: int = 3  # note：1 表示今日

#
enable_email_trigger_csv_transpose: bool = True
enable_email_trigger_csv_transpose_quick: bool = True
enable_email_trigger_csv_transpose_date: bool = True
enable_email_trigger_csv_transpose_trade: bool = True
enable_email_trigger_csv_transpose_param: bool = False
enable_email_trigger_csv_transpose_transaction: bool = False
enable_email_trigger_csv_transpose_summary: bool = False

#
enable_option_save_file_csvzip_sync: bool = False  # 20220315增加 note：csvzip保存太慢，异步处理吧

#
struct_bin_str_split_date_list_count: int = 30  # date数量太小时分date处理会导致multitask通讯消耗较高

#
fetch_zacks_interval_second: int = 5
#
fetch_akshare_interval_second: float = 0.1

#
enable_context_factor_expect: bool = False  # False 提高性能
enable_context_factor_moment: bool = True  # True 用于控制moment不可用

#
enable_notify_trade_email: bool = True

#
enable_fetch_spot_trade_division: bool = False

#
enable_quote_price_low_high_use_enough: bool = False  # 使用 "足够好" 算法来获取报价的最大最小取值

#
enable_simu_param_cache: bool = False  # note: 函数逻辑，以及，cache的key，都是字符串操作，测试发现不cache速度还更快些

#
enable_trade_auto_cache: bool = True
enable_trade_auto_transaction_cache: bool = True
enable_trade_track_cache: bool = True
enable_trade_track_transaction_cache: bool = True

# 备份方式
enable_trade_batch_backup: bool = True  # 批量更新（性能高）
enable_trade_change_backup: bool = False  # 变化更新（性能低）

#
# dfutil
#
dfutil_memory_verbose: int = 1  # 9
#
# note：有些cache很占据磁盘，这样性能可能反而降低，例如 act_trade 中 valid|enter|exit 方法，simu时达到50万个文件
dfutil_memory_enable_cache_model: bool = False  # note: 太多文件了，不要cache
dfutil_memory_enable_cache_trade: bool = False  # note: 太多文件了，不要cache
dfutil_memory_enable_cache_good: bool = False  # note: 太多文件了，不要cache
dfutil_memory_enable_cache_simu: bool = False  # note: 太多文件了，不要cache
#
dfutil_update_df_pandas_method: str = "update"  # "loc"
dfutil_update_df_pandas_update_slice_step: int = 1000
dfutil_multitask_dispatch_method: str = "zigzag"  # "same"
dfutil_multitask_backend_engine: str = "loky"  # "threading", "ray"
#
is_dfutil_multitask_dispatch_zigzag = lambda: dfutil_multitask_dispatch_method == "zigzag"
is_dfutil_multitask_backend_ray = lambda: dfutil_multitask_backend_engine == "ray"
#
# note: 有些程序可能需要在特定时段退出
# 全局配置
dfutil_log_force_exit_time_begin_end_tuple: Optional[tuple[int, int]] = None
# 特定程序
program_gather_force_exit_time_begin_end_tuple: Optional[tuple[int, int]] = None
program_trade_force_exit_time_begin_end_tuple: Optional[tuple[int, int]] = None
program_quote_force_exit_time_begin_end_tuple: Optional[tuple[int, int]] = None
program_fetch_force_exit_time_begin_end_tuple: Optional[tuple[int, int]] = None

#############################################
# 变量定义
#############################################

var_when = "$when$"
var_category = "$category$"

#############################################
# 下面定义的符号，可以让保存文件名称时，不会出现被操作系统限制的情况
#############################################

period_previous_alias = "p"  # previous
period_next_alias = "n"  # next

duration_day_alias = "d"  # day

delim_symbol = "_"

delim_file = "."

delim_range_slice = ":"

delim_funcarg = "(,)"  # funcarg：函数参数格式，例如 mean(11,12)
delim_funcarg_left = "("
delim_funcarg_arg = ","
delim_funcarg_right = ")"

# 完整格式：
#       main1@main2
#       sub1$sub2
#       expr1&expr2
#       k1=v1
delim_part_main = "@"  # "." # 特殊query条件中可能存在float占用了"."符号（例如 gss1=1.0&gss2=2.0 ）
delim_part_sub = "$"  # "_" # 特殊query条件中的col可能存在"_"符合（例如 gm_gss1=1 ）
delim_expr_multi = "&"
delim_expr_kev = "="

# delim_val_prefix = "#"  #

#############################################
# 常量定义
#############################################

# 用于日志grep的输出标志
line_main = dfutil.the_line_main
line_func = dfutil.the_line_func
line_part = dfutil.the_line_part
line_buyy = f"{dfutil.the_elem_main}>>>>>>>>"
line_sell = f"<<<<<<<<{dfutil.the_elem_main}"

encoding = "utf-8"

float_max = float("inf")
float_min = float("-inf")

int_max = sys.maxsize
int_min = 0 - sys.maxsize

num_q: int = 1000 * 1  # 千
num_w: int = 1000 * 10  # 万
num_m: int = 1000 * 1000  # 百万
num_y: int = 1000 * 1000 * 100  # 亿
num_10y: int = num_y * 10  # 10亿
num_100y: int = num_y * 100  # 100亿

money_unlimited: float = 999999999.0

token_unlimited: int = 999999999

datecount_unlimited: int = 9999

# 保证失效配置
date_default: int = 20020101
date_max: int = 22220101
date_min: int = 20020101

# 保证失效配置
timestamp_default: int = 20020101000000
timestamp_max: int = 22220101000000
timestamp_min: int = 20020101000000

# 保证失效配置
factor_max: float = 999999999.0
factor_min: float = 0.0

china_market_key: str = "zh"

set_delim = "|"  # set 中多个数值使用"|"分割
and_delim = "&"  # and 中多个数值使用"&"分割

worldrange_found = "found"

signalsymbol_all = None  # 空表示所有吧，兼容现在的文件格式
signalsymbol_non = "signon"  # 无信号
signalsymbol_def = "sigdef"  # 预定义（没有non信号）
signalsymbol_david = "sigdavid"  # david 定义
signalsymbol_caochen = "sigcaochen"  # caochen 定义
#
to_signal_symbol_list = lambda: dfutil.var_val_list(__name__, "signalsymbol_")
is_signal_symbol_all = lambda __symbol: __symbol == signalsymbol_all

#
sector_all = "uall"
#
sector_rise_equal_put = "urep"
sector_not_trigger = "nt"

# 板块
__the_sector_2_name: dict = {
    #
    "f0": "",  # 普通
    "f1": "单向",  # ETF
    "f2": "双向",  # ETF
    #
    "c": "做多",  # call
    "p": "做空",  # put
    #
    "nt": "无Trigger",  # no trigger # note: 类似资源类etf（商品/干散等）的波动与事件关系较大，很难判断概率，去除trigger先
    # Standard-defined
    "are": "区域",  # area
    "bio": "生物",  # biotechnology
    "cdt": "商品",  # commodity
    "eng": "能源",  # energy
    "est": "地产",  # estate
    "fin": "金融",  # financial
    "idx": "指数",  # index
    "res": "资源",  # resource
    "rtl": "零售",  # retail
    "tec": "科技",  # tech
    "tsp": "运输",  # transport
    "tvl": "旅游",  # travel
    "vix": "波动",  # volatility
    # User-defined
    "uall": "（所有）",  # note：用于程序处理，无需token中设置
    "uvix": "反向波动",  # vix 波动率相关
    "uwsb": "散户聚集",  # wall street bets，散户较多参与（gme/amc类型meme股票）
    "ubcc": "中国概念",  # board of china concept
    "urec": "上涨做多",  # rise equal call, 买入意味着做多（etf或etn）
    "urep": "上涨做空",  # rise equal put, 买入意味着做空（etf或etn）
    "ul3x": "3倍杠杆",  # leverage 3x, 3倍杠杆（etf或etn）
    "ul3c": "3倍做多",  # leverage 3x, 3倍杠杆（etf或etn）
    "ul3p": "3倍做空",  # leverage 3x, 3倍杠杆（etf或etn）
    "ul2x": "2倍杠杆",  # leverage 2x, 2倍杠杆（etf或etn）
    "ul2c": "2倍做多",  # leverage 2x, 2倍杠杆（etf或etn）
    "ul2p": "2倍做空",  # leverage 2x, 2倍杠杆（etf或etn）
    "ucxc": "商品做多",  # commodity x call, 商品做多（etf或etn）
    "ucxp": "商品做空",  # commodity x put, 商品做空（etf或etn）
    "uc1c": "1倍商品做多",  # commodity 1x call, 商品做多（etf或etn）
    "uc1p": "1倍商品做空",  # commodity 1x put, 商品做空（etf或etn）
    "uc2c": "2倍商品做多",  # commodity 2x call, 商品做多（etf或etn）
    "uc2p": "2倍商品做空",  # commodity 2x put, 商品做空（etf或etn）
    #
    "uts=": "(标的)",  # target set = , 标的集合 # note: 多个target之间以"&"分割（不采用"｜"，因为无法在windows上保存文件名称）
    "utp=": "",  # target prefix  = 标的集合
    #
    "000000": "(无)",  # note：表示没有分组
    "000016": "上证50",
    "000016p0": "上证50p0",
    "000016p3": "上证50p3",
    "000016p6": "上证50p6",
    "000016p688": "上证50p688",
    "000300": "沪深300",
    "000300p0": "沪深300p0",
    "000300p3": "沪深300p3",
    "000300p6": "沪深300p6",
    "000300p688": "沪深300p688",
    "000905": "中证500",
    "000905p0": "中证500p0",
    "000905p3": "中证500p3",
    "000905p6": "中证500p6",
    "000905p688": "中证500p688",
    "000852": "中证1000",
    "000852p0": "中证1000p0",
    "000852p3": "中证1000p3",
    "000852p6": "中证1000p6",
    "000852p688": "中证1000p688",
}

to_sector_name_of = lambda __sector: dfutil.to_dict_val(__the_sector_2_name, __sector, default=__sector)

is_sector_of_no_trigger = lambda __sector_list: sector_not_trigger in __sector_list

to_sector_target_set_of_uts = lambda __sector_list: dfutil.flat_list([
    dfutil.split_str_to_list(dfutil.kevstr_val(uts_sector, "="), "&", is_result_lower=True)
    for uts_sector in dfutil.sub_list_by_prefix(__sector_list, "uts=")
])


def to_sector_list(is_all, is_other) -> list[str]:
    # note：uall 用于程序处理，无需token中设置
    __all = lambda __sector: __sector if is_all else None
    __other = lambda __sector: __sector if is_other else None
    __list = lambda __sector_list: dfutil.sub_list_notnone([
        (__other(x) if x != sector_all else __all(x))
        for x in __sector_list
    ])

    sector_list = __list(model_sector_list)
    cluster_sector_list = __list(model_cluster_sector_list)

    # return return_check_sector(all_sector_list, cluster_sector_list)

    # todo: impl: 目前只判断普通sector的合法性，标的sector也可以判断，麻烦些
    # note: sector 如果为 uts= 开头，表示特定target组成
    # note: 多个target之间以"&"分割（不采用"｜"，因为无法在windows上保存文件名称）
    def __defined(__sector_list):
        sl = [
            x
            for x in __sector_list
            if False
               and (not dfutil.is_str_prefix_any(x, "uts="))
               and (not dfutil.is_str_prefix_any(x, "utp="))
        ]
        return len(dfutil.sub_list_exclude(sl, list(__the_sector_2_name.keys()))) == 0

    dfutil.not_empty(sector_list) and (not __defined(sector_list)) and dfutil.fatal_exit(
        f"check: {sector_list=} not in {__the_sector_2_name=}"
    )
    (cluster_sector_list != dfutil.sub_list_intersect(cluster_sector_list, sector_list)) and dfutil.fatal_exit(
        f"check: {cluster_sector_list=} not in {sector_list=}"
    )
    return sector_list


# def return_check_sector(sector_list: list[str], cluster_sector_list: list[str]) -> list[str]:
#     # todo: impl: 目前只判断普通sector的合法性，标的sector也可以判断，麻烦些
#     def __is(__sector_list):
#         # note: sector 如果为 uts= 开头，表示特定target组成
#         # note: 多个target之间以"&"分割（不采用"｜"，因为无法在windows上保存文件名称）
#         sl = [
#             x
#             for x in __sector_list
#             if not dfutil.is_str_prefix(x, "uts=")
#         ]
#
#         return len(dfutil.sub_list_exclude(sl, list(__the_sector_2_name.keys()))) == 0
#
#     dfutil.not_empty(sector_list) and (not __is(sector_list)) and dfutil.fatal_exit(
#         f"check: {sector_list=} not in {__the_sector_2_name=}"
#     )
#     (cluster_sector_list != dfutil.sub_list_intersect(cluster_sector_list, sector_list)) and dfutil.fatal_exit(
#         f"check: {cluster_sector_list=} not in {sector_list=}"
#     )
#     return sector_list


# 不支持sector时symbol为None（兼容旧的文件名称）
# to_sectorsymbol = lambda sector: None if not enable_stats_sector else f"sec{sector}"
to_sectorsymbol = lambda sector: f"sec{sector}"
#
sectorsymbol_all = to_sectorsymbol(sector_all)  # "secuall"

# 样例：duraall（所有），202201（特定月），1m（最近一个月），aapl（特定含义）
durationsymbol_all = "duraall"
durationdatecount_all = 999999999

#
daterange_dateall = "dateall"
daterange_recent = "recent"

stagesymbol = "stage"  # note：exec_task 中可以 load stage 文件继续没有完成的计算

#
timeflow_c = "c"
timeflow_c_mean = "c_mean"  # close 均值
timeflow_olhc = "olhc"  # open low high close
timeflow_olhcstep = "olhcstep"  # 插值
timeflow_ohlc = "ohlc"  # open high low close
timeflow_ohlcstep = "ohlcstep"  # 插值

#
ohlc_open = "open"  #
ohlc_high = "high"  #
ohlc_low = "low"  #
ohlc_close = "close"  #

#
moment_openpre = "openpre"  # 开盘 前
moment_open = "open"  # 开盘
moment_intra = "intra"  # 中盘
moment_close = "close"  # 收盘
moment_closepost = "closepost"  # 收盘 后
#
moment_range_high = "high"  # 中盘高点（无法预测，只能模拟回测）
moment_range_low = "low"  # 中盘低点（无法预测，只能模拟回测）
#
moment_trade_list = [moment_open, moment_intra, moment_close]  # 交易时段
moment_quote_list = [moment_openpre, moment_open, moment_intra, moment_close, moment_closepost]  # 报价时段
#
moment_pattern_pricedownrebound = "pattern_pricedownrebound"  # 根据pattern决定：open + intra + close，低点反弹
moment_pattern_triggercount = "pattern_triggercount"  # 根据pattern决定：triggercount增加开盘买入，triggercount减少收盘买入
moment_pattern_lowrisecontinue = "pattern_lowrisecontinue"  # 根据pattern决定：最近几天低点不断上移则开盘立刻买入

#
level_trade_check = "log"  # "open position"
level_trade_enter = "warn"  # "open position"
level_trade_exit = "warn"  # "close position"

# 用于 log grep
#
hint_fail_pre = "QL_FAIL_PRE"  # 前置条件不满足
hint_fail_exe = "QL_FAIL_EXE"  # 前置条件满足但是执行条件不满足，等待下次判断
#
hint_prompt_query = "QL_PROMPT_QUERY"  # 从channel检索订单状态
hint_prompt_buy = "QL_PROMPT_BUY"  # 执行买入
hint_prompt_sell = "QL_PROMPT_SELL"  # 执行卖出
#
hint_trade_valid = "QL_TRADE_VALID"  # "open position"
hint_trade_buy = "QL_TRADE_BUY"  # "open position"
hint_trade_sell = "QL_TRADE_SELL"  # "close position"
hint_trade_no = "QL_TRADE_NO"  #

# 交易算法
trade_sentence_vallist: str = "vallist"  # 根据buy/sell price取值执行
#
trade_sentence_buy_date_trade: str = "buy_date_trade"
trade_sentence_buy_date_trade2n: str = "buy_date_trade2n"
trade_sentence_buy_date_trade3n: str = "buy_date_trade3n"
trade_sentence_buy_date_trade2n3n: str = "buy_date_trade2n3n"
trade_sentence_buy_date_trade2n3n4n: str = "buy_date_trade2n3n4n"
to_trade_sentence_buy_date_by = \
    lambda date: f"buy_date_{date}"
#
trade_function_buy_date_cascade: str = "buy_date_cascade"  # func
to_trade_function_buy_date_cascade = lambda cascade_transid, cascade_buy_price_ratio: \
    f"{trade_function_buy_date_cascade}(" \
    f"cascade_transid={cascade_transid}," \
    f"cascade_buy_price_ratio={cascade_buy_price_ratio}," \
    f")"
#
trade_sentence_buy_price_trade: str = "buy_price_trade"
trade_sentence_buy_price_trade2n: str = "buy_price_trade2n"
trade_sentence_buy_price_trade3n: str = "buy_price_trade3n"
trade_sentence_buy_price_open2n: str = "buy_price_open2n"
trade_sentence_buy_price_close2n: str = "buy_price_close2n"
trade_sentence_buy_price_open3n: str = "buy_price_open3n"
trade_sentence_buy_price_close3n: str = "buy_price_close3n"
to_trade_sentence_buy_price_by = \
    lambda price: f"buy_price_{price}"
#
trade_sentence_buy_count_dynamic_avail: str = "buy_count_dynamic_avail"
trade_sentence_buy_count_dynamic_avail_max1w: str = "buy_count_dynamic_avail_max1w"
trade_sentence_buy_count_dynamic_avail_adj1w_min1h: str = "buy_count_dynamic_avail_adj1w_min1h"
trade_sentence_buy_count_dynamic_avail_max5q: str = "buy_count_dynamic_avail_max5q"
trade_sentence_buy_count_dynamic_avail_adj5q_min1h: str = "buy_count_dynamic_avail_adj5q_min1h"
trade_sentence_buy_count_dynamic_avail_max7q: str = "buy_count_dynamic_avail_max7q"
trade_sentence_buy_count_dynamic_avail_adj7q_min1h: str = "buy_count_dynamic_avail_adj7q_min1h"
to_trade_sentence_buy_count_by = \
    lambda count: f"buy_count_{count}"
#
trade_function_buy_count_cascade: str = "buy_count_cascade"  # func
to_trade_function_buy_count_cascade = lambda cascade_transid, cascade_buy_count_ratio: \
    None if dfutil.all_empty(cascade_transid, cascade_buy_count_ratio) else \
        f"{trade_function_buy_count_cascade}(" \
        f"cascade_transid={cascade_transid}," \
        f"cascade_buy_count_ratio={cascade_buy_count_ratio}," \
        f")"
#
trade_function_buy_moment: str = "buy_moment"  # func
to_trade_function_buy_moment = lambda buy_moment: \
    None if dfutil.empty(buy_moment) else \
        f"{trade_function_buy_moment}(" \
        f"buy_moment={buy_moment}," \
        f")"
#
trade_sentence_sell_price_below_ma5: str = "sell_price_below_ma5"
#
trade_sentence_sell_price_rise_none: str = "sell_price_rise_none"
trade_sentence_sell_price_rise_rule: str = "sell_price_rise_rule"
trade_sentence_sell_price_rise_rebound1d_percent10: str = "sell_price_rise_rebound1d_percent10"
trade_sentence_sell_price_rise_enough: str = "sell_price_rise_enough"
trade_sentence_sell_price_rise_percent1 = "sell_price_rise_percent1"
trade_sentence_sell_price_rise_percent2 = "sell_price_rise_percent2"
trade_sentence_sell_price_rise_percent3: str = "sell_price_rise_percent3"
trade_sentence_sell_price_rise_percent4: str = "sell_price_rise_percent4"
trade_sentence_sell_price_rise_percent5: str = "sell_price_rise_percent5"
trade_sentence_sell_price_rise_percent6: str = "sell_price_rise_percent6"
trade_sentence_sell_price_rise_percent7: str = "sell_price_rise_percent7"
trade_sentence_sell_price_rise_percent8: str = "sell_price_rise_percent8"
trade_sentence_sell_price_rise_percent9: str = "sell_price_rise_percent9"
trade_sentence_sell_price_rise_percent10: str = "sell_price_rise_percent10"
trade_sentence_sell_price_rise_percent11: str = "sell_price_rise_percent11"
trade_sentence_sell_price_rise_percent12: str = "sell_price_rise_percent12"
trade_sentence_sell_price_rise_percent13: str = "sell_price_rise_percent13"
trade_sentence_sell_price_rise_percent14: str = "sell_price_rise_percent14"
trade_sentence_sell_price_rise_percent15: str = "sell_price_rise_percent15"
trade_sentence_sell_price_rise_percent16: str = "sell_price_rise_percent16"
trade_sentence_sell_price_rise_percent17: str = "sell_price_rise_percent17"
trade_sentence_sell_price_rise_percent18: str = "sell_price_rise_percent18"
trade_sentence_sell_price_rise_percent19: str = "sell_price_rise_percent19"
trade_sentence_sell_price_rise_percent20: str = "sell_price_rise_percent20"
to_trade_sentence_sell_price_rise_percent_by = \
    lambda percent: f"sell_price_rise_percent{dfutil.int_safe(abs(percent))}"
#
trade_function_sell_price_rise: str = "sell_price_rise"
to_trade_function_sell_price_rise = lambda rise_ratio: \
    None if dfutil.empty(rise_ratio) else \
        f"{trade_function_sell_price_rise}(" \
        f"rise_ratio={rise_ratio}," \
        f")"
#
trade_sentence_sell_price_down_none: str = "sell_price_down_none"
trade_sentence_sell_price_down_rule: str = "sell_price_down_rule"
trade_sentence_sell_price_down_enough: str = "sell_price_down_enough"
trade_sentence_sell_price_down_percent1: str = "sell_price_down_percent1"
trade_sentence_sell_price_down_percent2: str = "sell_price_down_percent2"
trade_sentence_sell_price_down_percent3: str = "sell_price_down_percent3"
trade_sentence_sell_price_down_percent4: str = "sell_price_down_percent4"
trade_sentence_sell_price_down_percent5: str = "sell_price_down_percent5"
trade_sentence_sell_price_down_percent6: str = "sell_price_down_percent6"
trade_sentence_sell_price_down_percent7: str = "sell_price_down_percent7"
trade_sentence_sell_price_down_percent8: str = "sell_price_down_percent8"
trade_sentence_sell_price_down_percent9: str = "sell_price_down_percent9"
trade_sentence_sell_price_down_percent10: str = "sell_price_down_percent10"
trade_sentence_sell_price_down_percent11: str = "sell_price_down_percent11"
trade_sentence_sell_price_down_percent12: str = "sell_price_down_percent12"
trade_sentence_sell_price_down_percent13: str = "sell_price_down_percent13"
trade_sentence_sell_price_down_percent14: str = "sell_price_down_percent14"
trade_sentence_sell_price_down_percent15: str = "sell_price_down_percent15"
trade_sentence_sell_price_down_percent16: str = "sell_price_down_percent16"
trade_sentence_sell_price_down_percent17: str = "sell_price_down_percent17"
trade_sentence_sell_price_down_percent18: str = "sell_price_down_percent18"
trade_sentence_sell_price_down_percent19: str = "sell_price_down_percent19"
trade_sentence_sell_price_down_percent20: str = "sell_price_down_percent20"
to_trade_sentence_sell_price_down_percent_by = \
    lambda percent: f"sell_price_down_percent{dfutil.int_safe(abs(percent))}"
#
trade_function_sell_price_down: str = "sell_price_down"
to_trade_function_sell_price_down = lambda down_ratio: \
    None if dfutil.empty(down_ratio) else \
        f"{trade_function_sell_price_down}(" \
        f"down_ratio={down_ratio}," \
        f")"
#
trade_sentence_sell_datecount_timeout_none: str = "sell_datecount_timeout_none"
trade_sentence_sell_datecount_timeout_rule: str = "sell_datecount_timeout_rule"
trade_sentence_sell_datecount_timeout_enough: str = "sell_datecount_timeout_enough"
#
# trade_sentence_sell_datecount_timeout_signal1: str = "sell_datecount_timeout_signal1"
trade_sentence_sell_datecount_timeout_signal2: str = "sell_datecount_timeout_signal2"
trade_sentence_sell_datecount_timeout_signal3: str = "sell_datecount_timeout_signal3"
trade_sentence_sell_datecount_timeout_signal4: str = "sell_datecount_timeout_signal4"
trade_sentence_sell_datecount_timeout_signal5: str = "sell_datecount_timeout_signal5"
trade_sentence_sell_datecount_timeout_signal6: str = "sell_datecount_timeout_signal6"
trade_sentence_sell_datecount_timeout_signal7: str = "sell_datecount_timeout_signal7"
trade_sentence_sell_datecount_timeout_signal8: str = "sell_datecount_timeout_signal8"
trade_sentence_sell_datecount_timeout_signal9: str = "sell_datecount_timeout_signal9"
trade_sentence_sell_datecount_timeout_signal10: str = "sell_datecount_timeout_signal10"
trade_sentence_sell_datecount_timeout_signal11: str = "sell_datecount_timeout_signal11"
trade_sentence_sell_datecount_timeout_signal12: str = "sell_datecount_timeout_signal12"
trade_sentence_sell_datecount_timeout_signal13: str = "sell_datecount_timeout_signal13"
trade_sentence_sell_datecount_timeout_signal14: str = "sell_datecount_timeout_signal14"
trade_sentence_sell_datecount_timeout_signal15: str = "sell_datecount_timeout_signal15"
trade_sentence_sell_datecount_timeout_signal16: str = "sell_datecount_timeout_signal16"
trade_sentence_sell_datecount_timeout_signal17: str = "sell_datecount_timeout_signal17"
trade_sentence_sell_datecount_timeout_signal18: str = "sell_datecount_timeout_signal18"
trade_sentence_sell_datecount_timeout_signal19: str = "sell_datecount_timeout_signal19"
trade_sentence_sell_datecount_timeout_signal20: str = "sell_datecount_timeout_signal20"
to_trade_sentence_sell_datecount_timeout_signal_by = \
    lambda signal: f"sell_datecount_timeout_signal{dfutil.int_safe(abs(signal))}"
#
trade_sentence_sell_datecount_timeout_hold2: str = "sell_datecount_timeout_hold2"
trade_sentence_sell_datecount_timeout_hold3: str = "sell_datecount_timeout_hold3"
trade_sentence_sell_datecount_timeout_hold4: str = "sell_datecount_timeout_hold4"
trade_sentence_sell_datecount_timeout_hold5: str = "sell_datecount_timeout_hold5"
trade_sentence_sell_datecount_timeout_hold6: str = "sell_datecount_timeout_hold6"
trade_sentence_sell_datecount_timeout_hold7: str = "sell_datecount_timeout_hold7"
trade_sentence_sell_datecount_timeout_hold8: str = "sell_datecount_timeout_hold8"
trade_sentence_sell_datecount_timeout_hold9: str = "sell_datecount_timeout_hold9"
trade_sentence_sell_datecount_timeout_hold10: str = "sell_datecount_timeout_hold10"
trade_sentence_sell_datecount_timeout_hold11: str = "sell_datecount_timeout_hold11"
trade_sentence_sell_datecount_timeout_hold12: str = "sell_datecount_timeout_hold12"
trade_sentence_sell_datecount_timeout_hold13: str = "sell_datecount_timeout_hold13"
trade_sentence_sell_datecount_timeout_hold14: str = "sell_datecount_timeout_hold14"
trade_sentence_sell_datecount_timeout_hold15: str = "sell_datecount_timeout_hold15"
trade_sentence_sell_datecount_timeout_hold16: str = "sell_datecount_timeout_hold16"
trade_sentence_sell_datecount_timeout_hold17: str = "sell_datecount_timeout_hold17"
trade_sentence_sell_datecount_timeout_hold18: str = "sell_datecount_timeout_hold18"
trade_sentence_sell_datecount_timeout_hold19: str = "sell_datecount_timeout_hold19"
trade_sentence_sell_datecount_timeout_hold20: str = "sell_datecount_timeout_hold20"
to_trade_sentence_sell_datecount_timeout_hold_by = \
    lambda hold: f"sell_datecount_timeout_hold{dfutil.int_safe(abs(hold))}"
#
trade_function_sell_datecount_timeout: str = "sell_datecount_timeout"
to_trade_function_sell_datecount_timeout = lambda hold_datecount, signal_datecount: \
    None if dfutil.all_empty(hold_datecount, signal_datecount) else \
        f"{trade_function_sell_datecount_timeout}(" \
        f"hold_datecount={hold_datecount}," \
        f"signal_datecount={signal_datecount}," \
        f")"
#
to_trade_sentence_list = lambda: dfutil.var_val_list(__name__, "trade_sentence_")
to_trade_sentence_list_of_buy = lambda: \
    [trade_sentence_vallist] + dfutil.var_val_list(__name__, "trade_sentence_buy_")
to_trade_sentence_list_of_sell = lambda: \
    [trade_sentence_vallist] + dfutil.var_val_list(__name__, "trade_sentence_sell_")

#
trigger_prefix_simu = "simu"  # 模拟
#
trigger_prefix_temp = "temp"  # 临时字段
trigger_prefix_temp_forbid = f"{trigger_prefix_temp}_forbid"
trigger_prefix_temp_exclude = f"{trigger_prefix_temp}_exclude"
#
trigger_prefix_trigger = "trigger"  #
trigger_prefix_transaction = "transaction"  #
#
trigger_prefix_go = "gm"  # meta todo: impl: 新版本使用"go"，20220218之前版本使用"gm"
#
trigger_prefix_act_prewant = "predict"  # 预测（期望）# todo: impl: 旧trigger/trade中的字段"predict"更名为"prewant"
trigger_prefix_act_prerule = "prerule"  # 预测（规则）
trigger_prefix_act_tradewant = "tradepred"  # 交易（期望）# todo: impl: 旧trigger/trade中的字段"tradepred"更名为"tradewant"
trigger_prefix_act_traderule = "traderule"  # 交易（规则）
#
to_trigger_act_prefix_list = lambda: [
    trigger_prefix_act_prewant, trigger_prefix_act_prerule, trigger_prefix_act_tradewant, trigger_prefix_act_traderule,
]
#
# note：用于上下文处理，例如 update transaction 时，以及 trade 时，提供不同 row 不同的参数
trigger_prefix_context = "context"
#
trigger_context_transaction_model = f"{trigger_prefix_context}_transaction_model"  # 事务
trigger_context_repeat_count = f"{trigger_prefix_context}_repeat_count"  # 重复次数
trigger_context_hold_datecount = f"{trigger_prefix_context}_hold_datecount"  # hold 是 strip 计算出来的 param 中的 trade_param 的 hold 字段
trigger_context_grade_list = f"{trigger_prefix_context}_grade_list"  # 等级列表
trigger_context_board_name = f"{trigger_prefix_context}_board_name"  # 板块名称

#
trigger_appendix_date = "date"
trigger_appendix_sample = "sample"
trigger_appendix_trade = "trade"
trigger_appendix_quick = "quick"
trigger_appendix_sort = "sort"
trigger_appendix_rpt = "rpt"
trigger_appendix_new = "new"
trigger_appendix_position = "position"
trigger_appendix_param = "param"
trigger_appendix_transaction = "transaction"
trigger_appendix_summary = "summary"  # todo: impl: refactor

#
trade_appendix_trade = None
trade_appendix_channel = "channel"
trade_appendix_position = "position"
trade_appendix_summary = "summary"
#
trade_appendix_transaction = "transaction"
to_trade_appendix_transaction = lambda mode: f"transaction.{mode}"
is_trade_appendix_transaction = lambda appendix: dfutil.is_str_prefix_any(appendix, "transaction")

#
trade_sell_idx_range = range(1, 1 + 3)  # note: 最多分3阶段平仓

#
summary_duration_all = "all"
summary_duration_year = "year"
summary_duration_month = "month"
summary_duration_week = "week"
summary_duration_day = "day"
summary_duration_trade = "trade"
# summary_duration_transaction = "transaction"

#
channel_appendix_history = "history"

# 参数操作
param_op_gt = ">"  # 大于
param_op_eq = "="  # 等于
param_op_lt = "<"  # 小于
#
to_param_op_list = lambda: [param_op_gt, param_op_eq, param_op_lt]

#
param_filetype_space = "space"  # space 文件的的后缀
param_filetype_output = "output"  # output 文件的的后缀

#
param_prefix_trade_param = "trade_param="  # 交易参数
param_prefix_trigger_param = "trigger_param="  # trigger 参数
#
to_param_of_trigger_param = lambda key: f"{param_prefix_trigger_param}{key}"

#
# trigger_param_enable_flag = "enable_flag"
# trigger_param_board_count_min = "board_count_min"

#
# note: 必须以 stock_source_ 开头，因为 env track 需要
stock_source_akshare_sina = "sina"  # 新浪
stock_source_akshare_em = "em"  # 东财
stock_source_akshare_ths = "ths"  # 同花顺
stock_source_laohu = "laohu"
stock_source_futu = "futu"
#
to_akshare_stock_source_spot_list = lambda: [stock_source_akshare_em, stock_source_akshare_sina]
to_akshare_stock_source_day_list = lambda: [stock_source_akshare_em, stock_source_akshare_sina]
to_akshare_stock_source_minute_list = lambda: [stock_source_akshare_em]
to_akshare_stock_source_board_history_list = lambda: [stock_source_akshare_em, stock_source_akshare_ths]
to_akshare_stock_source_board_target_list = lambda: [stock_source_akshare_em, stock_source_akshare_ths]
#
use_akshare_enhance: bool = True

#
history_division_1d = "1d"
history_division_1m = "1m"
history_division_3m = "3m"
history_division_5m = "5m"
history_division_15m = "15m"
history_division_1h = "1h"
to_division_step_unit = lambda division: (int(division[0:-1]), division[-1])
#
to_history_day_col_list = lambda: [
    "date", "open", "high", "low", "close", "volume", "amount",
    "turnover_ratio"
]
to_history_minute_col_list = lambda: [
    "date", "open", "high", "low", "close", "volume", "timestamp", "create_timestamp",
    # "turnover_ratio"  # todo: impl: 没有换手率
]
to_board_history_col_list = lambda: [
    "source", "division",
    "board_type", "board_name", "board_code",
    "date",
    "open", "high", "low", "close",
    "change",  # 涨跌额（元）
    "change_ratio",  # 涨跌幅（百分比对应比率）
    "volume",  # 成交量（手）
    "amount",  # 成交额（元）
    "amplitude_ratio",  # 振幅（百分比对应比率）
    "turnover_ratio",  # 换手率（百分比对应比率)
]
to_board_target_col_list = lambda: [
    "source", "board_type", "board_name", "board_code", "target", "target_name",
    "turnover_ratio",  # 换手率（百分比对应比率)
]
to_board_col_list = lambda: [
    "source", "board_type", "board_name", "board_code", "board_date",
    "turnover_ratio",  # 换手率（百分比对应比率)
]
to_index_history_col_list = lambda: [
    "date", "open", "high", "low", "close", "volume", "amount",
    "turnover_ratio",  # todo: impl: 没有换手率
]
to_stock_info_col_list = lambda: [
    "target",
    "abbr",
    "mktcaptotal",
    "mktcapflow",
    "industry",
    "ttm",  # time to market
    "sharetotal",
    "shareflow",
]

# note: 新版本统一使用 timestamp（市场时间），而不是 create_timestamp（本地时间)
# _timestamp_col = "create_timestamp"
spot_col_date = "date"
spot_col_open = "open"
spot_col_high = "high"
spot_col_low = "low"
spot_col_close = "close"
spot_col_volume = "volume"
spot_col_timestamp = "timestamp"

#
sum_col_market = "market"
#
sum_col_transaction_model = "transaction_model"
sum_col_transaction_name = "transaction_name"
#
sum_col_definition = "definition"  # 统计口径：money_sum=资金累计取值，money_timeline=资金时间变化
#
sum_col_duration = "duration"
sum_col_duration_symbol = "duration_symbol"
#
sum_col_date_begin = "date_begin"
sum_col_date_end = "date_end"
#
# sum_col_money_init_sum = "money_init_sum"  # 初始总和 # todo: del
# sum_col_money_hold_sum = "money_hold_sum"  # 持仓总和 # todo: del
# sum_col_money_fini_sum = "money_fini_sum"  # 平仓总和 # todo: del
sum_col_money_init = "money_init"  # 初始
sum_col_money_hold = "money_hold"  # 持仓
sum_col_money_fini = "money_fini"  # 平仓
sum_col_money_avail = "money_avail"  # 可用
sum_col_money_capital = "money_capital"  # 账户价值 = 持仓 + 可用
sum_col_money_delta = "money_delta"
sum_col_money_assets_ratio = "money_assets_ratio"
sum_col_money_earning_ratio = "money_earning_ratio"
#
sum_col_simu_symbol = "simu_symbol"
sum_col_time_flow = "time_flow"
sum_col_factor_dist = "factor_dist"

#
board_type_list = ["industry", "concept"]

# env.generate.csv
#
# note：transaction id，本程序内全局唯一
env_trans_id = "trans_id"
#
# 从渠道获取的实时资金可用余额
env_trade_money_avail = "trade.money_avail"
#
# note: 鲁棒：防止trade文件被异常更改（例如清空），要求数目不能减少
# env_trade_count_recent = "trade.count.recent"
to_env_trade_count_recent_by = lambda kind, appendix: f"trade.count.recent.{kind}.{appendix}"
#
# gather 更新时，已经处理的目标数据的 date，防止反复处理
# env_update_trigger_date = "update.trigger.date"  # note: 目前未用
# env_update_transaction_date = "update.transaction.date"  # note: 目前未用
# env_update_summary_date = "update.summary.date"
to_env_update_summary_date_by = lambda trade_method: f"update.summary.date.{trade_method}"
#
# fetch时可能无法获取的标的
env_fetch_spot_miss = "fetch.spot_miss"
to_env_fetch_spot_miss_by = lambda source: f"fetch.spot_miss.{source}"
env_fetch_day_miss = "fetch.day_miss"
to_env_fetch_day_miss_by = lambda source: f"fetch.day_miss.{source}"
env_fetch_minute_miss = "fetch.minute_miss"
to_env_fetch_minute_miss_by = lambda source: f"fetch.minute_miss.{source}"
#
# fetch时发现存在不一致的标的
env_fetch_check_inconsistency = "fetch.check_inconsistency"
#
# fetch 断点续传
# note；需要 resume 的env必须以 resume 开头
to_env_resume_day_done_by = lambda source: f"resume.day_done.{source}"
to_env_resume_minute_done_by = lambda source: f"resume.minute_done.{source}"
to_env_resume_board_history_done_by = lambda source: f"resume.board_history_done.{source}"
to_env_resume_board_target_done_by = lambda source: f"resume.board_target_done.{source}"
# note: 下述方法 不能以 to_env_resume 开头，否则报错：参数不正确
to_all_env_resume_list = lambda: [
    dfutil.call_module_func(sys.modules[__name__], resume, source)
    for resume in dfutil.var_name_list(__name__, "to_env_resume_")
    for source in dfutil.var_val_list(__name__, "stock_source_")
]
#

# note: 先不要搞这么复杂，而是简单实现：hedge标的在交易未完成时，实时更新最新的quote价格，不在考虑与risk标的之间保持金额差值固定
# riskhedge_risk_wait = "riskwait"  # 风险标的等待对冲
# riskhedge_risk_done = "riskdone"  # 风险标的完成对冲
riskhedge_risk = "risk"  # 风险标的
riskhedge_risk_abort = "riskabort"  # 风险取消
# riskhedge_hedge_wait = "hedgewait"  # 对冲标的等待交易
# riskhedge_hedge_done = "hedgedone"  # 对冲标的结束交易
riskhedge_hedge = "hedge"  # 对冲标的
riskhedge_hedge_abort = "hedgeabort"  # 对冲取消

#
simutype_history1d = "h1d"  # "simu"
simutype_history1d_all = "h1dall"  # "simuall"  # 包括trigger中buy_count为0的标的
simutype_history15m = "h15m"
simutype_history15m_all = "h15mall"  # 包括trigger中buy_count为0的标的
simutype_history1m = "h1m"
simutype_history1m_all = "h1mall"  # 包括trigger中buy_count为0的标的
simutype_history1m3 = "h1m3"  # 1m -> 3m ( close )
simutype_history1m5 = "h1m5"  # 1m -> 5m ( close )
simutype_history1m5a = "h1m5a"  # 1m -> 5m ( close mean )

#
preset_caochen_board = "caochen_board"
preset_transaction = "transaction"
preset_context = "context"

# key
signal_key = 'signal_name'
inner_code_key = 'inner_code'
date_key = 'date'
volume_key = 'volume'
board_name_key = 'board_name'
stock_count_key = 'stock_count'
board_code_key = 'board_code'
sw_board_name_key = 'sw_board_name'
sw_board_code_key = 'sw_board_code'
mtn_key = 'mtn'
sm_key = 'sm'
target_key = 'target'
industry_key = 'industry'
trade_date_key = 'trade_date'
trade_type_key = 'trade_type'
sell_reason_key = 'sell_reason'
sector_id_key = 'sector_id'
industry_active_ratio_key = 'industry_active_ratio'
industry_threshold_key = 'industry_threshold'
industry_threshold_delta_key = 'industry_threshold_delta'
industry_active_ratio_delta_1d_key = 'industry_active_ratio_delta_1d'
regime_code_key = 'regime_code'
dynamic_stop_ma_key = 'dynamic_stop_ma'
ma_value_key = 'ma_value'
price_key = 'price'
strategy_name_key = 'strategy_name'
# --- standard column keys (required by databaseutil sqlite exporter) ---
open_key = "open"
high_key = "high"
low_key = "low"
close_key = "close"

prev_close_key = "prev_close"
trade_status_key = "trade_status"

turnover_vol_key = "volume"
turnover_value_key = "turnover"

company_code_key = "company_code"
target_name_key = "target_name"

# if you don't have it yet
china_market_key = "zh"

# (optional) compatibility alias if some old code uses amount_key
amount_key = turnover_value_key

# value
sw_industry_standard = 38  # 申万行业标准

# trade type
trade_buy_type = 'buy'  # 买入
trade_sell_type = 'sell'  # 卖出
trade_clear_type = 'clearance'  # 清仓
sell_reason_sector_cooldown = 'SectorCooldown'
sell_reason_dynamic_stop = 'DynamicStop'
sell_reason_sig_specific = 'SigSpecific'

def _env_bool(name, default=False):
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {'1', 'true', 'yes', 'y', 'on'}


enable_ab_disable_sector_cooldown = _env_bool('QL_AB_DISABLE_SECTOR_COOLDOWN', False)
enable_ab_disable_dynamic_stop = _env_bool('QL_AB_DISABLE_DYNAMIC_STOP', False)
enable_ab_disable_sig_specific = _env_bool('QL_AB_DISABLE_SIG_SPECIFIC', False)

this_strategy_ind_key = 'this_strategy_indicator'  # 本策略指标key
reference_ind_key = 'reference_indicators'  # 参考策略指标key（比如沪深300，上证50）

start_total_cash = 1000000.0  # 初始总资金

# 保存文件默认路径
if __debug__:
    file_cache_path = str(project_paths.get_runtime_cache_dir(debug=True))
else:
    file_cache_path = str(project_paths.get_runtime_cache_dir(debug=False))

# 保存文件路径
market_quotation_directory = str(project_paths.get_market_quote_dir(debug=__debug__))  # 保存个股日度行情数据文件 目录
market_SYWGIndexQuote_directory = os.path.join(file_cache_path, "market_SYWGIndexQuote_1d")  # 保存申万行业板块日度行情数据文件 目录
quantitative_result_directory = str(project_paths.get_quantitative_result_dir(debug=__debug__))  # 保存行业板块量化结果文件 目录
stocks_tobe_traded_directory = str(project_paths.get_stocks_tobe_traded_dir(debug=__debug__))  # 保存 每天即将交易的股票的文件 目录
stocks_tobe_traded_per_year_directory = os.path.join(file_cache_path, "stocks_tobe_traded_per_year")  # 保存 每年即将交易的股票的文件 目录

# 行情板块文件名
dc_board_target_file_name = "zh_0_board_target.csv"  # 东方财富行业板块
sw2_board_target_file_name = "zh_1_board_target.csv"  # 申万二级行业板块（包含个股信息）
sw_second_industry_file_name = "zh_sw_second_industry.csv"  # 申万二级行业板块（不包含个股信息）

# 沪深300 代码
hs300_code1 = dfutil.get_hs300_code1()
hs300_code2 = dfutil.get_hs300_code2()

# 收件邮箱列表
receiver_email_list = ['huanghuaxing@bosera.com', 'farben340@bosera.com']
# 是否发送邮箱
is_send_email = True
# 是否使用pymssql查询数据库
is_use_pymssql = True


# 日度行情数据类型
class daily_quote_type(Enum):
    stock_type = 1  # 个股类型（默认也会查询沪深300指数类型数据）
    hs300_type = 2  # 沪深300指数类型（仅查询沪深300指数类型数据）
    sw2_industry_type = 3  # 申万二级行业板块指数类型
