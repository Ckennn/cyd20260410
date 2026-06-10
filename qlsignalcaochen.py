# coding=utf-8
"""
策略（caochen）
"""

from enum import Enum
import pandas as pd

import dfutil
import qldef
import qlfocus
import qloption
import qlsignal0 as qls0
import qlsignal1 as qls1

"""
    策略与问题
"""

############################################

the_module_name = __name__
the_signal_symbol = qldef.signalsymbol_caochen

# __vc = lambda: qldef.var_category
# __vw = lambda: qldef.var_when
#
# def __mtd(df_ind, row_index):
#     return None if dfutil.empty(df_ind) \
#         else None if row_index not in df_ind.index \
#         else f'[ {df_ind["market"].loc[row_index]}' \
#              f', {df_ind["target"].loc[row_index]}' \
#              f', {df_ind["date"].loc[row_index]}' \
#              f']'
#
#
# def __valid_indicator(df_indicator: pd.DataFrame, row_begin) -> bool:
#     # 数据校验
#     funcname = __valid_indicator.__name__
#     # 时间首尾在2个月自然日内都算合理
#     return qlsignal.__is_date_valid(df_indicator, row_begin, 1, 20, 30 * 2, hint=funcname)
#
#
# def __valid_all(hint, *valid_tuple_of_item_or_list) -> bool:
#     # valid_array = [
#     #     [y for y in x] if dfutil.of_list(x) else x
#     #     for x in valid_array_of_item_or_list
#     # ]
#     valid_array = dfutil.flat_list(valid_tuple_of_item_or_list)
#     is_all = all(valid_array)
#
#     # note: 提醒日志，以便检查signal逻辑条件是否合理
#     with dfutil.CodeBlock():
#         valid_list = list(valid_array)
#         total_count = len(valid_list)
#         false_count = valid_list.count(False)
#         qldebug.log_signal_valid_condition and dfutil.log(
#             f"{hint}, false/total={false_count}/{total_count}({qlfunc.str_percent_2(false_count, total_count)})")
#         (0 < false_count <= 1) and dfutil.warn(
#             f"{hint}, check: {false_count=}"
#         )
#
#     #
#     return is_all
#
#
# ############################################
#
#
# def __is_ma5_above_ma10_above_ma20_above_ma30(df_indicator: pd.DataFrame, row_begin,
#                                               hint=None, is_log=False) -> list:
#     # 5日线＞10日线＞20日线＞30日线
#     funcname = __is_ma5_above_ma10_above_ma20_above_ma30.__name__
#     return [
#         # ma1(5) > ma1(10)
#         qlsignal.__is_col_large_2(df_indicator, "ma(5)", "ma(10)", row_begin, 1,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         # ma1(10) > ma1(20)
#         qlsignal.__is_col_large_2(df_indicator, "ma(10)", "ma(20)", row_begin, 1,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         # ma1(20) > ma1(30)
#         qlsignal.__is_col_large_2(df_indicator, "ma(20)", "ma(30)", row_begin, 1,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_ma5_above_ma20(df_indicator: pd.DataFrame, row_begin,
#                         hint=None, is_log=False) -> list:
#     # 5日线＞20日线
#     funcname = __is_ma5_above_ma20.__name__
#     return [
#         # ma1(5) > ma1(20)
#         qlsignal.__is_col_large_2(df_indicator, "ma(5)", "ma(20)", row_begin, 1,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         # # ma1(10) > ma1(20)
#         # qlsignal.__is_col_large_2(df_indicator, "ma(10)", "ma(20)", row_begin, 1),
#     ]
#
#
# def __is_ma5_rise_duration(df_indicator: pd.DataFrame, row_begin, row_count_begin, row_count_end,
#                            hint=None, is_log=False) -> list:
#     # 5日线上升
#     funcname = __is_ma5_rise_duration.__name__
#     return [
#         # ma20(5) < ma1(5)
#         qlsignal.__is_row_small_1(df_indicator, ["ma(5)"], row_begin,
#                                   row_count_begin, row_count_end,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_ma10_above_ma20(df_indicator: pd.DataFrame, row_begin,
#                          hint=None, is_log=False) -> list:
#     # 10日线＞20日线
#     funcname = __is_ma10_above_ma20.__name__
#     return [
#         # # ma1(5) > ma1(20)
#         # qlsignal.__is_col_large_2(df_indicator, "ma(5)", "ma(20)", row_begin, 1),
#         # ma1(10) > ma1(20)
#         qlsignal.__is_col_large_2(df_indicator, "ma(10)", "ma(20)", row_begin, 1,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_ma10_rise_duration(df_indicator: pd.DataFrame, row_begin, row_count_begin, row_count_end,
#                             hint=None, is_log=False) -> list:
#     # 10日线上升
#     funcname = __is_ma10_rise_duration.__name__
#     return [
#         # ma20(10) < ma1(10)
#         qlsignal.__is_row_small_1(df_indicator, ["ma(10)"], row_begin,
#                                   row_count_begin, row_count_end,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_ma20_rise_duration(df_indicator: pd.DataFrame, row_begin, row_count_begin, row_count_end,
#                             hint=None, is_log=False) -> list:
#     # 20日线上升
#     funcname = __is_ma20_rise_duration.__name__
#     return [
#         # ma20(20) < ma1(20)
#         qlsignal.__is_row_small_1(df_indicator, ["ma(20)"], row_begin,
#                                   row_count_begin, row_count_end,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_ma30_rise_duration(df_indicator: pd.DataFrame, row_begin, row_count_begin, row_count_end,
#                             hint=None, is_log=False) -> list:
#     # 30日线上升
#     funcname = __is_ma30_rise_duration.__name__
#     return [
#         # ma20(30) < ma1(30)
#         qlsignal.__is_row_small_1(df_indicator, ["ma(30)"], row_begin,
#                                   row_count_begin, row_count_end,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_ma250_rise_duration(df_indicator: pd.DataFrame, row_begin, row_count_begin, row_count_end,
#                              hint=None, is_log=False) -> list:
#     # 250日线上升
#     funcname = __is_ma250_rise_duration.__name__
#     return [
#         # ma20(250) < ma1(250)
#         qlsignal.__is_row_small_1(df_indicator, ["ma(250)"], row_begin,
#                                   row_count_begin, row_count_end,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_price_cross_above_ma5(df_indicator: pd.DataFrame, row_begin,
#                                hint=None, is_log=False) -> list:
#     # （综合考虑）股价上穿5日线
#     funcname = __is_price_cross_above_ma5.__name__
#     return [
#         # ma1(5) < close1
#         qlsignal.__is_col_large_2(df_indicator, "close", "ma(5)", row_begin, 1,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         # low2 < ma1(5)
#         qlsignal.__is_col_small_2(df_indicator, "low", "ma(5)", row_begin, 2,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_price_adjacent_ma20(df_indicator: pd.DataFrame, row_begin, row_count,
#                              ratio_limit_l, ratio_limit_h,
#                              hint=None, is_log=False) -> list:
#     # （综合考虑）在10-20日线成交
#     funcname = __is_price_adjacent_ma20.__name__
#     return [
#         # note: 使用 low 更加合理
#         # low1 ~ ma1(20)
#         qlsignal.__is_col_equalabout_2(df_indicator, "low", "ma(20)", row_begin, row_count,
#                                        ratio_limit_l, ratio_limit_h,
#                                        hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_price_down(df_indicator: pd.DataFrame, row_begin,
#                     hint=None, is_log=False) -> list:
#     # （综合考虑）股价回调
#     funcname = __is_price_down.__name__
#     return [
#         # # close3 > close1
#         # qlsignal.__is_row_large_1(df_indicator, "close", row_begin, 3, 1),
#         # # close2 > close1
#         # qlsignal.__is_row_large_1(df_indicator, "close", row_begin, 2, 1),
#         # # # close3 > close2
#         # # qlsignal.__is_row_large_1(df_indicator, "close", row_begin, 3, 2),
#
#         # avg: close3 > close1
#         qlsignal.__is_row_large_1(df_indicator, ["close", "high", "low"], row_begin, 3, 1,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         # avg: close2 > close1
#         qlsignal.__is_row_large_1(df_indicator, ["close", "high", "low"], row_begin, 2, 1,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         # # avg: close3 > close2
#         # qlsignal.__is_row_large_1(df_indicator, ["close", "high", "low"], row_begin, 3, 2),
#     ]
#
#
# def __is_price_rise_duration(df_indicator: pd.DataFrame, row_begin, row_count,
#                              ratio_limit_l, ratio_limit_h,
#                              hint=None, is_log=False) -> list:
#     # （综合考虑）10日内 最低点价格，到 今日收盘价格 之间 上涨幅度
#     funcname = __is_price_rise_duration.__name__
#     return [
#         qlsignal.__is_range_2_diffratio_4(df_indicator, ["close"], ["low"], row_begin,
#                                           1, 1, 1, row_count,
#                                           "median", "min",
#                                           ratio_limit_l, ratio_limit_h,
#                                           hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         qlsignal.__is_range_2_largeequal_4(df_indicator, ["close"], ["low"], row_begin,
#                                            1, 1, 1, row_count,
#                                            "median", "min",
#                                            hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_price_bound_duration(df_indicator: pd.DataFrame, row_begin,
#                               row_count_start, row_count_stop,
#                               diff_ratio_limit,
#                               hint=None, is_log=False) -> list:
#     # （综合考虑）股价横盘震荡
#     funcname = __is_price_bound_duration.__name__
#     return [
#         # note: 测试发现，600026.20220902 价格波动按照 hlc 均值判断好一些
#         # # diff(high[5:100], low[5:100]) <= 20%
#         # qlsignal.__is_range_diffrange_2(df_indicator, "high", "low", row_begin,
#         #                                 row_count_start, row_count_stop,
#         #                                 "max", "min",
#         #                                 diff_ratio_limit,
#         #                                 hint=hint),
#         # diff(high[5:100], low[5:100]) <= 20%
#         qlsignal.__is_range_1_diffratio_1(df_indicator, ["high", "low", "close"], row_begin,
#                                           row_count_start, row_count_stop,
#                                           "max", "min",
#                                           0, diff_ratio_limit,
#                                           hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_close_adjacent_low(df_indicator: pd.DataFrame, row_begin,
#                             ratio_limit_l, ratio_limit_h,
#                             hint=None, is_log=False) -> list:
#     # 收盘价接近最低价
#     funcname = __is_close_adjacent_low.__name__
#     return [
#         # close1 ~ ma1(10)
#         qlsignal.__is_col_equalabout_2(df_indicator, "close", "low", row_begin, 1,
#                                        ratio_limit_l, ratio_limit_h,
#                                        hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_close_adjacent_high(df_indicator: pd.DataFrame, row_begin,
#                              ratio_limit_l, ratio_limit_h,
#                              hint=None, is_log=False) -> list:
#     # 收盘价接近最高价
#     funcname = __is_close_adjacent_high.__name__
#     return [
#         # close1 ~ high1
#         qlsignal.__is_col_equalabout_2(df_indicator, "close", "high", row_begin, 1,
#                                        ratio_limit_l, ratio_limit_h,
#                                        hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_close_adjacent_ma10(df_indicator: pd.DataFrame, row_begin, row_count,
#                              ratio_limit_l, ratio_limit_h,
#                              hint=None, is_log=False) -> list:
#     # 沿10日线买入
#     funcname = __is_close_adjacent_ma10.__name__
#     return [
#         # close1 ~ ma1(10)
#         qlsignal.__is_col_equalabout_2(df_indicator, "close", "ma(10)", row_begin, row_count,
#                                        ratio_limit_l, ratio_limit_h,
#                                        hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_close_adjacent_ma20(df_indicator: pd.DataFrame, row_begin, row_count,
#                              ratio_limit_l, ratio_limit_h,
#                              hint=None, is_log=False) -> list:
#     # 在10-20日线成交
#     funcname = __is_close_adjacent_ma20.__name__
#     return [
#         # close1 ~ ma1(20)
#         qlsignal.__is_col_equalabout_2(df_indicator, "close", "ma(20)", row_begin, row_count,
#                                        ratio_limit_l, ratio_limit_h,
#                                        hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_close_adjacent_ma250(df_indicator: pd.DataFrame, row_begin, row_count,
#                               ratio_limit_l, ratio_limit_h,
#                               hint=None, is_log=False) -> list:
#     # 在250日线成交
#     funcname = __is_close_adjacent_ma250.__name__
#     return [
#         # close1 ~ ma1(250)
#         qlsignal.__is_col_equalabout_2(df_indicator, "close", "ma(250)", row_begin, row_count,
#                                        ratio_limit_l, ratio_limit_h,
#                                        hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_close_above_ma250(df_indicator: pd.DataFrame, row_begin, row_count,
#                            hint=None, is_log=False) -> list:
#     # 股价高于250日线
#     funcname = __is_close_above_ma250.__name__
#     return [
#         # ma[x](250) < close[x]
#         qlsignal.__is_col_large_2(df_indicator, "close", "ma(250)", row_begin, row_count,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         # # low[x+1] < ma[x](250)
#         # qlsignal.__is_col_small_2(df_indicator, "low", "ma(250)", row_begin, row_count + 1, hint=funcname),
#     ]
#
#
# def __is_close_above_bbi(df_indicator: pd.DataFrame, row_begin,
#                          hint=None, is_log=False) -> list:
#     # 股价高于BBI
#     funcname = __is_close_above_bbi.__name__
#     return [
#         # bbi1 < close1
#         qlsignal.__is_col_large_2(df_indicator, "close", "bbi(3,6,12,24)", row_begin, 1,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_close_above_bbi_first(df_indicator: pd.DataFrame, row_begin,
#                                hint=None, is_log=False) -> list:
#     # 股价首次高于BBI
#     funcname = __is_close_above_bbi_first.__name__
#     return [
#         # bbi1 < close1
#         qlsignal.__is_col_large_2(df_indicator, "close", "bbi(3,6,12,24)", row_begin, 1,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         # close[start:stop] < bbi[start:stop]
#         qlsignal.__is_col_large_2(df_indicator, "bbi(3,6,12,24)", "close", row_begin, 2,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         qlsignal.__is_col_large_2(df_indicator, "bbi(3,6,12,24)", "close", row_begin, 3,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         qlsignal.__is_col_large_2(df_indicator, "bbi(3,6,12,24)", "close", row_begin, 4,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         qlsignal.__is_col_large_2(df_indicator, "bbi(3,6,12,24)", "close", row_begin, 5,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         # diff(close[2:5], bbi[2:5]) <= 0
#         # qlsignal.__is_range_diffrange_2(df_indicator, "close", "bbi(3,6,12,24)", row_begin,
#         #                                 row_count_start, row_count_stop,
#         #                                 "max", "min",
#         #                                 0,
#         #                                 hint=hint),
#     ]
#
#
# def __is_close_above_high_duration(df_indicator: pd.DataFrame, row_begin,
#                                    row_count_2_start, row_count_2_stop,
#                                    hint=None, is_log=False) -> list:
#     # 股价向上突破横盘震荡区间
#     funcname = __is_close_above_high_duration.__name__
#     return [
#         # high[5:100] < close1
#         qlsignal.__is_range_2_large_2(df_indicator, "close", "high",
#                                       row_begin, 1,
#                                       row_count_2_start, row_count_2_stop, "max",
#                                       hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_close_below_ma10(df_indicator: pd.DataFrame, row_begin,
#                           hint=None, is_log=False) -> list:
#     # 股价低于10日线
#     funcname = __is_close_below_ma10.__name__
#     return [
#         # ma1(10) < close1
#         qlsignal.__is_col_small_2(df_indicator, "close", "ma(10)", row_begin, 1,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_close_below_ma250(df_indicator: pd.DataFrame, row_begin, row_count,
#                            hint=None, is_log=False) -> list:
#     # 股价低于250日线
#     funcname = __is_close_below_ma250.__name__
#     return [
#         # ma[x](250) < close[x]
#         qlsignal.__is_col_small_2(df_indicator, "close", "ma(250)", row_begin, row_count,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         # # low[x+1] < ma[x](250)
#         # qlsignal.__is_col_small_2(df_indicator, "low", "ma(250)", row_begin, row_count + 1, hint=funcname),
#     ]
#
#
# def __is_close_below_open(df_indicator: pd.DataFrame, row_begin,
#                           hint=None, is_log=False) -> list:
#     # 收盘价低于开盘价
#     funcname = __is_close_below_open.__name__
#     return [
#         # open1 < close1
#         qlsignal.__is_col_small_2(df_indicator, "close", "open", row_begin, 1,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_close_below_high_ratio(df_indicator: pd.DataFrame, row_begin,
#                                 ratio_limit,
#                                 hint=None, is_log=False) -> list:
#     # 收盘价低于最高价比率
#     funcname = __is_close_below_high_ratio.__name__
#     return [
#         # close1 << high1
#         qlsignal.__is_row_largemore_2(df_indicator, "high", "close", row_begin, 1, 1,
#                                       ratio_limit,
#                                       hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_close_down_ratio(df_indicator: pd.DataFrame, row_begin,
#                           ratio_limit,
#                           hint=None, is_log=False) -> list:
#     # 收盘价下跌
#     funcname = __is_close_down_ratio.__name__
#     return [
#         # avg: close2 > close1
#         qlsignal.__is_row_largemore_1(df_indicator, ["close"], row_begin, 2, 1,
#                                       ratio_limit,
#                                       hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_close_rise_ratio(df_indicator: pd.DataFrame, row_begin,
#                           ratio_limit,
#                           hint=None, is_log=False) -> list:
#     # 收盘价上涨
#     funcname = __is_close_rise_ratio.__name__
#     return [
#         # avg: close2 < close1
#         qlsignal.__is_row_smallmore_1(df_indicator, ["close"], row_begin, 2, 1,
#                                       ratio_limit,
#                                       hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_close_rise_least(df_indicator: pd.DataFrame, row_begin,
#                           duration_count: int, rise_count_l: int,
#                           hint=None, is_log=False) -> list:
#     # 股价x天内至少上涨y天
#     funcname = __is_close_rise_least.__name__
#
#     rise_list = [
#         # close2 < close1
#         qlsignal.__is_row_small_1(df_indicator, "close", row_begin, x, 1, hint=hint)
#         for x in range(1, duration_count + 1)
#     ]
#     is_check = (rise_list.count(True) >= rise_count_l)
#
#     (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
#     qldebug.log_signal_debug_1(df_indicator, row_begin,
#                                f"{qlsignal.__hint(hint, funcname)}, "
#                                f"{duration_count=}, {rise_count_l}, "
#                                f"{rise_list=}, "
#                                f"{is_check=}, "
#                                )
#
#     return [is_check]
#
#
# def __is_high_top_duration(df_indicator: pd.DataFrame, row_begin,
#                            row_count_2_start, row_count_2_stop,
#                            hint=None, is_log=False) -> list:
#     # 高点在周期内最高
#     funcname = __is_high_top_duration.__name__
#     return [
#         # high[5:100] < high1
#         qlsignal.__is_range_2_largeequal_2(df_indicator, "high", "high",
#                                            row_begin, 1,
#                                            row_count_2_start, row_count_2_stop, "max",
#                                            hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_low_above_ma250(df_indicator: pd.DataFrame, row_begin, row_count,
#                          hint=None, is_log=False) -> list:
#     # 低点高于250日线
#     funcname = __is_low_above_ma250.__name__
#     return [
#         # low1 < ma1(250)
#         qlsignal.__is_col_large_2(df_indicator, "low", "ma(250)", row_begin, row_count,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_low_below_ma250(df_indicator: pd.DataFrame, row_begin, row_count,
#                          hint=None, is_log=False) -> list:
#     # 低点低于250日线
#     funcname = __is_low_below_ma250.__name__
#     return [
#         # low1 < ma1(250)
#         qlsignal.__is_col_small_2(df_indicator, "low", "ma(250)", row_begin, row_count,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_low_adjacent_ma250(df_indicator: pd.DataFrame, row_begin, row_count,
#                             ratio_limit_l, ratio_limit_h,
#                             hint=None, is_log=False) -> list:
#     # 低点接近250日线
#     funcname = __is_low_adjacent_ma250.__name__
#     return [
#         # close1 ~ ma1(250)
#         qlsignal.__is_col_equalabout_2(df_indicator, "low", "ma(250)", row_begin, row_count,
#                                        ratio_limit_l, ratio_limit_h,
#                                        hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_low_duration_above_duration(df_indicator: pd.DataFrame, row_begin,
#                                      row_count_1_start, row_count_1_stop,
#                                      row_count_2_start, row_count_2_stop,
#                                      ratio_limit,
#                                      hint=None, is_log=False) -> list:
#     # 低点 在一个周期内 比 另一个周期内 要高
#     funcname = __is_low_duration_above_duration.__name__
#     return [
#         # low[5:100] < low[1:5]
#         qlsignal.__is_range_2_diffratio_4(df_indicator, "low", "low", row_begin,
#                                           row_count_1_start, row_count_1_stop,
#                                           row_count_2_start, row_count_2_stop,
#                                           "min", "min",
#                                           ratio_limit, 99,
#                                           hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         qlsignal.__is_range_2_largeequal_4(df_indicator, "low", "low", row_begin,
#                                            row_count_1_start, row_count_1_stop,
#                                            row_count_2_start, row_count_2_stop,
#                                            "min", "min",
#                                            hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_volume_shrink(df_indicator: pd.DataFrame, row_begin,
#                        hint=None, is_log=False) -> list:
#     # 成交量缩小
#     funcname = __is_volume_shrink.__name__
#     return [
#         # todo: impl: 股价回调，从回调的第一天起量能逐渐缩小，量能缩小至较调整第一天量能的70%以上时，股价在高点下跌10%-15%区间建仓
#
#         # note: 测试发现 600026，缩量可以定位为：mavol(3)的昨日高于本日
#         # mavol2(3) > mavol1(3)
#         qlsignal.__is_row_large_1(df_indicator, "mavol(3)", row_begin, 2, 1,
#                                   hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         # # mavol3(3) > mavol1(1)
#         # qlsignal.__is_row_largeequal_1(df_indicator, "mavol(3)", row_begin, 3, 1),
#         # # mavol3(3) > mavol2(3)
#         # qlsignal.__is_row_largeequal_1(df_indicator, "mavol(3)", row_begin, 3, 2),
#     ]
#
#
# def __is_volume_enlarge(df_indicator: pd.DataFrame, row_begin,
#                         ratio_diff_more,
#                         hint=None, is_log=False) -> list:
#     # 成交量放大
#     funcname = __is_volume_enlarge.__name__
#     return [
#         # note: 测试发现，600026 放量直接使用 volume 不能使用 mavol
#         # volume2 < volume1
#         qlsignal.__is_row_smallmore_1(df_indicator, "volume", row_begin, 2, 1, ratio_diff_more,
#                                       hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_volume_enlarge_duration(df_indicator: pd.DataFrame, row_begin,
#                                  duration_count, ratio_limit_l, ratio_limit_h,
#                                  hint=None, is_log=False) -> list:
#     # 成交量放大，在一定周期内
#     funcname = __is_volume_enlarge_duration.__name__
#     return [
#         qlsignal.__is_range_2_diffratio_4(df_indicator, ["volume"], ["volume"], row_begin,
#                                           1, 1, 1, duration_count,
#                                           "mean", "mean",
#                                           ratio_limit_l, ratio_limit_h,
#                                           hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         qlsignal.__is_range_2_largeequal_4(df_indicator, ["volume"], ["volume"], row_begin,
#                                            1, 1, 1, duration_count,
#                                            "mean", "mean",
#                                            hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_volume_bound_duration(df_indicator: pd.DataFrame, row_begin,
#                                row_count_start, row_count_stop, diff_ratio_limit,
#                                hint=None, is_log=False) -> list:
#     # 成交量横盘震荡
#     funcname = __is_volume_bound_duration.__name__
#     return [
#         # diff(mavol(3)[1:5], mavol(3)[1:5]) <= 20%
#         qlsignal.__is_range_1_diffratio_2(df_indicator, "mavol(3)", "mavol(3)", row_begin,
#                                           row_count_start, row_count_stop,
#                                           "max", "min",
#                                           0, diff_ratio_limit,
#                                           hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_amount_enlarge(df_indicator: pd.DataFrame, row_begin,
#                         ratio_diff_more,
#                         hint=None, is_log=False) -> list:
#     # 成交额放大
#     funcname = __is_amount_enlarge.__name__
#     return [
#         # amount2 * 2 <= amount1
#         qlsignal.__is_row_largemore_1(df_indicator, "amount", row_begin, 1, 2, ratio_diff_more,
#                                       hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_macd_rise_adjacent_zero(df_indicator: pd.DataFrame, row_begin,
#                                  zero_limit_l, zero_limit_h,
#                                  hint=None, is_log=False) -> list:
#     # MACD的DIF和DEA零轴 ±xxx 内形成金叉（DIF数值≥DEA数值） note：实现上转化为 "macd上涨接近零轴"
#     funcname = __is_macd_rise_adjacent_zero.__name__
#     return [
#
#         # 零轴上下：-0.2 <= macddif1(12,26,9) <= 0.2
#         qlsignal.__is_row_valuelimit_1(df_indicator, "macddif(12,26,9)", row_begin, 1, 1,
#                                        zero_limit_l, zero_limit_h,
#                                        hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         # 零轴上下：-0.2 <= macddea1(12,26,9) <= 0.2
#         qlsignal.__is_row_valuelimit_1(df_indicator, "macddea(12,26,9)", row_begin, 1, 1,
#                                        zero_limit_l, zero_limit_h,
#                                        hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         # 已经上升：macdbar(12,26,9) > 0 ( note: < 99 )
#         qlsignal.__is_col_valuelimit_1(df_indicator, "macdbar(12,26,9)", row_begin, 1,
#                                        0, 99,
#                                        hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# # todo: test:
# def __is_macd_gold_cross(df_indicator: pd.DataFrame, row_begin,
#                          date_limit_l, date_limit_h,
#                          hint=None, is_log=False) -> list:
#     # MACD的DIF和DEA形成金叉
#     funcname = __is_macd_gold_cross.__name__
#     return [
#
#         # 现在已经上升：macdbar1(12,26,9) > 0 ( note: < 99 )
#         qlsignal.__is_col_valuelimit_1(df_indicator, "macdbar(12,26,9)", row_begin, 1,
#                                        0, 99,
#                                        hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         # 以前存在下降：min( macdbar[2:5](12,26,9) ) < 0
#         qlsignal.__is_range_1_valuelimit_1(df_indicator, "macdbar(12,26,9)", row_begin,
#                                            date_limit_l, date_limit_h, "min", "min",
#                                            -99, 0,
#                                            hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#
# def __is_shape_of_upper_shadow_line(df_indicator: pd.DataFrame, row_begin,
#                                     hint=None, is_log=False) -> list:
#     # 形态：上影线
#     funcname = __is_shape_of_upper_shadow_line.__name__
#
#     class Param(Enum):
#         ratio_hm_ml_l = 1.0  # (high-middle)/(middle-low) 比率下限
#         ratio_hm_ml_h = 99.0  # (high-middle)/(middle-low) 比率上限
#         ratio_hc_cl_l = 1.5  # (high-close)/(close-low) 比率下限
#         ratio_hc_cl_h = 99.0  # (high-close)/(close-low) 比率上限
#         ratio_ho_ol_l = 1.5  # (high-open)/(open-low) 比率下限
#         ratio_ho_ol_h = 99.0  # (high-open)/(open-low) 比率上限
#
#     return [
#         # middle 判断
#         # diff( high1, avg(open1,close1)) >> diff( avg(open1, close1), low1 )
#         qlsignal.__is_col_splitdiffratio_2(df_indicator, ["open", "close"], "high", "low", row_begin, 1,
#                                            "mean", "mean", "mean",
#                                            __ev(Param.ratio_hm_ml_l), __ev(Param.ratio_hm_ml_h),
#                                            hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         # open 和 close 不能过于接近 high 和 low
#         qlsignal.__is_col_splitdiffratio_2(df_indicator, "close", "high", "low", row_begin, 1,
#                                            "mean", "mean", "mean",
#                                            __ev(Param.ratio_hc_cl_l), __ev(Param.ratio_hc_cl_h),
#                                            hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#         qlsignal.__is_col_splitdiffratio_2(df_indicator, "open", "high", "low", row_begin, 1,
#                                            "mean", "mean", "mean",
#                                            __ev(Param.ratio_ho_ol_l), __ev(Param.ratio_ho_ol_h),
#                                            hint=qlsignal.__hint(hint, funcname), is_log=is_log),
#     ]
#
#


