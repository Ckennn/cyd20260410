# coding=utf-8
"""
调试
"""

from typing import Callable, Any

import dfutil


# note: 不能 import ql 开头的文件，保持在 top 引用
# note: 不能 import qloption 会循环引用

# note: 缺省取值都应该是 False

################################

# 断点用于调试
def pause(debug_cond: bool) -> bool:
    return dfutil.pause(debug_cond)


################################
# 全局参数

global_debug: bool = True

################################
# 调试变量

# 代码调试
code_debug_trade_token: bool = global_debug and False  # todo: debug: 20231212 发现 600857 昨日已经buy，但是今日uph为空
code_debug_trade_query: bool = global_debug and False  # True = 如果需要调试 query 代码
code_debug_trade_buy: bool = global_debug and False  # True = 如果需要调试 buy 代码
code_debug_trade_sell: bool = global_debug and False  # True = 如果需要调试 sell 代码
code_debug_trade_value: bool = global_debug and False  # True = 如果需要调试 resolve/risk/qlfocus 代码
code_debug_calc_stats: bool = global_debug and False  # True = 如果需要调试 calc stats 代码
code_debug_finance_date: bool = global_debug and False  # True = 如果需要调试 calc stats 代码

#
# trade时的实时报价
fetch_spot_from_cache: bool = global_debug and False

#
fetch_spot_moment_as_open: bool = global_debug and False
fetch_spot_moment_as_intra: bool = global_debug and False
fetch_spot_moment_as_close: bool = global_debug and False

#
multitask_calc_stats_bin_dist_by_mp_20220212: bool = True
multitask_calc_stats_bin_dist_by_mp_20220125: bool = False
multitask_calc_stats_bin_dist_by_mp_20220124: bool = False
multitask_calc_stats_bin_dist_by_mp_20220123: bool = False

#
numpy_calc_stats_bin_dist_quantile: bool = global_debug and False  # todo: impl: 自己实现的性能很低

################################
# note: 以 "force_" 开头的flag

# note: 统一更改force调试变量，简化代码书写
the_force_switch = dfutil.FlagSwitch()
reset_force_flag = lambda: the_force_switch.reset_flag(__name__)
set_force_flag = lambda val: the_force_switch.set_flag(__name__, "force_", val)

# False用于测试（提高性能）
force_check_file_data_value: bool = global_debug and True

# False用于测试（提高性能）
force_check_stats_bin_str: bool = global_debug and True

# False用于测试（提高性能）
force_goodout_df_save_temp_for_trigger: bool = global_debug and True
force_goodout_df_save_temp_for_train: bool = global_debug and False

# force_log_save_temp: bool = global_debug and True

# False用于测试（提高性能）
force_backup_trigger: bool = global_debug and True
force_backup_trader: bool = global_debug and True

# False 用于日常操作
force_rpt_history: bool = global_debug and False

#
force_run_debug: bool = global_debug and False

#
force_sell_now_if_transaction_empty: bool = global_debug and False
force_fatal_exit_if_transaction_empty: bool = global_debug and True

#
force_trade_simu_using_cache: bool = True  # False

#
force_workflow_run: bool = False

################################

#
# enable_gather_trigger_refresh_transaction_use_transaction_created_flag: bool = global_debug and True
#
# enable_param_transaction_preset_single: bool = global_debug and True
# enable_param_transaction_preset_combo: bool = global_debug and True
# enable_param_transaction_preset_cross: bool = global_debug and True

#
# enable_filelock_trade_auto: bool = True
# enable_filelock_trade_track: bool = True

################################
# note: 以 "log_" 开头的flag

# note: 统一更改force调试变量，简化代码书写
the_log_switch = dfutil.FlagSwitch()
reset_log_flag = lambda: the_log_switch.reset_flag(__name__)
set_log_flag = lambda val: the_log_switch.set_flag(__name__, "log_", val)
set_log_flag_list = lambda val, flag_list: the_log_switch.set_flag_list(__name__, flag_list, val)

#
log_dfutil: bool = global_debug and False

log_debug: bool = global_debug and False
log_warn: bool = global_debug and True

