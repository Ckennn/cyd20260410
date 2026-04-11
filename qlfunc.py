# coding=utf-8
"""
通用方法
"""

import math

from typing import Union, Optional, Any
import pandas as pd
import numpy as np

import dfutil
import qldebug
import qldef
# import qlmarket

"""
"""


################################################################

# @qloption.memory_model.cache # note: 太多文件了，不要cache
def msg(hint=None,
        market=None, target=None, date=None, channel=None, transid=None, idx=None,
        transaction_model=None,
        when=None, category=None, sector=None, goodtype=None, gooddist=None,
        ):
    return f"{hint if hint is not None else ''}" + \
           f"(" \
           f"{market},{target}" \
           f"{f',{date}' if date is not None else ''}" \
           f"{f',{channel}' if channel is not None else ''}" \
           f"{f',{transid}' if transid is not None else ''}" \
           f"{f',{idx}' if idx is not None else ''}" \
           f"{f',{transaction_model}' if transaction_model is not None else ''}" \
           f"{f',{when}' if when is not None else ''}" \
           f"{f',{category}' if category is not None else ''}" \
           f"{f',{sector}' if sector is not None else ''}" \
           f"{f',{goodtype}' if goodtype is not None else ''}" \
           f"{f',{gooddist}' if gooddist is not None else ''}" \
           f")"


################################################################

def select_df(
        df_select: pd.DataFrame,
        #
        market: Optional[str] = None,
        target: Optional[str] = None,
        target_list: Optional[list[str]] = None,
        date: Optional[int] = None,
        date_begin: Optional[int] = None,
        date_end: Optional[int] = None,
        date_list: Optional[list[int]] = None,
        unit: Optional[int] = None,
        unit_begin: Optional[int] = None,
        unit_end: Optional[int] = None,
        unit_list: Optional[list[int]] = None,
        signal: Optional[str] = None,
        signal_list: Optional[list[str]] = None,
        bin_col_str_dict: dict[str, str] = None,
        #
        return_col_list: list[str] = None,
        #
        sort_asc_col_or_list: Optional[Union[str, list[str]]] = None,
        sort_dec_col_or_list: Optional[Union[str, list[str]]] = None,
        #
        col_market="market",
        col_target="target",
        col_date="date",
        col_unit="unit",
        col_signal="signal",
        #
        hint=None,
        is_log=qldebug.log_df_select,
) -> Optional[pd.DataFrame]:
    funcname = dfutil.funcname(select_df, hint)
    #
    if dfutil.empty(df_select):
        return None
    #
    log_list = []
    __log = lambda __str: log_list.append(__str if is_log else None)

    def __check_date(val_or_list) -> bool:
        return all([
            False if False
            else True if (dfutil.empty(val) or dfutil.is_date(val))
            else dfutil.fatal_exit(f"{funcname}, check: {val=}, {dfutil.is_date(val)=}", return_value=False)
            for val in (dfutil.convert_to_list(val_or_list))
        ])

    def __check_unit(val_or_list) -> bool:
        return all([
            False if False
            else True if (dfutil.empty(val) or dfutil.is_timestamp(val))
            else dfutil.fatal_exit(f"{funcname}, check: {val=}, {dfutil.is_timestamp(val)=}", return_value=False)
            for val in (dfutil.convert_to_list(val_or_list))
        ])

    def __str_equal(df, col, val):
        if (val is not None) and len(val):
            df = df[df[col] == val]
            __log(f"{col}={val}")
        return df

    def __int_equal(df, col, val, check_func=None):
        dfutil.not_empty(check_func) and check_func()
        if (val is not None) and (val != 0):
            df = df[df[col] == val]
            __log(f"{col}={val}")
        return df

    def __int_largeequal(df, col, val, check_func=None):
        dfutil.not_empty(check_func) and check_func()
        if (val is not None) and (val != 0):
            df = df[df[col] >= int(val)]
            __log(f"{col}_begin={val}")
        return df

    def __int_lessequal(df, col, val, check_func=None):
        dfutil.not_empty(check_func) and check_func()
        if (val is not None) and (val != 0):
            df = df[df[col] <= int(val)]
            __log(f"{col}_end={val}")
        return df

    def __list_in(df, col, val, check_func=None):
        dfutil.not_empty(check_func) and check_func()
        if (val is not None) and (len(val) > 0):
            df = df[df[col].isin(val)]
            __log(f"{col}_list={val}")
        return df

    def __bin_str_equal(df, col_2_val):
        # note: 特定bin的数据（"*"通配，不过滤）
        for col in (col_2_val or {}):
            val = col_2_val[col]
            df = df[df[col] == val] if val != "*" else df
        return df

    #
    df_result = df_select
    df_result = __str_equal(df_result, col_market, market)
    df_result = __str_equal(df_result, col_target, target)
    df_result = __list_in(df_result, col_target, target_list)
    df_result = __int_equal(df_result, col_date, date, check_func=lambda: __check_date(date))
    df_result = __int_largeequal(df_result, col_date, date_begin, check_func=lambda: __check_date(date_begin))
    df_result = __int_lessequal(df_result, col_date, date_end, check_func=lambda: __check_date(date_end))
    df_result = __list_in(df_result, col_date, date_list, check_func=lambda: __check_date(date_list))
    df_result = __int_equal(df_result, col_unit, unit, check_func=lambda: __check_unit(unit))
    df_result = __int_largeequal(df_result, col_unit, unit_begin, check_func=lambda: __check_unit(unit_begin))
    df_result = __int_lessequal(df_result, col_unit, unit_end, check_func=lambda: __check_unit(unit_end))
    df_result = __list_in(df_result, col_unit, unit_list, check_func=lambda: __check_unit(unit_list))
    df_result = __str_equal(df_result, col_signal, signal)
    df_result = __list_in(df_result, col_signal, signal_list)
    df_result = __bin_str_equal(df_result, bin_col_str_dict)
    #
    if (return_col_list is not None) and (len(return_col_list) > 0):
        cl = dfutil.sub_list_contain_by_arg(return_col_list, df_result.columns.to_list())
        df_result = df_result[cl] if dfutil.not_empty(cl) else None  # note：没有需要的字段时返回None
        __log(f"{return_col_list=}")
    #
    if sort_asc_col_or_list is not None:
        df_result = df_result.sort_values(by=sort_asc_col_or_list, ascending=True)
        __log(f"{sort_asc_col_or_list=}")
    if sort_dec_col_or_list is not None:
        df_result = df_result.sort_values(by=sort_dec_col_or_list, ascending=False)
        __log(f"{sort_dec_col_or_list=}")
    #
    is_log and dfutil.not_empty(log_list) and dfutil.log(
        f"{funcname}, {dfutil.join_str_none_empty(', ', log_list)}, {dfutil.pd_len_repr(df_result)=}"
    )
    #
    return df_result