############################################

__enum_key = lambda __enum: __enum.name
__enum_val = lambda __enum: __enum.value
__enum_dict = lambda __enum: {x.name: x.value for x in __enum}

__hint = lambda __context, __current: dfutil.funcname(__context, __current)


############################################
# 这里的 anno_signal 方法，用于注册 下面的 方法 作为一个signal note by hhx 2024.07.24
# 可以看到这里的 the_signal_symbol ，取值在文件最前面进行了设置，就是 qldef.signalsymbol_caochen
@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_volume_bloom_above_bottom_x_20220915
)
def caochen_volume_bloom_above_bottom_x_20220915(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        底部放量突破区间横盘震荡
        建仓信号
            1.成交额较前一天放大≥2倍
            2.股价连续5-100交易日处于低位横盘震荡，股价向上突破横盘震荡区间最高价
            3.股价上穿BBI线上方
            4.MACD的DIF和DEA零轴±0.2内形成金叉（DIF数值≥DEA数值）
        止盈信号
            1.涨幅达到20%
            2.成交额为近期最高，股价没有新高
        止损信号
            1.股价第二日跌破5日线
    """
    memo_str = "caochen.底部上破(最近100日至5日内横盘).20220915"

    class Param(Enum):
        amount_ratio = 1.0  # 成交额涨幅200%
        volatility_day_l = 5  # 横盘震荡交易日长度
        volatility_day_h = 100  # 横盘震荡交易日长度
        volatility_ratio = 0.2  # 横盘震荡高低差值20%
        macd_range_l = -0.25  # 差值0.2 # note：负数
        macd_range_h = 0.25  # 差值0.2

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_amount_enlarge(df_indicator, row_begin,
                               __enum_val(Param.amount_ratio)),

        qls1.is_close_above_high_duration(df_indicator, row_begin,
                                          __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h)),

        qls1.is_price_bound_duration(df_indicator, row_begin,
                                     __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h),
                                     __enum_val(Param.volatility_ratio)),

        qls1.is_close_above_bbi(df_indicator, row_begin),

        qls1.is_macd_rise_adjacent_zero(df_indicator, row_begin,
                                        __enum_val(Param.macd_range_l), __enum_val(Param.macd_range_h)),

    )

    plot_dictlist = []
    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_volume_bloom_above_bottom_x_20221011
)
def caochen_volume_bloom_above_bottom_x_20221011(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        底部放量突破区间横盘震荡
        建仓信号
            1.成交额较前一天放大≥2倍
            2.股价连续5-60交易日处于低位横盘震荡，股价向上突破横盘震荡区间最高价
            3．股价上穿BBI线上方
            4.MACD的DIF和DEA零轴±0.25内形成金叉（DIF数值≥DEA数值）
        止盈信号
            1.涨幅达到20%
            2.股价跌破5日线
        止损信号
            1.股价第二日跌破5日线
    """
    memo_str = "caochen.底部上破(最近60日至5日内横盘).20221011"

    class Param(Enum):
        amount_ratio = 1.0  # 成交额涨幅200%
        volatility_day_l = 5  # 横盘震荡交易日长度
        volatility_day_h = 60  # 横盘震荡交易日长度
        volatility_ratio = 0.2  # 横盘震荡高低差值20%
        macd_range_l = -0.25  # 差值0.25 # note：负数
        macd_range_h = 0.25  # 差值0.25

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_amount_enlarge(df_indicator, row_begin,
                               __enum_val(Param.amount_ratio)),

        qls1.is_close_above_high_duration(df_indicator, row_begin,
                                          __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h)),

        qls1.is_price_bound_duration(df_indicator, row_begin,
                                     __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h),
                                     __enum_val(Param.volatility_ratio)),

        qls1.is_close_above_bbi(df_indicator, row_begin),

        qls1.is_macd_rise_adjacent_zero(df_indicator, row_begin,
                                        __enum_val(Param.macd_range_l), __enum_val(Param.macd_range_h)),

    )

    plot_dictlist = []
    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_volume_bloom_above_bottom_x_20230110
)
def caochen_volume_bloom_above_bottom_x_20230110(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        底部放量突破区间横盘震荡
        建仓信号
            1.成交额较前一天放大≥2倍
            # 2.股价连续5-60交易日处于低位横盘震荡，股价向上突破横盘震荡区间最高价 # note: caochen: 20230110 去除
            3.股价上穿BBI线上方
            4.MACD的DIF和DEA零轴±0.25内形成金叉（DIF数值≥DEA数值）
        止盈信号
            1.涨幅达7%，热点板块涨幅达15%-20%
            2.股价跌破5日线
        止损信号
            1.股价第二日跌破5日线
        备注
            行业板块有集体上涨的趋势为主，个别公司则需要关注放量情况
    """
    memo_str = "caochen.底部上破(无时长).20230110"

    class Param(Enum):
        amount_ratio = 1.0  # 成交额涨幅200%
        # volatility_day_l = 5  # 横盘震荡交易日长度
        # volatility_day_h = 60  # 横盘震荡交易日长度
        # volatility_ratio = 0.2  # 横盘震荡高低差值20%
        macd_range_l = -0.25  # 边界下限 # note：负数
        macd_range_h = 0.25  # 边界上限

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_amount_enlarge(df_indicator, row_begin,
                               __enum_val(Param.amount_ratio)),

        # __is_price_close_above_high_range(df_indicator, row_begin,
        #                                   __ev(Param.volatility_day_l), __ev(Param.volatility_day_h)),
        #
        # __is_price_bound_range(df_indicator, row_begin,
        #                        __ev(Param.volatility_day_l), __ev(Param.volatility_day_h),
        #                        __ev(Param.volatility_ratio)),

        qls1.is_close_above_bbi(df_indicator, row_begin),

        qls1.is_macd_rise_adjacent_zero(df_indicator, row_begin,
                                        __enum_val(Param.macd_range_l), __enum_val(Param.macd_range_h)),

    )

    plot_dictlist = []
    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_volume_bloom_above_bottom_x_20230111
)
def caochen_volume_bloom_above_bottom_x_20230111(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        底部放量突破区间横盘震荡
        建仓信号
            1.成交额较前一天放大≥2倍
            2.股价连续5-60交易日处于低位横盘震荡，股价向上突破横盘震荡区间最高价 # note: caochen: 20230111 调整为60日
            3.股价上穿BBI线上方
            4.MACD的DIF和DEA零轴±0.25内形成金叉（DIF数值≥DEA数值）
        止盈信号
            1.涨幅达7%，热点板块涨幅达15%-20%
            2.股价跌破5日线
        止损信号
            1.股价第二日跌破5日线
        备注
            行业板块有集体上涨的趋势为主，个别公司则需要关注放量情况
    """
    memo_str = "caochen.底部上破(最近60日至5日内横盘).20230111"

    class Param(Enum):
        amount_ratio = 2.0  # 成交额涨幅200%（2倍）
        volatility_day_l = 5  # 横盘震荡交易日长度
        volatility_day_h = 60  # 横盘震荡交易日长度
        volatility_ratio = 0.2  # 横盘震荡高低差值20%
        macd_range_l = -0.25  # 边界下限 # note：负数
        macd_range_h = 0.25  # 边界上限

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_amount_enlarge(df_indicator, row_begin,
                               __enum_val(Param.amount_ratio)),

        qls1.is_close_above_high_duration(df_indicator, row_begin,
                                          __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h)),

        qls1.is_price_bound_duration(df_indicator, row_begin,
                                     __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h),
                                     __enum_val(Param.volatility_ratio)),

        qls1.is_close_above_bbi(df_indicator, row_begin),

        qls1.is_macd_rise_adjacent_zero(df_indicator, row_begin,
                                        __enum_val(Param.macd_range_l), __enum_val(Param.macd_range_h)),

    )

    plot_dictlist = []
    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_volume_bloom_above_bottom_x_20230112
)
def caochen_volume_bloom_above_bottom_x_20230112(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        底部放量突破区间横盘震荡
        建仓信号
            1.成交额较前一天放大≥2倍
            2.股价连续10-20交易日处于低位横盘震荡，股价向上突破横盘震荡区间最高价 # note: caochen: 20230112 调整为20日
            3.股价上穿BBI线上方
            4.MACD的DIF和DEA零轴±0.25内形成金叉（DIF数值≥DEA数值）
        止盈信号
            1.涨幅达7%，热点板块涨幅达15%-20%
            2.股价跌破5日线
        止损信号
            1.股价第二日跌破5日线
        备注
            行业板块有集体上涨的趋势为主，个别公司则需要关注放量情况
    """
    memo_str = "caochen.底部上破(最近20日至10日内横盘).20230112"

    class Param(Enum):
        amount_ratio = 1.0  # 成交额涨幅200%
        volatility_day_l = 10  # 横盘震荡交易日长度
        volatility_day_h = 20  # 横盘震荡交易日长度
        volatility_ratio = 0.2  # 横盘震荡高低差值20%
        macd_range_l = -0.25  # 边界下限 # note：负数
        macd_range_h = 0.25  # 边界上限

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_amount_enlarge(df_indicator, row_begin,
                               __enum_val(Param.amount_ratio)),

        qls1.is_close_above_high_duration(df_indicator, row_begin,
                                          __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h)),

        qls1.is_price_bound_duration(df_indicator, row_begin,
                                     __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h),
                                     __enum_val(Param.volatility_ratio)),

        qls1.is_close_above_bbi(df_indicator, row_begin),

        qls1.is_macd_rise_adjacent_zero(df_indicator, row_begin,
                                        __enum_val(Param.macd_range_l), __enum_val(Param.macd_range_h)),

    )

    plot_dictlist = []
    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_rise_predict_rise_x_20220914
)
def caochen_price_rise_predict_rise_x_20220914(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        上升趋势
        建仓信号
            1.股价上穿5日线买入
            2. MACD的DIF和DEA在零轴±0.25形成金叉（DIF数值≥DEA数值）
            3.股价首次站上BBI # note: caochen: 首次
        止盈信号
            1.股价跌破5日线
            2.涨幅达7%，热点板块涨幅达15%-20%
            3.成交额为近期最高，股价没有新高
        止损信号
            1.股价跌破5日线
        备注
            需要关注量的情况，如果成交额较前几日放大2倍以上，则配合上边的条件建仓.
    """
    memo_str = "caochen.上升趋势(上涨)(上穿5日线).20220914"

    class Param(Enum):
        macd_range_l = -0.25  # 边界下限 # note：负数
        macd_range_h = 0.25  # 边界上限
        # volatility_day_l = 2  # 横盘震荡交易日长度
        # volatility_day_h = 5  # 横盘震荡交易日长度

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_price_cross_above_ma5(df_indicator, row_begin),

        qls1.is_close_above_bbi_first(df_indicator, row_begin),

        qls1.is_macd_rise_adjacent_zero(df_indicator, row_begin,
                                        __enum_val(Param.macd_range_l), __enum_val(Param.macd_range_h)),

    )

    plot_dictlist = []
    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_rise_predict_rise_x_20220915
)
def caochen_price_rise_predict_rise_x_20220915(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        上升趋势
        建仓信号
            1.股价上穿5日线买入
            2.MACD的DIF和DEA在零轴下形成金叉（DIF数值≥DEA数值）
            3.股价站上BBI
        止盈信号
            1.股价跌破5日线
            2.涨幅达20%
            3.成交额为近期最高，股价没有新高
        止损信号
            1.股价跌破5日线
        备注：需要关注量的情况，如果成交额较前几日放大2倍以上，则配合上边的条件建仓
    """
    memo_str = "caochen.上升趋势(上涨)(上穿5日线).20220915"

    class Param(Enum):
        macd_range_l = -0.25  # 差值0.2 # note：负数
        macd_range_h = 0.25  # 差值0.2

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_price_cross_above_ma5(df_indicator, row_begin),

        qls1.is_close_above_bbi(df_indicator, row_begin),

        qls1.is_macd_rise_adjacent_zero(df_indicator, row_begin,
                                        __enum_val(Param.macd_range_l), __enum_val(Param.macd_range_h)),

    )

    plot_dictlist = []
    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_down_predict_rise_1_x_20220915
)
def caochen_price_down_predict_rise_1_x_20220915(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        上涨中继（1）
        建仓信号
            1. 股价在回调时成交量缩小，沿10日线买入
            2. MACD的DIF和DEA在零轴下形成金叉（DIF数值≥DEA数值）
        止盈信号
            1.股价跌破5日线
            2.涨幅达20%
            3.成交额为近期最高，股价没有新高
        止损信号
            1.股价跌破5日线
        备注：股价回调，从回调的第一天起量能逐渐缩小，量能缩小至较调整第一天量能的70%以上时，在下跌10%-15%区间建仓
    """
    memo_str = "caochen.上涨中继1(下跌)(缩量)(接近10日线).20220915"

    class Param(Enum):
        ma10_ratio_l = -0.1  # 范围10% # note：负数
        ma10_ratio_h = 0.1  # 范围10%
        macd_range_l = -0.25  # 差值0.2 # note：负数
        macd_range_h = 0.25  # 差值0.2

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_close_adjacent_ma10(df_indicator, row_begin, 1,
                                    __enum_val(Param.ma10_ratio_l), __enum_val(Param.ma10_ratio_h)),

        qls1.is_price_down(df_indicator, row_begin),

        qls1.is_volume_shrink(df_indicator, row_begin),

        qls1.is_macd_rise_adjacent_zero(df_indicator, row_begin,
                                        __enum_val(Param.macd_range_l), __enum_val(Param.macd_range_h)),

    )

    plot_dictlist = []
    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_down_predict_rise_1_x_20221020
)
def caochen_price_down_predict_rise_1_x_20221020(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        上涨中继（1）
        建仓信号
            1. 股价在回调时成交量缩小，沿10日线买入
            2. 5日线/10日线＞20日线＞30日线
        止盈信号
            1.股价跌破5日线
            2.涨幅达7%，热点板块涨幅达15%-20%
            3.成交额为近期最高，股价没有新高
        止损信号
            1.股价跌破5日线
        备注
            股价回调，从回调的第一天起量能逐渐缩小，量能缩小至较调整第一天量能的70%以上时，股价在高点下跌10%-15%区间建仓
    """
    memo_str = "caochen.上涨中继1(下跌)(缩量)(接近10日线).20221020"

    class Param(Enum):
        ma10_ratio_l = -0.1  # 比率下界 # note：负数
        ma10_ratio_h = 0.1  # 比率上界

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_price_down(df_indicator, row_begin),

        # todo: impl: 股价回调，从回调的第一天起量能逐渐缩小，量能缩小至较调整第一天量能的70%以上时，股价在高点下跌10%-15%区间建仓
        qls1.is_volume_shrink(df_indicator, row_begin),

        qls1.is_close_adjacent_ma10(df_indicator, row_begin, 1,
                                    __enum_val(Param.ma10_ratio_l), __enum_val(Param.ma10_ratio_h)),

        qls1.is_ma5_above_ma10_above_ma20_above_ma30(df_indicator, row_begin),

    )

    plot_dictlist = []
    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_down_predict_rise_1_x_20221129
)
def caochen_price_down_predict_rise_1_x_20221129(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        上涨中继（1）
        建仓信号
            1. 股价在回调时成交量缩小，沿10日线买入
            2. 5日线/10日线＞20日线＞30日线
            3. 10日内，最低点价格，到 今日收盘价格之间的斜率，是30-45度 # note: david：斜率定义取决于时间轴的缩放，很难统一。更改为涨幅
        止盈信号
            1.股价跌破5日线
            2.涨幅达7%，热点板块涨幅达15%-20%
            3.成交额为近期最高，股价没有新高
        止损信号
            1.股价跌破5日线
        备注
            股价回调，从回调的第一天起量能逐渐缩小，量能缩小至较调整第一天量能的70%以上时，股价在高点下跌10%-15%区间建仓
    """
    memo_str = "caochen.上涨中继1(下跌)(缩量)(接近10日线).20221129"

    class Param(Enum):
        ma10_ratio_h = 0.1  # 比率上界
        ma10_ratio_l = -0.1  # 比率下界 # note：负数
        # slope_datecount = 10  # 斜率时长天数
        # slope_degree_h = 40  # 斜率角度上限
        # slope_degree_l = 30  # 斜率角度下限
        rise_datecount = 10  # 涨幅时长天数
        rise_ratio_h = 0.4  # 涨幅上限
        rise_ratio_l = 0.15  # 涨幅下限

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_price_down(df_indicator, row_begin),

        # todo: impl: 股价回调，从回调的第一天起量能逐渐缩小，量能缩小至较调整第一天量能的70%以上时，股价在高点下跌10%-15%区间建仓
        qls1.is_volume_shrink(df_indicator, row_begin),

        qls1.is_close_adjacent_ma10(df_indicator, row_begin, 1,
                                    __enum_val(Param.ma10_ratio_l), __enum_val(Param.ma10_ratio_h)),

        qls1.is_ma5_above_ma10_above_ma20_above_ma30(df_indicator, row_begin),

        # note: david：斜率定义取决于时间轴的缩放，很难统一。更改为涨幅
        # __is_price_slope(df_indicator, row_begin,
        #                  __ev(Param.slope_datecount), __ev(Param.slope_degree_l), __ev(Param.slope_degree_h)),
        qls1.is_price_rise_duration(df_indicator, row_begin,
                                    __enum_val(Param.rise_datecount),
                                    __enum_val(Param.rise_ratio_l), __enum_val(Param.rise_ratio_h)),

    )

    plot_dictlist = []
    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_down_predict_rise_2_1_x_20220915
)
def caochen_price_down_predict_rise_2_1_x_20220915(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        上涨中继（2）
        建仓信号
            1. 股价回调时成交量缩小，在10-20日线成交。
            2. MACD的DIF和DEA在零轴下形成金叉（DIF数值≥DEA数值）
            3. note: david: ma5和ma10不能低于ma20（例如：600026.20220630不合理）
        止盈信号
            1.股价跌破5日线
            2.涨幅达20%
            3.成交额为近期最高，股价没有新高
        止损信号
            1.股价跌破5日线
        备注：股价回调，从回调的第一天起量能逐渐缩小，量能缩小至较第一天量能的70%以上时，在下跌15%-25%区间建仓
    """
    memo_str = "caochen.上涨中继2(下跌)(缩量)(接近20日线)(有macd).20220915"

    class Param(Enum):
        ma20_ratio_h = 0.05  # 范围10%
        ma20_ratio_l = -0.05  # 范围10% # note：负数
        macd_range_h = 0.25  # 差值0.2
        macd_range_l = -0.25  # 差值0.2 # note：负数

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_price_adjacent_ma20(df_indicator, row_begin, 1,
                                    __enum_val(Param.ma20_ratio_l), __enum_val(Param.ma20_ratio_h)),

        qls1.is_ma5_above_ma20(df_indicator, row_begin),

        qls1.is_ma10_above_ma20(df_indicator, row_begin),

        qls1.is_price_down(df_indicator, row_begin),

        qls1.is_volume_shrink(df_indicator, row_begin),

        qls1.is_macd_rise_adjacent_zero(df_indicator, row_begin,
                                        __enum_val(Param.macd_range_l), __enum_val(Param.macd_range_h)),

    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_down_predict_rise_2_2_x_20220915
)
def caochen_price_down_predict_rise_2_2_x_20220915(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        上涨中继（2）
        建仓信号
            1. 股价回调时成交量缩小，在10-20日线成交。
            # note: 测试发现 600026.20220930，走势不符合macd金叉
            # 2. MACD的DIF和DEA在零轴下形成金叉（DIF数值≥DEA数值）
            3. note: david: ma5和ma10不能低于ma20（例如：600026.20220630不合理）
        止盈信号
            1.股价跌破5日线
            2.涨幅达20%
            3.成交额为近期最高，股价没有新高
        止损信号
            1.股价跌破5日线
        备注：股价回调，从回调的第一天起量能逐渐缩小，量能缩小至较第一天量能的70%以上时，在下跌15%-25%区间建仓
    """
    memo_str = "caochen.上涨中继2(下跌)(缩量)(接近20日线)(无macd).20220915"

    class Param(Enum):
        ma20_ratio_h = 0.05  # 范围10%
        ma20_ratio_l = -0.05  # 范围10% # note：负数
        macd_range_h = 0.25  # 差值0.2
        macd_range_l = -0.25  # 差值0.2 # note：负数

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_price_adjacent_ma20(df_indicator, row_begin, 1,
                                    __enum_val(Param.ma20_ratio_l), __enum_val(Param.ma20_ratio_h)),

        qls1.is_ma5_above_ma20(df_indicator, row_begin),

        qls1.is_ma10_above_ma20(df_indicator, row_begin),

        qls1.is_price_down(df_indicator, row_begin),

        qls1.is_volume_shrink(df_indicator, row_begin),

    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_down_predict_rise_2_x_20221011
)
def caochen_price_down_predict_rise_2_x_20221011(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        上涨中继（2）
        建仓信号
            1. 股价回调时成交量缩小，在10-20日线成交。
            2. MACD的DIF和DEA在零轴下形成金叉（DIF数值≥DEA数值）
            3. 5日线＞10日线＞20日线＞30日线
            todo: impl: 备注：股价回调，从回调的第一天起量能逐渐缩小，量能缩小至较第一天量能的70%以上时，在下跌15%-25%区间建仓。
        止盈信号
            1.股价跌破5日线
            2.涨幅达20%
            3.成交额为近期最高，股价没有新高
        止损信号
            1.
    """
    memo_str = "caochen.上涨中继2(下跌)(缩量)(接近20日线).20221011"

    class Param(Enum):
        ma20_ratio_h = 0.05  # 范围10%
        ma20_ratio_l = -0.05  # 范围10% # note：负数
        macd_range_h = 0.25  # 差值0.2
        macd_range_l = -0.25  # 差值0.2 # note：负数

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_price_adjacent_ma20(df_indicator, row_begin, 1,
                                    __enum_val(Param.ma20_ratio_l), __enum_val(Param.ma20_ratio_h)),

        qls1.is_ma5_above_ma10_above_ma20_above_ma30(df_indicator, row_begin),

        qls1.is_price_down(df_indicator, row_begin),

        # todo: impl: 备注：股价回调，从回调的第一天起量能逐渐缩小，量能缩小至较第一天量能的70%以上时，在下跌15%-25%区间建仓。
        qls1.is_volume_shrink(df_indicator, row_begin),

        qls1.is_macd_rise_adjacent_zero(df_indicator, row_begin,
                                        __enum_val(Param.macd_range_l), __enum_val(Param.macd_range_h)),

    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_down_predict_rise_2_x_20221020
)
def caochen_price_down_predict_rise_2_x_20221020(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        上涨中继（2）
        建仓信号
            1. 股价回调时成交量缩小，在10-20日线成交。
            2. MACD的DIF和DEA在零轴下形成金叉（DIF数值≥DEA数值）
            3. 5日线＞10日线＞20日线＞30日线
        止盈信号
            1.股价跌破5日线
            2.涨幅达7%，热点板块涨幅达15%-20%
            3.成交额为近期最高，股价没有新高
        止损信号
            1.
        备注
            股价回调，从回调的第一天起量能逐渐缩小，量能缩小至较第一天量能的70%以上时，在下跌15%-25%区间建仓
    """
    memo_str = "caochen.上涨中继2(下跌)(缩量)(接近20日线).20221020"

    class Param(Enum):
        ma20_ratio_h = 0.05  # 比率上界
        ma20_ratio_l = -0.05  # 比率下界 # note：负数
        macd_range_h = 0.25  # 边界上界
        macd_range_l = -0.25  # 边界下界 # note：负数

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_price_down(df_indicator, row_begin),

        # todo: impl: 备注：股价回调，从回调的第一天起量能逐渐缩小，量能缩小至较第一天量能的70%以上时，在下跌15%-25%区间建仓。
        qls1.is_volume_shrink(df_indicator, row_begin),

        qls1.is_price_adjacent_ma20(df_indicator, row_begin, 1,
                                    __enum_val(Param.ma20_ratio_l), __enum_val(Param.ma20_ratio_h)),

        qls1.is_macd_rise_adjacent_zero(df_indicator, row_begin,
                                        __enum_val(Param.macd_range_l), __enum_val(Param.macd_range_h)),

        qls1.is_ma5_above_ma10_above_ma20_above_ma30(df_indicator, row_begin),

    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_down_predict_rise_3_x_20221011
)
def caochen_price_down_predict_rise_3_x_20221011(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        上涨中继（3） note: 针对 600026 20220917 之后的走势
        建仓信号
            1.成交量较前一天放大
            2.5个交易日内股价横盘震荡，成交量没有出现大幅下降
            3.股价上穿5日线
        止盈信号
            1.股价跌破5日线
            2.涨幅达20%
            3.成交额为近期最高，股价没有新高
        止损信号
            1.
    """
    memo_str = "caochen.上涨中继3(放量)(上穿5日线).20221011"

    class Param(Enum):
        volume_ratio = 0.10  # 放大10%
        volatility_day_l = 2  # 横盘震荡交易日长度
        volatility_day_h = 6  # 横盘震荡交易日长度
        volatility_price_ratio = 0.2  # 横盘震荡高低差值20%
        volatility_volume_ratio = 0.3  # 横盘震荡高低差值30%
        ma20_ratio_h = 0.05  # 范围10%
        ma20_ratio_l = -0.05  # 范围10% # note：负数
        # macd_range_h = 0.25  # 差值0.2
        # macd_range_l = -0.25  # 差值0.2 # note：负数

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_volume_enlarge(df_indicator, row_begin,
                               __enum_val(Param.volume_ratio)),

        qls1.is_price_bound_duration(df_indicator, row_begin,
                                     __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h),
                                     __enum_val(Param.volatility_price_ratio)),

        qls1.is_volume_bound_duration(df_indicator, row_begin,
                                      __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h),
                                      __enum_val(Param.volatility_volume_ratio)),

        qls1.is_price_cross_above_ma5(df_indicator, row_begin),

    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_down_predict_rise_3_x_20221020
)
def caochen_price_down_predict_rise_3_x_20221020(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        上涨中继（3）
        建仓信号
            成交量较前一天放大
            5个交易日内股价横盘震荡，成交量没有出现大幅下降
            股价上穿5日线
            5日线/10日线＞20日线＞30日线
        止盈信号
            1.股价跌破5日线
            2.涨幅达7%，热点板块涨幅达15%-20%
            3.成交额为近期最高，股价没有新高
        止损信号
            1.
    """
    memo_str = "caochen.上涨中继3(放量)(上穿5日线).20221020"

    class Param(Enum):
        volume_ratio = 0.10  # 量能比率
        volatility_day_l = 2  # 横盘震荡交易日长度
        volatility_day_h = 6  # 横盘震荡交易日长度
        volatility_price_ratio = 0.2  # 横盘震荡高低差值20%
        volatility_volume_ratio = 0.3  # 横盘震荡高低差值30%
        ma20_ratio_h = 0.05  # 范围10%
        ma20_ratio_l = -0.05  # 范围10% # note：负数

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_volume_enlarge(df_indicator, row_begin,
                               __enum_val(Param.volume_ratio)),

        qls1.is_price_bound_duration(df_indicator, row_begin,
                                     __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h),
                                     __enum_val(Param.volatility_price_ratio)),

        qls1.is_volume_bound_duration(df_indicator, row_begin,
                                      __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h),
                                      __enum_val(Param.volatility_volume_ratio)),

        qls1.is_price_cross_above_ma5(df_indicator, row_begin),

        qls1.is_ma5_above_ma10_above_ma20_above_ma30(df_indicator, row_begin),

    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_rise_keep_close_1_x_20221121
)
def caochen_price_rise_keep_close_1_x_20221121(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        单阳不破（1）
        建仓信号
            1.涨幅达到8%以上，收盘价为当日最高价
            2.随后三个交易日，当天的最低价未跌破第一天收盘价，在第四天建仓
        止盈信号
            1.股价跌破10日线
            2.股价较前一天新高，成交量较前一天缩小，收盘价卖出
        止损信号
            按持仓时间动态调整
            跌破第一天收盘价卖出
    """
    memo_str = "caochen.单阳不破1(猛涨)(其后3日未跌破).20221121"

    class Param(Enum):
        # start_datecount = 4  # 上涨日距离今日的天数(基数为1表示今日）
        rise_ratio_l = 0.08  # 上涨日涨幅下限
        high_ratio_l = 0.00  # 上涨日close接近high的比率下限
        high_ratio_h = 0.02  # 上涨日close接近high的比率上限
        keep_ratio_l = 0.00  # 保持low不跌破close的比率下限

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        # close5 < close4
        qls0.is_row_smallmore_1(df_indicator, ["close"], row_begin, 5, 4,
                                __enum_val(Param.rise_ratio_l)),
        # close4 ~ high4
        qls0.is_col_equalabout_2(df_indicator, "close", "high", row_begin, 4,
                                 __enum_val(Param.high_ratio_l), __enum_val(Param.high_ratio_h)),
        # close4 <= low3
        qls0.is_row_smallmore_2(df_indicator, ["close"], ["low"], row_begin, 4, 3,
                                __enum_val(Param.keep_ratio_l)),
        # close4 <= low2
        qls0.is_row_smallmore_2(df_indicator, ["close"], ["low"], row_begin, 4, 2,
                                __enum_val(Param.keep_ratio_l)),
        # close4 <= low1
        qls0.is_row_smallmore_2(df_indicator, ["close"], ["low"], row_begin, 4, 1,
                                __enum_val(Param.keep_ratio_l)),

    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_reach_year_rise_x_20230203
)
def caochen_price_reach_year_rise_x_20230203(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        年线企稳上涨
        样例
            601600中国铝业（2021.11.29）# note: david: 测试发现 20211130 符合
        建仓信号
            1.标的股价在250日线附近
            2.股价第二天和第三天的收盘价大于250日线价格 # note: david: 即 连续2天站上年线
        止盈信号
            1.股价跌破10日线
            2.股价较前一天新高，成交量较前一天缩小，收盘价卖出
        止损信号
            按持仓时间动态调整
    """
    memo_str = "caochen.年线企稳(最近2日高于年线).20230203"

    class Param(Enum):
        equal_ratio_l = -0.03  # 信号日close和年线比率下限
        equal_ratio_h = 0.03  # 信号日close和年线比率上限

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_close_adjacent_ma250(df_indicator, row_begin, 3,
                                     __enum_val(Param.equal_ratio_l), __enum_val(Param.equal_ratio_h)),

        qls1.is_close_above_ma250(df_indicator, row_begin, 2),
        qls1.is_close_above_ma250(df_indicator, row_begin, 1),
    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_reach_year_rise_3_x_20230208
)
def caochen_price_reach_year_rise_3_x_20230208(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        年线企稳上涨
        样例
            601600中国铝业（2021.11.29）
        建仓信号
            1.标的股价在250日线附近
            2.股价第二天和第三天的收盘价大于250日线价格 # note: david: 增加连续3天站上年线
        止盈信号
            1.股价跌破10日线
            2.股价较前一天新高，成交量较前一天缩小，收盘价卖出
        止损信号
            按持仓时间动态调整
    """
    memo_str = "caochen.年线企稳(最近3日高于年线).20230208"

    class Param(Enum):
        equal_ratio_l = -0.03  # 信号日close和年线比率下限
        equal_ratio_h = 0.03  # 信号日close和年线比率上限
        #
        duration_day = 3  # 连续企稳天数

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_close_adjacent_ma250(df_indicator, row_begin, (__enum_val(Param.duration_day) + 1),
                                     __enum_val(Param.equal_ratio_l), __enum_val(Param.equal_ratio_h)),

        [
            qls1.is_close_above_ma250(df_indicator, row_begin, datecount)
            for datecount in range(__enum_val(Param.duration_day), 0, -1)
        ],
    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_reach_year_rise_4_x_20230208
)
def caochen_price_reach_year_rise_4_x_20230208(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        年线企稳上涨
        样例
            601600中国铝业（2021.11.29）
        建仓信号
            1.标的股价在250日线附近
            2.股价第二天和第三天的收盘价大于250日线价格 # note: david: 增加连续4天站上年线
        止盈信号
            1.股价跌破10日线
            2.股价较前一天新高，成交量较前一天缩小，收盘价卖出
        止损信号
            按持仓时间动态调整
    """
    memo_str = "caochen.年线企稳(最近4日高于年线).20230208"

    class Param(Enum):
        equal_ratio_l = -0.03  # 信号日close和年线比率下限
        equal_ratio_h = 0.03  # 信号日close和年线比率上限
        #
        duration_day = 4  # 连续企稳天数

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_close_adjacent_ma250(df_indicator, row_begin, (__enum_val(Param.duration_day) + 1),
                                     __enum_val(Param.equal_ratio_l), __enum_val(Param.equal_ratio_h)),

        [
            qls1.is_close_above_ma250(df_indicator, row_begin, datecount)
            for datecount in range(__enum_val(Param.duration_day), 0, -1)
        ],
    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_reach_year_rise_5_x_20230208
)
def caochen_price_reach_year_rise_5_x_20230208(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        年线企稳上涨
        样例
            601600中国铝业（2021.11.29）
        建仓信号
            1.标的股价在250日线附近
            2.股价第二天和第三天的收盘价大于250日线价格 # note: david: 增加连续5天站上年线
        止盈信号
            1.股价跌破10日线
            2.股价较前一天新高，成交量较前一天缩小，收盘价卖出
        止损信号
            按持仓时间动态调整
    """
    memo_str = "caochen.年线企稳(近5日高于年线).20230208"

    class Param(Enum):
        equal_ratio_l = -0.03  # 信号日close和年线比率下限
        equal_ratio_h = 0.03  # 信号日close和年线比率上限
        #
        duration_day = 5  # 连续企稳天数

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_close_adjacent_ma250(df_indicator, row_begin, (__enum_val(Param.duration_day) + 1),
                                     __enum_val(Param.equal_ratio_l), __enum_val(Param.equal_ratio_h)),

        [
            qls1.is_close_above_ma250(df_indicator, row_begin, datecount)
            for datecount in range(__enum_val(Param.duration_day), 0, -1)
        ],
    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_reach_year_rise_1_x_20230210
)
def caochen_price_reach_year_rise_1_x_20230210(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        年线企稳上涨
        样例
            601600中国铝业（2021.11.29）# note: david: 需要caochen提供案例
        建仓信号
            1.标的股价在250日线附近
            2.股价第二天和第三天的收盘价大于250日线价格
            3.第一天股价跌破年线，收盘价大于年线 # caochen: 20230210增加
            4.20个交易日内，250日线起始点数值低于终止点数值 # caochen: 20230210增加
        止盈信号
            1.股价跌破10日线
            2.股价较前一天新高，成交量较前一天缩小，收盘价卖出
        止损信号
            按持仓时间动态调整
    """
    memo_str = "caochen.年线稳涨1(3日前低于年线)(近2日高于年线).20230210"

    class Param(Enum):
        # equal_ratio_l = -0.03  # 信号日close和年线比率下限
        # equal_ratio_h = 0.03  # 信号日close和年线比率上限
        ma250_duration_day = 20  # 年线斜率判断天数
        pass

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        # qls1.__is_close_adjacent_ma250(df_indicator, row_begin, 3,
        #                           __ev(Param.equal_ratio_l), __ev(Param.equal_ratio_h)),
        qls1.is_low_below_ma250(df_indicator, row_begin, 3),
        qls1.is_close_above_ma250(df_indicator, row_begin, 3),

        qls1.is_close_above_ma250(df_indicator, row_begin, 2),
        qls1.is_close_above_ma250(df_indicator, row_begin, 1),

        qls1.is_ma250_rise_duration(df_indicator, row_begin, 1 + __enum_val(Param.ma250_duration_day), 1),
    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_reach_year_rise_1_x_20230212
)
def caochen_price_reach_year_rise_1_x_20230212(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        年线企稳上涨
        样例
            601600中国铝业（2021.11.29）# note: david: 需要caochen提供案例
        建仓信号
            1.标的股价在250日线附近
            2.股价第二天和第三天的收盘价大于250日线价格
            3.第一天股价跌破年线，收盘价大于年线 # caochen: 20230210增加
            4.20个交易日内，250日线起始点数值低于终止点数值 # caochen: 20230210增加
            5.第一天之前收盘价格高于年线  # note：david：20230212: 否则可能和"年线稳涨3"重合
        止盈信号
            1.股价跌破10日线
            2.股价较前一天新高，成交量较前一天缩小，收盘价卖出
        止损信号
            按持仓时间动态调整
    """
    memo_str = "caochen.年线稳涨1(3日前低于年线)(近2日高于年线).20230212"

    class Param(Enum):
        # equal_ratio_l = -0.03  # 信号日close和年线比率下限
        # equal_ratio_h = 0.03  # 信号日close和年线比率上限
        ma250_duration_day = 20  # 年线斜率判断天数
        pass

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        # qls1.__is_close_adjacent_ma250(df_indicator, row_begin, 3,
        #                           __ev(Param.equal_ratio_l), __ev(Param.equal_ratio_h)),
        qls1.is_close_above_ma250(df_indicator, row_begin, 4),
        qls1.is_low_below_ma250(df_indicator, row_begin, 3),
        qls1.is_close_above_ma250(df_indicator, row_begin, 3),

        qls1.is_close_above_ma250(df_indicator, row_begin, 2),
        qls1.is_close_above_ma250(df_indicator, row_begin, 1),

        qls1.is_ma250_rise_duration(df_indicator, row_begin, 1 + __enum_val(Param.ma250_duration_day), 1),
    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_reach_year_rise_2_x_20230210
)
def caochen_price_reach_year_rise_2_x_20230210(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        年线企稳上涨
        样例
            601600中国铝业（2021.11.29）# note: david: 需要caochen提供案例
        建仓信号
            1.标的股价在250日线附近
            2.股价第二天和第三天的收盘价大于250日线价格
            3.第一天股价最低价接近250日线 # caochen: 20230210增加
            4.20个交易日内，250日线起始点数值低于终止点数值 # caochen: 20230210增加
        止盈信号
            1.股价跌破10日线
            2.股价较前一天新高，成交量较前一天缩小，收盘价卖出
        止损信号
            按持仓时间动态调整
    """
    memo_str = "caochen.年线稳涨2(3日前接近年线)(近2日高于年线).20230210"

    class Param(Enum):
        equal_ratio_l = 0.00  # 信号日close和年线比率下限
        equal_ratio_h = 0.03  # 信号日close和年线比率上限
        ma250_duration_day = 20  # 年线斜率判断天数
        pass

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_low_adjacent_ma250(df_indicator, row_begin, 3,
                                   __enum_val(Param.equal_ratio_l), __enum_val(Param.equal_ratio_h)),
        qls1.is_low_above_ma250(df_indicator, row_begin, 3),
        qls1.is_close_above_ma250(df_indicator, row_begin, 3),

        qls1.is_close_above_ma250(df_indicator, row_begin, 2),
        qls1.is_close_above_ma250(df_indicator, row_begin, 1),

        qls1.is_ma250_rise_duration(df_indicator, row_begin, 1 + __enum_val(Param.ma250_duration_day), 1),
    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_reach_year_rise_3_x_20230210
)
def caochen_price_reach_year_rise_3_x_20230210(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        年线企稳上涨
        样例
            601600中国铝业（2021.11.29）# note: david: 需要caochen提供案例
        建仓信号
            1.标的股价在250日线附近
            2.股价第二天和第三天的收盘价大于250日线价格
            3.股价第一天上涨突破250日线且收盘价大于250日线 # caochen: 20230210增加 # note: david: 即 昨日收盘价低于昨日年线
            4.20个交易日内，250日线起始点数值低于终止点数值 # caochen: 20230210增加
        止盈信号
            1.股价跌破10日线
            2.股价较前一天新高，成交量较前一天缩小，收盘价卖出
        止损信号
            按持仓时间动态调整
    """
    memo_str = "caochen.年线稳涨3(3日前上穿年线)(近2日高于年线).20230210"

    class Param(Enum):
        equal_ratio_l = 0.00  # 信号日close和年线比率下限
        equal_ratio_h = 0.03  # 信号日close和年线比率上限
        ma250_duration_day = 20  # 年线斜率判断天数
        pass

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_close_below_ma250(df_indicator, row_begin, 4),
        qls1.is_close_above_ma250(df_indicator, row_begin, 3),

        qls1.is_close_above_ma250(df_indicator, row_begin, 2),
        qls1.is_close_above_ma250(df_indicator, row_begin, 1),

        qls1.is_ma250_rise_duration(df_indicator, row_begin, 1 + __enum_val(Param.ma250_duration_day), 1),
    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_reach_year_rise_3_x_20230213
)
def caochen_price_reach_year_rise_3_x_20230213(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        年线企稳上涨
        样例
            601600中国铝业（2021.11.29）# note: david: 需要caochen提供案例
        建仓信号
            1.标的股价在250日线附近
            2.股价第二天和第三天的收盘价大于250日线价格
            3.股价第一天上涨突破250日线且收盘价大于250日线 # caochen: 20230210增加 # note: david: 即 昨日收盘价低于昨日年线
            # 4.20个交易日内，250日线起始点数值低于终止点数值 # caochen: 20230210增加 # note: caochen: 20230213: 去掉条件4
        止盈信号
            1.股价跌破10日线
            2.股价较前一天新高，成交量较前一天缩小，收盘价卖出
        止损信号
            按持仓时间动态调整
    """
    memo_str = "caochen.年线稳涨3(3日前上穿年线)(近2日高于年线).20230213"

    class Param(Enum):
        equal_ratio_l = 0.00  # 信号日close和年线比率下限
        equal_ratio_h = 0.03  # 信号日close和年线比率上限
        # ma250_duration_day = 20  # 年线斜率判断天数
        pass

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_close_below_ma250(df_indicator, row_begin, 4),
        qls1.is_close_above_ma250(df_indicator, row_begin, 3),

        qls1.is_close_above_ma250(df_indicator, row_begin, 2),
        qls1.is_close_above_ma250(df_indicator, row_begin, 1),

        # qls1.__is_ma250_rise_duration(df_indicator, row_begin, 1 + __ev(Param.ma250_duration_day), 1),
    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_low_above_previous_x_20230203
)
def caochen_price_low_above_previous_x_20230203(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        低点中线上移
        样例
            600216浙江医药（2021.07.07） # note: david: 测试发现 20210709 符合
        建仓信号
            1.5天内横盘（高价和低价波动幅度5%以内）
            2.横盘期间的低点高于20日到5日间的低点，高1%以上
        止盈信号
            1.股价跌破10日线
            2.股价较前一天新高，成交量较前一天缩小，收盘价卖出
        止损信号
            按持仓时间动态调整
    """
    memo_str = "caochen.低点上移(最近5日内横盘)(横盘低点高于最近20日到5日内低点1%).20230203"

    class Param(Enum):
        volatility_day_l = 1  # 横盘震荡交易日长度
        volatility_day_h = 5  # 横盘震荡交易日长度
        volatility_ratio = 0.05  # 横盘震荡高低差值5%
        previous_day_l = 6  # 更早时间段交易日长度
        previous_day_h = 20  # 更早时间段交易日长度
        previous_ratio = 0.01  # 横盘震荡交易日价格比更早时间段交易日价格上涨高1%

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_price_bound_duration(df_indicator, row_begin,
                                     __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h),
                                     __enum_val(Param.volatility_ratio)),

        qls1.is_low_duration_above_duration(df_indicator, row_begin,
                                            __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h),
                                            __enum_val(Param.previous_day_l), __enum_val(Param.previous_day_h),
                                            __enum_val(Param.previous_ratio)),

    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_price_low_above_previous_10_x_20230208
)
def caochen_price_low_above_previous_10_x_20230208(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        低点中线上移
        样例
            600216浙江医药（2021.07.07） # note: david: 测试发现 20210709 符合
        建仓信号
            1.5天内横盘（高价和低价波动幅度5%以内）
            2.横盘期间的低点高于20日到5日间的低点，高1%以上 # note: david: 0.01 数据太多了
        止盈信号
            1.股价跌破10日线
            2.股价较前一天新高，成交量较前一天缩小，收盘价卖出
        止损信号
            按持仓时间动态调整
    """
    memo_str = "caochen.低点上移(最近5日内横盘)(横盘低点高于最近20日到5日内低点10%).20230208"

    class Param(Enum):
        volatility_day_l = 1  # 横盘震荡交易日长度
        volatility_day_h = 5  # 横盘震荡交易日长度
        volatility_ratio = 0.05  # 横盘震荡高低差值5%
        previous_day_l = 6  # 更早时间段交易日长度
        previous_day_h = 20  # 更早时间段交易日长度
        previous_ratio = 0.10  # 横盘震荡交易日价格比更早时间段交易日价格上涨高1% # note: david: 0.01 数据太多了

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        qls1.is_price_bound_duration(df_indicator, row_begin,
                                     __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h),
                                     __enum_val(Param.volatility_ratio)),

        qls1.is_low_duration_above_duration(df_indicator, row_begin,
                                            __enum_val(Param.volatility_day_l), __enum_val(Param.volatility_day_h),
                                            __enum_val(Param.previous_day_l), __enum_val(Param.previous_day_h),
                                            __enum_val(Param.previous_ratio)),

    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