log_env: bool = global_debug and False
log_file: bool = global_debug and True
log_error_file_not_found: bool = global_debug and True
log_warn_file_not_found: bool = global_debug and True
# log_select: bool = global_debug and True

log_delete_temp: bool = global_debug and False
forbid_delete_temp: bool = global_debug and False

log_save_temp_detail: bool = global_debug and False

forbid_module_notify: bool = global_debug and False

log_main: bool = global_debug and True

log_func: bool = global_debug and False

log_cache: bool = global_debug and False
log_cache_reset: bool = global_debug and True

log_qlinit: bool = global_debug and True

log_qlfocus: bool = global_debug and False
log_qlfocus_risk_trade_param: bool = global_debug and True

log_qlunit: bool = global_debug and False
log_qlunit_detail: bool = global_debug and False

log_qlmodel: bool = global_debug and False

log_qlmarket: bool = global_debug and False

log_pattern: bool = global_debug and True

log_bins: bool = global_debug and False
log_bins_ind: bool = global_debug and False

log_adjust_column: bool = global_debug and False

log_multitask_arg: bool = global_debug and False  # note: 参数很多时很慢

log_df_select: bool = global_debug and False  # note: 日志频繁导致报错：[Errno 28] No space left on device

log_goodout_select: bool = global_debug and True
log_goodout_score: bool = global_debug and True
log_goodout_weight: bool = global_debug and True

log_goodmerge_adjust: bool = global_debug and False

log_context_handler: bool = global_debug and True
log_context_detail: bool = global_debug and False  # note: context 存在 df 字段，trade 时 log 比较慢

log_quote: bool = global_debug and True
log_quote_sched: bool = global_debug and True
log_quote_init: bool = global_debug and True
log_quote_curr: bool = global_debug and False
log_quote_detail: bool = global_debug and False
log_quote_moment: bool = global_debug and False

#
# log_trigger_trade: bool = global_debug and True

log_notify: bool = global_debug and True
log_notify_detail: bool = global_debug and False

log_trigger_select: bool = global_debug and True
log_trigger_select_detail: bool = global_debug and False
log_trigger_update: bool = global_debug and True
log_trigger_create: bool = global_debug and True

log_transaction_context: bool = global_debug and True
log_transaction_trigger: bool = global_debug and True
log_transaction_trigger_detail: bool = global_debug and False
log_transaction_transaction: bool = global_debug and True
log_transaction_select: bool = global_debug and True
log_transaction_select_detail: bool = global_debug and False
log_transaction_create: bool = global_debug and True
log_transaction_create_detail: bool = global_debug and False
log_transaction_update: bool = global_debug and True
log_transaction_update_detail: bool = global_debug and False
log_transaction_update_only_calc: bool = global_debug and True
log_transaction_parse: bool = global_debug and True
log_transaction_parse_detail: bool = global_debug and False
log_transaction_save: bool = global_debug and True
log_transaction_save_detail: bool = global_debug and False
log_transaction_limit: bool = global_debug and True
log_transaction_limit_detail: bool = global_debug and False
log_transaction_value: bool = global_debug and False
log_transaction_value_detail: bool = global_debug and False

log_training_create: bool = global_debug and True
log_training_create_detail: bool = global_debug and False

log_trade_sched: bool = global_debug and True
#
log_trade_select: bool = global_debug and True
log_trade_select_detail: bool = global_debug and False
log_trade_select_spottrade: bool = global_debug and True
log_trade_select_spottrade_detail: bool = global_debug and False
log_trade_select_spottrade_struct: bool = global_debug and False
log_trade_select_spottrade_world: bool = global_debug and False
log_trade_select_ema11a22: bool = global_debug and True
log_trade_select_ema11a22_detail: bool = global_debug and False
#
log_trade_update: bool = global_debug and True
log_trade_update_detail: bool = global_debug and False
#
log_trade_create: bool = global_debug and True