################################################################

def is_timestamp_reach(
        market,
        quote_timestamp: Optional[int],
        begin_timestamp: Optional[int],
        duration_second: Optional[Union[int, float]]
) -> bool:
    # note: 参数 None 时返回 True（从而支持 None 配置）
    return True if dfutil.any_empty(quote_timestamp, begin_timestamp, duration_second) else \
        dfutil.is_duration_reach_by_timestamp(
            # 暂时不用这个方法 delete by hhx 2024.07.24
            # begin_timestamp, quote_timestamp, duration_second, timezone_str=qlmarket.to_market_timezone(market)
        )


################################################################

def val_money_by_key(kv_dict: dict, key_money, default_key_price, default_key_count) -> float:
    # 可能money字段不存在
    return None if False \
        else kv_dict[key_money] if key_money in kv_dict \
        else kv_dict[default_key_price] * kv_dict[default_key_count]


def val_money_by_val(kv_dict: dict, key_money, default_val_price, default_val_count) -> float:
    # 可能money字段不存在
    return None if False \
        else kv_dict[key_money] if key_money in kv_dict \
        else default_val_price * default_val_count


################################################################

def is_value_down(value: float, ratio_down: float = None) -> bool:
    value_down = calc_value_down(value, ratio_down)
    return value < value_down


def calc_value_down(value: float, ratio_down: float, default: Any = float("-inf")) -> float:
    """ 向下变化 (note：ratio_down 负数，None 表示无效）"""
    result_value = None if False \
        else value * (1 + dfutil.negative_safe(ratio_down)) if dfutil.not_empty(ratio_down) \
        else default  # todo: impl: None表示无效
    return result_value


def is_value_rise(value: float, ratio_rise: float) -> bool:
    value_rise = calc_value_rise(value, ratio_rise)
    return value_rise < value