@qls0.anno_signal(
    the_module_name, the_signal_symbol, qldef.enable_signal_caochen_volume_enlarge_price_rise_4_x_20230310
)
def caochen_volume_enlarge_price_rise_4_x_20230310(
        df_indicator: pd.DataFrame, row_begin: int) -> [bool, str, dict, list[dict]]:
    """
        量增价涨
        样例
        建仓信号
        止盈信号
        止损信号
    """
    memo_str = "caochen.量增价涨(5+10+20+30日线向上)(放量4倍).20230310"

    class Param(Enum):
        volume_multiply_l = 4  # 交易量今日 相对于 昨日的3日平均交易量 的倍数 # note: 600118中国卫星20230221量比为4.470222
        ma5_duration_day = 20  # 5日线斜率判断天数 # note: 600118中国卫星20230221昨日之前近一个月斜率向上
        ma10_duration_day = 20  # 10日线斜率判断天数 # note: 600118中国卫星20230221昨日之前近一个月斜率向上
        ma20_duration_day = 20  # 20日线斜率判断天数 # note: 600118中国卫星20230221昨日之前近一个月斜率向上
        ma30_duration_day = 20  # 30日线斜率判断天数 # note: 600118中国卫星20230221昨日之前近一个月斜率向上
        # close_down_ratio_min = -0.5  # 今日收盘价格下跌最大比率（超过则不符合本信号） # note: 负数

    param_dict = __enum_dict(Param)

    is_signal = qls1.is_indicator_valid(df_indicator, row_begin) and qls1.is_all_valid(
        f"{qls1.mtd(df_indicator, row_begin)}",

        # 将"mrvolmavol(3,1)" 改为 "mavol(3,1)" modify by hhx 2024.07.26
        qls0.is_val_largeequal(df_indicator, "mrvolmavol(3,1)", row_begin, 1, __enum_val(Param.volume_multiply_l)),

        # note: caochen: 20230424: 002399 价格猛跌，不应该是这个信号，检查发现，应该按照今日ma进行判断，而不是昨日ma进行判断
        qls1.is_ma5_rise_duration(df_indicator, row_begin, 1 + __enum_val(Param.ma5_duration_day), 1),
        qls1.is_ma10_rise_duration(df_indicator, row_begin, 1 + __enum_val(Param.ma10_duration_day), 1),
        qls1.is_ma20_rise_duration(df_indicator, row_begin, 1 + __enum_val(Param.ma20_duration_day), 1),
        qls1.is_ma30_rise_duration(df_indicator, row_begin, 1 + __enum_val(Param.ma30_duration_day), 1),

        # caochen: 20230424: 002399 价格猛跌，增加价格跌幅限制
        # xxx__is_close_down_ratio_max(df_indicator, row_begin, __ev(Param.close_down_ratio_min)),

    )

    plot_dictlist = []

    return is_signal, memo_str, param_dict, plot_dictlist