log_trade_value_df: bool = global_debug and False
log_trade_value_query: bool = global_debug and True
log_trade_value_buy: bool = global_debug and True
log_trade_value_sell: bool = global_debug and True
log_trade_value_resolve: bool = global_debug and True
log_trade_value_risk: bool = global_debug and True
log_trade_value_qlfocus: bool = global_debug and True

log_trade_judge_valid_false: bool = global_debug and True
log_trade_judge_valid_true: bool = global_debug and True
log_trade_judge_reason_false: bool = global_debug and True
log_trade_judge_reason_true: bool = global_debug and True
#
log_trade_prompt_false: bool = global_debug and True

log_summary: bool = global_debug and True
log_summary_detail: bool = global_debug and False

log_channel_update: bool = global_debug and True
log_channel_api_qmt: bool = global_debug and True

log_order_history: bool = global_debug and True

log_eason: bool = global_debug and True

log_risk: bool = global_debug and True
log_risk_token_limit_reach_detail: bool = global_debug and True
log_risk_not_control_as_error: bool = global_debug and True

log_fetch_spot: bool = global_debug and True
log_fetch_hour: bool = global_debug and True
log_fetch_date: bool = global_debug and True
log_fetch_market: bool = global_debug and False
#
log_track_env: bool = global_debug and False

log_indicator_create: bool = global_debug and False
log_indicator_adjust_ohlcv: bool = global_debug and False
log_indicator_calc_indicator: bool = global_debug and False
log_indicator_handle_exception: bool = global_debug and False

log_calc_struct_binstr_exist: bool = global_debug and False  # note: 日志频繁导致报错：[Errno 28] No space left on device
log_calc_struct_binstr_calc_before: bool = global_debug and False  # note: 日志频繁导致报错：[Errno 28] No space left on device
log_calc_struct_binstr_calc_after: bool = global_debug and False  # note: 日志频繁导致报错：[Errno 28] No space left on device

log_calc_stats_dist: bool = global_debug and False
log_transf_stats_dist: bool = global_debug and False
log_adjust_stats_dist: bool = global_debug and False

log_calc_stats_signal_dist: bool = global_debug and False
log_transf_stats_signal_dist: bool = global_debug and False
log_adjust_stats_signal_dist: bool = global_debug and False

log_calc_stats_bin_dist: bool = global_debug and False
log_transf_stats_bin_dist: bool = global_debug and False
log_adjust_stats_bin_dist: bool = global_debug and False

log_calc_stats_bin_rank: bool = global_debug and False
log_transf_stats_bin_rank: bool = global_debug and False

log_stats_check: bool = global_debug and False

log_world: bool = global_debug and False

log_calc_goodfilter_expect: bool = global_debug and False
log_calc_goodfilter_confid: bool = global_debug and False
log_calc_goodfilter_using_vec: bool = global_debug and False

# log_param_train: bool = global_debug and False
#
log_param_goodout_space: bool = global_debug and True
log_param_eason_space: bool = global_debug and True
log_param_transaction_space: bool = global_debug and True
log_param_transaction_space_detail: bool = global_debug and False
log_param_calc: bool = global_debug and False
#
log_calc_buy_price_middle_high_low: bool = global_debug and False
log_calc_signal_price_enr_epr: bool = global_debug and False
log_calc_goodout_sort_level_ratio: bool = global_debug and False
log_calc_goodmerge_for_trade: bool = global_debug and False

#
log_signal_register: bool = global_debug and False
log_signal_detect_detail: bool = global_debug and False
#
log_signal_valid_date: bool = global_debug and False  # 太频繁日志导致错误：LOG-EXCEPTION-ERROR:  OSERR
log_signal_valid_value: bool = global_debug and False  # 太频繁日志导致错误：LOG-EXCEPTION-ERROR:  OSERR
log_signal_valid_condition: bool = global_debug and False  # 太频繁日志导致错误：LOG-EXCEPTION-ERROR:  OSERR

#
log_traverse_data: bool = global_debug and False
log_traverse_reduce_space: bool = global_debug and True
log_traverse_iterate: bool = global_debug and True

#
log_copy_trigger: bool = global_debug and False