def calc_value_rise(value: float, ratio_rise: float, default: Any = float("inf")) -> float:
    """ 向上变化 (note：ratio_rise 正数，None 表示无效）"""
    result_value = None if False \
        else value * (1 + dfutil.positive_safe(ratio_rise)) if dfutil.not_empty(ratio_rise) \
        else default  # todo: impl: None表示无效
    return result_value


def calc_value_change(value: float, ratio_change: float, default: Any = None) -> float:
    """ value 变化 (note：ratio_change 正数 or 负数，None 表示无效）"""
    result_value = None if False \
        else value * (1 + ratio_change) if dfutil.not_empty(ratio_change) \
        else default  # todo: impl: None表示无效
    return result_value


################################################################

def calc_price_by(price: float, ratio: float) -> float:
    # note: 损失比率是负数，盈利比率是正数
    # return price * (1 + ratio)
    return calc_value_change(price, ratio, default=None)


def calc_price_rise(price: float, gain_ratio: float) -> float:
    # sell_price = buy_price * (1 + dfutil.positive_safe(gain_ratio))
    # return sell_price
    return calc_value_rise(price, gain_ratio, default=None)


def calc_price_down(price: float, lose_ratio: float) -> float:
    # sell_price = buy_price * (1 + dfutil.negative_safe(lose_ratio))
    # return sell_price
    return calc_value_down(price, lose_ratio, default=None)


def calc_mpc_money(price: float, count: int) -> float:
    # mpc = money price count
    return price * count


def calc_mpc_count(money: float, price: float) -> float:
    # mpc = money price count
    return money / price if price != 0 else 0


def calc_mpc_price(money: float, count: int) -> float:
    # mpc = money price count
    return money / count if count != 0 else 0


def calc_ohlcv_amount(hint,
                      ohlc_open: float, ohlc_high: float, ohlc_low: float, ohlc_close: float, volume: int,
                      is_log=False):
    # ohlcv = open high low close volume
    funcname = dfutil.funcname(
        calc_ohlcv_amount, hint,
        f"{ohlc_open=}", f"{ohlc_high=}", f"{ohlc_low=}", f"{ohlc_close=}", f"{volume=}"
    ) if is_log else None
    amount = volume * (ohlc_close + ohlc_high + ohlc_low) / 3
    is_log and dfutil.log(f"{funcname}, {amount=}")
    return amount


def calc_buy_count(money_limit: float, money_avail: float, buy_price: float, unit_per_hand: int) -> int:
    # 根据手数计算买入股数
    # note: 实盘发现程序退出，增加日志查看原因：ValueError: cannot convert float NaN to integer
    if dfutil.any_empty(money_limit, money_avail, buy_price, unit_per_hand):
        dfutil.trace(
            f"check: any_empty({money_limit=}, {money_avail=}, {buy_price=}, {unit_per_hand=})"
        )
    #
    result_buy_count = unit_per_hand * int(
        np.floor(np.min([money_limit, money_avail]) / (buy_price * unit_per_hand))
    )
    qldebug.log_func and dfutil.log(
        f"{money_limit=}, {money_avail=}, {buy_price=}, {unit_per_hand=}, {result_buy_count=}"
    )
    return result_buy_count


def calc_sell_count(total_count: int, sell_weight: float, unit_per_hand: int) -> int:
    # 根据权重计算卖出股数
    sell_count = np.ceil(total_count * sell_weight / unit_per_hand) * unit_per_hand
    return sell_count