############################################

def __to_indicator_row_begin(market, target, date):
    df_indicator = qloption.database.load_indicator_by_target(
        # qldef.division_1d 改成 qldef.history_division_1d modify by hhx 2024.07.24
        market, target, division=qldef.history_division_1d,
    )
    df_indicator = df_indicator.query(f"date<={date}") if dfutil.not_empty(df_indicator) else None
    row_begin = df_indicator.index[0] if dfutil.not_empty(df_indicator) else 0
    dfutil.empty(df_indicator) and dfutil.warn(
        f"{__to_indicator_row_begin.__name__}, indicator empty, {market=}, {target=}, {date=}"
    )
    return df_indicator, row_begin


def __exec_step_chain(hint, memo_func_tuplelist):
    memo = ""
    for step_memo, step_func in memo_func_tuplelist:
        memo += step_memo
        if not qls1.is_all_valid(hint, step_func()):
            return False, None
    dfutil.log(f"{hint}, pattern found, {memo=}")
    return True, memo


def return_pattern_memo_of_price_max_down_volume_enlarge(
        market, target, date,
        hint=None, is_log=False) -> [bool, str]:
    """ # caochen: 20221212: 过滤条件：当天出现上影线（股价创近3个交易日新高后回落5%以上，收盘价低于开盘价）且成交量放大。 """
    hint = __hint(hint, dfutil.funcname(
        return_pattern_memo_of_price_max_down_volume_enlarge,
        market, target, date
    ))

    df_indicator, row_begin = __to_indicator_row_begin(market, target, date)

    class Param(Enum):
        datecount = 3  # 最高价近期天数
        volume_ratio_l = 0.01  # 成交量比率下限
        down_ratio = 0.05  # 跌幅比率

    memo_func_tuplelist = [
        (
            f"(今日最高价高于过去{__enum_val(Param.datecount)}日最高价)",
            lambda: qls1.is_high_top_duration(
                df_indicator, row_begin,
                1, __enum_val(Param.datecount),
                hint=hint, is_log=is_log),
        ),
        (
            f"(今日收盘价比今日最高价跌幅{__enum_val(Param.down_ratio)}以上)",
            lambda: qls1.is_close_below_high_ratio(
                df_indicator, row_begin,
                __enum_val(Param.down_ratio),
                hint=hint, is_log=is_log),
        ),
        (
            f"(今日收盘价低于今日开盘价)",
            lambda: qls1.is_close_below_open(
                df_indicator, row_begin,
                hint=hint, is_log=is_log),
        ),
        (
            f"(成交量比昨日增加)",
            lambda: qls1.is_volume_enlarge(
                df_indicator, row_begin,
                __enum_val(Param.volume_ratio_l),
                hint=hint, is_log=is_log),
        ),
    ]
    return __exec_step_chain(hint, memo_func_tuplelist)


