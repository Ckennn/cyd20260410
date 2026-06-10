# coding=utf-8
"""
策略（caochen）
"""

from enum import Enum
import pandas as pd

import dfutil
import qlfunc
import qldebug
import qlsignal0 as qls0

"""
    策略与问题
"""

############################################

__enum_key = lambda __enum: __enum.name
__enum_val = lambda __enum: __enum.value
__enum_dict = lambda __enum: {x.name: x.value for x in __enum}

__hint = lambda __context, __current: dfutil.funcname(__context, __current)


############################################


def mtd(df_ind, row_index):
    return None if dfutil.empty(df_ind) \
        else None if row_index not in df_ind.index \
        else f'[ {df_ind["market"].loc[row_index]}' \
             f', {df_ind["target"].loc[row_index]}' \
             f', {df_ind["date"].loc[row_index]}' \
             f']'


def is_indicator_valid(df_indicator: pd.DataFrame, row_begin) -> bool:
    # 数据校验
    funcname = is_indicator_valid.__name__
    # 时间首尾在2个月自然日内都算合理
    return qls0.is_date_valid(df_indicator, row_begin, 1, 20, 30 * 2, hint=funcname)


def is_all_valid(hint, *valid_tuple_of_item_or_list) -> bool:
    # valid_array = [
    #     [y for y in x] if dfutil.of_list(x) else x
    #     for x in valid_array_of_item_or_list
    # ]
    valid_array = dfutil.flat_list(valid_tuple_of_item_or_list)
    is_all = all(valid_array)

    # note: 提醒日志，以便检查signal逻辑条件是否合理
    with dfutil.CodeBlock():
        valid_list = list(valid_array)
        total_count = len(valid_list)
        false_count = valid_list.count(False)
        qldebug.log_signal_valid_condition and dfutil.log(
            f"{hint}, false/total={false_count}/{total_count}({qlfunc.str_percent_2(false_count, total_count)})")
        (0 < false_count <= 1) and dfutil.warn(
            f"{hint}, check: {false_count=}"
        )

    #
    return is_all


############################################


