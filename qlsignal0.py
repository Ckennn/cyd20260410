# coding=utf-8
"""
策略（通用方法）
"""

import sys

from typing import Optional
import pandas as pd
import numpy as np

import dfutil
import qldebug
import qldef
import qloption

"""
    策略与问题
"""
# todo: 自适应参数：通过机器学习来调整这里的参数和判断条件
# todo: 提高性能：替换为 np 的 array 操作，包括 isclose 等
# todo: 提高性能：频繁的计算操作，变为指标，放置到indicator中预先计算
# todo: 增加signal：ema11高于ema22时，价格上超ema后持续下行，本日收盘接近或低于ema11
# todo: 增加signal：ema向上ema11大于ema22并持续加宽。是否需要？
# todo: 计算指标：signal出现后，如果低于ema，那么距离ema有多大的ratio？这个可能是幅度上限
# todo: impl: 将旧的param都调整为qldebug.var格式

################################
"""
    var 名称规范
        x           x 今天（即 x1，即 x1p，即 x1n）
        x[n]        x 今天之前的第 n-1 天（省略了 x[n]p 中的 p ）
        x[n]p       x 今天之前的第 n-1 天
        x[n]n       x 今天之后的第 n-1 天
    var 运算符号
        =           等于
        >           大于
        <           小于
        ~           约等于
        >>          远大于
        <<          远小于
"""
"""
    其它变量的名称定义
    ema        
        emaf = ema_fast = ema(11) 
        emas = ema_slow = ema(22)
"""

############################################

# 策略名称列表

# __the_name_2_module: dict[str, str] = {}
__the_symbol_2_model: dict[str, str] = {}
__the_symbol_2_name_list: dict[str, list[str]] = {}


# signal_symbol 用于区分不同的 策略，对于caochen策略来说，就是“sigcaochen” - 其他可以删除吧 note by hhx 2024.07.24
def list_signal(signal_symbol: str) -> list[str]:
    #
    if qldef.is_signal_symbol_all(signal_symbol):
        return dfutil.merge_list_list(dfutil.to_dict_val_list_by_key_prefix(__the_symbol_2_name_list, None))
    #

    signal_name_list = dfutil.to_dict_val(__the_symbol_2_name_list, signal_symbol)

    if dfutil.not_empty(signal_name_list):
        return signal_name_list
    # 由于业务逻辑异常，无法回复，然后发送通知邮件或短信，然后退出程序（这里可以简化为直接退出程序）note by hhx 2024.07.22
    return qloption.notify_unsupported_exit(f"{signal_symbol=}")


# 对于 signal_name 来说，取值可以是具体的方法名称了，例如上面的代码里，就是 “caochen_volume_bloom_above_bottom_x_20220915”
# 对于 abbr_signal 来说，是 signal_name 的缩写，因为 name 太长了，我们用 abbr 会更简单【注意：新增加 的 方法，abbr 后需要唯一（保证我们数据字段处理上比较简单），
# abbr_signal 方法会判断唯一性，不唯一时报错退出。比如例如 caochen_volume_bloom_above_bottom_x_20220915 进行 abbr 后应该是 cvbabx20220915】
# 缩写的代码 在 abbr_signal 中有实现，那么，以后你们写新策略时，会比较简单 note by hhx 2024.07.22
# 比如：1. 在 qlsignalcaochen 中增加一个新方法；2. 对这个新方法，用 anno_signal 进行注册；3. 调用 list_signal 就可以获得所有注册的 方法名称了，即 signal_name；
# 4. 通过 call_signal 可以调用某个方法。
def abbr_signal(signal_name: str) -> str:
    # note: 保持x不变吧，"." 容易混淆
    # note: python 方法名称不能为特殊符号，因此采用 "_x_" 表示分隔符，缩写时替换为 "."
    return "".join([
        (
            None if False
            else "x" if x == "x"  # else "." if x == "x"  # note: 保持x不变吧，"." 容易混淆
            else x if dfutil.is_int(x)
            else x[0]
        )
        for x in signal_name.split("_")
    ])


def call_signal(
        signal_symbol: str, signal_name: str, df_indicator: Optional[pd.DataFrame], row_begin: int,
        is_exception_exit=True, default=(False, None, None, None),
) -> [bool, str, dict, list[dict]]:
    funcname = call_signal.__name__
    try:
        # module = dfutil.to_dict_val(__the_name_2_module, signal_name)
        # dfutil.empty(module) and dfutil.warn(f"{funcname}, {module=} empty, {signal_name=}, {__the_name_2_module=}")
        module = dfutil.to_dict_val(__the_symbol_2_model, signal_symbol)
        dfutil.empty(module) and dfutil.warn(f"{funcname}, {module=} empty, {signal_name=}, {__the_symbol_2_model=}")
        #
        impl_func = getattr(sys.modules[module], "%s" % signal_name)
        dfutil.empty(impl_func) and dfutil.warn(f"{funcname}, {impl_func=} empty, {signal_name=}")
        #
        # if impl_func is not None:
        return impl_func(df_indicator, row_begin)
        #
    except Exception as err:
        dfutil.exception(err, f"{signal_name=}, {dfutil.pd_head(df_indicator)=}, {row_begin=}")

    if is_exception_exit:
        return qloption.notify_fatal_exit(f"{funcname}, check: {signal_name=} invalid")
    else:
        return dfutil.error(f"{funcname}, default, {signal_name=}", return_value=default)


def anno_signal(module_name: str, signal_symbol: str, is_enable: bool = True):
    funcname = anno_signal.__name__

    def annotation(func):
        signal_name = func.__name__

        if not is_enable:
            qldebug.log_signal_register and dfutil.log(
                f"{funcname}, ignore, {module_name=}, {signal_symbol=}, {is_enable=}"
            )

        else:
            if signal_symbol not in __the_symbol_2_name_list:
                __the_symbol_2_name_list[signal_symbol] = []
            signal_name_list = __the_symbol_2_name_list[signal_symbol]

            (signal_name in signal_name_list) and qloption.notify_fatal_exit(
                f"check: dup signal name, {signal_symbol=} {signal_name=}"
            )

            signal_name_list.append(signal_name)

            abbr_list = [abbr_signal(name) for name in signal_name_list]
            (len(signal_name_list) != len(abbr_list)) and qloption.notify_fatal_exit(
                f"check: dup signal abbr, {signal_symbol=}, {signal_name=}, {signal_name_list=}"
            )

            # __the_name_2_module[signal_name] = module_name
            # qldebug.log_signal_register and dfutil.log(
            #     f"{__anno_signal.__name__}, registered, {module_name=}, {signal_symbol=}, {signal_name=}"
            # )
            __the_symbol_2_model[signal_symbol] = module_name
            qldebug.log_signal_register and dfutil.log(
                f"{funcname}, registered, {module_name=}, {signal_symbol=}, {signal_name=}"
            )

        return func

    return annotation


############################################

__enum_key = lambda __enum: __enum.name
__enum_val = lambda __enum: __enum.value
__enum_dict = lambda __enum: {x.name: x.value for x in __enum}

__hint = lambda __context, __current: dfutil.funcname(__context, __current)


def __date(df, row_index) -> Optional[int]:
    return df["date"].loc[row_index] if row_index <= df.index.max() else None