def return_pattern_memo_of_board(
        board_name_list, market, target, date,
        hint=None, is_log=False) -> [bool, str]:
    """ 过滤板块 """
    hint = __hint(hint, dfutil.funcname(
        return_pattern_memo_of_board,
        board_name_list, market, target, date
    ))

    class Param(Enum):
        board_name_list = qlfocus.trigger_score_adjust_zero_board_name_list  # 排除板块列表

    memo_func_tuplelist = [
        (
            f"(排除板块{__enum_val(Param.board_name_list)})(板块={board_name_list})",
            lambda: dfutil.is_list_contain_any(
                board_name_list, __enum_val(Param.board_name_list)
            )
        ),
    ]
    return __exec_step_chain(hint, memo_func_tuplelist)


def return_pattern_memo_of_pdpr3_price_rise_shape_usl(
        signal_list, market, target, date,
        hint=None, is_log=False) -> [bool, str]:
    """ 信号上涨中继3，出现形态上影线，此前连续上涨5-8天
        # note: david: 调整为 "8天内有5天收盘价上涨"
    """
    hint = __hint(hint, dfutil.funcname(
        return_pattern_memo_of_pdpr3_price_rise_shape_usl,
        market, target, date
    ))

    df_indicator, row_begin = __to_indicator_row_begin(market, target, date)

    class Param(Enum):
        recent_datecount = 8  # 持续天数
        rise_datecount = 5  # 上涨天数

    memo_func_tuplelist = [
        (
            f"(上涨中继3)",
            lambda: dfutil.is_list_contain_any(signal_list, [
                caochen_price_down_predict_rise_3_x_20221011.__name__,
                caochen_price_down_predict_rise_3_x_20221020.__name__,
            ])),
        (
            f"(今日上影线)",
            lambda: qls1.is_shape_of_upper_shadow_line(
                df_indicator, row_begin,
                hint=hint, is_log=is_log)
        ),
        (
            f"(过去{__enum_val(Param.recent_datecount)}日内有{__enum_val(Param.rise_datecount)}日收盘价上涨)",
            lambda: qls1.is_close_rise_least(
                df_indicator, row_begin,
                __enum_val(Param.recent_datecount), __enum_val(Param.rise_datecount),
                hint=hint, is_log=is_log)
        ),
    ]
    return __exec_step_chain(hint, memo_func_tuplelist)