def is_ema11_above_ema22(df_indicator: pd.DataFrame, row_begin, row_count,
                         hint=None, is_log=False) -> list:
    # ema11快线＞ema22慢线
    funcname = is_ema11_above_ema22.__name__
    return [
        # ema(11) > ema(22)
        qls0.is_col_large_2(df_indicator, "ema(11)", "ema(22)", row_begin, row_count,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_ema11_below_ema22(df_indicator: pd.DataFrame, row_begin, row_count,
                         hint=None, is_log=False) -> list:
    # ema11快线<ema22慢线
    funcname = is_ema11_below_ema22.__name__
    return [
        # ema(11) > ema(22)
        qls0.is_col_small_2(df_indicator, "ema(11)", "ema(22)", row_begin, row_count,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_ma5_above_ma10_above_ma20_above_ma30(df_indicator: pd.DataFrame, row_begin,
                                            hint=None, is_log=False) -> list:
    # 5日线＞10日线＞20日线＞30日线
    funcname = is_ma5_above_ma10_above_ma20_above_ma30.__name__
    return [
        # ma1(5) > ma1(10)
        qls0.is_col_large_2(df_indicator, "ma(5)", "ma(10)", row_begin, 1,
                            hint=__hint(hint, funcname), is_log=is_log),
        # ma1(10) > ma1(20)
        qls0.is_col_large_2(df_indicator, "ma(10)", "ma(20)", row_begin, 1,
                            hint=__hint(hint, funcname), is_log=is_log),
        # ma1(20) > ma1(30)
        qls0.is_col_large_2(df_indicator, "ma(20)", "ma(30)", row_begin, 1,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_ma5_above_ma20(df_indicator: pd.DataFrame, row_begin,
                      hint=None, is_log=False) -> list:
    # 5日线＞20日线
    funcname = is_ma5_above_ma20.__name__
    return [
        # ma1(5) > ma1(20)
        qls0.is_col_large_2(df_indicator, "ma(5)", "ma(20)", row_begin, 1,
                            hint=__hint(hint, funcname), is_log=is_log),
        # # ma1(10) > ma1(20)
        # qlsignal.__is_col_large_2(df_indicator, "ma(10)", "ma(20)", row_begin, 1),
    ]


def is_ma5_rise_duration(df_indicator: pd.DataFrame, row_begin, row_count_begin, row_count_end,
                         hint=None, is_log=False) -> list:
    # 5日线上升
    funcname = is_ma5_rise_duration.__name__
    return [
        # ma20(5) < ma1(5)
        qls0.is_row_small_1(df_indicator, ["ma(5)"], row_begin,
                            row_count_begin, row_count_end,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_ma10_above_ma20(df_indicator: pd.DataFrame, row_begin,
                       hint=None, is_log=False) -> list:
    # 10日线＞20日线
    funcname = is_ma10_above_ma20.__name__
    return [
        # # ma1(5) > ma1(20)
        # qlsignal.__is_col_large_2(df_indicator, "ma(5)", "ma(20)", row_begin, 1),
        # ma1(10) > ma1(20)
        qls0.is_col_large_2(df_indicator, "ma(10)", "ma(20)", row_begin, 1,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_ma10_rise_duration(df_indicator: pd.DataFrame, row_begin, row_count_begin, row_count_end,
                          hint=None, is_log=False) -> list:
    # 10日线上升
    funcname = is_ma10_rise_duration.__name__
    return [
        # ma20(10) < ma1(10)
        qls0.is_row_small_1(df_indicator, ["ma(10)"], row_begin,
                            row_count_begin, row_count_end,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_ma20_rise_duration(df_indicator: pd.DataFrame, row_begin, row_count_begin, row_count_end,
                          hint=None, is_log=False) -> list:
    # 20日线上升
    funcname = is_ma20_rise_duration.__name__
    return [
        # ma20(20) < ma1(20)
        qls0.is_row_small_1(df_indicator, ["ma(20)"], row_begin,
                            row_count_begin, row_count_end,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_ma30_rise_duration(df_indicator: pd.DataFrame, row_begin, row_count_begin, row_count_end,
                          hint=None, is_log=False) -> list:
    # 30日线上升
    funcname = is_ma30_rise_duration.__name__
    return [
        # ma20(30) < ma1(30)
        qls0.is_row_small_1(df_indicator, ["ma(30)"], row_begin,
                            row_count_begin, row_count_end,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_ma250_rise_duration(df_indicator: pd.DataFrame, row_begin, row_count_begin, row_count_end,
                           hint=None, is_log=False) -> list:
    # 250日线上升
    funcname = is_ma250_rise_duration.__name__
    return [
        # ma20(250) < ma1(250)
        qls0.is_row_small_1(df_indicator, ["ma(250)"], row_begin,
                            row_count_begin, row_count_end,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_price_cross_above_ma5(df_indicator: pd.DataFrame, row_begin,
                             hint=None, is_log=False) -> list:
    # （综合考虑）股价上穿5日线
    funcname = is_price_cross_above_ma5.__name__
    return [
        # ma1(5) < close1
        qls0.is_col_large_2(df_indicator, "close", "ma(5)", row_begin, 1,
                            hint=__hint(hint, funcname), is_log=is_log),
        # low2 < ma1(5)
        qls0.is_col_small_2(df_indicator, "low", "ma(5)", row_begin, 2,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_price_adjacent_ma20(df_indicator: pd.DataFrame, row_begin, row_count,
                           ratio_limit_l, ratio_limit_h,
                           hint=None, is_log=False) -> list:
    # （综合考虑）在10-20日线成交
    funcname = is_price_adjacent_ma20.__name__
    return [
        # note: 使用 low 更加合理
        # low1 ~ ma1(20)
        qls0.is_col_equalabout_2(df_indicator, "low", "ma(20)", row_begin, row_count,
                                 ratio_limit_l, ratio_limit_h,
                                 hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_price_down(df_indicator: pd.DataFrame, row_begin,
                  hint=None, is_log=False) -> list:
    # （综合考虑）股价回调
    funcname = is_price_down.__name__
    return [
        # # close3 > close1
        # qlsignal.__is_row_large_1(df_indicator, "close", row_begin, 3, 1),
        # # close2 > close1
        # qlsignal.__is_row_large_1(df_indicator, "close", row_begin, 2, 1),
        # # # close3 > close2
        # # qlsignal.__is_row_large_1(df_indicator, "close", row_begin, 3, 2),

        # avg: close3 > close1
        qls0.is_row_large_1(df_indicator, ["close", "high", "low"], row_begin, 3, 1,
                            hint=__hint(hint, funcname), is_log=is_log),
        # avg: close2 > close1
        qls0.is_row_large_1(df_indicator, ["close", "high", "low"], row_begin, 2, 1,
                            hint=__hint(hint, funcname), is_log=is_log),
        # # avg: close3 > close2
        # qlsignal.__is_row_large_1(df_indicator, ["close", "high", "low"], row_begin, 3, 2),
    ]


def is_price_rise_duration(df_indicator: pd.DataFrame, row_begin, row_count,
                           ratio_limit_l, ratio_limit_h,
                           hint=None, is_log=False) -> list:
    # （综合考虑）10日内 最低点价格，到 今日收盘价格 之间 上涨幅度
    funcname = is_price_rise_duration.__name__
    return [
        qls0.is_range_2_diffratio_4(df_indicator, ["close"], ["low"], row_begin,
                                    1, 1, "median",
                                    1, row_count, "min",
                                    ratio_limit_l, ratio_limit_h,
                                    hint=__hint(hint, funcname), is_log=is_log),
        qls0.is_range_2_largeequal_4(df_indicator, ["close"], ["low"], row_begin,
                                     1, 1, "median",
                                     1, row_count, "min",
                                     hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_price_bound_duration(df_indicator: pd.DataFrame, row_begin,
                            row_count_start, row_count_stop,
                            diff_ratio_limit,
                            hint=None, is_log=False) -> list:
    # （综合考虑）股价横盘震荡
    funcname = is_price_bound_duration.__name__
    return [
        # note: 测试发现，600026.20220902 价格波动按照 hlc 均值判断好一些
        # # diff(high[5:100], low[5:100]) <= 20%
        # qlsignal.__is_range_diffrange_2(df_indicator, "high", "low", row_begin,
        #                                 row_count_start, row_count_stop,
        #                                 "max", "min",
        #                                 diff_ratio_limit,
        #                                 hint=hint),
        # diff(high[5:100], low[5:100]) <= 20%
        qls0.is_range_1_diffratio_2(df_indicator, ["high", "low", "close"], row_begin, row_count_start, row_count_stop,
                                    "max", "min", 0, diff_ratio_limit,
                                    hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_half_low_ema11(df_indicator: pd.DataFrame, row_begin, row_count,
                            ratio_limit,
                            hint=None, is_log=False) -> list:
    # close 处于 low 和 ema11 之间（意味着存在向上的可能性）
    funcname = is_close_half_low_ema11.__name__
    return [
        # close1 ~ ma1(10)
        qls0.is_range_2_diffratio_4(df_indicator, ["low", "close"], ["close", "ema(11)"], row_begin,
                                    1, row_count, "min",
                                    1, row_count, "max",
                                    0, ratio_limit,
                                    hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_adjacent_low(df_indicator: pd.DataFrame, row_begin,
                          ratio_limit_l, ratio_limit_h,
                          hint=None, is_log=False) -> list:
    # 收盘价接近最低价
    funcname = is_close_adjacent_low.__name__
    return [
        # close1 ~ ma1(10)
        qls0.is_col_equalabout_2(df_indicator, "close", "low", row_begin, 1,
                                 ratio_limit_l, ratio_limit_h,
                                 hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_adjacent_high(df_indicator: pd.DataFrame, row_begin,
                           ratio_limit_l, ratio_limit_h,
                           hint=None, is_log=False) -> list:
    # 收盘价接近最高价
    funcname = is_close_adjacent_high.__name__
    return [
        # close1 ~ high1
        qls0.is_col_equalabout_2(df_indicator, "close", "high", row_begin, 1,
                                 ratio_limit_l, ratio_limit_h,
                                 hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_adjacent_ema11(df_indicator: pd.DataFrame, row_begin, row_count,
                            ratio_limit_l, ratio_limit_h,
                            hint=None, is_log=False) -> list:
    # ema11附近（快线）
    funcname = is_close_adjacent_ema11.__name__
    return [
        # close1 ~ ma1(10)
        qls0.is_col_equalabout_2(df_indicator, "close", "ema(11)", row_begin, row_count,
                                 ratio_limit_l, ratio_limit_h,
                                 hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_adjacent_ema22(df_indicator: pd.DataFrame, row_begin, row_count,
                            ratio_limit_l, ratio_limit_h,
                            hint=None, is_log=False) -> list:
    # ema22附近（慢线）
    funcname = is_close_adjacent_ema22.__name__
    return [
        # close1 ~ ma1(10)
        qls0.is_col_equalabout_2(df_indicator, "close", "ema(22)", row_begin, row_count,
                                 ratio_limit_l, ratio_limit_h,
                                 hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_adjacent_ma10(df_indicator: pd.DataFrame, row_begin, row_count,
                           ratio_limit_l, ratio_limit_h,
                           hint=None, is_log=False) -> list:
    # 沿10日线买入
    funcname = is_close_adjacent_ma10.__name__
    return [
        # close1 ~ ma1(10)
        qls0.is_col_equalabout_2(df_indicator, "close", "ma(10)", row_begin, row_count,
                                 ratio_limit_l, ratio_limit_h,
                                 hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_adjacent_ma20(df_indicator: pd.DataFrame, row_begin, row_count,
                           ratio_limit_l, ratio_limit_h,
                           hint=None, is_log=False) -> list:
    # 在10-20日线成交
    funcname = is_close_adjacent_ma20.__name__
    return [
        # close1 ~ ma1(20)
        qls0.is_col_equalabout_2(df_indicator, "close", "ma(20)", row_begin, row_count,
                                 ratio_limit_l, ratio_limit_h,
                                 hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_adjacent_ma250(df_indicator: pd.DataFrame, row_begin, row_count,
                            ratio_limit_l, ratio_limit_h,
                            hint=None, is_log=False) -> list:
    # 在250日线成交
    funcname = is_close_adjacent_ma250.__name__
    return [
        # close1 ~ ma1(250)
        qls0.is_col_equalabout_2(df_indicator, "close", "ma(250)", row_begin, row_count,
                                 ratio_limit_l, ratio_limit_h,
                                 hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_above_ma250(df_indicator: pd.DataFrame, row_begin, row_count,
                         hint=None, is_log=False) -> list:
    # 股价高于250日线
    funcname = is_close_above_ma250.__name__
    return [
        # ma[x](250) < close[x]
        qls0.is_col_large_2(df_indicator, "close", "ma(250)", row_begin, row_count,
                            hint=__hint(hint, funcname), is_log=is_log),
        # # low[x+1] < ma[x](250)
        # qlsignal.__is_col_small_2(df_indicator, "low", "ma(250)", row_begin, row_count + 1, hint=funcname),
    ]


def is_close_above_bbi(df_indicator: pd.DataFrame, row_begin,
                       hint=None, is_log=False) -> list:
    # 股价高于BBI
    funcname = is_close_above_bbi.__name__
    return [
        # bbi1 < close1
        qls0.is_col_large_2(df_indicator, "close", "bbi(3,6,12,24)", row_begin, 1,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_above_bbi_first(df_indicator: pd.DataFrame, row_begin,
                             hint=None, is_log=False) -> list:
    # 股价首次高于BBI
    funcname = is_close_above_bbi_first.__name__
    return [
        # bbi1 < close1
        qls0.is_col_large_2(df_indicator, "close", "bbi(3,6,12,24)", row_begin, 1,
                            hint=__hint(hint, funcname), is_log=is_log),
        # close[start:stop] < bbi[start:stop]
        qls0.is_col_large_2(df_indicator, "bbi(3,6,12,24)", "close", row_begin, 2,
                            hint=__hint(hint, funcname), is_log=is_log),
        qls0.is_col_large_2(df_indicator, "bbi(3,6,12,24)", "close", row_begin, 3,
                            hint=__hint(hint, funcname), is_log=is_log),
        qls0.is_col_large_2(df_indicator, "bbi(3,6,12,24)", "close", row_begin, 4,
                            hint=__hint(hint, funcname), is_log=is_log),
        qls0.is_col_large_2(df_indicator, "bbi(3,6,12,24)", "close", row_begin, 5,
                            hint=__hint(hint, funcname), is_log=is_log),
        # diff(close[2:5], bbi[2:5]) <= 0
        # qlsignal.__is_range_diffrange_2(df_indicator, "close", "bbi(3,6,12,24)", row_begin,
        #                                 row_count_start, row_count_stop,
        #                                 "max", "min",
        #                                 0,
        #                                 hint=hint),
    ]


def is_close_above_high_duration(df_indicator: pd.DataFrame, row_begin,
                                 row_count_2_start, row_count_2_stop,
                                 hint=None, is_log=False) -> list:
    # 股价向上突破横盘震荡区间
    funcname = is_close_above_high_duration.__name__
    return [
        # high[5:100] < close1
        qls0.is_range_2_large_2(df_indicator, "close", "high",
                                row_begin, 1,
                                row_count_2_start, row_count_2_stop, "max",
                                hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_below_ma10(df_indicator: pd.DataFrame, row_begin,
                        hint=None, is_log=False) -> list:
    # 股价低于10日线
    funcname = is_close_below_ma10.__name__
    return [
        # ma1(10) < close1
        qls0.is_col_small_2(df_indicator, "close", "ma(10)", row_begin, 1,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_below_ma250(df_indicator: pd.DataFrame, row_begin, row_count,
                         hint=None, is_log=False) -> list:
    # 股价低于250日线
    funcname = is_close_below_ma250.__name__
    return [
        # ma[x](250) < close[x]
        qls0.is_col_small_2(df_indicator, "close", "ma(250)", row_begin, row_count,
                            hint=__hint(hint, funcname), is_log=is_log),
        # # low[x+1] < ma[x](250)
        # qlsignal.__is_col_small_2(df_indicator, "low", "ma(250)", row_begin, row_count + 1, hint=funcname),
    ]


def is_close_below_open(df_indicator: pd.DataFrame, row_begin,
                        hint=None, is_log=False) -> list:
    # 收盘价低于开盘价
    funcname = is_close_below_open.__name__
    return [
        # open1 < close1
        qls0.is_col_small_2(df_indicator, "close", "open", row_begin, 1,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_below_high_ratio(df_indicator: pd.DataFrame, row_begin,
                              ratio_limit,
                              hint=None, is_log=False) -> list:
    # 收盘价低于最高价比率
    funcname = is_close_below_high_ratio.__name__
    return [
        # close1 << high1
        qls0.is_row_largemore_2(df_indicator, "high", "close", row_begin, 1, 1,
                                ratio_limit,
                                hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_down_ratio(df_indicator: pd.DataFrame, row_begin,
                        ratio_limit,
                        hint=None, is_log=False) -> list:
    # 收盘价下跌
    funcname = is_close_down_ratio.__name__
    return [
        # avg: close2 > close1
        qls0.is_row_largemore_1(df_indicator, ["close"], row_begin, 2, 1,
                                ratio_limit,
                                hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_rise_ratio(df_indicator: pd.DataFrame, row_begin,
                        ratio_limit,
                        hint=None, is_log=False) -> list:
    # 收盘价上涨
    funcname = is_close_rise_ratio.__name__
    return [
        # avg: close2 < close1
        qls0.is_row_smallmore_1(df_indicator, ["close"], row_begin, 2, 1,
                                ratio_limit,
                                hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_close_rise_least(df_indicator: pd.DataFrame, row_begin,
                        duration_count: int, rise_count_l: int,
                        hint=None, is_log=False) -> list:
    # 股价x天内至少上涨y天
    funcname = is_close_rise_least.__name__

    rise_list = [
        # close2 < close1
        qls0.is_row_small_1(df_indicator, "close", row_begin, x, 1, hint=hint)
        for x in range(1, duration_count + 1)
    ]
    is_check = (rise_list.count(True) >= rise_count_l)

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{duration_count=}, {rise_count_l}, "
                               f"{rise_list=}, "
                               f"{is_check=}, "
                               )

    return [is_check]


def is_high_top_duration(df_indicator: pd.DataFrame, row_begin,
                         row_count_2_start, row_count_2_stop,
                         hint=None, is_log=False) -> list:
    # 高点在周期内最高
    funcname = is_high_top_duration.__name__
    return [
        # high[5:100] < high1
        qls0.is_range_2_largeequal_2(df_indicator, "high", "high",
                                     row_begin, 1,
                                     row_count_2_start, row_count_2_stop, "max",
                                     hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_low_above_ma250(df_indicator: pd.DataFrame, row_begin, row_count,
                       hint=None, is_log=False) -> list:
    # 低点高于250日线
    funcname = is_low_above_ma250.__name__
    return [
        # low1 < ma1(250)
        qls0.is_col_large_2(df_indicator, "low", "ma(250)", row_begin, row_count,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_low_below_ma250(df_indicator: pd.DataFrame, row_begin, row_count,
                       hint=None, is_log=False) -> list:
    # 低点低于250日线
    funcname = is_low_below_ma250.__name__
    return [
        # low1 < ma1(250)
        qls0.is_col_small_2(df_indicator, "low", "ma(250)", row_begin, row_count,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_low_adjacent_ma250(df_indicator: pd.DataFrame, row_begin, row_count,
                          ratio_limit_l, ratio_limit_h,
                          hint=None, is_log=False) -> list:
    # 低点接近250日线
    funcname = is_low_adjacent_ma250.__name__
    return [
        # close1 ~ ma1(250)
        qls0.is_col_equalabout_2(df_indicator, "low", "ma(250)", row_begin, row_count,
                                 ratio_limit_l, ratio_limit_h,
                                 hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_low_duration_above_duration(df_indicator: pd.DataFrame, row_begin,
                                   row_count_1_start, row_count_1_stop,
                                   row_count_2_start, row_count_2_stop,
                                   ratio_limit,
                                   hint=None, is_log=False) -> list:
    # 低点 在一个周期内 比 另一个周期内 要高
    funcname = is_low_duration_above_duration.__name__
    return [
        # low[5:100] < low[1:5]
        qls0.is_range_2_diffratio_4(df_indicator, "low", "low", row_begin,
                                    row_count_1_start, row_count_1_stop, "min",
                                    row_count_2_start, row_count_2_stop, "min",
                                    ratio_limit, 99,
                                    hint=__hint(hint, funcname), is_log=is_log),
        qls0.is_range_2_largeequal_4(df_indicator, "low", "low", row_begin,
                                     row_count_1_start, row_count_1_stop, "min",
                                     row_count_2_start, row_count_2_stop, "min",
                                     hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_volume_shrink(df_indicator: pd.DataFrame, row_begin,
                     hint=None, is_log=False) -> list:
    # 成交量缩小
    funcname = is_volume_shrink.__name__
    return [
        # todo: impl: 股价回调，从回调的第一天起量能逐渐缩小，量能缩小至较调整第一天量能的70%以上时，股价在高点下跌10%-15%区间建仓

        # note: 测试发现 600026，缩量可以定位为：mavol(3)的昨日高于本日
        # mavol2(3) > mavol1(3)
        qls0.is_row_large_1(df_indicator, "mavol(3)", row_begin, 2, 1,
                            hint=__hint(hint, funcname), is_log=is_log),
        # # mavol3(3) > mavol1(1)
        # qlsignal.__is_row_largeequal_1(df_indicator, "mavol(3)", row_begin, 3, 1),
        # # mavol3(3) > mavol2(3)
        # qlsignal.__is_row_largeequal_1(df_indicator, "mavol(3)", row_begin, 3, 2),
    ]


def is_volume_enlarge(df_indicator: pd.DataFrame, row_begin,
                      ratio_diff_more,
                      hint=None, is_log=False) -> list:
    # 成交量放大
    funcname = is_volume_enlarge.__name__
    return [
        # note: 测试发现，600026 放量直接使用 volume 不能使用 mavol
        # volume2 < volume1
        qls0.is_row_smallmore_1(df_indicator, "volume", row_begin, 2, 1, ratio_diff_more,
                                hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_volume_enlarge_duration(df_indicator: pd.DataFrame, row_begin,
                               duration_count, ratio_limit_l, ratio_limit_h,
                               hint=None, is_log=False) -> list:
    # 成交量放大，在一定周期内
    funcname = is_volume_enlarge_duration.__name__
    return [
        qls0.is_range_2_diffratio_4(df_indicator, ["volume"], ["volume"], row_begin,
                                    1, 1, "mean",
                                    1, duration_count, "mean",
                                    ratio_limit_l, ratio_limit_h,
                                    hint=__hint(hint, funcname), is_log=is_log),
        qls0.is_range_2_largeequal_4(df_indicator, ["volume"], ["volume"], row_begin,
                                     1, 1, "mean",
                                     1, duration_count, "mean",
                                     hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_volume_bound_duration(df_indicator: pd.DataFrame, row_begin,
                             row_count_start, row_count_stop, diff_ratio_limit,
                             hint=None, is_log=False) -> list:
    # 成交量横盘震荡
    funcname = is_volume_bound_duration.__name__
    return [
        # diff(mavol(3)[1:5], mavol(3)[1:5]) <= 20%
        qls0.is_range_2_diffratio_2(df_indicator, "mavol(3)", "mavol(3)", row_begin, row_count_start, row_count_stop,
                                    "max", "min", 0, diff_ratio_limit,
                                    hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_amount_enlarge(df_indicator: pd.DataFrame, row_begin,
                      ratio_diff_more,
                      hint=None, is_log=False) -> list:
    # 成交额放大
    funcname = is_amount_enlarge.__name__
    return [
        # amount2 * 2 <= amount1
        qls0.is_row_largemore_1(df_indicator, "amount", row_begin, 1, 2, ratio_diff_more,
                                hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_macd_positive(df_indicator: pd.DataFrame, row_begin, row_count,
                     high_low_diffratio_max,  # high 和 low 的 diffratio 的上限（高于这个取值，不符合条件）
                     hint=None, is_log=False) -> list:
    # MACD 为正数（在 最近 count 天数内 high 和 low 的 diffratio 不超过 限制）
    funcname = is_macd_positive.__name__
    return [

        # 零轴以上
        # qls0.is_col_valuelimit_1(df_indicator, "macdbar(12,26,9)", row_begin, 1,
        #                          0.01, 99.0,
        #                          hint=__hint(hint, funcname), is_log=is_log),
        # qls0.is_col_valuelimit_1(df_indicator, "macdbar(12,26,9)", row_begin, row_count,
        #                          0.01, 99.0,
        #                          hint=__hint(hint, funcname), is_log=is_log),
        qls0.is_range_1_valuelimit_2(df_indicator, "macdbar(12,26,9)", row_begin, 1, row_count,
                                     "min", "min", 0.01, 99,
                                     hint=__hint(hint, funcname), is_log=is_log),
        # high low 差异比率
        qls0.is_range_1_diffratio_2(df_indicator, "macdbar(12,26,9)", row_begin, 1, row_count,
                                    "max", "min", 0, high_low_diffratio_max,
                                    hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_macd_negative(df_indicator: pd.DataFrame, row_begin, row_count,
                     high_low_diffratio_max,  # high 和 low 的 diffratio 的上限（高于这个取值，不符合条件）
                     hint=None, is_log=False) -> list:
    # MACD 为负数（在 最近 count 天数内 high 和 low 的 diffratio 不超过 限制）
    funcname = is_macd_negative.__name__
    return [

        # 零轴以上
        # qls0.is_col_valuelimit_1(df_indicator, "macdbar(12,26,9)", row_begin, 1,
        #                          0.01, 99.0,
        #                          hint=__hint(hint, funcname), is_log=is_log),
        # qls0.is_col_valuelimit_1(df_indicator, "macdbar(12,26,9)", row_begin, row_count,
        #                          0.01, 99.0,
        #                          hint=__hint(hint, funcname), is_log=is_log),
        qls0.is_range_1_valuelimit_2(df_indicator, "macdbar(12,26,9)", row_begin, 1, row_count,
                                     "min", "min", -99, -0.01,
                                     hint=__hint(hint, funcname), is_log=is_log),
        # high low 差异比率
        qls0.is_range_1_diffratio_2(df_indicator, "macdbar(12,26,9)", row_begin, 1, row_count,
                                    "max", "min", 0, high_low_diffratio_max,
                                    hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_macd_rise(df_indicator: pd.DataFrame, row_begin, row_count,
                 hint=None, is_log=False) -> list:
    # MACD BAR 斜率向上
    funcname = is_macd_rise.__name__
    return [

        # macdbar[n](12,26,9) < macdbar[1](12,26,9)
        qls0.is_row_large_1(df_indicator, "macdbar(12,26,9)", row_begin, 1, row_count,
                            hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_macd_rise_adjacent_zero(df_indicator: pd.DataFrame, row_begin,
                               zero_limit_l, zero_limit_h,
                               hint=None, is_log=False) -> list:
    # MACD的DIF和DEA零轴 ±xxx 内形成金叉（DIF数值≥DEA数值） note：实现上转化为 "macd上涨接近零轴"
    funcname = is_macd_rise_adjacent_zero.__name__
    return [

        # 零轴上下：-0.2 <= macddif1(12,26,9) <= 0.2
        qls0.is_row_valuelimit_1(df_indicator, "macddif(12,26,9)", row_begin, 1, 1,
                                 zero_limit_l, zero_limit_h,
                                 hint=__hint(hint, funcname), is_log=is_log),
        # 零轴上下：-0.2 <= macddea1(12,26,9) <= 0.2
        qls0.is_row_valuelimit_1(df_indicator, "macddea(12,26,9)", row_begin, 1, 1,
                                 zero_limit_l, zero_limit_h,
                                 hint=__hint(hint, funcname), is_log=is_log),
        # 已经上升：macdbar(12,26,9) > 0 ( note: < 99 )
        qls0.is_col_valuelimit_1(df_indicator, "macdbar(12,26,9)", row_begin, 1,
                                 0, 99,
                                 hint=__hint(hint, funcname), is_log=is_log),
    ]


# todo: test:
def is_macd_gold_cross(df_indicator: pd.DataFrame, row_begin,
                       row_count_start, row_count_stop,
                       hint=None, is_log=False) -> list:
    # MACD的DIF和DEA形成金叉
    funcname = is_macd_gold_cross.__name__
    return [

        # 现在已经上升：macdbar1(12,26,9) > 0 ( note: < 99 )
        qls0.is_col_valuelimit_1(df_indicator, "macdbar(12,26,9)", row_begin, 1,
                                 0, 99,
                                 hint=__hint(hint, funcname), is_log=is_log),
        # 以前存在下降：min( macdbar[2:5](12,26,9) ) < 0
        qls0.is_range_1_valuelimit_2(df_indicator, "macdbar(12,26,9)", row_begin, row_count_start, row_count_stop,
                                     "min", "min", -99, 0,
                                     hint=__hint(hint, funcname), is_log=is_log),
    ]


def is_shape_of_upper_shadow_line(df_indicator: pd.DataFrame, row_begin,
                                  hint=None, is_log=False) -> list:
    # 形态：上影线
    funcname = is_shape_of_upper_shadow_line.__name__

    class Param(Enum):
        ratio_hm_ml_l = 1.0  # (high-middle)/(middle-low) 比率下限
        ratio_hm_ml_h = 99.0  # (high-middle)/(middle-low) 比率上限
        ratio_hc_cl_l = 1.5  # (high-close)/(close-low) 比率下限
        ratio_hc_cl_h = 99.0  # (high-close)/(close-low) 比率上限
        ratio_ho_ol_l = 1.5  # (high-open)/(open-low) 比率下限
        ratio_ho_ol_h = 99.0  # (high-open)/(open-low) 比率上限

    return [
        # middle 判断
        # diff( high1, avg(open1,close1)) >> diff( avg(open1, close1), low1 )
        qls0.is_col_splitdiffratio_2(df_indicator, ["open", "close"], "high", "low", row_begin, 1,
                                     "mean", "mean", "mean",
                                     __enum_val(Param.ratio_hm_ml_l), __enum_val(Param.ratio_hm_ml_h),
                                     hint=__hint(hint, funcname), is_log=is_log),
        # open 和 close 不能过于接近 high 和 low
        qls0.is_col_splitdiffratio_2(df_indicator, "close", "high", "low", row_begin, 1,
                                     "mean", "mean", "mean",
                                     __enum_val(Param.ratio_hc_cl_l), __enum_val(Param.ratio_hc_cl_h),
                                     hint=__hint(hint, funcname), is_log=is_log),
        qls0.is_col_splitdiffratio_2(df_indicator, "open", "high", "low", row_begin, 1,
                                     "mean", "mean", "mean",
                                     __enum_val(Param.ratio_ho_ol_l), __enum_val(Param.ratio_ho_ol_h),
                                     hint=__hint(hint, funcname), is_log=is_log),
    ]

############################################