def __valid_value(df, col_name_or_list, row_index) -> [bool, float]:
    if dfutil.empty(df):
        qldebug.log_signal_valid_value and dfutil.log(f"check: df empty")
        return False, 0
    if row_index >= len(df):
        qldebug.log_signal_valid_value and dfutil.log(f"check: {row_index=} >= {len(df)=}")
        return False, 0

    #
    def __col(__df, __col_or_list, __index):
        if dfutil.of_list(__col_or_list):
            return np.mean([__df.loc[__index, x] for x in __col_or_list])
        else:
            return __df.loc[__index, __col_or_list]

    #
    val = __col(df, col_name_or_list, row_index)
    #
    #
    if np.isnan(val):
        qldebug.log_signal_valid_value and dfutil.log(f"check: {np.isnan(val)=}")
        return False, 0
    else:
        return True, val


def __valid_value_of_range(df, col_name_or_list, row_index_start, row_index_stop, row_dist) -> [bool, float]:
    if dfutil.empty(df):
        qldebug.log_signal_valid_value and dfutil.log(f"check: df empty")
        return False, 0
    if row_index_start >= len(df):
        qldebug.log_signal_valid_value and dfutil.log(f"check: {row_index_start=} >= {len(df)=}")
        return False, 0
    if row_index_stop >= len(df):
        qldebug.log_signal_valid_value and dfutil.log(f"check: {row_index_stop=} >= {len(df)=}")
        return False, 0

    #
    def __row(__df, __col, __index_start, __index_stop, __dist):
        # note: bug: pd 的 loc[start:stop]（闭区间） 与 iloc[start:stop] （左闭***右开***区间），不同
        if __dist == "min":
            # return __df.loc[__index_start:__index_stop + 1, __col].min()
            return __df.loc[__index_start:__index_stop, __col].min()
        elif __dist == "max":
            # return __df.loc[__index_start:__index_stop + 1, __col].max()
            return __df.loc[__index_start:__index_stop, __col].max()
        elif __dist == "mean":
            # return __df.loc[__index_start:__index_stop + 1, __col].mean()
            return __df.loc[__index_start:__index_stop, __col].mean()
        elif __dist == "median":
            # return __df.loc[__index_start:__index_stop + 1, __col].median()
            return __df.loc[__index_start:__index_stop, __col].median()
        else:
            return qloption.notify_unsupported_exit(f"{__dist=}", return_value=np.nan)

    #
    def __col(__val_or_list):
        if dfutil.of_list(__val_or_list):
            return np.mean(__val_or_list)
        else:
            return __val_or_list

    #
    if dfutil.of_list(col_name_or_list):
        val = __col([
            __row(df, col_name, row_index_start, row_index_stop, row_dist)
            for col_name in col_name_or_list
        ])
    else:
        col_name = col_name_or_list
        val = __col(
            __row(df, col_name, row_index_start, row_index_stop, row_dist)
        )
    #
    if np.isnan(val):
        qldebug.log_signal_valid_value and dfutil.log(f"check: {np.isnan(val)=}")
        return False, 0
    else:
        return True, val


############################################

def is_date_valid(df_indicator,
                  row_begin, row_count_1, row_count_2,
                  nature_date_count_max,
                  hint=None, is_log=False) -> bool:
    """ note: 标的存在停盘情况，时间太长，信号就不合理了 """
    funcname = is_date_valid.__name__

    if dfutil.empty(df_indicator):
        dfutil.warn(f"{funcname}, indicator empty, {hint=}")
        return False

    rangeindex_1 = row_begin + row_count_1 - 1
    rangeindex_2 = row_begin + row_count_2 - 1
    valid_min, date_min = __valid_value_of_range(df_indicator, "date", rangeindex_1, rangeindex_2, "min")
    valid_max, date_max = __valid_value_of_range(df_indicator, "date", rangeindex_1, rangeindex_2, "max")

    # todo: 性能提高，数据量大时 - is_in_date_nature_count 改为 in_date_count modify by hhx 2024.07.24
    check = dfutil.in_date_count(date_min, date_max, nature_date_count_max) \
        if (valid_min and valid_max) else False

    not check and qldebug.log_signal_valid_date and dfutil.warn(
        f"{__hint(hint, funcname)}, "
        f"{qloption.database.to_market_of(df_indicator)}, "
        f"{qloption.database.to_target_of(df_indicator)}, "
        f"{rangeindex_1}, {rangeindex_2}, {nature_date_count_max}, "
        f"{valid_min=}, {date_min=}, "
        f"{valid_max=}, {date_max=}, "
        f"{check=}, "
    )
    # not check and qldebug.log_signal_valid_date and dfutil.warn(
    #     f"{__hint(hint, funcname)}, "
    #     f"{rangeindex_1}, {rangeindex_2}, {nature_date_count_max}, "
    #     f"{valid_min=}, {date_min=}, "
    #     f"{valid_max=}, {date_max=}, "
    #     f"{check=}, "
    # )

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{rangeindex_1}, {rangeindex_2}, "
                               f"{valid_min=}, {date_min=}, "
                               f"{valid_max=}, {date_max=}, "
                               f"{check=}, "
                               )

    return check


# def __is_range_large_1(df_indicator,
#                        col_name_or_list,
#                        row_begin, row_count_1, row_count_2_start, row_count_2_stop, row_dist_2,
#                        hint=None,
#                        ) -> bool:
#     return __is_range_large_2(df_indicator,
#                               col_name_or_list_a=col_name_or_list, col_name_or_list_b=col_name_or_list,
#                               row_begin=row_begin,
#                               row_count_1=row_count_1,
#                               row_count_2_start=row_count_2_start,
#                               row_count_2_stop=row_count_2_stop,
#                               row_dist_2=row_dist_2,
#                               hint=hint)


def is_range_2_large_2(df_indicator,
                       col_name_or_list_a, col_name_or_list_b,
                       row_begin,
                       row_count_1,
                       row_count_2_start, row_count_2_stop, row_dist_2,
                       hint=None, is_log=False) -> bool:
    funcname = is_range_2_large_2.__name__

    #
    index_1 = row_begin + row_count_1 - 1
    index_1_date = __date(df_indicator, index_1)
    valid_1, val_1 = __valid_value(df_indicator, col_name_or_list_a, index_1)
    #
    range_start = row_begin + row_count_2_start - 1
    range_start_date = __date(df_indicator, range_start)
    range_stop = row_begin + row_count_2_stop - 1
    range_stop_date = __date(df_indicator, range_stop)
    range_dist = row_dist_2
    valid_2, val_2 = __valid_value_of_range(df_indicator, col_name_or_list_b, range_start, range_stop, range_dist)
    #
    check = valid_1 and valid_2 and (val_1 > val_2)

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index_1}({index_1_date}), {valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, {range_start}({range_start_date}), {range_stop}({range_stop_date}), "
                               f"{range_dist=}, {valid_2=}, {val_2=}, "
                               f"{check=}, "
                               )

    return check


def is_range_2_largeequal_2(df_indicator,
                            col_name_or_list_a, col_name_or_list_b,
                            row_begin,
                            row_count_1,
                            row_count_2_start, row_count_2_stop, row_dist_2,
                            hint=None, is_log=False) -> bool:
    funcname = is_range_2_largeequal_2.__name__

    #
    index_1 = row_begin + row_count_1 - 1
    index_1_date = __date(df_indicator, index_1)
    valid_1, val_1 = __valid_value(df_indicator, col_name_or_list_a, index_1)
    #
    range_start = row_begin + row_count_2_start - 1
    range_start_date = __date(df_indicator, range_start)
    range_stop = row_begin + row_count_2_stop - 1
    range_stop_date = __date(df_indicator, range_stop)
    range_dist = row_dist_2
    valid_2, val_2 = __valid_value_of_range(df_indicator, col_name_or_list_b, range_start, range_stop, range_dist)
    #
    check = valid_1 and valid_2 and (val_1 >= val_2)

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index_1}({index_1_date}), {valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, {range_start}({range_start_date}), {range_stop}({range_stop_date}), "
                               f"{range_dist=}, {valid_2=}, {val_2=}, "
                               f"{check=}, "
                               )

    return check