def return_pattern_memo_of_pdpr1_price_rise_price_down_volume_enlarge(
        signal_list, market, target, date,
        hint=None, is_log=False) -> [bool, str]:
    """ 上涨中继1，当策略选出股票涨幅超过10%，当天价格较前一天收盘价跌幅7%以上，且当天最低点为收盘价，成交量增加为近20日3倍以上
        note: david: "涨幅" 定义为 "近20日内从低点到今日收盘"
        note: david: "成交量增加的比较基准" 定义为 "近20日平均成交量"
    """
    hint = __hint(hint, dfutil.funcname(
        return_pattern_memo_of_pdpr1_price_rise_price_down_volume_enlarge,
        market, target, date
    ))

    df_indicator, row_begin = __to_indicator_row_begin(market, target, date)

    class Param(Enum):
        datecount = 20  # 近期天数
        down_ratio = 0.07  # 跌幅比率
        rise_ratio_l = 0.1  # 涨幅比率下限
        rise_ratio_h = 99  # 涨幅比率上限
        volume_ratio_l = 3  # 成交量比率下限
        volume_ratio_h = 99  # 成交量比率上限
        low_ratio_l = 0.00  # close接近low的比率下限
        low_ratio_h = 0.02  # close接近low的比率下限

    memo_func_tuplelist = [
        (
            f"(上涨中继1)",
            lambda: dfutil.is_list_contain_any(signal_list, [
                caochen_price_down_predict_rise_1_x_20220915.__name__,
                caochen_price_down_predict_rise_1_x_20221020.__name__,
                caochen_price_down_predict_rise_1_x_20221129.__name__,
            ])
        ),
        (
            f"(过去{__enum_val(Param.datecount)}日最低价到今日收盘价涨幅{__enum_val(Param.rise_ratio_l)}以上)",
            lambda: qls1.is_price_rise_duration(
                df_indicator, row_begin,
                __enum_val(Param.datecount), __enum_val(Param.rise_ratio_l), __enum_val(Param.rise_ratio_h),
                hint=hint, is_log=is_log),
        ),
        (
            f"(今日收盘价比昨日收盘价跌幅{__enum_val(Param.down_ratio)}以上)",
            lambda: qls1.is_close_down_ratio(
                df_indicator, row_begin,
                __enum_val(Param.down_ratio),
                hint=hint, is_log=is_log),
        ),
        (
            f"(今日收盘价接近今日最低价)",
            lambda: qls1.is_close_adjacent_low(
                df_indicator, row_begin,
                __enum_val(Param.low_ratio_l), __enum_val(Param.low_ratio_h),
                hint=hint, is_log=is_log),
        ),
        (
            f"(今日成交量为过去{__enum_val(Param.datecount)}日平均成交量{__enum_val(Param.volume_ratio_l)}倍以上)",
            lambda: qls1.is_volume_enlarge_duration(
                df_indicator, row_begin,
                __enum_val(Param.datecount), __enum_val(Param.volume_ratio_l), __enum_val(Param.volume_ratio_h),
                hint=hint, is_log=is_log),
        ),
    ]
    return __exec_step_chain(hint, memo_func_tuplelist)