def calc_buycount_buymoney_moneyavail_tokenavail(
        money_limit_max, money_limit_min, money_avail, token_avail, buy_price, unit_per_hand, hint
) -> [int, float, float, int]:
    funcname = dfutil.funcname(
        calc_buycount_buymoney_moneyavail_tokenavail, hint,
        f"{money_limit_max=}", f"{money_limit_min=}", f"{money_avail=}", f"{token_avail=}", f"{buy_price=}",
    )

    __zero = lambda __s: dfutil.warn(f"{funcname}, {__s}, set buy_count = 0", return_value=0)

    # 建仓数目
    buy_count = None if False \
        else __zero(f"{token_avail=} <= 0") if (token_avail <= 0) \
        else calc_buy_count(money_limit_max, money_avail, buy_price, unit_per_hand)
    buy_count = None if False \
        else __zero(f"{buy_count=} < {unit_per_hand=}") if (0 < buy_count < unit_per_hand) \
        else buy_count
    buy_count = None if False \
        else __zero(f"{buy_price=} * {buy_count=} < {money_limit_min=}") if (buy_price * buy_count < money_limit_min) \
        else buy_count
    (buy_count <= 0) and dfutil.warn(f"{funcname}, {buy_count=} <= 0")

    # 建仓金额
    buy_money = max(0, buy_price * buy_count)
    (buy_money <= 0) and dfutil.warn(f"{funcname}, {buy_money=} <= 0")

    # 剩余金额
    money_avail = max(0, money_avail - buy_money)
    (money_avail <= 0) and dfutil.warn(f"{funcname}, {money_avail=} <= 0")

    # 剩余标的
    token_avail = max(0, token_avail - 1) if buy_count > 0 else token_avail
    (token_avail <= 0) and dfutil.warn(f"{funcname}, {token_avail=} <= 0")

    return buy_count, buy_money, money_avail, token_avail


def calc_ratio_valid_middle_high_low(ratio_5, ratio_7, ratio_3) -> [bool, float, float, float]:
    """ 计算 middle,high,low
        # note: high 表示下跌后反弹到这里一定要买入，因为可能上涨了
                low  表示下跌到这里一定要买入，因为很难更低了
                middle 意义不大
    """
    funcname = dfutil.funcname(
        calc_ratio_valid_middle_high_low,
        f"{ratio_5=}", f"{ratio_7=}", f"{ratio_3=}",
    )

    # note: 可能存在5=7=3的情况，此时可能只有一条记录，那么过滤掉也是合理的，置信度不足

    is_valid = True

    def __invalid(hint):
        dfutil.trace(hint)
        nonlocal is_valid
        is_valid = False

    # ratio_low_5, ratio_low_7, ratio_low_3 都是负数
    dfutil.not_valid(ratio_3 <= ratio_5 <= ratio_7 <= 0) and __invalid(
        f"check: {ratio_3=} <= {ratio_5=} <= {ratio_7=} <= 0"
    )

    # note: 实盘发现，只有open/close时，相对容易到达5，但是还是存在低价高于5的情况(70%左右)，因此high稍微高一些，以便包括更多标的
    #       例如：cei, 20220510 的 buy_price_high = 0.560611883，而 20220512 的实际low为0.5661，高出 0.8%
    # result_h = ratio_low_5
    init_h = ratio_5
    delta_h = (ratio_7 - np.quantile([ratio_7, ratio_5], q=0.5))  # todo：impl：q可以学习（q越大越趋于rl7）
    result_h = init_h + delta_h
    dfutil.log(f"{funcname}, {init_h=}, {delta_h=}, {result_h=}")

    # note: 实盘发现，只有open/close时，比较难到达3
    init_m = ratio_3
    delta_m = 0
    result_m = init_m + delta_m
    dfutil.log(f"{funcname}, {init_m=}, {delta_m=}, {result_m=}")

    # 比3再低5和3差值的一半
    init_l = ratio_3
    delta_l = 0 - (ratio_5 - np.mean([ratio_5, ratio_3]))
    result_l = init_l + delta_l
    dfutil.log(f"{funcname}, {init_l=}, {delta_l=}, {result_l=}")

    # result_m, result_h, result_l 都是负数
    dfutil.not_valid(result_l <= result_m <= result_h <= 0) and __invalid(
        f"check: {result_l=} <= {result_m=} <= {result_h=} <= 0"
    )

    return is_valid, result_m, result_h, result_l


################################################################


# 向下取整，防止和阈值比较时出现不合理情况
# note: 有些取值差异较大，例如 e2gr3 = 0.00001, e2lr3 = -0.03851, 取整倍数如果较小，则multiple结果为0，不合理
__multi_floor: int = 10000