def is_range_2_largeequal_4(df_indicator,
                            col_name_or_list_a, col_name_or_list_b,
                            row_begin,
                            row_count_1_start, row_count_1_stop, row_dist_1,
                            row_count_2_start, row_count_2_stop, row_dist_2,
                            hint=None, is_log=False) -> bool:
    funcname = is_range_2_largeequal_4.__name__

    #
    range_1_start = row_begin + row_count_1_start - 1
    range_1_start_date = __date(df_indicator, range_1_start)
    range_1_stop = row_begin + row_count_1_stop - 1
    range_1_stop_date = __date(df_indicator, range_1_stop)
    range_1_dist = row_dist_1
    valid_1, val_1 = __valid_value_of_range(df_indicator, col_name_or_list_a, range_1_start, range_1_stop, range_1_dist)
    #
    range_2_start = row_begin + row_count_2_start - 1
    range_2_start_date = __date(df_indicator, range_2_start)
    range_2_stop = row_begin + row_count_2_stop - 1
    range_2_stop_date = __date(df_indicator, range_2_stop)
    range_2_dist = row_dist_2
    valid_2, val_2 = __valid_value_of_range(df_indicator, col_name_or_list_b, range_2_start, range_2_stop, range_2_dist)
    #
    check = valid_1 and valid_2 and (val_1 >= val_2)

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, "
                               f"{range_1_start}({range_1_start_date}), {range_1_stop}({range_1_stop_date}), {range_1_dist=}, "
                               f"{valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, "
                               f"{range_2_start}({range_2_start_date}), {range_2_stop}({range_2_stop_date}), {range_2_dist=}, "
                               f"{valid_2=}, {val_2=}, "
                               f"{check=}, "
                               )

    return check


# def __is_range_small_1(df_indicator,
#                        col_name_or_list,
#                        row_begin, row_count_1, row_count_2_start, row_count_2_stop, row_dist_2,
#                        hint=None,
#                        ) -> bool:
#     return __is_range_small_2(df_indicator,
#                               col_name_or_list_a=col_name_or_list, col_name_or_list_b=col_name_or_list,
#                               row_begin=row_begin,
#                               row_count_1=row_count_1,
#                               row_count_2_start=row_count_2_start,
#                               row_count_2_stop=row_count_2_stop,
#                               row_dist_2=row_dist_2,
#                               hint=hint)


def is_range_2_small_2(df_indicator,
                       col_name_or_list_a, col_name_or_list_b,
                       row_begin,
                       row_count_1,
                       row_count_2_start, row_count_2_stop, row_dist_2,
                       hint=None, is_log=False) -> bool:
    funcname = is_range_2_small_2.__name__

    #
    index_1 = row_begin + row_count_1 - 1
    index_1_date = __date(df_indicator, index_1)
    valid_1, val_1 = __valid_value(df_indicator, col_name_or_list_a, index_1)
    #
    range_start = row_begin + row_count_2_start - 1
    range_start_date = __date(df_indicator, range_start)
    range_stop = row_begin + row_count_2_stop - 1
    range_stop_date = __date(df_indicator, range_stop)
    range_dist = row_dist_2
    valid_2, val_2 = __valid_value_of_range(df_indicator, col_name_or_list_b, range_start, range_stop, range_dist)
    #
    check = valid_1 and valid_2 and (val_1 < val_2)

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index_1}({index_1_date}), {valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, {range_start}({range_start_date}), {range_stop}({range_stop_date}), "
                               f"{range_dist=}, {valid_2=}, {val_2=}, "
                               f"{check=}, "
                               )

    return check


def is_range_2_smallequal_2(df_indicator,
                            col_name_or_list_a, col_name_or_list_b,
                            row_begin,
                            row_count_1,
                            row_count_2_start, row_count_2_stop, row_dist_2,
                            hint=None, is_log=False) -> bool:
    funcname = is_range_2_smallequal_2.__name__

    #
    index_1 = row_begin + row_count_1 - 1
    index_1_date = __date(df_indicator, index_1)
    valid_1, val_1 = __valid_value(df_indicator, col_name_or_list_a, index_1)
    #
    range_start = row_begin + row_count_2_start - 1
    range_start_date = __date(df_indicator, range_start)
    range_stop = row_begin + row_count_2_stop - 1
    range_stop_date = __date(df_indicator, range_stop)
    range_dist = row_dist_2
    valid_2, val_2 = __valid_value_of_range(df_indicator, col_name_or_list_b, range_start, range_stop, range_dist)
    #
    check = valid_1 and valid_2 and (val_1 <= val_2)

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index_1}({index_1_date}), {valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, {range_start}({range_start_date}), {range_stop}({range_stop_date}), "
                               f"{range_dist=}, {valid_2=}, {val_2=}, "
                               f"{check=}, "
                               )

    return check


def is_range_2_smallequal_4(df_indicator,
                            col_name_or_list_a, col_name_or_list_b,
                            row_begin,
                            row_count_1_start, row_count_1_stop, row_dist_1,
                            row_count_2_start, row_count_2_stop, row_dist_2,
                            hint=None, is_log=False) -> bool:
    funcname = is_range_2_smallequal_4.__name__

    #
    range_1_start = row_begin + row_count_1_start - 1
    range_1_start_date = __date(df_indicator, range_1_start)
    range_1_stop = row_begin + row_count_1_stop - 1
    range_1_stop_date = __date(df_indicator, range_1_stop)
    range_1_dist = row_dist_1
    valid_1, val_1 = __valid_value_of_range(df_indicator, col_name_or_list_a, range_1_start, range_1_stop, range_1_dist)
    #
    range_2_start = row_begin + row_count_2_start - 1
    range_2_start_date = __date(df_indicator, range_2_start)
    range_2_stop = row_begin + row_count_2_stop - 1
    range_2_stop_date = __date(df_indicator, range_2_stop)
    range_2_dist = row_dist_2
    valid_2, val_2 = __valid_value_of_range(df_indicator, col_name_or_list_b, range_2_start, range_2_stop, range_2_dist)
    #
    check = valid_1 and valid_2 and (val_1 <= val_2)

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, "
                               f"{range_1_start}({range_1_start_date}), {range_1_stop}({range_1_stop_date}), {range_1_dist=}, "
                               f"{valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, "
                               f"{range_2_start}({range_2_start_date}), {range_2_stop}({range_2_stop_date}), {range_2_dist=}, "
                               f"{valid_2=}, {val_2=}, "
                               f"{check=}, "
                               )

    return check


def is_range_1_diffratio_1(df_indicator,
                           col_name_or_list,
                           row_begin,
                           row_count_start, row_count_stop, row_dist,
                           diff_ratio_limit_l, diff_ratio_limit_h,
                           hint=None, is_log=False) -> bool:
    return is_range_2_diffratio_2(df_indicator,
                                  col_name_or_list_a=col_name_or_list, col_name_or_list_b=col_name_or_list,
                                  row_begin=row_begin,
                                  row_count_start=row_count_start,
                                  row_count_stop=row_count_stop,
                                  row_dist_1=row_dist,
                                  row_dist_2=row_dist,
                                  diff_ratio_limit_l=diff_ratio_limit_l,
                                  diff_ratio_limit_h=diff_ratio_limit_h,
                                  hint=hint, is_log=is_log)