#
log_merge_df_trigger_prediction: bool = global_debug and False
log_select_trigger_by_stone_scalping_kdjjd_rsi_macd: bool = global_debug and False
log_select_trigger_by_stone_scalping_kdjjd_rsi_macd0: bool = global_debug and False

#
log_option_token: bool = global_debug and True
log_option_sector: bool = global_debug and True
log_option_calc: bool = global_debug and True
log_option_load: bool = global_debug and True
log_option_save: bool = global_debug and True
log_option_delete: bool = global_debug and True
log_option_backup: bool = global_debug and True
log_option_env_load: bool = global_debug and False
log_option_env_save: bool = global_debug and False
log_option_env_fetch: bool = global_debug and False
log_option_env_update: bool = global_debug and True
log_option_env_data_detail: bool = global_debug and False

################################

#
debug_simu: bool = global_debug and False
#
simu_trade_config_bm_list: list[str] = [
    "open", "close",
]
simu_trade_config_sm_list: list[str] = [
    "open", "close",
]
simu_trade_config_hd_list: list[str] = [
    "2", "3", "4", "5", "6", "7", "8", "9",
]
#
simu_trigger_config_tq_list: list[str] = [
    "all",
]
simu_trigger_config_ts_list: list[str] = [
    "all", "score", "weight",
]
simu_trigger_config_tp_list: list[str] = [
    "0:100", "0:70", "0:50", "0:30",
    "0:10", "10:20", "20:30", "30:40", "40:50", "50:60", "60:70", "70:80", "80:90", "90:100",
]
simu_trigger_config_tu_list: list[str] = [
    "hand", "full",
]
simu_trigger_config_tm_list: list[str] = [
    "equal", "ratio",
]

################################

#
__track_trigger_debug = [
    # {"market": "hk", "target": "00388", "count": 100, "buy": 330, "rise": 350, "down": 328, },
    # {"market": "hk", "target": "01810", "count": 1000, "buy": 11.5, "rise": 15, "down": 10, },
]

# debug
# def to_track_trigger_debug_list():
#     d_l = []
#     for c in __track_trigger_debug:
#         d = c.copy()
#         d_l.append(d)
#         #
#         m = d["market"]
#         t = d["target"]
#         d.update({
#             "date": qlmarket.to_nature_date_from_now(m, -2),  # 昨日
#             "channel": "laohu",
#             "trigger_date": qlmarket.to_nature_date_from_now(m, -2),  # 昨日
#             "trigger_when": "open2n",
#             "trigger_category": "next05d",
#         })
#         for p in [qldef.trigger_prefix_prewant, qldef.trigger_prefix_tradewant]:
#             d.update({
#                 f"{p}_buy_moment": "open",
#                 f"{p}_buy_datecount_middle": "2",
#                 f"{p}_buy_datecount_begin": "2",
#                 f"{p}_buy_datecount_end": "5",
#                 f"{p}_buy_date_middle": qlmarket.to_nature_date_from_now(m, 2),  # 明日
#                 f"{p}_buy_date_begin": qlmarket.to_nature_date_from_now(m, 2),
#                 f"{p}_buy_date_end": qlmarket.to_nature_date_from_now(m, 5),
#                 f"{p}_buy_price_middle": c["buy"],
#                 f"{p}_buy_price_high": c["buy"] * 0.01,
#                 f"{p}_buy_price_low": c["buy"] * 0.99,
#                 f"{p}_buy_count_middle": c["count"],
#                 f"{p}_buy_count_high": c["count"],
#                 f"{p}_buy_count_low": c["count"],
#                 f"{p}_sell_price_rise_1": c["rise"] * 1,
#                 f"{p}_sell_price_rise_2": c["rise"] * 1.07,
#                 f"{p}_sell_price_down_1": c["down"] * 1,
#                 f"{p}_sell_price_down_2": c["down"] * 0.93,
#                 f"{p}_sell_datecount_timeout_1": 5,
#                 f"{p}_sell_date_now_1": qlmarket.to_nature_date_from_now(m, 5),
#             })
#
#     return d_l


################################