# todo: impl: probe_good中倍数需要替换为float_multiple_2（g和l的数值较小时，比较结果更加明显）
def float_multiple_1(val_g: float, val_l: float) -> float:
    """ 倍数（g/l）
        取值 大于 1，表示g好于l（越大则g越好）
        取值 等于 1，表示g等于l
        取值 0 到-1，表示l好于g（越大越接近0则l越好）
        如果g为0而l非0，则取值-inf
        如果g非0而l为0，则取值inf
        如果g为0而l为0，则取值0
    """
    # todo: 替换inf为99，替换-inf为-99，调整所有取值范围在-99到99之间
    abs_g = abs(val_g)
    abs_l = abs(val_l)
    multi = dfutil.to_divide(abs_g, abs_l,
                             default_n0d0=0,
                             default_n0d1=float("-inf"),
                             default_n1d0=float("inf"),
                             is_log=qldebug.log_func
                             )
    if np.isnan(multi):  # nan 直接返回吧
        return np.nan
    if (multi != float("inf")) and (multi != float("-inf")):
        multi = math.floor(multi * __multi_floor) / __multi_floor  # 向下取整，防止和阈值比较时出现不合理情况
    if (abs_g < abs_l) and (val_l < 0) and (multi > 0):
        return -1 * multi  # 负数大时，返回负数
    return multi


def float_multiple_2(val_g: float, val_l: float) -> float:
    """ 倍数（g/l，或者，l/g）
        取值 大于 1，表示g好于l（越大则g越好）
        取值 等于 1，表示g等于l
        取值 小于-1，表示l好于g（越小则l越好）
        如果g为0而l非0，则取值-inf
        如果g非0而l为0，则取值inf
        如果g为0而l为0，则取值0
    """
    # todo: 替换inf为99，替换-inf为-99，调整所有取值范围在-99到99之间
    abs_g = abs(val_g)
    abs_l = abs(val_l)
    if (abs_g == 0) and (abs_l == 0):
        multi = 0
    elif abs_g >= abs_l:
        if abs_l == 0:
            multi = float("inf")
        else:
            multi = abs_g / abs_l
    else:
        if abs_g == 0:
            multi = float("-inf")
        else:
            multi = abs_l / abs_g * -1
    if np.isnan(multi):  # nan 直接返回吧
        return np.nan
    if (multi != float("inf")) and (multi != float("-inf")):
        multi = math.floor(multi * __multi_floor) / __multi_floor  # 向下取整，防止和阈值比较时出现不合理情况
    # if abs_g < abs_l and val_l < 0 and multi > 0:
    #     return -1 * multi  # 负数大时，返回负数
    return multi


def str_multiple_float(val_g: float, val_l: float) -> str:
    """倍数"""
    if val_g is None or np.isnan(val_g) or val_l is None or np.isnan(val_l):
        return "***.*"
    elif val_g > 0 and val_l == 0:  # 只有盈利没有损失
        return "+++.+"
    elif val_g == 0 and val_l < 0:  # 没有盈利只有损失
        return "---.-"
    elif val_g == 0 and val_l == 0:  # 没有盈利没有损失
        return "000.0"

    abs_g = abs(val_g)
    abs_l = abs(val_l)
    multi = dfutil.to_divide(abs_g, abs_l, is_log=qldebug.log_func)
    multi = math.floor(multi * __multi_floor) / __multi_floor  # 向下取整，防止和阈值比较时出现不合理情况
    if multi < 100:
        if abs_g >= abs_l:
            return "{:+>5.1f}".format(multi)  # 盈利大于损失
        else:
            return "{:->5.1f}".format(multi)  # 损失大于盈利
    else:
        if abs_g >= abs_l:
            return "{:+>5.0f}".format(multi)  # 盈利大于损失
        else:
            return "{:->5.0f}".format(multi)  # 损失大于盈利


def return_islimit_multiple(val_g: float, val_l: float, limit_l: float = -99, limit_h: float = 99) -> [bool, float]:
    """是否超过limit，倍数"""
    if val_g is None or np.isnan(val_g) or val_l is None or np.isnan(val_l):
        return False, 0
    elif val_g > 0 and val_l == 0:  # 只有盈利没有损失
        return True, limit_h
    elif val_g == 0 and val_l < 0:  # 没有盈利只有损失
        return True, limit_l
    elif val_g == 0 and val_l == 0:  # 没有盈利没有损失
        return False, 0

    abs_g = abs(val_g)
    abs_l = abs(val_l)
    multi = dfutil.to_divide(abs_g, abs_l, is_log=qldebug.log_func)
    if abs_g >= abs_l:
        return False, +multi  # 盈利大于损失
    else:
        return False, -multi  # 损失大于盈利