def is_range_1_diffratio_2(df_indicator,
                           col_name_or_list,
                           row_begin,
                           row_count_start, row_count_stop, row_dist_1, row_dist_2,
                           diff_ratio_limit_l, diff_ratio_limit_h,
                           hint=None, is_log=False) -> bool:
    return is_range_2_diffratio_2(df_indicator,
                                  col_name_or_list_a=col_name_or_list, col_name_or_list_b=col_name_or_list,
                                  row_begin=row_begin,
                                  row_count_start=row_count_start,
                                  row_count_stop=row_count_stop,
                                  row_dist_1=row_dist_1,
                                  row_dist_2=row_dist_2,
                                  diff_ratio_limit_l=diff_ratio_limit_l,
                                  diff_ratio_limit_h=diff_ratio_limit_h,
                                  hint=hint, is_log=is_log)


def is_range_2_diffratio_2(df_indicator,
                           col_name_or_list_a, col_name_or_list_b,
                           row_begin,
                           row_count_start, row_count_stop, row_dist_1, row_dist_2,
                           diff_ratio_limit_l, diff_ratio_limit_h,
                           hint=None, is_log=False) -> bool:
    """
        diff_ratio_limit_l <= diff (
            row_dist_1 ( [ row_begin + row_count_start : row_begin + row_count_stop ], [ col_name_or_list_a ] ),
            row_dist_2 ( [ row_begin + row_count_start : row_begin + row_count_stop ], [ col_name_or_list_b ] ),
        ) <= diff_ratio_limit_h

        note: ratio_limit_h 正数, ratio_limit_l 正数
    """
    funcname = is_range_2_diffratio_2.__name__
    dfutil.valid_or_exit(diff_ratio_limit_l >= 0, f"check: {diff_ratio_limit_l=} >= 0")
    dfutil.valid_or_exit(diff_ratio_limit_h >= 0, f"check: {diff_ratio_limit_h=} >= 0")

    #
    range_start = row_begin + row_count_start - 1
    range_start_date = __date(df_indicator, range_start)
    range_stop = row_begin + row_count_stop - 1
    range_stop_date = __date(df_indicator, range_stop)
    range_dist_1 = row_dist_1
    range_dist_2 = row_dist_2
    valid_1, val_1 = __valid_value_of_range(df_indicator, col_name_or_list_a, range_start, range_stop, range_dist_1)
    valid_2, val_2 = __valid_value_of_range(df_indicator, col_name_or_list_b, range_start, range_stop, range_dist_2)
    #
    check = check_1 = check_2 = False
    # val_min = val_max = val_limit_l = val_limit_h = np.nan
    diff = ratio_1 = ratio_2 = np.nan
    if valid_1 and valid_2:
        diff = abs(val_1 - val_2)
        ratio_1 = abs(dfutil.to_ratio(diff, val_1))
        ratio_2 = abs(dfutil.to_ratio(diff, val_2))
        check_1 = (diff_ratio_limit_l <= ratio_1 <= diff_ratio_limit_h)
        check_2 = (diff_ratio_limit_l <= ratio_2 <= diff_ratio_limit_h)
        check = check_1 and check_2

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {col_name_or_list_b=}, "
                               f"{range_start}({range_start_date}), {range_stop}({range_stop_date}), "
                               f"{range_dist_1=}, {range_dist_2=}, "
                               f"{valid_1=}, {val_1=}, {valid_2=}, {val_2=}, "
                               f"{diff_ratio_limit_h=}, {diff_ratio_limit_l=}, "
                               # f"{val_min=}, {val_max=}, {val_limit_l=}, {val_limit_h=}, "
                               f"{diff=}, {ratio_1=}, {ratio_2=}, "
                               f"{check_1=}, {check_2=}, {check=}, "
                               )

    return check


def is_range_2_diffratio_4(df_indicator,
                           col_name_or_list_a, col_name_or_list_b,
                           row_begin,
                           row_count_1_start, row_count_1_stop, row_dist_1,
                           row_count_2_start, row_count_2_stop, row_dist_2,
                           diff_ratio_limit_l, diff_ratio_limit_h,
                           hint=None, is_log=False) -> bool:
    """
        diff_ratio_limit_l <= diff (
            row_dist_1 ( [ row_begin + row_count_start_1 : row_begin + row_count_stop_1 ], [ col_name_or_list_a ] ),
            row_dist_2 ( [ row_begin + row_count_start_2 : row_begin + row_count_stop_2 ], [ col_name_or_list_b ] ),
        ) <= diff_ratio_limit_h

        note: ratio_limit_h 正数, ratio_limit_l 正数
    """
    funcname = is_range_2_diffratio_4.__name__
    dfutil.valid_or_exit(diff_ratio_limit_l >= 0, f"check: {diff_ratio_limit_l=} >= 0")
    dfutil.valid_or_exit(diff_ratio_limit_h >= 0, f"check: {diff_ratio_limit_h=} >= 0")

    #
    range_1_start = row_begin + row_count_1_start - 1
    range_1_start_date = __date(df_indicator, range_1_start)
    range_1_stop = row_begin + row_count_1_stop - 1
    range_1_stop_date = __date(df_indicator, range_1_stop)
    range_1_dist = row_dist_1
    #
    range_2_start = row_begin + row_count_2_start - 1
    range_2_start_date = __date(df_indicator, range_2_start)
    range_2_stop = row_begin + row_count_2_stop - 1
    range_2_stop_date = __date(df_indicator, range_2_stop)
    range_2_dist = row_dist_2
    #
    valid_1, val_1 = __valid_value_of_range(df_indicator, col_name_or_list_a, range_1_start, range_1_stop, range_1_dist)
    valid_2, val_2 = __valid_value_of_range(df_indicator, col_name_or_list_b, range_2_start, range_2_stop, range_2_dist)
    #
    check = check_1 = check_2 = False
    diff = ratio_1 = ratio_2 = np.nan
    if valid_1 and valid_2:
        diff = abs(val_1 - val_2)
        ratio_1 = abs(dfutil.to_ratio(diff, val_1))
        ratio_2 = abs(dfutil.to_ratio(diff, val_2))
        check_1 = (diff_ratio_limit_l <= ratio_1 <= diff_ratio_limit_h)
        check_2 = (diff_ratio_limit_l <= ratio_2 <= diff_ratio_limit_h)
        check = check_1 and check_2

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, "
                               f"{range_1_start}({range_1_start_date}), {range_1_stop}({range_1_stop_date}), {range_1_dist=}, "
                               f"{valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, "
                               f"{range_2_start}({range_2_start_date}), {range_2_stop}({range_2_stop_date}), {range_2_dist=}, "
                               f"{valid_2=}, {val_2=}, "
                               # f"{val_min=}, {val_max=}, {val_limit_l=}, {val_limit_h=}, "
                               f"{diff_ratio_limit_h=}, {diff_ratio_limit_l=}, {diff=}, {ratio_1=}, {ratio_2=}, "
                               f"{check_1=}, {check_2=}, {check=}, "
                               )

    return check


def is_range_1_valuelimit_1(df_indicator,
                            col_name_or_list,
                            row_begin,
                            row_count_start, row_count_stop, row_dist,
                            value_limit_l, value_limit_h,
                            hint=None, is_log=False) -> bool:
    return is_range_2_valuelimit_2(df_indicator,
                                   col_name_or_list_a=col_name_or_list, col_name_or_list_b=col_name_or_list,
                                   row_begin=row_begin,
                                   row_count_start=row_count_start,
                                   row_count_stop=row_count_stop,
                                   row_dist_1=row_dist,
                                   row_dist_2=row_dist,
                                   value_limit_l=value_limit_l,
                                   value_limit_h=value_limit_h,
                                   hint=hint, is_log=is_log)