# debug
__signal_debug_list = [
    # target, date
    # ("00746", 20210831),  # 应该符合 cont_flat_sudden_rise。原因：close上涨没有到达阈值0.05
    # ("00746", 20210906),  # 应该符合 cont_flat_sudden_rise。原因：high上涨没有到达阈值0.05
    # ("00189", 20210728),  # 20210714收盘9.63，20210728收盘12.94，应 rise_good_after_days（实际 20210715收盘11.62）
    # ("01548", 20210728),  # 应该符合 cont_down_turn_rise # 原因：high 32.45 比 32.8 稍低一点 :-(
    # ("02399", 20210803),  # 应该符合 cont_flat_sudden_rise # 原因：high4 与 high3 的值 0.62 与 0.6 之间不是 equalabout
    # ("06110", 20210712),  # 应该符合 cont_down_turn_rise # 原因：代码错误，high1 应该可以大于 high2
    # ("06110", 20210728),  # 应该符合 cont_down_turn_rise or down_fast_turn_slow # 原因：降低 cont_down_turn_rise 条件
    # ("00175", 20210728),  # 应该符合 cont_down_turn_rise # 原因：降低 cont_down_turn_rise 条件
    # ("xm", 20210128),  # 交易数据不连续，20170914 后到了 20210128
    # ("cfac", 20210811),  # signal 出现重复，例如 down_fast_turn_slow 和 cont_down_turn_rise
    # ("tsla", 20211110),  # 问题：今日猛涨应该有信号。结果：计算正确，信号都没有满足触发条件
    # ("000863", 20220909),  # test
    # ("000863", 20220812),  # test
    # ("000419", 20220919),  # test
    # ("000419", 20220916),  # test
    # ("688596", 20220927),  # test
    # ("688596", 20220803),  # test
    # ("688596", 20220728),  # test
    # ("000716", 20220824),  # close 低于 100日 high
    ("600026", 20220926),  # caochen_volume_bloom_above_bottom 有 2 个条件不满足
    ("600026", 20220719),  # caochen_price_rise_predict_rise
    ("600026", 20220805),  # caochen_price_down_predict_rise_2
    ("600026", 20220808),  # caochen_price_down_predict_rise_2
    ("600026", 20220809),  # caochen_price_down_predict_rise_2
    ("600026", 20220831),  # caochen_price_down_predict_rise_2
    ("600026", 20220901),  # caochen_price_down_predict_rise_2
    ("600026", 20220902),  # caochen_price_down_predict_rise_2
    ("600026", 20220916),  # caochen_price_down_predict_rise_2
    ("600026", 20220919),  # caochen_price_down_predict_rise_2
    ("600026", 20220929),  # caochen_price_down_predict_rise_2
    ("600026", 20220930),  # caochen_price_down_predict_rise_2
    ("600026", 20220630),  # 不应该有 caochen_price_down_predict_rise_2_2
    ("600026", 20220614),  # note: 符合 caochen_price_down_predict_rise_2_2 但是未来下跌（合理损失概率）
    ("600026", 20220401),  # caochen_price_rise_predict_rise
    ("600873", 20220930),  # 20221016版本有caochen_price_rise_predict_rise，20221014版本无
    ("601975", 20220902),  # 第二天 caochen_price_rise_predict_rise
    ("601975", 20220905),  # 今日   caochen_price_rise_predict_rise
    ("601975", 20220906),  # 前一天 caochen_price_rise_predict_rise
    ("600152", 20220926),  # is_shape_of_upper_shadow_line
    ("600152", 20220909),  # is_shape_of_upper_shadow_line
    ("688111", 20221024),  # 不应该是 上影线
    ("688248", 20221021),  # 上影线
    ("688248", 20220824),  # 也应该算 上影线
    ("002311", 20221018),  # qlsignalcaochen.is_pattern_of_pdpr3_usl
    ("002489", 20221020),  # qlsignalcaochen.is_pattern_of_pdpr3_usl
    ("688248", 20221021),  # qlsignalcaochen.is_pattern_of_pdpr3_usl
    ("000066", 20221103),  # 报错：ValueError: too many inputs
    ("000725", 20221012),  # 报错：ValueError: too many inputs
    ("603815", 20221128),  # 测试 drop: is_pattern_of_pdpr1_volume_rise_price_down_below_ma10 ( caochen 认为不是上涨中继1 )
    ("002017", 20221128),  # 测试 drop: is_pattern_of_pdpr1_price_rise_shape_usl_volume_enlarge ( caochen 认为不是上涨中继1 )
    ("600872", 20221118),  # 测试 上涨中继3 __is_volume_bound_range
    ("600570", 20221118),  # 测试 上涨中继3 __is_volume_bound_range
    ("600570", 20220919),  # 测试 不是 上涨中继3 __is_price_rise_ratio
    ("600570", 20221108),  # 测试 是 上涨中继3 __is_price_rise_ratio
    ("600570", 20221103),  # 测试 是 上涨中继3 __is_price_rise_ratio
    ("301087", 20221209),  # 测试 过滤条件 当天出现上影线（股价创近3个交易日新高后回落5%以上，收盘价低于开盘价）且成交量放大
    ("600216", 20210707),  # 测试 caochen_price_low_above_previous_x_20230203
    ("600216", 20210708),  # 测试 caochen_price_low_above_previous_x_20230203
    ("600216", 20210709),  # 测试 caochen_price_low_above_previous_x_20230203
    ("601600", 20211125),  # 测试 caochen_price_reach_year_rise_x_20230203
    ("601600", 20211126),  # 测试 caochen_price_reach_year_rise_x_20230203
    ("601600", 20211129),  # 测试 caochen_price_reach_year_rise_x_20230203
    ("601600", 20211130),  # 测试 caochen_price_reach_year_rise_x_20230203
    ("601600", 20211201),  # 测试 caochen_price_reach_year_rise_x_20230203
    ("600118", 20230221),  # 测试 caochen_volume_enlarge_price_rise_4_x_20230310
    ("600507", 20230324),  # 测试 caochen_price_low_above_previous_10_x_20230208 = False
    ("002912", 20230324),  # 测试 caochen_price_low_above_previous_10_x_20230208 = True
    ("002399", 20230424),  # 测试 caochen_volume_enlarge_price_rise_4_x_20230310 = True
    ("600742", 20230602),  # 测试 caochen_price_rise_predict_rise_x_20220914, caochen 认为 False
    ("300433", 20230615),  # 测试 caochen_price_down_predict_rise_2_x_20221020, caochen 认为 False
]