def float_ratio(val_n: float, val_d: float, default=np.nan) -> float:
    """比率，n/d（分子 numerator, 分母 denominator）"""
    if dfutil.any_empty(val_n, val_d):
        dfutil.warn(f"{float_ratio.__name__}, check: any_empty({val_n=}, {val_d=})")
        return default
    return dfutil.to_divide(val_n, val_d, is_log=qldebug.log_func)


def str_ratio_1(val_n: float, val_d: float) -> str:
    """比率，n/d（分子 numerator, 分母 denominator）"""
    return str_sign_float(dfutil.to_divide(val_n, val_d, is_log=qldebug.log_func))


def str_ratio_2(val_r: float) -> str:
    """比率，n/d（分子 numerator, 分母 denominator）"""
    return str_sign_float(val_r)


def float_diff_ratio(val_a: float, val_b: float) -> float:
    """差值比率，(n-d)/d（分子 numerator, 分母 denominator）"""
    return np.nan if dfutil.any_none(val_a, val_b) \
        else dfutil.to_divide(val_a - val_b, val_b, is_log=qldebug.log_func)


def str_diff_ratio(val_a: float, val_b: float) -> str:
    """差值比率，(n-d)/d（分子 numerator, 分母 denominator）"""
    val_result = None if dfutil.any_none(val_a, val_b) \
        else dfutil.to_divide(val_a - val_b, val_b, is_log=qldebug.log_func)
    return str_sign_float(val_result)


def str_diff_percent(val_a: float, val_b: float, is_sign=True) -> str:
    """差值比率，(n-d)/d（分子 numerator, 分母 denominator）"""
    val_result = None if dfutil.any_none(val_a, val_b) \
        else dfutil.to_divide(val_a - val_b, val_b, is_log=qldebug.log_func)
    return str_percent_1(val_result, is_sign=is_sign)


def str_percent_1(val_r: float, is_percent_already=False, is_sign=True) -> str:
    """百分比，r比率"""
    if val_r is None or np.isnan(val_r):
        return "***.**%"

    if is_percent_already:
        val_r /= 100

    if not is_sign:
        return "{:0>6.2%}".format(val_r)

    if -1 < val_r < 1:
        if val_r < 0:
            return "{:->+7.2%}".format(val_r)
        else:
            return "{:+>+7.2%}".format(val_r)
    else:  # 超出100%的小数点后少显示，保持长度对齐
        if val_r < 0:
            return "{:->+7.1%}".format(val_r)
        else:
            return "{:+>+7.1%}".format(val_r)


def str_percent_2(val_n: float, val_d: float, is_sign=True) -> str:
    """百分比，n/d（分子 numerator, 分母 denominator）"""
    return str_percent_1(dfutil.to_divide(val_n, val_d, is_log=qldebug.log_func), is_sign=is_sign)


def str_rank_int(val_r: int) -> str:
    """排行整数"""
    if val_r is None or np.isnan(val_r):
        return "**"
    return "{:0>2.0f}".format(val_r)


def str_count_int(val_c: int, justify_char=None, str_len=4) -> str:
    """数目整数"""
    if val_c is None or np.isnan(val_c):
        return "*".rjust(str_len, "*")
    if justify_char is None:
        return f"{val_c:0>{str_len}.0f}"
    return f"{val_c:>.0f}".rjust(str_len, justify_char)


def float_value_w(val_v: float, ) -> float:
    """数值（万）"""
    return val_v / 10000


def int_value_w(val_v: float, ) -> int:
    """数值（万）"""
    return int(val_v / 10000)


def str_value_w(val_v: float, justify_char=None, ) -> str:
    """数值（万）"""
    if val_v is None or np.isnan(val_v):
        return "******"
    w = val_v / 10000
    if justify_char is None:
        return f"{w:0>5.0f}W"
    return f"{w:>.0f}".rjust(6, justify_char) + "W"


def float_value_m(val_v: float, ) -> float:
    """数值（百万）"""
    return val_v / (10000 * 100)


def int_value_m(val_v: float, ) -> int:
    """数值（百万）"""
    return int(val_v / (10000 * 100))


def str_value_m(val_v: float, justify_char=None, ) -> str:
    """数值（百万）"""
    if val_v is None or np.isnan(val_v):
        return "***"
    m = val_v / (10000 * 100)
    if justify_char is None:
        return f"{m:0>3.0f}M"
    return f"{m:>.0f}".rjust(3, justify_char) + "M"