def is_range_1_valuelimit_2(df_indicator,
                            col_name_or_list,
                            row_begin,
                            row_count_start, row_count_stop, row_dist_1, row_dist_2,
                            value_limit_l, value_limit_h,
                            hint=None, is_log=False) -> bool:
    return is_range_2_valuelimit_2(df_indicator,
                                   col_name_or_list_a=col_name_or_list, col_name_or_list_b=col_name_or_list,
                                   row_begin=row_begin,
                                   row_count_start=row_count_start,
                                   row_count_stop=row_count_stop,
                                   row_dist_1=row_dist_1,
                                   row_dist_2=row_dist_2,
                                   value_limit_l=value_limit_l,
                                   value_limit_h=value_limit_h,
                                   hint=hint, is_log=is_log)


def is_range_2_valuelimit_2(df_indicator,
                            col_name_or_list_a, col_name_or_list_b,
                            row_begin,
                            row_count_start, row_count_stop, row_dist_1, row_dist_2,
                            value_limit_l, value_limit_h,
                            hint=None, is_log=False) -> bool:
    """
        and (
            value_limit_l <= row_dist_1 (
                [ row_begin + row_count_start : row_begin + row_count_stop ], [ col_name_or_list_a ]
            ) <= value_limit_h
            value_limit_l <= row_dist_2 (
                [ row_begin + row_count_start : row_begin + row_count_stop ], [ col_name_or_list_b ]
            ) <= value_limit_h
        )
    """
    funcname = is_range_2_valuelimit_2.__name__

    #
    range_start = row_begin + row_count_start - 1
    range_start_date = __date(df_indicator, range_start)
    range_stop = row_begin + row_count_stop - 1
    range_stop_date = __date(df_indicator, range_stop)
    range_dist_1 = row_dist_1
    range_dist_2 = row_dist_2
    valid_1, val_1 = __valid_value_of_range(df_indicator, col_name_or_list_a, range_start, range_stop, range_dist_1)
    valid_2, val_2 = __valid_value_of_range(df_indicator, col_name_or_list_b, range_start, range_stop, range_dist_2)
    #
    check = check_1 = check_2 = False
    val_limit_h = val_limit_l = np.nan
    if valid_1 and valid_2:
        val_limit_h = value_limit_h
        val_limit_l = value_limit_l
        check_1 = val_limit_l <= val_1 <= val_limit_h
        check_2 = val_limit_l <= val_2 <= val_limit_h
        check = check_1 and check_2

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {col_name_or_list_b=}, "
                               f"{range_start}({range_start_date}), {range_stop}({range_stop_date}), "
                               f"{range_dist_1=}, {range_dist_2=}, "
                               f"{valid_1=}, {val_1=}, {valid_2=}, {val_2=}, "
                               f"{val_limit_h=}, {value_limit_h=}, "
                               f"{val_limit_l=}, {value_limit_l=}, "
                               f"{check_1=}, {check_2=}, {check=}, "
                               )

    return check


def is_row_large_1(df_indicator,
                   col_name_or_list,
                   row_begin, row_count_1, row_count_2,
                   hint=None, is_log=False) -> bool:
    return is_row_large_2(df_indicator,
                          col_name_or_list_a=col_name_or_list, col_name_or_list_b=col_name_or_list,
                          row_begin=row_begin,
                          row_count_1=row_count_1,
                          row_count_2=row_count_2,
                          hint=hint, is_log=is_log)


def is_row_large_2(df_indicator,
                   col_name_or_list_a, col_name_or_list_b,
                   row_begin, row_count_1, row_count_2,
                   hint=None, is_log=False) -> bool:
    funcname = is_row_large_2.__name__

    index_1 = row_begin + row_count_1 - 1
    index_1_date = __date(df_indicator, index_1)
    valid_1, val_1 = __valid_value(df_indicator, col_name_or_list_a, index_1)
    index_2 = row_begin + row_count_2 - 1
    index_2_date = __date(df_indicator, index_2)
    valid_2, val_2 = __valid_value(df_indicator, col_name_or_list_b, index_2)
    check = valid_1 and valid_2 and (val_1 > val_2)

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index_1}({index_1_date}), {valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, {index_2}({index_2_date}), {valid_2=}, {val_2=}, "
                               f"{check=}, "
                               )

    return check


def is_row_largeequal_1(df_indicator,
                        col_name_or_list,
                        row_begin, row_count_1, row_count_2,
                        hint=None, is_log=False
                        ) -> bool:
    return is_row_largeequal_2(df_indicator,
                               col_name_or_list_a=col_name_or_list, col_name_or_list_b=col_name_or_list,
                               row_begin=row_begin,
                               row_count_1=row_count_1,
                               row_count_2=row_count_2,
                               hint=hint, is_log=is_log)


def is_row_largeequal_2(df_indicator,
                        col_name_or_list_a, col_name_or_list_b,
                        row_begin, row_count_1, row_count_2,
                        hint=None, is_log=False) -> bool:
    funcname = is_row_largeequal_2.__name__

    index_1 = row_begin + row_count_1 - 1
    index_1_date = __date(df_indicator, index_1)
    valid_1, val_1 = __valid_value(df_indicator, col_name_or_list_a, index_1)
    index_2 = row_begin + row_count_2 - 1
    index_2_date = __date(df_indicator, index_2)
    valid_2, val_2 = __valid_value(df_indicator, col_name_or_list_b, index_2)
    check = valid_1 and valid_2 and (val_1 >= val_2)

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index_1}({index_1_date}), {valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, {index_2}({index_2_date}), {valid_2=}, {val_2=}, "
                               f"{check=}, "
                               )

    return check


def is_row_largemore_1(df_indicator,
                       col_name_or_list,
                       row_begin, row_count_1, row_count_2,
                       ratio_diff_more,
                       hint=None, is_log=False) -> bool:
    return is_row_largemore_2(df_indicator,
                              col_name_or_list_a=col_name_or_list, col_name_or_list_b=col_name_or_list,
                              row_begin=row_begin,
                              row_count_1=row_count_1,
                              row_count_2=row_count_2,
                              ratio_diff_more=ratio_diff_more,
                              hint=hint, is_log=is_log)


def is_row_largemore_2(df_indicator,
                       col_name_or_list_a, col_name_or_list_b,
                       row_begin, row_count_1, row_count_2,
                       ratio_diff_more,
                       hint=None, is_log=False) -> bool:
    funcname = is_row_largemore_2.__name__

    check = False
    val_diff = np.nan
    index_1 = row_begin + row_count_1 - 1
    index_1_date = __date(df_indicator, index_1)
    valid_1, val_1 = __valid_value(df_indicator, col_name_or_list_a, index_1)
    index_2 = row_begin + row_count_2 - 1
    index_2_date = __date(df_indicator, index_2)
    valid_2, val_2 = __valid_value(df_indicator, col_name_or_list_b, index_2)
    check_large = (val_1 > val_2)
    if valid_1 and valid_2 and check_large:
        val_diff = val_2 * ratio_diff_more
        check = (val_1 - val_2) >= val_diff

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index_1}({index_1_date}), {valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, {index_2}({index_2_date}), {valid_2=}, {val_2=}, "
                               f"{val_diff=}, {ratio_diff_more=}, "
                               f"{check_large=}, {check=}, "
                               )

    return check


def is_row_small_1(df_indicator,
                   col_name_or_list,
                   row_begin, row_count_1, row_count_2,
                   hint=None, is_log=False) -> bool:
    return is_row_small_2(df_indicator,
                          col_name_or_list_a=col_name_or_list, col_name_or_list_b=col_name_or_list,
                          row_begin=row_begin,
                          row_count_1=row_count_1,
                          row_count_2=row_count_2,
                          hint=hint, is_log=is_log)