__len_signal_debug_list = len(__signal_debug_list)

__signal_debug_trigger_0: Callable[[Any, Any], tuple[Any, Any]] = \
    lambda target, date: (
        target,
        date,
    )

"""
Callable[[Any, Any], tuple[Any, Any]]是一个类型注解，用于指定一个函数或者lambda
表达式的类型。因此，它描述了一个函数，接收任意类型的两个参数，并返回一个包含两个任意类型
元素的元组（tuple）。note by hhx 2024.08.08
"""
__signal_debug_trigger_1: Callable[[Any, Any], tuple[Any, Any]] = \
    lambda df_indicator, row_begin: (
        df_indicator["target"].iloc[0],
        # note: bug: indicator 使用 index
        # df_indicator["date"].iloc[row_begin] if row_begin < len(df_indicator) else -1,
        df_indicator["date"].loc[row_begin] if row_begin < len(df_indicator) else -1,
    )


def is_signal_debug_0(target, row_begin) -> bool:
    return False if not __len_signal_debug_list \
        else dfutil.is_debug(__signal_debug_list, __signal_debug_trigger_0(target, row_begin))


def log_signal_debug_0(target, row_begin, *args):
    dfutil.log_debug(__signal_debug_trigger_0(target, row_begin), *args)


def is_signal_debug_1(df_indicator, row_begin) -> bool:
    return False if dfutil.empty(df_indicator) \
        else False if not __len_signal_debug_list \
        else dfutil.is_debug(__signal_debug_list, __signal_debug_trigger_1(df_indicator, row_begin))


def log_signal_debug_1(df_indicator, row_begin, *args):
    dfutil.log_debug(__signal_debug_trigger_1(df_indicator, row_begin), *args)