def float_value_y(val_v: float, ) -> float:
    """数值（亿）"""
    return val_v / qldef.num_y


def int_value_y(val_v: float, ) -> int:
    """数值（亿）"""
    return int(val_v / qldef.num_y)


def str_value_y(val_v: float, justify_char=None, ) -> str:
    """数值（亿）"""
    if val_v is None or np.isnan(val_v):
        return "***"
    y = val_v / qldef.num_y
    len_total = 3
    len_decimal = 1
    pad_char = justify_char or "0"
    return f"{y:{pad_char}>{len_total}.{len_decimal}f}Y"


def str_sign_int(val_r: int) -> str:
    """符号整数"""
    if val_r is None or np.isnan(val_r):
        return "***"
    elif val_r < 0:
        return "{:->+3.0f}".format(val_r)
    else:
        return "{:+>+3.0f}".format(val_r)


def str_sign_float(val_r: float, fmt_width: int = 5, fmt_precision: int = 2) -> str:
    """小数"""
    if val_r is None or np.isnan(val_r):
        # "***.**"
        return dfutil.pad_str_right('*', fmt_width - 1 - fmt_precision, '*') \
               + "." \
               + dfutil.pad_str_right('*', fmt_precision, '*')
    elif val_r < 0:
        return f"{val_r:->+{fmt_width}.{fmt_precision}f}"
    else:
        return f"{val_r:+>+{fmt_width}.{fmt_precision}f}"


def str_date_count(val_c: float) -> str:
    """天数"""
    if val_c is None or np.isnan(val_c):
        return "**"
    else:
        return "{:0>2.0f}".format(val_c)


def str_price_float_1(val_p: float, is_justify=True) -> str:
    """价格"""
    if val_p is None or np.isnan(val_p):
        return "*****.***"
    else:
        return "{: >8.3f}".format(val_p) if is_justify \
            else "{:.3f}".format(val_p)


def str_price_float_2(val_p: float) -> str:
    return str_price_float_1(val_p, is_justify=False)


def str_price_float_2_for_list(val_p_list: list[float]) -> list[str]:
    if dfutil.empty(val_p_list):
        return []
    return [str_price_float_1(val_p, is_justify=False) for val_p in val_p_list]


def str_price_int_1(val_p: float, is_justify=True) -> str:
    """价格"""
    if val_p is None or np.isnan(val_p):
        return "*****"
    else:
        return "{: >5.0f}".format(val_p) if is_justify \
            else "{:.0f}".format(val_p)


def str_price_int_2(val_p: float) -> str:
    return str_price_int_1(val_p, is_justify=False)


################################################################


def to_str_or_none(s: Optional[str]) -> str:
    # 如果s空则返回"none"
    return dfutil.str_safe(s, "none")


def from_str_or_none(s) -> Optional[str]:
    # 如果s为"none"则返回空
    return None if s == "none" else s


################################################################

# 程序内校验时，防止过于频繁
def is_check_timestamp():
    return (dfutil.timestamp_yyyymmddhhmmss() % 100) < 5


def check_col_exist(df: pd.DataFrame, col_or_list: list[str], hint=None):
    col_list = dfutil.convert_to_list(col_or_list)
    miss_col_list = dfutil.sub_list_exclude(col_list, df.columns.to_list())
    # todo: impl: qloption.fatal_exit 会循环包引用
    dfutil.not_empty(miss_col_list) and dfutil.fatal_exit(
        f"check: {miss_col_list=}, {dfutil.name_safe(hint)}", return_value=False
    )


def check_col_not_exist(df: pd.DataFrame, col_or_list: Union[str, list[str]], hint=None):
    col_list = dfutil.convert_to_list(col_or_list)
    # todo: impl: qloption.fatal_exit 会循环包引用
    dfutil.is_pd_col_list(df, col_list) and dfutil.fatal_exit(
        f"check: {col_list} not exist, {dfutil.name_safe(hint)}, {dfutil.pd_col_list_1(df)=}"
    )


def check_equal(val_a, val_b, hint=None):
    # todo: impl: qloption.fatal_exit 会循环包引用
    dfutil.not_valid(val_a == val_b) and dfutil.fatal_exit(
        f"check: {val_a} == {val_b}, {dfutil.name_safe(hint)}"
    )

################################################################