def is_row_small_2(df_indicator,
                   col_name_or_list_a, col_name_or_list_b,
                   row_begin, row_count_1, row_count_2,
                   hint=None, is_log=False) -> bool:
    funcname = is_row_small_2.__name__

    index_1 = row_begin + row_count_1 - 1
    index_1_date = __date(df_indicator, index_1)
    valid_1, val_1 = __valid_value(df_indicator, col_name_or_list_a, index_1)
    index_2 = row_begin + row_count_2 - 1
    index_2_date = __date(df_indicator, index_2)
    valid_2, val_2 = __valid_value(df_indicator, col_name_or_list_b, index_2)
    check = valid_1 and valid_2 and (val_1 < val_2)

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index_1}({index_1_date}), {valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, {index_2}({index_2_date}), {valid_2=}, {val_2=}, "
                               f"{check=}, "
                               )

    return check


def is_row_smallequal_1(df_indicator,
                        col_name_or_list,
                        row_begin, row_count_1, row_count_2,
                        hint=None, is_log=False) -> bool:
    return is_row_smallequal_2(df_indicator,
                               col_name_or_list_a=col_name_or_list, col_name_or_list_b=col_name_or_list,
                               row_begin=row_begin,
                               row_count_1=row_count_1,
                               row_count_2=row_count_2,
                               hint=hint, is_log=is_log)


def is_row_smallequal_2(df_indicator,
                        col_name_or_list_a, col_name_or_list_b,
                        row_begin, row_count_1, row_count_2,
                        hint=None, is_log=False) -> bool:
    funcname = is_row_smallequal_2.__name__

    index_1 = row_begin + row_count_1 - 1
    index_1_date = __date(df_indicator, index_1)
    valid_1, val_1 = __valid_value(df_indicator, col_name_or_list_a, index_1)
    index_2 = row_begin + row_count_2 - 1
    index_2_date = __date(df_indicator, index_2)
    valid_2, val_2 = __valid_value(df_indicator, col_name_or_list_b, index_2)
    check = valid_1 and valid_2 and (val_1 <= val_2)

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index_1}({index_1_date}), {valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, {index_2}({index_2_date}), {valid_2=}, {val_2=}, "
                               f"{check=}, "
                               )

    return check


def is_row_smallmore_1(df_indicator,
                       col_name_or_list,
                       row_begin, row_count_1, row_count_2,
                       ratio_diff_more,
                       hint=None, is_log=False) -> bool:
    return is_row_smallmore_2(df_indicator,
                              col_name_or_list_a=col_name_or_list, col_name_or_list_b=col_name_or_list,
                              row_begin=row_begin,
                              row_count_1=row_count_1,
                              row_count_2=row_count_2,
                              ratio_diff_more=ratio_diff_more,
                              hint=hint, is_log=is_log)


def is_row_smallmore_2(df_indicator,
                       col_name_or_list_a, col_name_or_list_b,
                       row_begin, row_count_1, row_count_2,
                       ratio_diff_more,
                       hint=None, is_log=False) -> bool:
    funcname = is_row_smallmore_2.__name__

    check = False
    val_diff = np.nan
    index_1 = row_begin + row_count_1 - 1
    index_1_date = __date(df_indicator, index_1)
    valid_1, val_1 = __valid_value(df_indicator, col_name_or_list_a, index_1)
    index_2 = row_begin + row_count_2 - 1
    index_2_date = __date(df_indicator, index_2)
    valid_2, val_2 = __valid_value(df_indicator, col_name_or_list_b, index_2)
    check_small = (val_1 < val_2)
    if valid_1 and valid_2 and check_small:
        val_diff = val_1 * ratio_diff_more
        check = val_2 - val_1 >= val_diff

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index_1}({index_1_date}), {valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, {index_2}({index_2_date}), {valid_2=}, {val_2=}, "
                               f"{val_diff=}, {ratio_diff_more=}, "
                               f"{check_small=}, {check=}, "
                               )

    return check


def is_row_equalabout_1(df_indicator,
                        col_name_or_list,
                        row_begin, row_count_1, row_count_2,
                        ratio_limit_l, ratio_limit_h,
                        hint=None, is_log=False) -> bool:
    return is_row_equalabout_2(df_indicator,
                               col_name_or_list_a=col_name_or_list, col_name_or_list_b=col_name_or_list,
                               row_begin=row_begin,
                               row_count_1=row_count_1,
                               row_count_2=row_count_2,
                               ratio_limit_l=ratio_limit_l,
                               ratio_limit_h=ratio_limit_h,
                               hint=hint, is_log=is_log)


def is_row_equalabout_2(df_indicator,
                        col_name_or_list_a, col_name_or_list_b,
                        row_begin, row_count_1, row_count_2,
                        ratio_limit_l, ratio_limit_h,
                        hint=None, is_log=False) -> bool:
    """
        col_name_or_list 为list时取值 mean
        note: ratio_limit_h 正数, ratio_limit_l 负数
    """
    funcname = is_row_equalabout_2.__name__
    # dfutil.valid_or_exit(ratio_limit_h >= 0, f"check: {ratio_limit_h=} >= 0")
    dfutil.valid_or_exit(ratio_limit_h >= ratio_limit_l, f"check: {ratio_limit_h=} >= {ratio_limit_l=}")
    dfutil.valid_or_exit(ratio_limit_l <= 0, f"check: {ratio_limit_l=} <= 0")

    check = check_1 = check_2 = False
    val_limit_h = val_limit_l = np.nan
    index_1 = row_begin + row_count_1 - 1
    index_1_date = __date(df_indicator, index_1)
    valid_1, val_1 = __valid_value(df_indicator, col_name_or_list_a, index_1)
    index_2 = row_begin + row_count_2 - 1
    index_2_date = __date(df_indicator, index_2)
    valid_2, val_2 = __valid_value(df_indicator, col_name_or_list_b, index_2)
    if valid_1 and valid_2:
        val_limit_h = max(val_1 * (1 + ratio_limit_h), val_2 * (1 + ratio_limit_h))
        val_limit_l = max(val_1 * (1 + ratio_limit_l), val_2 * (1 + ratio_limit_l))
        check_1 = val_limit_l <= val_1 <= val_limit_h
        check_2 = val_limit_l <= val_2 <= val_limit_h
        check = check_1 and check_2

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index_1}({index_1_date}), {valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, {index_2}({index_2_date}), {valid_2=}, {val_2=}, "
                               f"{val_limit_h=}, {ratio_limit_h=}, "
                               f"{val_limit_l=}, {ratio_limit_l=}, "
                               f"{check_1=}, {check_2=}, {check=}, "
                               )

    return check


def is_row_deltalimit_1(df_indicator,
                        col_name_or_list,
                        row_begin, row_count_1, row_count_2,
                        delta_limit_l, delta_limit_h,
                        hint=None, is_log=False) -> bool:
    return is_row_deltalimit_2(df_indicator,
                               col_name_or_list_a=col_name_or_list, col_name_or_list_b=col_name_or_list,
                               row_begin=row_begin,
                               row_count_1=row_count_1,
                               row_count_2=row_count_2,
                               delta_limit_l=delta_limit_l,
                               delta_limit_h=delta_limit_h,
                               hint=hint, is_log=is_log)