def return_pattern_memo_of_pdpr1_volume_enlarge_price_down_below_ma10(
        signal_list, market, target, date,
        hint=None, is_log=False) -> [bool, str]:
    """ 上涨中继1，当策略选出股票成交量较前一天增加，当天的收盘价跌破十日线且当天股价下跌的最低点为当天的收盘价，直接排除
    """
    hint = __hint(hint, dfutil.funcname(
        return_pattern_memo_of_pdpr1_volume_enlarge_price_down_below_ma10,
        market, target, date
    ))

    df_indicator, row_begin = __to_indicator_row_begin(market, target, date)

    class Param(Enum):
        volume_ratio_l = 0.01  # 成交量比率下限
        low_ratio_l = 0.00  # close接近low的比率下限
        low_ratio_h = 0.02  # close接近low的比率下限

    memo_func_tuplelist = [
        (
            f"(上涨中继1)",
            lambda: dfutil.is_list_contain_any(signal_list, [
                caochen_price_down_predict_rise_1_x_20220915.__name__,
                caochen_price_down_predict_rise_1_x_20221020.__name__,
                caochen_price_down_predict_rise_1_x_20221129.__name__,
            ]),
        ),
        (
            f"(成交量比昨日增加)",
            lambda: qls1.is_volume_enlarge(
                df_indicator, row_begin,
                __enum_val(Param.volume_ratio_l),
                hint=hint, is_log=is_log),
        ),
        (
            f"(今日收盘价跌破十日线)",
            lambda: qls1.is_close_below_ma10(
                df_indicator, row_begin,
                hint=hint, is_log=is_log),
        ),
        (
            f"(今日收盘价接近今日最低价)",
            lambda: qls1.is_close_adjacent_low(
                df_indicator, row_begin,
                __enum_val(Param.low_ratio_l), __enum_val(Param.low_ratio_h),
                hint=hint, is_log=is_log),
        ),
    ]

    return __exec_step_chain(hint, memo_func_tuplelist)

############################################