def set_signal_debug_list(__list):
    global __signal_debug_list
    global __len_signal_debug_list
    __signal_debug_list = __list
    __len_signal_debug_list = len(__signal_debug_list)
    return


################################

# debug
__bins_debug_list = [
    # target, date
    ################
    # 验证: 新股，但是
    #       bin0.col.trend_40_21=18(/++), bin0.col.trend_20_11=18(/++),bin0.col.trend_10_05=18(/++),bin0.col.trend_04_01=08(\-2)
    #       bin0.col.vary_close_40_21=360(/++/++), bin0.col.vary_close_20_11=360(/++/++),
    #       bin0.col.vary_close_10_05=151(\-3/++), bin0.col.vary_close_04_01=180(~00~00)
    #       bin0.col.macd_relation=02(>0), bin0.col.macd_change=06(\-3)
    #       bin0.col.ema_relation=02(11>22), bin0.col.ema_change=08(/++5)
    #       bin0.col.closeema_01=47(+30+40)
    #   原因：为什么 us_rely_1d.csv 历史文件中，有2017年的数据（这导致了上述计算）？
    #   有家"Real Industry Stock Forecast（NASDAQ:RELY）"在2018年没有了数据，是不是 "Remitly Global (NASDAQ: RELY)" 重用了代码？
    #   调整binstr计算prev后（如果date取值过小则不合法，返回合法的最早取值），trend/vary计算正确，但是macd/ema计算还是不对
    #   分析发现是talib的ema和macd方法计算时还是获取了2017年的数据，按照预计来说，新股没有数据时应该计算为nan（虽然与富途的计算还是不同）
    # ("rely", 20211001),
    ################
    # ("urty", 20210923),  # 验证 b1.t = '04(/+2)' 而 b2.t = 24(~00~00)。原因：bin1使用20日h/l，而bin2使用2个10日h/l，并通过close决定如何使用，导致确实不同
    # ("izea", 20210614),
    # ("tme", 20210624),
    # ("bngo", 20210420),
    # ("rblx", 20210624),
    # ("uco", 20210726),  # trend计算，20日为～00，10日为～00，奇怪
    # ("aapl", 20210702),
    # ("aapl", 20210609),
    # ("aapl", 20210520),
    # ("aapl", 20210513),
    # ("bfly", 20210217),  # 存在prev不足2条的情况
    # ("aeva", 20210405),  # 20日前high提示len不足，原因：可能是s股票上市导致，富途有历史数据，但是akshare新浪数据从20210315开始
    # ("aeva", 20210401),  # ema(22) 为 nan
    # ("afrm", 20210208),  # 20210113上市，不足20日
    # ("btcm", 20210726),  # bin2.col.trend验证： 01(\--\-5)
    # ("zom", 20210909),  # 验证：b1.c.t10=09(~00)但ema向下，b1.c.t00=09(~00)但ema向下。原因：计算没有问题。但是close作为阈值是否合理？直接使用high/low？
    # ("se", 20210910),  # 验证：b2.c.vc=1249(~00/+2~00~00)但图形有方向。原因：计算没有错误，百分比不到10%，属于binstr的十分位取值定义
    # ("07552", 20210705),
    # ("00883", 20210702),
    # ("01119", 20210705),
    # ("08032", 20210709),  # rise_good_after_days 连续出现 从 20210622
    # ("03878", 20210729),  # macd 变化挺高，感觉不应该是bin2 的 (>0~),而应该是 (>0/)
    # ("02208", 20210727),  # macd 变化不高，bin3应该不是 (>0/++)。原因：slope=78.86715496492644，超过了bin范围60
    # ("07552", 20210820),  # 验证bin3.col.trend=4551(/+4/+3/+2)，有些奇怪，10～20之间的slope有这么大？
    # ("00975", 20210506),  # 验证bin3.col.trend=4551(/+4/+3/+2)，有些奇怪，10～20之间的slope有这么大？
    # ("01368", 20210813),  # 验证 bin0.col.macd_change，数据其实很小。原因：调整slope计算，排除diff_as_equal
    # ("01368", 20210819),  # 验证 bin0.col.macd_change，数据其实很小。原因：调整slope计算，排除diff_as_equal
    # ("03600", 20210819),  # 测试: bin0.col.macd_change，数据应该向上
    # ("03600", 20210625),  # 验证 bin0.col.macd_change=10(/+3)，数据其实向下。原因：bug，dfutil.to_diff_ratio 符号计算错误
    # ("01029", 20210908),  # todo：验证 b2.c.e=07(11>22~)但ema向上，b2.c.m=04(=0~)但macd大于0。
]