def is_row_deltalimit_2(df_indicator,
                        col_name_or_list_a, col_name_or_list_b,
                        row_begin, row_count_1, row_count_2,
                        delta_limit_l, delta_limit_h,
                        hint=None, is_log=False) -> bool:
    """ 变化范围
        col_name_or_list 为list时取值 mean
        note: delta_limit_h 和 delta_limit_l 取值可能 正数或负数
    """
    funcname = is_row_deltalimit_2.__name__

    check = check_1 = check_2 = False
    val_limit_h = val_limit_l = np.nan
    index_1 = row_begin + row_count_1 - 1
    index_1_date = __date(df_indicator, index_1)
    valid_1, val_1 = __valid_value(df_indicator, col_name_or_list_a, index_1)
    index_2 = row_begin + row_count_2 - 1
    index_2_date = __date(df_indicator, index_2)
    valid_2, val_2 = __valid_value(df_indicator, col_name_or_list_b, index_2)
    if valid_1 and valid_2:
        val_limit_h = max(val_1 + delta_limit_h, val_2 + delta_limit_h)
        val_limit_l = max(val_1 + delta_limit_l, val_2 + delta_limit_l)
        check_1 = val_limit_l <= val_1 <= val_limit_h
        check_2 = val_limit_l <= val_2 <= val_limit_h
        check = check_1 and check_2

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index_1}({index_1_date}), {valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, {index_2}({index_2_date}), {valid_2=}, {val_2=}, "
                               f"{val_limit_h=}, {val_limit_l=}, "
                               f"{check_1=}, {check_2=}, {check=}, "
                               )

    return check


def is_row_valuelimit_1(df_indicator,
                        col_name_or_list,
                        row_begin, row_count_1, row_count_2,
                        value_limit_l, value_limit_h,
                        hint=None, is_log=False) -> bool:
    return is_row_valuelimit_2(df_indicator,
                               col_name_or_list_a=col_name_or_list, col_name_or_list_b=col_name_or_list,
                               row_begin=row_begin,
                               row_count_1=row_count_1,
                               row_count_2=row_count_2,
                               value_limit_l=value_limit_l,
                               value_limit_h=value_limit_h,
                               hint=hint, is_log=is_log)


def is_row_valuelimit_2(df_indicator,
                        col_name_or_list_a, col_name_or_list_b,
                        row_begin, row_count_1, row_count_2,
                        value_limit_l, value_limit_h,
                        hint=None, is_log=False) -> bool:
    """
        and (
            value_limit_l <= ( [ row_begin + row_count_1 - 1 ], [ col_name_or_list_a ] ) <= value_limit_h
            value_limit_l <= ( [ row_begin + row_count_2 - 1 ], [ col_name_or_list_b ] ) <= value_limit_h
        )

        取值范围
            col_name_or_list 为list时取值 mean
            note: range_limit_h 和 range_limit_l 取值可能 正数或负数
    """
    funcname = is_row_valuelimit_2.__name__

    check = check_1 = check_2 = False
    val_limit_h = val_limit_l = np.nan
    index_1 = row_begin + row_count_1 - 1
    index_1_date = __date(df_indicator, index_1)
    valid_1, val_1 = __valid_value(df_indicator, col_name_or_list_a, index_1)
    index_2 = row_begin + row_count_2 - 1
    index_2_date = __date(df_indicator, index_2)
    valid_2, val_2 = __valid_value(df_indicator, col_name_or_list_b, index_2)
    if valid_1 and valid_2:
        val_limit_h = value_limit_h
        val_limit_l = value_limit_l
        check_1 = val_limit_l <= val_1 <= val_limit_h
        check_2 = val_limit_l <= val_2 <= val_limit_h
        check = check_1 and check_2

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index_1}({index_1_date}), {valid_1=}, {val_1=}, "
                               f"{col_name_or_list_b=}, {index_2}({index_2_date}), {valid_2=}, {val_2=}, "
                               f"{val_limit_h=}, {value_limit_h=}, "
                               f"{val_limit_l=}, {value_limit_l=}, "
                               f"{check_1=}, {check_2=}, {check=}, "
                               )

    return check


def is_col_small_2(df_indicator,
                   col_name_or_list_a, col_name_or_list_b,
                   row_begin, row_count,
                   hint=None, is_log=False) -> bool:
    funcname = is_col_small_2.__name__

    index = row_begin + row_count - 1
    index_date = __date(df_indicator, index)
    valid_a, val_a = __valid_value(df_indicator, col_name_or_list_a, index)
    valid_b, val_b = __valid_value(df_indicator, col_name_or_list_b, index)
    check = valid_a and valid_b and (val_a < val_b)

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index}({index_date}), {valid_a=}, {val_a=}, "
                               f"{col_name_or_list_b=}, {index}({index_date}), {valid_b=}, {val_b=}, "
                               f"{check=}, "
                               )

    return check


def is_col_large_2(df_indicator,
                   col_name_or_list_a, col_name_or_list_b,
                   row_begin, row_count,
                   hint=None, is_log=False) -> bool:
    funcname = is_col_large_2.__name__

    index = row_begin + row_count - 1
    index_date = __date(df_indicator, index)
    valid_a, val_a = __valid_value(df_indicator, col_name_or_list_a, index)
    valid_b, val_b = __valid_value(df_indicator, col_name_or_list_b, index)
    check = valid_a and valid_b and (val_a > val_b)

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index}({index_date}), {valid_a=}, {val_a=}, "
                               f"{col_name_or_list_b=}, {index}({index_date}), {valid_b=}, {val_b=}, "
                               f"{check=}, "
                               )

    return check


def is_col_equalabout_1(df_indicator,
                        col_name,
                        row_begin, row_count,
                        ratio_limit_l, ratio_limit_h,
                        hint=None, is_log=False) -> bool:
    return is_col_equalabout_2(df_indicator,
                               col_name_or_list_a=col_name, col_name_or_list_b=col_name,
                               row_begin=row_begin,
                               row_count=row_count,
                               ratio_limit_l=ratio_limit_l,
                               ratio_limit_h=ratio_limit_h,
                               hint=hint, is_log=is_log)


def is_col_equalabout_2(df_indicator,
                        col_name_or_list_a, col_name_or_list_b,
                        row_begin, row_count,
                        ratio_limit_l, ratio_limit_h,
                        hint=None, is_log=False) -> bool:
    """
        note: ratio_limit_h 正数, ratio_limit_l 负数
    """
    funcname = is_col_equalabout_2.__name__
    # dfutil.valid_or_exit(ratio_limit_h >= 0, f"check: {ratio_limit_h=} >= 0")
    dfutil.valid_or_exit(ratio_limit_h >= ratio_limit_l, f"check: {ratio_limit_h=} >= {ratio_limit_l=}")
    dfutil.valid_or_exit(ratio_limit_l <= 0, f"check: {ratio_limit_l=} <= 0")

    check = check_a = check_b = False
    val_limit_h = val_limit_l = np.nan
    index = row_begin + row_count - 1
    index_date = __date(df_indicator, index)
    valid_a, val_a = __valid_value(df_indicator, col_name_or_list_a, index)
    valid_b, val_b = __valid_value(df_indicator, col_name_or_list_b, index)
    if valid_a and valid_b:
        val_limit_h = max(val_a * (1 + ratio_limit_h), val_b * (1 + ratio_limit_h))
        # val_limit_l = max(val_a * (1 - ratio_limit_l), val_b * (1 - ratio_limit_l))
        val_limit_l = max(val_a * (1 + ratio_limit_l), val_b * (1 + ratio_limit_l))
        check_a = val_limit_l <= val_a <= val_limit_h
        check_b = val_limit_l <= val_b <= val_limit_h
        check = check_a and check_b

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index}({index_date}), {valid_a=}, {val_a=}, "
                               f"{col_name_or_list_b=}, {index}({index_date}), {valid_b=}, {val_b=}, "
                               f"{val_limit_h=}, {ratio_limit_h=}, "
                               f"{val_limit_l=}, {ratio_limit_l=}, "
                               f"{check_a=}, {check_b=}, {check=}, "
                               )

    return check


def is_col_valuelimit_1(df_indicator,
                        col_name,
                        row_begin, row_count,
                        value_limit_l, value_limit_h,
                        hint=None, is_log=False) -> bool:
    return is_col_valuelimit_2(df_indicator,
                               col_name_or_list_a=col_name, col_name_or_list_b=col_name,
                               row_begin=row_begin,
                               row_count=row_count,
                               value_limit_l=value_limit_l,
                               value_limit_h=value_limit_h,
                               hint=hint, is_log=is_log)


def is_col_valuelimit_2(df_indicator,
                        col_name_or_list_a, col_name_or_list_b,
                        row_begin, row_count,
                        value_limit_l, value_limit_h,
                        hint=None, is_log=False) -> bool:
    """ 取值范围
        col_name_or_list 为list时取值 mean
        note: range_limit_h 和 range_limit_l 取值可能 正数或负数
    """
    funcname = is_col_valuelimit_2.__name__

    check = check_a = check_b = False
    val_limit_h = val_limit_l = np.nan
    index = row_begin + row_count - 1
    index_date = __date(df_indicator, index)
    valid_a, val_a = __valid_value(df_indicator, col_name_or_list_a, index)
    valid_b, val_b = __valid_value(df_indicator, col_name_or_list_b, index)
    if valid_a and valid_b:
        val_limit_h = value_limit_h
        val_limit_l = value_limit_l
        check_a = val_limit_l <= val_a <= val_limit_h
        check_b = val_limit_l <= val_a <= val_limit_h
        check = check_a and check_b

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_a=}, {index}({index_date}), {valid_a=}, {val_a=}, "
                               f"{col_name_or_list_b=}, {index}({index_date}), {valid_b=}, {val_b=}, "
                               f"{val_limit_h=}, {value_limit_h=}, "
                               f"{val_limit_l=}, {value_limit_l=}, "
                               f"{check_a=}, {check_b=}, {check=}, "
                               )

    return check


def is_col_splitdiffratio_2(df_indicator,
                            col_name_or_list_m, col_name_or_list_h, col_name_or_list_l,
                            row_begin, row_count, row_dist_m, row_dist_h, row_dist_l,
                            diff_ratio_limit_l, diff_ratio_limit_h,
                            hint=None, is_log=False) -> bool:
    """
        diff_ratio_limit_l <=
            diff (
                diff (
                    row_dist_h ( [ row_begin + row_count ], [ col_name_or_list_h ] ),
                    row_dist_m ( [ row_begin + row_count ], [ col_name_or_list_m ] ),
                ),
                diff (
                    row_dist_m ( [ row_begin + row_count ], [ col_name_or_list_m ] ),
                    row_dist_l ( [ row_begin + row_count ], [ col_name_or_list_l ] ),
                )
            )
        <= diff_ratio_limit_h

        note: ratio_limit_h 正数, ratio_limit_l 正数
    """
    funcname = is_col_splitdiffratio_2.__name__
    dfutil.valid_or_exit(diff_ratio_limit_l >= 0, f"check: {diff_ratio_limit_l=} >= 0")
    dfutil.valid_or_exit(diff_ratio_limit_h >= 0, f"check: {diff_ratio_limit_h=} >= 0")

    #
    index = row_begin + row_count - 1
    index_date = __date(df_indicator, index)
    range_dist_m = row_dist_m
    range_dist_h = row_dist_h
    range_dist_l = row_dist_l
    valid_m, val_m = __valid_value_of_range(df_indicator, col_name_or_list_m, index, index, range_dist_m)
    valid_h, val_h = __valid_value_of_range(df_indicator, col_name_or_list_h, index, index, range_dist_h)
    valid_l, val_l = __valid_value_of_range(df_indicator, col_name_or_list_l, index, index, range_dist_l)
    #
    check = False
    diff_hm = diff_ml = ratio_hm_ml = np.nan
    if valid_m and valid_h and valid_l:
        diff_hm, diff_ml = abs(val_h - val_m), abs(val_m - val_l)
        ratio_hm_ml = abs(dfutil.to_ratio(diff_hm, diff_ml))
        check = diff_ratio_limit_l <= ratio_hm_ml <= diff_ratio_limit_h

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list_m=}, {col_name_or_list_h=}, {col_name_or_list_l=}, "
                               f"{index}({index_date}), {range_dist_m=}, {range_dist_h=}, {range_dist_l=}, "
                               f"{valid_m=}, {val_m=}, {valid_h=}, {val_h=}, {valid_l=}, {val_l=}, "
                               f"{diff_ratio_limit_l=}, {diff_ratio_limit_h=}, "
                               f"{diff_hm=}, {diff_ml=}, {ratio_hm_ml=}, "
                               f"{check=}, "
                               )

    return check


def is_val_large(df_indicator,
                 col_name_or_list,
                 row_begin, row_count,
                 check_val,
                 hint=None, is_log=False) -> bool:
    funcname = is_val_large.__name__

    index = row_begin + row_count - 1
    index_date = __date(df_indicator, index)
    valid, val = __valid_value(df_indicator, col_name_or_list, index)
    check = valid and (val > check_val)

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list=}, {index}({index_date}), {valid=}, {val=}, {check_val=}, "
                               f"{check=}, "
                               )

    return check


def is_val_largeequal(df_indicator,
                      col_name_or_list,
                      row_begin, row_count,
                      check_val,
                      hint=None, is_log=False) -> bool:
    funcname = is_val_largeequal.__name__

    index = row_begin + row_count - 1
    index_date = __date(df_indicator, index)
    valid, val = __valid_value(df_indicator, col_name_or_list, index)
    check = valid and (val >= check_val)

    (is_log or qldebug.is_signal_debug_1(df_indicator, row_begin)) and \
    qldebug.log_signal_debug_1(df_indicator, row_begin,
                               f"{__hint(hint, funcname)}, "
                               f"{col_name_or_list=}, {index}({index_date}), {valid=}, {val=}, {check_val=}, "
                               f"{check=}, "
                               )

    return check


############################################


def plot_of_signal_point():
    # 符号 信号圆圈
    r_l = [
        {"type": "sig", "date.key": "date", "price.key": "close", },
    ]
    return r_l


def plot_of_pattern_main(close=None, low=None):
    # 符号 水平箭头
    r_l = []
    r_l.extend(
        [
            {"type": "cond.ohlc", "date.key": "date", "price.key": "close", "date.prev": x, }
            for x in close
        ] if close is not None else []
    )
    r_l.extend(
        [
            {"type": "cond.ohlc", "date.key": "date", "price.key": "low", "date.prev": x, }
            for x in low
        ] if low is not None else []
    )
    return r_l


def plot_of_pattern_aid(high=None, low=None):
    # 符号 取值打叉
    r_l = []
    r_l.extend(
        [
            {"type": "cond.ema", "date.key": "date", "price.key": "high", "date.prev": x, }
            for x in high
        ] if high is not None else [])
    r_l.extend(
        [
            {"type": "cond.ema", "date.key": "date", "price.key": "low", "date.prev": x, }
            for x in low
        ] if low is not None else [])
    return r_l


def plot_of_earning_range():
    # 符号 垂直箭头
    __category = lambda: qldef.var_category
    __when = lambda: qldef.var_when
    r_l = [
        {"type": "next.c.max", "date.key": f"{__when()}.{__category()}.close.max.date", "price.key": "close", },
        {"type": "next.c.min", "date.key": f"{__when()}.{__category()}.close.min.date", "price.key": "close", },
        {"type": "next.h.max", "date.key": f"{__when()}.{__category()}.high.max.date", "price.key": "high", },
        {"type": "next.l.min", "date.key": f"{__when()}.{__category()}.low.min.date", "price.key": "low", },
    ]
    return r_l

############################################