__len_bins_debug_list = len(__bins_debug_list)

__bins_debug_trigger_0: Callable[[Any, Any], tuple[Any, Any]] = \
    lambda target, date: (
        target,
        date,
    )

__bins_debug_trigger_1: Callable[[Any, Any], tuple[Any, Any]] = \
    lambda df_indicator, date: (
        df_indicator["target"].iloc[0],
        date,
    )


def is_bins_debug_0(target, date) -> bool:
    return False if not __len_bins_debug_list \
        else dfutil.is_debug(__bins_debug_list, __bins_debug_trigger_0(target, date))


def log_bins_debug_0(target, date, *args):
    dfutil.log_debug(__bins_debug_trigger_0(target, date), *args)


def is_bins_debug_1(df_indicator, date) -> bool:
    return False if dfutil.empty(df_indicator) \
        else False if not __len_bins_debug_list \
        else dfutil.is_debug(__bins_debug_list, __bins_debug_trigger_1(df_indicator, date))


def log_bins_debug_1(df_indicator, date, *args):
    dfutil.log_debug(__bins_debug_trigger_1(df_indicator, date), *args)


################################

# debug
__calc_debug_list = [
    # market, target
    # ("us", "aapl"),
    # ("hk", "03800"),
    # ("hk", "06913"),
]

__len_calc_debug_list = len(__calc_debug_list)

__calc_debug_trigger_0: Callable[[Any, Any], tuple[Any, Any]] = \
    lambda market, target: (
        market,
        target,
    )


def is_calc_debug_0(market, target) -> bool:
    return False if not __len_calc_debug_list \
        else dfutil.is_debug(__calc_debug_list, __calc_debug_trigger_0(market, target))


def log_calc_debug_0(market, target, *args):
    dfutil.log_debug(__calc_debug_trigger_0(market, target), *args)


################################

# debug
__query_debug_list = [
    # market, target, date
    # ("hk", "07552", "20210813"),
]

__len_query_debug_list = len(__query_debug_list)

__query_debug_trigger_0: Callable[[Any, Any, Any], tuple[Any, Any, Any]] = \
    lambda market, target, date: (
        market,
        target,
        date,
    )


def is_query_debug_0(market, target, date) -> bool:
    return False if not __len_query_debug_list \
        else dfutil.is_debug(__query_debug_list, __query_debug_trigger_0(market, target, date))


def log_query_debug_0(market, target, date, *args):
    dfutil.log_debug(__query_debug_trigger_0(market, target, date), *args)


################################

# debug
__show_debug_list = [
    # target, date
    # ("task", 20210709),
    # ("pcor", 20210730),  # --token us 时没有列出来，单独 --token us.pcor 可以看到
    # ("lit", 20210730),  # 是不是 显示成 lit ？
]

__len_show_debug_list = len(__show_debug_list)

__show_debug_trigger_0: Callable[[Any, Any], tuple[Any, Any]] = \
    lambda target, date: (
        target,
        date,
    )

# debug
__show_debug_trigger_2: Callable[[Any], tuple[Any, Any]] = \
    lambda stats_row: (
        stats_row["target"],
        stats_row["date"],
    )


def is_show_debug_2(stats_row) -> bool:
    return False if not __len_show_debug_list \
        else dfutil.is_debug(__show_debug_list, __show_debug_trigger_2(stats_row))


def log_show_debug_2(stats_row, *args):
    dfutil.log_debug(__show_debug_trigger_2(stats_row), *args)

############################################
