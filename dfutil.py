"""
df util
"""
# coding=utf-8

# print("__name__ :", __name__)


# note: 请勿引用任何公共库之外的其它库，特别是 project 的文件

import email.header
import email.mime.application
import email.mime.multipart
import email.mime.text
import email.utils
import logging
import math
import multiprocessing
import os
import pathlib
import pprint
import shutil
import signal
import smtplib
import sys
import time
import functools
import traceback
from datetime import datetime, timedelta, timezone
from decimal import *
from typing import Optional, Any, Union, Callable, Tuple

try:
    import beepy
except ModuleNotFoundError:
    # 退化实现：缺省用 winsound 发声，避免依赖 beepy/simpleaudio
    try:
        import winsound
    except ImportError:
        winsound = None

    class _BeePyStub:
        def beep(self, *args, **kwargs):
            if winsound is None:
                return None
            # 简单的蜂鸣音，频率/时长可按需调整
            try:
                winsound.Beep(880, 180)
            except Exception:
                pass

    beepy = _BeePyStub()
import joblib
import numpy as np
import pandas as pd
import pytz
try:
    import ray
    from ray.util.joblib import register_ray
except ImportError:
    ray = None
    register_ray = None

# from pyodbc import Row  # pyodbc查询数据库，处理查询的数据时报错 add by hhx 2025.02.17
from tqdm import tqdm

# def add_search_path():
#     curr_path = os.path.abspath(os.path.dirname(__file__))
#     search_path = curr_path + "/src/qlong"
#     sys.path.append(search_path)
#     log("search = {}".format(search_path))
#     sys.stdout.flush()
#


#############################################
# 用于日志grep的输出标志

#

# the_file = "__dfutil__"

the_elem_main = "===="
the_elem_func = "----"
the_elem_part = "...."
#
the_line_main = the_elem_main.join("" for _ in range(4 + 1))
the_line_func = the_elem_func.join("" for _ in range(4 + 1))
the_line_part = the_elem_part.join("" for _ in range(4 + 1))

#############################################

# 显示毫秒用于分析性能瓶颈
__the_log_tag_microsecond = True
__the_log_tag_microsecond_digit = 3  # 3位对于文件名称来说在快速环境下可能不够

# 邮件
__the_smtp_encoding = 'utf-8'
__the_smtp_debuglevel = 0
__the_smtp_ssl = True

index_false = False
index_true = True

#
# todo: deploy机器上now总是与UTC时间相同，并不是机器本地时间，原因未知。临时方案：强制设置为中国时区
__the_datetime_now_hours = 8
__the_datetime_now_tzinfo = datetime.now(timezone(timedelta(hours=__the_datetime_now_hours))).tzinfo

#
__datetime_now = lambda: datetime.now(timezone(timedelta(hours=__the_datetime_now_hours)))
#
# note: 如果tzinfo为None，则 __datetime_now().astimezone(tz) 会返回UTC时间，不是我们设置的北京时间，因此需要显示返回缺省设置
__tzinfo = lambda timezone_str: __the_datetime_now_tzinfo if timezone_str is None else pytz.timezone(timezone_str)


#
# __datetime_fmt_readable = "%Y-%m-%d %H:%M:%S"
# __datetime_fmt_digital = "%Y%m%d%H%M%S"


#############################################

def __log_tag():
    if __the_log_tag_microsecond:
        return f"[{timestamp_hhmmss_str()}.{timestamp_microsecond_str(__the_log_tag_microsecond_digit)}] "
    else:
        return f"[{timestamp_hhmmss_str()}] "


def __log_pd_str(*args) -> str:
    def __is_pd(__a):
        return isinstance(__a, pd.DataFrame) \
            or isinstance(__a, pd.Series) \
            or False

    s = __log_tag()
    for a in args:
        s += f"\npd, len = {pd_len_row(a)}, data = \n" if __is_pd(a) else ""
        s += f"{a}"
    s += "\n"
    return s


def __exit_impl(code):
    """
        In python, we have an in-built quit() function which is used to exit a python program. When it encounters the quit() function in the system, it terminates the execution of the program completely.
        We can also use the in-built exit() function in python to exit and come out of the program in python. It should be used in the interpreter only, it is like a synonym of quit() to make python more user-friendly
        In python, sys.exit() is considered good to be used in production code unlike quit() and exit() as sys module is always available. It also contains the in-built function to exit the program and come out of the execution process. The sys.exit() also raises the SystemExit exception.
        The os.exit() method is used to terminate the process with the specified status. We can use this method without flushing buffers or calling any cleanup handlers.
        The SystemExit is an exception which is raised, when the program is running needs to be stop.
        Difference between exit() and sys.exit() in python
            exit() – If we use exit() in a code and run it in the shell, it shows a message asking whether I want to kill the program or not. The exit() is considered bad to use in production code because it relies on site module.
            sys.exit() – But sys.exit() is better in this case because it closes the program and does not ask. It is considered good to use in production code because the sys module will always be there.
    """
    # todo: impl: joblib 中村砸退出无效的情况
    log("**** EXIT: ", f"{__exit_impl.__name__}, {code=}")
    #
    exit(code)
    sys.exit(code)
    # return


def __exit_as_error():
    log("**** EXIT ERROR ****")
    __exit_impl(1)


def __exit_but_not_error():
    log("**** EXIT BUT NOT ERROR ****")
    __exit_impl(255)  # note: gen.sh 中会判断 255 这个数值（此时不发送ops邮件）


def main_safe(main):
    try:
        main()
    except Exception as err:
        trace(f"{main_safe.__name__}, {errinfo(err)}")
        # __exit_main()
        __exit_as_error()


def logger(logger_name, logger_level=logging.DEBUG) -> logging.Logger:
    # 使用logger对象
    l_o = logging.getLogger(logger_name)

    l_o.setLevel(logger_level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(name)s] [%(asctime)s] [%(levelname)s] %(message)s ')
    handler.setFormatter(formatter)
    l_o.addHandler(handler)

    return l_o


# 日志输出目的地
__log_out: dict[str, Any] = {
    # sys.stdout是Python标准库sys模块的一个对象，它代表标准输出流（通常是屏幕或者控制台），这个对象是一个文件类对象，具有写入（如write()）
    "stdout": sys.stdout,
    "userout": None,  # 默认print日志不保存文件，仅输出到屏幕或者控制台 note by hhx 2024.08.08
}


# 设置print日志保存文件名 note by hhx 2024.08.08
def set_log_out(out_file: str):
    if __log_out["userout"] is not None:
        __log_out["userout"].close()
    path_safe(out_file)
    # todo：deploy的windows机器执行报告错误：UnicodeEncodeError: 'charmap' codec can't encode characters in position
    #       原因是日志输出中有中文
    #       参见解决：https://stackoverflow.com/questions/44391671/python3-unicodeencodeerror-charmap-codec-cant-encode-characters-in-position
    #       但是无效
    # __log_out["userout"] = open(out_file, "w")
    __log_out["userout"] = open(out_file, "w", encoding='utf-8')


def reset_log_out():
    if __log_out["userout"] is not None:
        __log_out["userout"].close()
    __log_out["userout"] = None


# todo: joblib多进程时发现可能在日志打印频繁时报告错误：[Errno 28] No space left on device
#       参见：https://stackoverflow.com/questions/6998083/python-causing-ioerror-errno-28-no-space-left-on-device-results-32766-h
#       参见：https://stackoverflow.com/questions/107705/disable-output-buffering
#       原因：应该是超出了stdout文件的某个os限制导致的（windows+cygwin），错误就在print那行代码
#       解决1：出现该错误后，降低flush频率，过一段时间在恢复（无效）
#       解决2：关闭 python stdout buffer 功能（无效）
#       解决3：降低日志频率，参见qldebug.force_xxx （有效，不过应该有更好办法）
__the_log_flush = True


def log(*args, is_prefix_tag=True, is_force_stdout=False, is_only_stdout=False, return_value: any = None) -> any:
    global __the_log_flush
    if not __the_log_flush and timestamp_yyyymmddhhmmss() % 100 < 10:
        __the_log_flush = True

    tag = __log_tag()
    try:
        is_done_out = False
        if not is_only_stdout and __log_out["userout"] is not None:
            is_done_out = True
            if is_prefix_tag:
                print(tag, *args, file=__log_out["userout"], flush=__the_log_flush)
            else:
                print(*args, file=__log_out["userout"], flush=__the_log_flush)

        if is_force_stdout or is_only_stdout or not is_done_out:
            if is_prefix_tag:
                print(tag, *args, file=__log_out["stdout"], flush=__the_log_flush)
            else:
                print(*args, file=__log_out["stdout"], flush=__the_log_flush)
    except UnicodeEncodeError as err:
        # todo: impl: 输出中文时，windows机器可能报错：UnicodeEncodeError: 'charmap' codec can't encode characters
        #       先屏蔽之，再想办法解决。可能是代码中trace的地方有中文注释导致的（traceback会输出完整代码行包括注释）
        #       不输出err名称（含有error，grep时太多了）
        #       不输出errifo，只输出errname，否则可能继续报错（trace时代码中有中文注释）
        print(tag, "**** LOG-TODO", errname(err), file=__log_out["stdout"], flush=True)
        print(tag, "**** LOG-TODO", errname(err), file=__log_out["userout"], flush=True)
        __the_log_flush = False
    except Exception as err:
        print(tag, "**** LOG-EXCEPTION-ERROR: ", errname(err), file=__log_out["stdout"], flush=True)
        print(tag, "**** LOG-EXCEPTION-ERROR: ", errname(err), file=__log_out["userout"], flush=True)
        __the_log_flush = False

    return return_value  # return_value 用于 chain 操作


def log_fmt(val, hint=None, width=1, indent=2, sort_dicts=True):
    """ 格式化 """
    x = val
    if of_pd_to_list(val):
        x = val.to_list()
    log(
        hint if hint is not None else "",
        pprint.pformat(x, width=width, indent=indent, sort_dicts=sort_dicts),
        is_prefix_tag=False
    )


def log_fmt_of_dir(val, hint=None, width=1, indent=2, sort_dicts=True):
    """ 格式化 dir 结果"""
    x = dir(val)
    log(
        hint if hint is not None else "",
        pprint.pformat(x, width=width, indent=indent, sort_dicts=sort_dicts),
        is_prefix_tag=False
    )


def log_pd(*args, is_force_stdout=False, is_only_stdout=False):
    """ pandas """
    set_pd_option()
    log(__log_pd_str(*args), is_prefix_tag=False, is_force_stdout=is_force_stdout, is_only_stdout=is_only_stdout)
    reset_pd_option()


def log_pd_col(*args, is_force_stdout=False, is_only_stdout=False):
    """ pandas （col完整显示，row不一定）"""
    set_pd_option_col()
    log(__log_pd_str(*args), is_prefix_tag=False, is_force_stdout=is_force_stdout, is_only_stdout=is_only_stdout)
    reset_pd_option()


def log_pd_group(df, key_col_list, is_force_stdout=False, is_only_stdout=False, hint=None):
    """ tricky: 同时显示 group 的 key 和 value """

    # df.groupby(pk_list).apply(dfutil.log_pd)
    # df.groupby(pk_list, as_index=False)[trade_list].agg(lambda x: list(x))

    aid_col_list = [f"{pd_col_add_prefix(x, is_temp=True)}" for x in key_col_list]
    df[aid_col_list] = df[key_col_list]  # create a shadow column for MultiIndexing
    df.sort_values(key_col_list, inplace=True)
    df.set_index(key_col_list, inplace=True)
    log_pd(
        hint,
        df.loc[:, [x for x in df.columns if x not in aid_col_list]],
        is_force_stdout=is_force_stdout,
        is_only_stdout=is_only_stdout,
    )


def level(log_level="log", *args, return_value: any = None) -> any:
    if log_level == "log":
        log(*args)
    elif log_level == "info":
        info(*args)
    elif log_level == "warn":
        warn(*args)
    elif log_level == "error":
        error(*args)
    elif log_level == "trace":
        trace(*args)
    else:
        trace(*args)  # 打印堆栈，防止没有指定 level 参数
    return return_value  # return_value 用于 chain 操作


def info(*args, return_value: any = None) -> any:
    log("**** INFO: ", *args)
    return return_value  # return_value 用于 chain 操作


def warn(*args, return_value: any = None) -> any:
    log("**** WARN: ", *args)
    return False  #return_value  # return_value 用于 chain 操作


def warn_pd(*args, return_value: any = None) -> any:
    log_pd("**** WARN: ", *args)
    return return_value  # return_value 用于 chain 操作


def error(*args, return_value: any = None) -> any:
    # 需要关注的错误（grep）
    log("**** ERROR: ", *args)
    return return_value  # return_value 用于 chain 操作


def error_pd(*args, return_value: any = None) -> any:
    # 需要关注的错误（grep）
    log_pd("**** ERROR: ", *args)
    return return_value  # return_value 用于 chain 操作


def trace(*args, return_value: any = None) -> any:
    """ 打印日志，并在stdout中立刻显，同时打印程序调用堆栈 """
    # 需要关注的错误（grep）
    log("**** TRACE-ERROR: ", *args)
    traceback.print_stack()
    return return_value  # return_value 用于 chain 操作


def trace_pd(*args, return_value: any = None) -> any:
    """ 打印日志，并在stdout中立刻显，同时打印程序调用堆栈 """
    # 需要关注的错误（grep）
    log_pd("**** TRACE-ERROR: ", *args)
    traceback.print_stack()
    return return_value  # return_value 用于 chain 操作


def trace_exit_but_not_error(*args) -> bool:
    """ 打印日志 退出程序 """
    trace(*args)
    __exit_but_not_error()
    return False


def exception(err: Exception, *args, return_value: any = None) -> any:
    # 需要关注的错误（grep）
    log("**** EXCEPTION-ERROR: ", f"{errinfo(err)}, ", *args)
    traceback.print_exception(*sys.exc_info())
    return return_value  # return_value 用于 chain 操作


def log_exit(*args, return_value: any = None) -> any:
    # 无法继续需要退出（不是错误）
    log(*args)
    __exit_but_not_error()
    return return_value


# def fatal_exit(*args, return_value: any = None) -> any:
def fatal_exit(msg, return_value: any = None) -> any:
    # 无法继续需要退出的错误
    log("**** FATAL-ERROR: ", msg)
    traceback.print_stack()
    __exit_as_error()
    return return_value


def impl_exit(msg, return_value: any = None) -> any:
    return fatal_exit(f"{msg}, IMPL", return_value=return_value)


def unsupported_exit(msg, return_value: any = None) -> any:
    return fatal_exit(f"{msg}, UNSUPPORTED", return_value=return_value)


def unsupported_warn(msg, return_value: any = None) -> any:
    return warn(f"{msg}, UNSUPPORTED", return_value=return_value)


def exception_exit(err: Exception, *args, return_value: any = None) -> any:
    # 无法继续需要退出的错误
    log("**** EXCEPTION-ERROR: ", f"{errinfo(err)}, ", *args)
    traceback.print_exception(*sys.exc_info())
    __exit_as_error()
    return return_value


def log_return(msg, ret, is_trace, is_fatal, is_log):
    return fatal_exit(msg, return_value=ret) if is_fatal \
        else trace(msg, return_value=ret) if is_trace \
        else log(msg, return_value=ret) if is_log \
        else ret


def not_valid(v, is_trace=False, is_warn=False) -> bool:
    return not is_valid(v, is_trace=is_trace, is_warn=is_warn)


def is_valid(v, is_trace=False, is_warn=False) -> bool:
    """ 检查取值合法性 """
    # log(f"{type(v)=}, {v=}")
    if v is None:
        trace(f"var none") if is_trace else warn(f"var none") if is_warn else False
        return False
    if isinstance(v, float) and np.isnan(v):
        trace(f"float nan") if is_trace else warn(f"float nan") if is_warn else False
        return False
    if isinstance(v, bool) and not v:
        trace(f"bool false") if is_trace else warn(f"bool false") if is_warn else False
        return False
    if isinstance(v, np.bool_) and not v:
        trace(f"bool false") if is_trace else warn(f"bool false") if is_warn else False
        return False
    return True


def valid(v, *args) -> bool:
    """ 检查取值合法性（note：需要计算参数字符串，可能会有性能问题） """
    # log(f"{type(v)=}, {v=}")
    if v is None:
        trace(f"var none : ", *args)
        return False
    if isinstance(v, float) and np.isnan(v):
        trace(f"float nan : ", *args)
        return False
    if isinstance(v, bool) and not v:
        trace(f"bool false : ", *args)
        return False
    if isinstance(v, np.bool_) and not v:
        trace(f"bool false : ", *args)
        return False
    return True


def valid_or_exit(v, *args) -> bool:
    """ 检查取值合法性（不合法则退出程序） """
    check = valid(v, *args)
    not check and __exit_as_error()
    return check


def valid_or_exit_but_not_error(v, *args) -> bool:
    """ 检查取值合法性（不合法则退出程序） """
    check = valid(v, *args)
    not check and __exit_but_not_error()
    return check


def is_debug(debug_tuplelist, trigger_tuple) -> bool:
    """ 是否需要debug """
    for dt in debug_tuplelist:
        # if all([trigger_tuple[i] == dt[i] for i in range(0, len(debug_tuple_list[0]))]):
        if all([trigger_tuple[i] == dt[i] for i in range(0, len(dt))]):
            return True
    return False


def log_debug(trigger_tuple, *args):
    log("debug...." +
        "[" + ",".join(["{}".format(x) for x in trigger_tuple]) + "] " +
        ", ".join(args if args is not None else "")
        )


def debug(debug_tuplelist, trigger_tuple, *args) -> bool:
    """ 打印 debug """
    # 返回 bool 用于chain调用
    check = is_debug(debug_tuplelist, trigger_tuple)
    check and log_debug(trigger_tuple, *args)
    return check


def pause(debug_cond: bool) -> bool:
    """ 加断点 """
    # 返回 bool 用于chain调用
    if debug_cond:
        return True  # note: 此处加断点
    return False


def any_false(*v_tuplelist) -> bool:
    # 存在元素False或None
    return any(not v for v in v_tuplelist)


def any_false_by_list(v_l: list) -> bool:
    # 存在元素False或None
    return True if empty(v_l) else any(not v for v in v_l)


def all_false(*v_tuplelist) -> bool:
    # 所有元素False或None
    return all(not v for v in v_tuplelist)


def all_false_by_list(v_l: list) -> bool:
    # 所有元素False或None
    return True if empty(v_l) else all(not v for v in v_l)


def all_func_true(
        a0r1func_list: list[Callable]
) -> bool:
    """ a0r1func：0个参数1个返回值
    """
    all_valid = True
    for a0r1_func in a0r1func_list:
        if all_valid:  # 只要出现 False 就不在执行其它 func
            func_valid = a0r1_func()
            all_valid = func_valid
    return all_valid


def all_func_true_reason(
        a0r2func_list: list[Callable],
        true_reason_list: list[str]
) -> bool:
    """ a0r2func：0个参数2个返回值
    """
    all_valid = True
    for a0r2_func in a0r2func_list:
        if all_valid:  # 只要出现 False 就不在执行其它 func
            func_valid, func_reason = a0r2_func()
            all_valid = func_valid
            if func_valid:
                true_reason_list.append(func_reason)
    return all_valid


def any_func_true_reason(
        a0r2func_list: list[Callable],
        true_reason_list: list[str]
) -> bool:
    """ a0r2func：0个参数2个返回值
        note：只要有一次调用 func 返回结果为true，则不在调用后面的 func
    """
    any_valid = False
    for a0r2_func in a0r2func_list:
        if not any_valid:  # 只要出现 True 就不在执行其它 func
            func_valid, func_reason = a0r2_func()
            any_valid = func_valid
            if func_valid:
                true_reason_list.append(func_reason)
    return any_valid


def any_func_true_reason_by_arg(
        a1r2func_arglist_tuplelist: list[[Callable, list]],
        true_reason_list: list[str]
) -> bool:
    """ a1r2func：1个参数2个返回值（ 所需的 arglist 包括了多次调用 func 时每次不同的参数 ）
        note：只要有一次调用 func 返回结果为true，则不在调用后面的 func
    """
    any_valid = False
    for a1r2func_arglist in a1r2func_arglist_tuplelist:
        if not any_valid:  # 只要出现 True 就不在执行其它 func
            a1r2_func = a1r2func_arglist[0]
            arglist = a1r2func_arglist[1]
            for arg in arglist:
                if not any_valid:  # 只要出现 True 就不在执行其它 func
                    func_valid, func_reason = a1r2_func(arg)
                    any_valid = func_valid
                    if func_valid:
                        true_reason_list.append(func_reason)
    return any_valid


def any_func_true_reason_by_argfunc(
        a1r2func_arglistfunc_tuplelist: list[[Callable[[Any], Any], Callable[[], list[Any]]]],
        true_reason_list: list[str]
) -> bool:
    """ a1r2func：1个参数2个返回值（ 所需的 arglist 包括了多次调用 func 时每次不同的参数 ）
        arglistfunc: tuplelist of 调用 a1r2func 所需的 arglist
        note：只要有一次调用 func 返回结果为true，则不在调用后面的 func
    """
    any_valid = False
    for a1r2func_arglistfunc in a1r2func_arglistfunc_tuplelist:
        if not any_valid:  # 只要出现 True 就不在执行其它 func
            a1r2_func = a1r2func_arglistfunc[0]
            arglist_func = a1r2func_arglistfunc[1]
            arglist = arglist_func()
            for arg in arglist:
                if not any_valid:  # 只要出现 True 就不在执行其它 func
                    func_valid, func_reason = a1r2_func(arg)
                    any_valid = func_valid
                    if func_valid:
                        true_reason_list.append(func_reason)
    return any_valid


def any_func_true_reason_by_resolve(
        a1r2func_resolvefunc_resolvesignaturefunc_tuplelist: list[[
            Callable[[Any], Any],
            Callable[[Any, Any], Any],
            Callable[[], list[Any]]
        ]],
        true_reason_list: list[str],
) -> bool:
    """ a1r2func：1个参数2个返回值（ 所需的 arglist 包括了多次调用 func 时每次不同的参数 ）
        resolvefunc: 函数用于将 ( resolve_method, resolve_arglist ) 转换为 调用 a1r2func 所需的 arglist
        resolvesignaturefunc: 函数返回 tuplelist of ( resolve_method, resolve_arglist )
        note：只要有一次调用 func 返回结果为true，则不在调用后面的 func
    """
    any_valid = False
    for a1r2func_resolvefunc_resolvesignaturefunc in a1r2func_resolvefunc_resolvesignaturefunc_tuplelist:
        if not any_valid:  # 只要出现 True 就不在执行其它 func
            a1r2_func = a1r2func_resolvefunc_resolvesignaturefunc[0]
            resolve_func = a1r2func_resolvefunc_resolvesignaturefunc[1]
            resolvesignature_tuplelist_func = a1r2func_resolvefunc_resolvesignaturefunc[2]
            for resolve_method, resolve_arglist in resolvesignature_tuplelist_func():
                arglist = resolve_func(resolve_method, resolve_arglist)
                for arg in arglist:
                    if not any_valid:  # 只要出现 True 就不在执行其它 func
                        func_valid, func_reason = a1r2_func(arg)
                        any_valid = func_valid
                        if func_valid:
                            true_reason_list.append(func_reason)
    return any_valid


#############################################
# pandas


def set_pd_option(is_col=True, is_row=True, is_warn=True):
    """ 设置显示参数 """
    #
    if is_col:
        pd.set_option("display.max.columns", None)
        # pd.set_option('display.width', None)
        # pd.set_option('display.max.colwidth', None)
        # Don't wrap repr(DataFrame) across additional lines
        pd.set_option("display.expand_frame_repr", False)
    #
    if is_row:
        pd.set_option("display.max_rows", None)

    #
    if not is_warn:
        # note: 屏蔽告警："value is trying to be set on a copy of a slice from a DataFrame."
        pd.set_option("mode.chained_assignment", None)
        # pd.set_option("chained_assignment", None)

    # # Use 3 decimal places in output display
    # pd.set_option("display.precision", 3)

    pd.set_option("display.float_format", '{:,.4f}'.format)

    pass


def reset_pd_option():
    """ 设置显示参数 """
    #
    pd.reset_option("display.max.columns")
    # pd.reset_option('display.width')
    # pd.reset_option('display.max.colwidth')
    pd.reset_option("display.expand_frame_repr")
    #
    pd.reset_option('display.max_rows')
    #
    pd.reset_option("display.float_format")
    #
    pd.reset_option("mode.chained_assignment")


def set_pd_option_col():
    set_pd_option(is_col=True, is_row=False)


def set_pd_option_warn():
    set_pd_option(is_col=False, is_row=False, is_warn=False)


# def pd_len(df: pd.DataFrame, default: int = 0) -> int:
#     # return len(df) if not_empty(df) else default  # len(None) 会报错
#     return pd_len_row(df, default)


def pd_len_row(df: pd.DataFrame, default: int = 0) -> int:
    return len(df) if not_empty(df) else default  # len(None) 会报错


def pd_len_col(df: pd.DataFrame, default: int = 0) -> int:
    return len(df.columns) if df is not None else default  # len(None) 会报错


def convert_to_pd_col_list(df: pd.DataFrame, col_or_list: Union[str, list[str]],
                           is_return_none_if_any_col_notin=False
                           ) -> Optional[list[str]]:
    col_list = convert_to_list(col_or_list)
    # return [x for x in col_list if is_pd_col(df, x)]
    if is_return_none_if_any_col_notin and any([not is_pd_col(df, x) for x in col_list]):
        return None
    return [x for x in col_list if is_pd_col(df, x)]


def is_pd_col(df: pd.DataFrame, col: str) -> bool:
    return df is not None and col in df.columns


def is_pd_col_list(df: pd.DataFrame, col_list: list[str]) -> bool:
    return all([is_pd_col(df, x) for x in col_list])


def pd_col_list_safe(df: pd.DataFrame, col_list: list[str]) -> list[str]:
    return [x for x in col_list if is_pd_col(df, x)]


def pd_col_safe(df: pd.DataFrame, col: str, default=None):
    return col if df is not None and col in df.columns else default


def to_pd_col_prefix(is_alias=False, is_delim=False, is_placeholder=False, is_temp=False):
    """ 用于特殊处理的pd字段修饰符"""
    return None if False \
        else "$" if is_temp \
        else "_" if is_alias \
        else "?" if is_placeholder \
        else "@" if is_delim \
        else ''


def pd_col_add_prefix(col: Optional[str], is_temp=False, is_alias=False, is_placeholder=False, is_delim=False) -> str:
    """ 用于特殊处理的pd字段（添加修饰符）"""
    prefix = to_pd_col_prefix(is_alias, is_delim, is_placeholder, is_temp)
    return f"{prefix}{col if col is not None else ''}"


def pd_col_list_1(df_or_row: Union[pd.DataFrame, pd.Series],
                  prefix: str = "",
                  *contain_or,
                  exclude_delim: str = None,
                  ) -> list[str]:
    # 可能传入参数为"(None,)"，需要过滤掉
    if empty(df_or_row):
        return []

    col_list = None if False \
        else df_or_row.columns.to_list() if of_pd_dataframe(df_or_row) \
        else list(df_or_row.keys()) if of_pd_series(df_or_row) \
        else []

    col_c_o_l = [x for x in contain_or if not_empty(x)] if not_empty(contain_or) else None
    col_e = exclude_delim

    __new = lambda __col, __l: (__l.count(__col) <= 0)
    __contain = lambda __col, __col_l: all(__col.find(x) >= 0 for x in __col_l)
    __exclude = lambda __col, __ex: __col.find(__ex) < 0 if __ex is not None else True

    r_l = []
    col_p_l = [x for x in col_list if x.startswith(prefix)]
    if empty(col_c_o_l):
        # r_l = col_p_l
        for col_p in col_p_l:
            __exclude(col_p, col_e) and __new(col_p, r_l) \
            and r_l.append(col_p)
    else:
        for col_c in col_c_o_l:
            col_l = col_c if of_list(col_c) else [col_c]
            for col_p in col_p_l:
                __contain(col_p, col_l) and __exclude(col_p, col_e) and __new(col_p, r_l) \
                and r_l.append(col_p)

    # return sorted(r_l)
    return r_l


def pd_col_list_2(df_or_row: Union[pd.DataFrame, pd.Series],
                  prefix_list: list[str] = None,
                  contain_list: list[str] = None,
                  notin_list: list[str] = None,
                  exclude_delim: str = None,
                  is_sort_col=True,
                  ) -> list[str]:
    if empty(df_or_row):
        return []

    col_list = None if False \
        else df_or_row.columns.to_list() if of_pd_dataframe(df_or_row) \
        else list(df_or_row.keys()) if of_pd_series(df_or_row) \
        else []

    __sort = lambda x: sorted(x) if is_sort_col else x

    cl = []
    for prefix in prefix_list or [""]:
        for contain in contain_list or [""]:
            cl += [
                x for x in __sort(pd_col_list_1(df_or_row, prefix, contain, exclude_delim=exclude_delim))
                if x in col_list and (
                    x not in notin_list if notin_list is not None else True
                )
            ]
    return cl


def pd_row_val(row: pd.Series, col: str, default: any = None, is_not_empty=True) -> any:
    val = row[col] if row is not None and col in row else None
    return val if is_not_empty and not_empty(val) else default


def pd_row_val_as_int(row: pd.Series, col: str, default: int = None, is_not_empty=True) -> int:
    return int_safe(pd_row_val(row, col, default, is_not_empty))


def pd_row_val_as_float(row: pd.Series, col: str, default: int = None, is_not_empty=True) -> float:
    return float_safe(pd_row_val(row, col, default, is_not_empty))


def pd_row_val_equal(row: pd.Series, col: str, val_equal: any, default: bool = False, is_not_empty=True) -> bool:
    val = (row[col] == val_equal) if (row is not None and col in row) else default
    return val if (is_not_empty and not_empty(val)) else default


def pd_head(df: pd.DataFrame, head_count: int = 5) -> pd.DataFrame:
    return df.head(head_count) if not_empty(df) else None


def pd_iloc_val(df: pd.DataFrame, col: str, iloc: int = 0, default: any = None,
                is_not_empty=True, is_fatal_default=False) -> any:
    if not_empty(df) and col in df.columns and iloc < len(df):
        val = df.iloc[iloc][col]
        return val if is_not_empty and not_empty(val) else default
    if is_fatal_default:
        fatal_exit(f"df iloc val error, {col=}, {iloc=}, {pd_head(df)=}")
    return default


def pd_iloc_row(df: pd.DataFrame, iloc: int = 0, default: any = None, is_not_empty=True) -> Optional[pd.Series]:
    if not_empty(df) and iloc < len(df):
        val = df.iloc[iloc]
        return val if is_not_empty and not_empty(val) else default
    return default


def pd_cell_val(df: pd.DataFrame,
                k_col: str, k_val: str, v_col: str, default: any = None,
                is_not_empty=True
                ) -> any:
    """ k_col 对应列的取值为 k_val 的行中的 v_col 列 的取值（即 v_val）note: 只处理df首行row """
    if not_empty(df) and k_col in df.columns and v_col in df.columns:
        df2 = df.melt(k_col, v_col, value_name="value")
        #
        # note: pd 需要根据数据类型检索，例如 "date=='20220916'" 无法检索处数据，但是 "date==20220916" 可以
        if pd.api.types.is_string_dtype(df2[f"{k_col}"]):
            df3 = df2.query(f"{k_col}=='{k_val}'")
        else:
            df3 = df2.query(f"{k_col}=={k_val}")
        #
        ds = df3["value"] if not_empty(df3) else None
        if empty(ds):
            val = None
        else:
            val = ds.iloc[0]
            (len(ds) > 1) and warn(
                f"{pd_cell_val.__name__}, row > 1, use iloc 0, {len(ds)=}, "
                f"{k_col=}, f{k_val=}, {v_col=}, {df.head()=}"
            )
        #
        return val if is_not_empty and not_empty(val) else default
    return default


def pd_cell_val_as_int(df: pd.DataFrame,
                       k_col: str, k_val: str, v_col: str, default: int = 0,
                       is_not_empty=True
                       ) -> int:
    return int_safe(pd_cell_val(df, k_col, k_val, v_col, default, is_not_empty))


def pd_cell_val_as_float(df: pd.DataFrame,
                         k_col: str, k_val: str, v_col: str, default: float = 0,
                         is_not_empty=True
                         ) -> float:
    return float_safe(pd_cell_val(df, k_col, k_val, v_col, default, is_not_empty))


def pd_pv_list(df: pd.DataFrame, pk_list: list[str]) -> list:
    """ pk_list 对应的value tuple list """
    return list(df[pk_list].apply(tuple, axis=1).to_dict().values()) if df is not None else []


def convert_pd_time(df: pd.DataFrame, col_time, to_timezone, from_timezone="UTC") -> pd.Series:
    # 将 time 转换为对应时区的日期时间
    return pd.to_datetime(df[col_time], unit="ms") \
        .dt.tz_localize(from_timezone) \
        .dt.tz_convert(to_timezone)


def fill_pd_na_for_numeric(df: pd.DataFrame, fill_val: int):
    __type = lambda __df, __col: pd.api.types.is_numeric_dtype(__df[__col])
    for col in [x for x in df.columns if __type(df, x)]:
        df[col].fillna(fill_val, inplace=True)
    return


def adjust_pd_miss_col_1(df: pd.DataFrame, result_col: str, default: Any, apply_col: str = None):
    if empty(df):
        return
    if result_col not in df.columns:
        df[result_col] = None
    col = apply_col if apply_col in df.columns else result_col
    df[result_col] = df[col].apply(
        lambda x: default if empty(x) else x
    )
    return


def adjust_pd_miss_col_2(df: pd.DataFrame, result_col: str, row_func: Callable[[pd.Series], Any] = None):
    if empty(df):
        return
    if result_col not in df.columns:
        df[result_col] = None
    if row_func is not None:
        df[result_col] = df.apply(
            lambda row: row_func(row),
            axis=1
        )
    return


def select_pd_by_pk(df: pd.DataFrame, pk_dict: dict
                    ) -> Optional[pd.DataFrame]:
    if empty(df) or empty(pk_dict):
        return empty_pd(df)  # None
    pk_list = pk_dict.keys()
    pv_tuple = tuple(pk_dict.values())
    return df[
        df[pk_list].apply(tuple, axis=1).isin([pv_tuple])
    ]


def select_pd_by_pk_from_dictlist(df: pd.DataFrame, kv_dictlist: list[dict], pk_list: list = None, is_notin=False,
                                  is_log=False) -> pd.DataFrame:
    """ 返回df中具有 kv_dictlist 中 pk_list对应取值 的所有结果 """
    fn = select_pd_by_pk_from_dictlist.__name__ if is_log else None
    #
    is_log and (pk_list is None) and log(f"{fn}, pk_list none, use kv_dictlist key")
    pk_list = pk_list or to_dictlist_key_list(kv_dictlist)
    is_log and log(f"{fn}, {pk_list=}")
    #
    is_log and log(f"{fn}, vtl, before")
    vtl = [tuple(kv_dict[pk] for pk in pk_list) for kv_dict in kv_dictlist]
    is_log and log(f"{fn}, vtl, afterr, {vtl=}")
    #
    is_log and log(f"{fn}, df_result calc, before")
    if is_notin:
        df_result = df[~df[pk_list].apply(tuple, axis=1).isin(vtl)]
    else:
        df_result = df[df[pk_list].apply(tuple, axis=1).isin(vtl)]
    is_log and log(f"{fn}, df_result calc, afterr, {df_result=}")
    #
    return df_result


def select_pd_by_pk_from_row(df: pd.DataFrame, row: pd.Series, pk_list: list
                             ) -> Optional[pd.DataFrame]:
    """ 返回df中具有 row中pk_list对应取值 的所有结果 """
    # todo：impl: 性能提高：很慢？？？
    if empty(df) or empty(row) or empty(pk_list):
        return empty_pd(df)  # None
    pv_tuple = tuple(row[pk_list])
    return df[
        df[pk_list].apply(tuple, axis=1).isin([pv_tuple])
    ]


def select_pd_vtl_by_pk_from_row(df: pd.DataFrame, row: pd.Series, pk_list: list,
                                 is_log=False) -> [pd.DataFrame, list[tuple]]:
    """ 返回df中具有 row中pk_list对应取值 的所有结果 """
    fn = select_pd_vtl_by_pk_from_row.__name__ if is_log else None
    #
    is_log and log(f"{fn}, ds_vtl, before")
    ds_vtl = row.to_frame().transpose()[pk_list].apply(tuple, axis=1)
    is_log and log(f"{fn}, ds_vtl, afterr, {ds_vtl=}")
    #
    is_log and log(f"{fn}, df_result, before")
    df_result = df[df[pk_list].apply(tuple, axis=1).isin(ds_vtl)]
    is_log and log(f"{fn}, df_result, afterr, {df_result=}")
    #
    return df_result, ds_vtl.to_list()


def select_pd_of_minus(df_from: pd.DataFrame, df_to: pd.DataFrame, pk_list: list,
                       ) -> Optional[pd.DataFrame]:
    """ df1与df2的差集（集合操作） """
    if empty(df_from):
        return empty_pd(df_from)  # None
    if empty(df_to):
        return df_from.copy()
    df_minus = df_from[
        ~df_from[pk_list].apply(tuple, axis=1).isin(
            df_to[pk_list].apply(tuple, axis=1)  # .to_list()
        )
    ]
    return df_minus


def select_pd_of_intersect(df_a: pd.DataFrame, df_b: pd.DataFrame, pk_list: list,
                           ) -> Optional[pd.DataFrame]:
    """ df1与df2的交集（集合操作） """
    # if empty(df_a) or empty(df_b):
    #     return None
    if empty(df_a):
        return empty_pd(df_a)  # None
    if empty(df_b):
        return empty_pd(df_b)  # None
    # todo: impl: 性能：需要 0.04s
    df_a_pk_tuple = df_a[pk_list].apply(tuple, axis=1)
    df_b_pk_tuple = df_b[pk_list].apply(tuple, axis=1)
    df_intersect = df_a[
        df_a_pk_tuple.isin(df_b_pk_tuple)
    ]
    return df_intersect


def select_pd_range(df: pd.DataFrame, col: str, val_begin, val_end
                    ) -> Optional[pd.DataFrame]:
    if empty(df) or col not in df.columns:
        return empty_pd(df)  # None
    df = df[df[col] >= val_begin]
    df = df[df[col] <= val_end]
    return df


def select_pd_empty(df: pd.DataFrame, col: str,
                    ) -> Optional[pd.DataFrame]:
    # col list 中 任意 val 为 empty
    if empty(df):
        return empty_pd(df)  # None
    if not is_pd_col(df, col):
        return empty_pd(df)  # None
    df = df[df[col].isnull() | df[col].isna() | (df[col].astype("str").str.len() == 0)]
    return df


def select_pd_notempty(df: pd.DataFrame, col: str,
                       ) -> Optional[pd.DataFrame]:
    # col 中 val 为 not empty
    if empty(df):
        return empty_pd(df)  # None
    if not is_pd_col(df, col):
        return empty_pd(df)  # None
    df = df[df[col].notnull() & df[col].notna() & (df[col].astype("str").str.len() > 0)]
    return df


def select_pd_any_empty(df: pd.DataFrame, col_or_list: Union[str, list[str]],
                        ) -> Optional[pd.DataFrame]:
    # col list 中 任意 val 为 empty
    if empty(df):
        return empty_pd(df)  # None
    col_list = convert_to_list(col_or_list)
    if not is_pd_col_list(df, col_list):
        return empty_pd(df)  # None
    for col in pd_col_list_safe(df, col_list):
        df = df[df[col].isnull() | df[col].isna() | (df[col].astype("str").str.len() == 0)]
    return df


def select_pd_all_notempty(df: pd.DataFrame, col_or_list: Union[str, list[str]],
                           ) -> Optional[pd.DataFrame]:
    # col list 中 所有 val 为 not empty
    if empty(df):
        return empty_pd(df)  # None
    col_list = convert_to_list(col_or_list)
    if not is_pd_col_list(df, col_list):
        return empty_pd(df)  # None
    for col in pd_col_list_safe(df, col_list):
        df = df[df[col].notnull() & df[col].notna() & (df[col].astype("str").str.len() > 0)]
    return df


def select_pd_contain(df: pd.DataFrame, col: str, val
                      ) -> Optional[pd.DataFrame]:
    if empty(df) or col not in df.columns:
        return empty_pd(df)  # None
    df = df[df[col].astype("str").str.contains(str_safe(val))]
    return df


def select_pd_prefix(df: pd.DataFrame, col: str, val
                     ) -> Optional[pd.DataFrame]:
    if empty(df) or col not in df.columns:
        return empty_pd(df)  # None
    df = df[df[col].astype("str").str.startswith(str_safe(val))]
    return df


def select_pd_postfix(df: pd.DataFrame, col: str, val
                      ) -> Optional[pd.DataFrame]:
    if empty(df) or col not in df.columns:
        return empty_pd(df)  # None
    df = df[df[col].astype("str").str.endswith(str_safe(val))]
    return df


def select_pd_in(df: pd.DataFrame, col: str, val_list: list,
                 ) -> Optional[pd.DataFrame]:
    if empty(df):
        return empty_pd(df)  # None
    if not is_pd_col(df, col):
        return empty_pd(df)  # None
    df = df[df[col].isin(val_list)]
    return df


def select_pd_equal(df: pd.DataFrame, col: str, val,
                    ) -> Optional[pd.DataFrame]:
    if empty(df) or not is_pd_col(df, col):
        return empty_pd(df)  # None
    # if not is_pd_col(df, col):
    #     return empty_pd(df)  # None
    df = df[df[col] == val]
    return df


def select_pd_not_equal(df: pd.DataFrame, col: str, val
                        ) -> Optional[pd.DataFrame]:
    if empty(df) or col not in df.columns:
        return empty_pd(df)  # None
    df = df[df[col] != val]
    return df


def select_pd_or_greatequal(df: pd.DataFrame, col_list, val) -> Optional[pd.DataFrame]:
    df_result = pd.DataFrame(columns=df.columns)
    for col in col_list:
        df_temp = df[df[col] >= val]
        df_result = df_temp if empty(df_result) \
            else df_result.append(df_temp[~df_temp.index.isin(df_result.index)])
    return df_result


def select_pd_or_lessequal(df: pd.DataFrame, col_list, val) -> Optional[pd.DataFrame]:
    df_result = pd.DataFrame(columns=df.columns)
    for col in col_list:
        df_temp = df[df[col] <= val]
        df_result = df_temp if empty(df_result) \
            else df_result.append(df_temp[~df_temp.index.isin(df_result.index)])
    return df_result


# def query_pd(df: pd.DataFrame,
#              query_op2kv: dict,
#              is_log=False) -> Optional[pd.DataFrame]:
#     """ 将dict中的key和val按照operator组合后进行检索
#         格式：op2kv = { op : op2kv }，可以嵌套
#              op 包括 >, >=, <, <=, ==, "or", "and"
#         例如：
#         {
#             "or" : {
#                 "and" : {
#                     "==" : { "x" : 1 },
#                     ">"  : { "y" : 2 },
#                 },
#                 "==" : {
#                     "z" : 3
#                 },
#             }
#         }
#     """
#     fn = query_pd.__name__ if is_log else None
#     #
#     if empty(df):
#         return None
#     #
#     query_str = None
#     for key in query_dict if not_empty(query_dict) else []:
#         val = query_dict[key]
#         query_str = \
#             (f"{query_str}" if query_str is not None else "") \
#             + (f"&" if query_str is not None and val is not None else "") \
#             + (
#                 f"({key}{query_op}'{val}')" if val is not None and of_str(val)
#                 else f"({key}{query_op}{val})" if val is not None
#                 else query_str
#             )
#     is_log and log(f"{fn}, {query_op=}, {query_dict=}, {query_str=}")
#     #
#     is_log and log(f"{fn}, before query, {pd_len(df)=}")
#     df_result = df if empty(query_str) else df.query(query_str)
#     is_log and log(f"{fn}, afterr query, {pd_len(df_result)=}")
#     #
#     return df_result


def query_pd_equal(df: pd.DataFrame,
                   key: str, val: str = None,  # note: 支持None（返回所有）
                   is_log=False) -> Optional[pd.DataFrame]:
    """ (使用 pandas query 方法进行检索) """
    fn = query_pd_equal.__name__ if is_log else None
    #
    if empty(df):
        return empty_pd(df)  # None
    #
    query_str = f"{key}=='{val}'" if not_empty(val) else None
    is_log and log(f"{fn}, {query_str=}")
    #
    is_log and log(f"{fn}, before query, {pd_len_row(df)=}")
    df_result = df if empty(query_str) else df.query(query_str)
    is_log and log(f"{fn}, afterr query, {pd_len_row(df_result)=}")
    #
    return df_result


def query_pd_notequal(df: pd.DataFrame,
                      key: str, val: str = None,  # note: 支持None（返回所有）
                      is_log=False) -> Optional[pd.DataFrame]:
    """ (使用 pandas query 方法进行检索) """
    fn = query_pd_notequal.__name__ if is_log else None
    #
    if empty(df):
        return empty_pd(df)  # None
    #
    query_str = f"{key}!='{val}'" if not_empty(val) else None
    is_log and log(f"{fn}, {query_str=}")
    #
    is_log and log(f"{fn}, before query, {pd_len_row(df)=}")
    df_result = df if empty(query_str) else df.query(query_str)
    is_log and log(f"{fn}, afterr query, {pd_len_row(df_result)=}")
    #
    return df_result


def query_pd_and(df: pd.DataFrame,
                 query_operator: str, query_dict: dict,
                 is_query_by_array=False,
                 is_log=False) -> Optional[pd.DataFrame]:
    """ (使用 pandas query 方法进行检索)
        将dict中的key和val按照operator组合后进行检索
        note: operator 包括 >, >=, <, <=, ==
        note：组合逻辑为 "与"
    """
    return query_pd_logic(
        df,
        query_logic="&",
        query_operator=query_operator,
        query_kvlist=convert_dict_to_kvlist(query_dict),
        is_query_by_array=is_query_by_array,
        is_log=is_log
    )


def query_pd_or(df: pd.DataFrame,
                query_operator: str, query_dict: dict,
                is_query_by_array=False,
                is_log=False) -> Optional[pd.DataFrame]:
    """ (使用 pandas query 方法进行检索)
        将dict中的key和val按照operator组合后进行检索
        note: operator 包括 >, >=, <, <=, ==
        note：组合逻辑为 "或"
    """
    return query_pd_logic(
        df,
        query_logic="|",
        query_operator=query_operator,
        query_kvlist=convert_dict_to_kvlist(query_dict),
        is_query_by_array=is_query_by_array,
        is_log=is_log
    )


def query_pd_logic(df: pd.DataFrame,
                   query_logic: str,
                   query_operator: str, query_kvlist: list[tuple[str, str]],
                   is_query_by_array=False,
                   is_log=False) -> Optional[pd.DataFrame]:
    """ (使用 pandas query 方法进行检索)
        将dict中的key和val按照operator组合后进行检索
        note: operator 包括 >, >=, <, <=, ==
        note: logic 包括 &, |
    """
    fn = query_pd_logic.__name__ if is_log else None
    #
    if empty(df):
        return empty_pd(df)  # None
    #
    # note: 测试发现，pandas 的 query 子条件数目有限制
    """ 
        如下报错：ValueError: too many inputs
            (board_name=='光学光电子')|(board_name=='AB股')|(board_name=='苹果概念')|(board_name=='LED')|(board_name=='UWB概念')|(board_name=='OLED')|(board_name=='MSCI中国')|(board_name=='MicroLED')|(board_name=='HS300_')|(board_name=='融资融券')|(board_name=='标准普尔')|(board_name=='新零售')|(board_name=='华为概念')|(board_name=='富时罗素')|(board_name=='小米概念')|(board_name=='国产芯片')|(board_name=='物联网')|(board_name=='深成500')|(board_name=='虚拟现实')|(board_name=='超清视频')|(board_name=='深股通')|(board_name=='智慧城市')|(board_name=='MiniLED')|(board_name=='深证100R')|(board_name=='电子纸概念')|(board_name=='智能穿戴')|(board_name=='电子竞技')|(board_name=='人工智能')|(board_name=='医疗美容')|(board_name=='屏下摄像')|(board_name=='互联医疗')|(board_name=='气溶胶检测')
        如下正常
            (board_name=='光学光电子')|(board_name=='AB股')|(board_name=='苹果概念')|(board_name=='LED')|(board_name=='UWB概念')|(board_name=='OLED')|(board_name=='MSCI中国')|(board_name=='MicroLED')|(board_name=='HS300_')|(board_name=='融资融券')|(board_name=='标准普尔')|(board_name=='新零售')|(board_name=='华为概念')|(board_name=='富时罗素')|(board_name=='小米概念')|(board_name=='国产芯片')|(board_name=='物联网')|(board_name=='深成500')|(board_name=='虚拟现实')|(board_name=='超清视频')|(board_name=='深股通')|(board_name=='智慧城市')|(board_name=='MiniLED')|(board_name=='深证100R')|(board_name=='电子纸概念')|(board_name=='智能穿戴')|(board_name=='电子竞技')|(board_name=='人工智能')|(board_name=='医疗美容')|(board_name=='屏下摄像')|(board_name=='互联医疗')
        即子条件数目不能到达 32 个
    """
    if is_query_by_array:
        return __query_pd_logic_by_array(df, query_operator, query_logic, query_kvlist, is_log)
    elif len_safe(query_kvlist) >= 32:
        is_log and log(f"{fn}, query by array, {len_safe(query_kvlist)=} >= 32")
        return __query_pd_logic_by_array(df, query_operator, query_logic, query_kvlist, is_log)
    else:
        return __query_pd_logic_by_string(df, query_operator, query_logic, query_kvlist, is_log)


def __query_pd_logic_by_string(df: pd.DataFrame,
                               query_operator: str, query_logic: str, query_kvlist: list[tuple[str, str]],
                               is_log=False) -> Optional[pd.DataFrame]:
    """ (使用 pandas query 方法进行检索)
        将dict中的key和val按照operator组合后进行检索
        note: operator 包括 >, >=, <, <=, ==
        note: logic 包括 &, |
    """
    fn = __query_pd_logic_by_string.__name__ if is_log else None
    (query_operator not in ["==", ">", ">=", "<", "<="]) and unsupported_exit(f"{fn}, {query_operator=}")
    (query_logic not in ["&", "|"]) and unsupported_exit(f"{fn}, {query_logic=}")
    #
    query_str = None
    if not_empty(query_kvlist):
        for key, val in query_kvlist:
            query_str = \
                (f"{query_str}" if query_str is not None else "") \
                + (f"{query_logic}" if query_str is not None and val is not None else "") \
                + (
                    f"({key}{query_operator}'{val}')" if val is not None and of_str(val)
                    else f"({key}{query_operator}{val})" if val is not None
                    else query_str
                )
    is_log and log(f"{fn}, {query_operator=}, {query_logic=}, {query_kvlist=}, {query_str=}")
    #
    is_log and log(f"{fn}, before query, {pd_len_row(df)=}")
    df_result = df if empty(query_str) else df.query(query_str)
    is_log and log(f"{fn}, afterr query, {pd_len_row(df_result)=}")
    #
    return df_result


def __query_pd_logic_by_array(df: pd.DataFrame,
                              query_operator: str, query_logic: str, query_kvlist: list[tuple[str, str]],
                              is_log=False) -> Optional[pd.DataFrame]:
    """ (使用 pandas query 方法进行检索)
        将dict中的key和val按照operator组合后进行检索
        note: operator 包括 >, >=, <, <=, ==
        note: logic 包括 &, |
    """
    fn = __query_pd_logic_by_array.__name__ if is_log else None
    (query_operator not in ["==", ">", ">=", "<", "<="]) and unsupported_exit(f"{fn}, {query_operator=}")
    (query_logic not in ["&", "|"]) and unsupported_exit(f"{fn}, {query_logic=}")
    #
    cond_result = None if False \
        else (df.index == df.index) if query_logic == "&" \
        else (df.index != df.index) if query_logic == "|" \
        else None
    if empty(query_kvlist):
        cond_result = (df.index == df.index)
    else:
        for key, val in query_kvlist:
            cond_item = None if False \
                else (df[key] == val) if query_operator == "==" \
                else (df[key] > val) if query_operator == ">" \
                else (df[key] >= val) if query_operator == ">=" \
                else (df[key] < val) if query_operator == "<" \
                else (df[key] <= val) if query_operator == "<=" \
                else (df.index == df.index)
            cond_result = None if False \
                else (cond_result & cond_item) if query_logic == "&" \
                else (cond_result | cond_item) if query_logic == "|" \
                else None
    is_log and log(f"{fn}, {query_operator=}, {query_logic=}, {query_kvlist=}, {cond_result=}")
    #
    is_log and log(f"{fn}, before query, {pd_len_row(df)=}")
    df_result = df[cond_result]
    is_log and log(f"{fn}, afterr query, {pd_len_row(df_result)=}")
    #
    return df_result


def query_pd_str(df: pd.DataFrame,
                 query_str: str, dec_group_col_list: list[str],
                 is_log=False, is_warn=True) -> Optional[pd.DataFrame]:
    """ (使用 pandas query 方法进行检索)
        先检索特定"条件"的结果，再对结果的"条件"进行降序，取排序最前的"条件"对应的数据
    """
    fn = query_pd_str.__name__ if is_log or is_warn else None
    #
    is_log and log(f"{fn}, {query_str=}, {dec_group_col_list=}")
    if any_empty(query_str, dec_group_col_list):
        is_warn and warn(f"{fn}, condition empty")
        return df
    #
    index_list = list(
        df.query(query_str)
        .sort_values(dec_group_col_list, ascending=False)
        .groupby(dec_group_col_list, as_index=False, sort=False)
        .groups.values()
    )
    #
    is_log and log(f"{fn}, before query, {pd_len_row(df)=}")
    df_result = df[df.index.isin(index_list[0])] if not_empty(index_list) else None
    is_log and log(f"{fn}, afterr query, {pd_len_row(df_result)=}")
    #
    return df_result


def sort_pd(df: pd.DataFrame, col_or_list: Union[str, list], is_ascending: bool
            ) -> Optional[pd.DataFrame]:
    if any_empty(df, col_or_list):
        return empty_pd(df)  # None
    col_list = col_or_list if of_list(col_or_list) else [col_or_list]
    df = df.sort_values(by=col_list, ascending=is_ascending)
    return df


def sort_group_count_pd(df: pd.DataFrame,
                        first_sort_col_or_list: Union[list[str], str],
                        is_first_ascending: bool,
                        group_col_or_list: Union[str, list[str]],
                        second_sort_col_or_list: Union[str, list[str]],
                        is_second_ascending: bool,
                        count_dist_begin: str = "max",  # all, max, min, q50 # note: qX前X%，X越大结果数越小（q100=max，q0=min）
                        count_dist_end: str = None,  # all, max, min, q50 # note: qX前X%，X越大结果数越小（q100=max，q0=min）
                        is_reset_index=False,
                        is_log=False) -> Optional[pd.DataFrame]:
    """ 先按照指定列排序后分组，每组结果中再按照参数排序后，取最前面的几个记录 """
    fn = sort_group_count_pd.__name__ if is_log else None

    #
    first_sort_col_list = convert_to_list(first_sort_col_or_list)
    group_col_list = convert_to_list(group_col_or_list)
    second_sort_col_list = convert_to_list(second_sort_col_or_list)
    is_log and log(f"{fn}, {first_sort_col_list=}, {group_col_list=}, {second_sort_col_list=}, "
                   f"{count_dist_begin=}, {count_dist_end=}")

    #
    is_log and log(f"{fn}, before query, {pd_len_row(df)=}")
    __limit = lambda dist: max(1, min(99, int(sub_str(dist, "q"))))
    __ratio = lambda dist: 1 - __limit(dist) / 100.0  # note: qX表示前X%，X数值越大结果数量越小（q100=max，q0=min）
    __dist_start = lambda: count_dist_begin
    __dist_stopp = lambda: count_dist_end or count_dist_begin  # note: 没有指定stop参数时使用start参数
    __iloc_start = lambda dgf: None if False \
        else 0 if __dist_start() == "all" \
        else 0 if __dist_start() == "max" \
        else (len(dgf) - 1) if __dist_start() == "min" \
        else 0 if __dist_start() == "q100" \
        else (len(dgf) - 1) if __dist_start() == "q0" \
        else int(len(dgf) * __ratio(__dist_start())) if __dist_start().startswith("q") \
        else unsupported_exit(f"{ __dist_start()=}")
    __iloc_stopp = lambda dgf: None if False \
        else 1 + (len(dgf) - 1) if __dist_stopp() == "all" \
        else 1 if __dist_stopp() == "max" \
        else 1 if __dist_stopp() == "q100" \
        else 1 + (len(dgf) - 1) if __dist_stopp() == "min" \
        else 1 + (len(dgf) - 1) if __dist_stopp() == "q0" \
        else 1 + int(len(dgf) * __ratio(__dist_stopp())) if __dist_stopp().startswith("q") \
        else unsupported_exit(f"{ __dist_stopp()=}")
    df_result = df \
        .sort_values(by=first_sort_col_list, ascending=is_first_ascending) \
        .groupby(group_col_list, as_index=False, sort=False) \
        .apply(lambda dgf: dgf \
               .sort_values(by=second_sort_col_list, ascending=is_second_ascending) \
               .iloc[__iloc_start(dgf):__iloc_stopp(dgf)]
               )
    is_log and log(f"{fn}, afterr query, {pd_len_row(df_result)=}")

    #
    if is_reset_index:
        df_result.reset_index(drop=True, inplace=True)

    #
    return df_result


def agg_pd(df: pd.DataFrame,
           agg_group_col: str, agg_item_col: str,
           col_first: str, col_max: str, col_min: str, col_last: str, col_sum: str,
           hint=None, is_log=False,
           ) -> pd.DataFrame:
    """ 将 item_col 排序后 按照 group_col 进行 聚集，返回 结果 col_xxx """
    df_result = pd.DataFrame(columns=[
        agg_group_col,
        col_first,
        col_max,
        col_min,
        col_last,
        col_sum,
    ])
    dg = df.groupby(agg_group_col)
    for group in dg.groups:
        dgf = dg.get_group(group)
        val_first = dgf[dgf.index == dgf[agg_item_col].idxmin()].iloc[0][col_first]
        val_last = dgf[dgf.index == dgf[agg_item_col].idxmax()].iloc[0][col_last]
        val_max = dgf[col_max].max()
        val_min = dgf[col_min].min()
        val_sum = dgf[col_sum].sum()
        d = {
            agg_group_col: group,
            col_first: val_first,
            col_max: val_max,
            col_min: val_min,
            col_last: val_last,
            col_sum: val_sum,
        }
        is_log and log(f"{name_safe(hint)}, {d}")
        df_result = df_result.append(d, ignore_index=True)
    #
    return df_result


def copy_dict_by_pd_row_or_dict(row_or_dict: Union[pd.Series, dict]) -> dict:
    return row_or_dict.copy().to_dict() if of_pd_series(row_or_dict) \
        else row_or_dict.copy()


def sort_reset_pd(df_result: pd.DataFrame, sort_col_or_list: Union[str, list[str]], sort_ascending: bool,
                  is_inplace: bool = True
                  ) -> pd.DataFrame:
    if empty(df_result):
        return df_result
    sort_col_list = convert_to_list(sort_col_or_list)
    if is_inplace:
        df_result.sort_values(sort_col_list, ascending=sort_ascending, inplace=True)
        df_result.reset_index(drop=True, inplace=True)
    else:
        df_result = df_result.sort_values(sort_col_list, ascending=sort_ascending, inplace=False)
        df_result = df_result.reset_index(drop=True, inplace=False)
    return df_result


def empty_pd(df_copy: Optional[pd.DataFrame]) -> pd.DataFrame:
    # 复制 空 df，保持 col 定义
    # note: 很多时候需要判断 df 是否None，不如直接用保持 col 定义的 空 df，简化代码
    return pd.DataFrame(columns=df_copy.columns) if df_copy is not None else pd.DataFrame()


def copy_pd_col(df: pd.DataFrame, col_src: str, col_dst: str) -> pd.DataFrame:
    df[col_dst] = df[col_src] if is_pd_col(df, col_src) else None
    return df


def update_pd(df_result: pd.DataFrame,
              val_data: Union[pd.DataFrame, pd.Series, np.ndarray],
              col_list: list[str] = None,
              pandas_method="update",
              pandas_update_slice_step=100,
              hint=None, is_log=False):
    """ 更改 df_result 的取值
        # note: 如果 val_data 为 pd.DataFrame 并且 pandas_method = loc 时，数据大时很慢
        测试：gen.sh --shell stats --token hk
                          df_val大小44940x720        df_val大小44940x180
            loc         : 1253s(21m)                NA
            update      : 23s,                      18~25s
        # note: 如果 val_data 为 np.ndarray 或 pd.Series 并且 pandas_method = update 时，很慢（无论数据大小）
        测试：gen.sh --shell good --token us.aapl
                          __calc_good_filter_expect_by
            loc         ： 25s
            update      ： 1320s(22m)
    """
    fn = update_pd.__name__ if is_log else None

    is_log and log(f"{fn}, {hint}, {pandas_method=}, "
                   f"{pd_len_row(df_result)=}, "
                   f"{pd_len_col(df_result)=}, "
                   f"{type(val_data)=}, "
                   f"{len_safe(col_list)=}")

    # update_col_list: list[str] = col_list if col_list is not None \
    #     else val_data.columns if of_pd_dataframe(val_data) \
    #     else val_data.name if of_pd_series(val_data) \
    #     else fatal_and_exit(f"{fn}, col, unsupported {type(val_data)=}", return_value=None)
    # update_val_df_or_ds = val_data[update_col_list] if of_pd_dataframe(val_data) \
    #     else val_data if of_pd_series(val_data) \
    #     else pd.Series(val_data, index=df_result.index, name=update_col_list[0]) if of_np_ndarray(val_data) \
    #     else fatal_and_exit(f"{fn}, val, unsupported {type(val_data)=}", return_value=None)
    # update_index = val_data.index if of_pd_dataframe(val_data) \
    #     else val_data.index if of_pd_series(val_data) \
    #     else fatal_and_exit(f"{fn}, index, unsupported {type(val_data)=}", return_value=None) if pandas_method == "loc" \
    #     else None

    if of_pd_series(val_data) or of_np_ndarray(val_data):
        is_log and log(f"{fn}, direct loc, {type(val_data)=}")
        valid_or_exit(col_list is not None, f"series or ndarray {col_list=} empty, {val_data=}")
        df_result.loc[:, col_list[0]] = val_data
        return

    if not of_pd_dataframe(val_data):
        return fatal_exit(f"{fn}, col, unsupported {type(val_data)=}", return_value=None)

    update_col_list = col_list or val_data.columns

    # note: col很多时可能内存不足，多次处理
    is_log and log(f"{fn}, {hint}, before, {pd_len_row(df_result)=}, {pd_len_col(df_result)=}")
    #
    len_col = len(update_col_list)
    slice_count = int(np.ceil(len_col / pandas_update_slice_step))
    for slice_index in range(0, slice_count):
        slice_start = slice_index * pandas_update_slice_step
        slice_stop = slice_start + pandas_update_slice_step
        update_col_list_slice = update_col_list[slice_start:slice_stop]
        is_log and log(f"{fn}, {hint}, slice, {len_col=}, {slice_count=}, {slice_start=}, {slice_stop=}")
        #
        update_val_df = val_data[update_col_list_slice]
        is_log and log(f"{fn}, {hint}, {pd_len_row(update_val_df)=}, {pd_len_col(update_val_df)=}")
        #
        with TimeLog(f"{hint}, {slice_index=}"):
            if pandas_method == "loc":
                update_index = val_data.index
                df_result.loc[update_index, update_col_list_slice] = update_val_df
            elif pandas_method == "update":
                df_result[update_col_list_slice] = np.nan
                df_result.update(update_val_df, errors="raise")
            else:
                fatal_exit(f"{fn}, unsupported {pandas_method=}")
        #
        is_log and log(f"{fn}, {hint}, dooooo, {pd_len_row(df_result)=}, {pd_len_col(df_result)=}")
    #
    is_log and log(f"{fn}, {hint}, afterr, {pd_len_row(df_result)=}, {pd_len_col(df_result)=}")

    return


def update_pd_row(row_result: pd.Series, from_data: Union[pd.Series, dict],
                  hint=None, is_log=False):
    # note: 不知道为什么 series.update() 方法不起作用，也许是copy的row无法update。我们自己实现
    # fn = update_pd_row.__name__
    if any_empty(row_result, from_data):
        return
    with PandasWarningFalse():
        col_list = None if False \
            else list(from_data.keys()) if isinstance(from_data, dict) \
            else from_data.columns.to_list() if of_pd_series(from_data) \
            else []
        for col in col_list:
            row_result[col] = from_data[col]
    return


def update_pd_col(df_result: pd.DataFrame, col, val,
                  hint=None, is_skip_empty_val=True, is_log=False):
    if not_empty(df_result):
        is_update = False \
                    or (not is_skip_empty_val) \
                    or (is_skip_empty_val and not_empty(val))
        if is_update:
            is_log and log(f"{hint}, set {col=}, {val=}")
            df_result[col] = val
        else:
            is_log and log(f"{hint}, set {col=}, {val=}, val empty, ignore, {is_skip_empty_val=}")
    return


def update_pd_val(df_result: pd.DataFrame, index_or_list: Union[Any, list], from_data: Union[pd.Series, dict],
                  hint=None, is_log=False):
    # note: pandas愚蠢：不进行str转换可能报错：ValueError: Cannot set non-string value '27789449995878400' into a StringArray
    if any_empty(df_result, from_data):
        return

    # todo: impl: 问题：dict中的col在df中还不存在，此时新增到df中的col，是否会需要string转换？

    # note: code："string" 与 pd.api.types.is_string_dtype 不同
    # note: code：不能直接用 "string" dtype类型，报错：TypeError: data type 'string' not understood
    # note: code：不能用 dtype == pandas_dtype 判断，报错：TypeError: Cannot interpret 'StringDtype' as a data type
    __string = lambda __df, __col: \
        pd.api.types.is_dtype_equal(__df[__col].dtype, pd.api.types.pandas_dtype("string")) \
            if is_pd_col(__df, __col) else False

    __value = lambda __df, __col, __val: None if False \
        else str_safe(__val) if __string(__df, __col) \
        else __val

    col_list = None if False \
        else list(from_data.keys()) if isinstance(from_data, dict) \
        else from_data.columns.to_list() if of_pd_series(from_data) \
        else []
    val_list = [
        __value(df_result, col, from_data[col])
        for col in col_list
    ]
    index_list = convert_to_list(index_or_list)
    df_result.loc[index_list, col_list] = val_list

    return


def append_pd(df_result: Optional[pd.DataFrame],
              df_append: pd.DataFrame,
              is_ignore_index=True
              ) -> pd.DataFrame:
    return df_append if empty(df_result) \
        else df_result.append(df_append, ignore_index=is_ignore_index)


def append_pd_list(df_result: Optional[pd.DataFrame],
                   df_append_list: list[pd.DataFrame],
                   is_ignore_index=True,
                   ) -> pd.DataFrame:
    df_result = pd.DataFrame() if df_result is None else df_result
    for df_append in df_append_list:
        df_result = df_result.append(df_append, ignore_index=is_ignore_index)
    return df_result


def append_pd_row(df_result: pd.DataFrame,
                  row_append: pd.Series,
                  is_ignore_index=True,
                  ) -> pd.DataFrame:
    return None if False \
        else pd.DataFrame([row_append]) if empty(df_result) \
        else df_result.append(pd.DataFrame([row_append]), ignore_index=is_ignore_index)


def drop_pd_index(df_result: pd.DataFrame, drop_index, is_inplace=True
                  ) -> pd.DataFrame:
    if empty(df_result):
        return df_result
    # note: 检查index不重复，防止代码错误
    if df_result.index.has_duplicates:
        trace_pd(f"index dup, df_result.head() = ", df_result.head(10))
    #
    df_result.drop(index=drop_index, inplace=is_inplace)
    return df_result


def drop_pd_duplicate(df_result: pd.DataFrame, pk_list: list[str], not_empty_col_list=None,
                      is_log=False) -> pd.DataFrame:
    is_log and log_pd(
        f"{drop_pd_duplicate.__name__}, before, {pd_len_row(df_result)=}, df_result = ", df_result
    )
    df_result.drop_duplicates(pk_list, keep="first", inplace=True, ignore_index=True)
    is_log and log_pd(
        f"{drop_pd_duplicate.__name__}, afterr, {pd_len_row(df_result)=}, df_result = ", df_result
    )
    return df_result


def drop_pd_intersect(df_result: pd.DataFrame, df_check, pk_list: list[str],
                      is_log=False) -> pd.DataFrame:
    df_intersect = select_pd_of_intersect(df_result, df_check, pk_list)
    not_empty(df_intersect) and df_result.drop(index=df_intersect.index, inplace=True)
    is_log and not_empty(df_intersect) and log_pd(
        f"{drop_pd_intersect.__name__}, {pd_len_row(df_intersect)=}, df_intersect = ", df_intersect
    )
    return df_result


def merge_pd(df_list: Union[pd.DataFrame, list[pd.DataFrame]],
             pk_list: list[str],
             how="left",
             ) -> pd.DataFrame:
    """ 合并 （note：要求除了pk其它字段不能重复 """
    df_list = sub_list_notnone(df_list if of_list(df_list) else [df_list])
    return __merge_pd(merge_pd.__name__, df_list, pk_list, how=how, is_drop_dup=True, is_fatal_dup=False)


def merge_pd_partition(df_or_list: Union[pd.DataFrame, list[pd.DataFrame]],
                       pk_list: list[str],
                       ) -> pd.DataFrame:
    """
        note: partition df 定义：不能含有除了 pk_list 以外的相同字段，并且长度相同
        note: 多个partition存在main和sub时col的名称规律不同，简化实现，直接删除相同名称的多余col（假设这些字段取值相同）
    """
    fn = merge_pd_partition.__name__

    def __check(__df_list):
        # 可能不存在
        is_exist = all_not_empty_by_list(__df_list)
        if not is_exist:
            return
        # 必须存在
        # valid_or_exit(is_exist,
        #               f"merge partition df, df exist empty")
        # 长度相同
        len_set = set(len(x) for x in __df_list)
        valid_or_exit(len(len_set) == 1,
                      f"merge partition df, df len diff, "
                      f"{len_set=}, {__df_list=}")
        # todo: bugfix
        # # 不能含有除了pk以为的相同列
        # col_list_list = [pk_list] + [x.columns.to_list() for x in sub_list_skip_none(__df_list)]
        # intersect_col_list = sub_list_intersect(*col_list_list)
        # valid_or_exit(intersect_col_list == pk_list,
        #               f"merge partition df, df col same except pk, "
        #               f"{pk_list=}, {intersect_col_list=}, {col_list_list=}")
        return

    df_list = sub_list_notnone(df_or_list if of_list(df_or_list) else [df_or_list])

    __check(df_list)

    return __merge_pd(fn, df_list, pk_list, how="inner", is_drop_dup=True, is_fatal_dup=False)


def __merge_pd(msg, df_list, pk_list, how, is_drop_dup=True, is_fatal_dup=False):
    suffix_dup = pd_col_add_prefix('dup', is_delim=True)
    df_result: pd.DataFrame = None

    for i, df in enumerate(df_list):
        #
        with TimeLog(f"{msg}, merge, {i}/{len(df_list)}"):
            df_result = df.copy() if df_result is None \
                else df_result.merge(df, how=how, on=pk_list, suffixes=("", f"{suffix_dup}"))
        #
        with TimeLog(f"{msg}, drop, {i}/{len(df_list)}"):
            dup_col_list = sub_list_by_suffix(df_result.columns.to_list(), suffix_dup)
            is_dup = not_empty(dup_col_list)
            is_dup and is_fatal_dup and fatal_exit(
                f"{msg}, dup col, {dup_col_list=}"
            )
            if is_dup and is_drop_dup:
                warn(f"{msg}, drop dup col, {dup_col_list=}")
                df_result.drop(columns=dup_col_list, inplace=True)

    # note: 代码中很多地方需要访问index，例如multitask中cache pk 到 index，需要保持index不变
    # if df_result is not None:
    #     df_result.reset_index(drop=True, inplace=True)

    return df_result


def split_pd_as_dict(df: pd.DataFrame,
                     common_col_list: list[str],
                     col_prefix_list: list[str], col_prefix_delim: str = None,
                     ) -> dict[str, pd.DataFrame]:
    return {
        prefix: df[
            common_col_list +
            sub_list_exclude(pd_col_list_1(df, f"{prefix}{col_prefix_delim or ''}"), common_col_list)  # 排重
            ]
        for prefix in col_prefix_list
    }


def split_pd_as_list(df: pd.DataFrame,
                     common_col_list: list[str],
                     col_prefix_list: list[str], col_prefix_delim: str = None,
                     ) -> list[pd.DataFrame]:
    return [
        df[
            common_col_list +
            sub_list_exclude(pd_col_list_1(df, f"{prefix}{col_prefix_delim or ''}"), common_col_list)  # 排重
            ]
        for prefix in col_prefix_list
    ]


def sub_pd_by_col(df: pd.DataFrame, *col_list_list) -> pd.DataFrame:
    """ col_list 列表排重，但是保证顺序 """
    if empty(df):
        return df
    result_col_list = []
    for col_list in col_list_list:
        result_col_list.extend([x for x in col_list if x not in result_col_list])
    return df[result_col_list]


def sub_pd_of_pk_by_row(df_source: pd.DataFrame, df_exclude: pd.DataFrame, pk_list: list[str]) -> pd.DataFrame:
    """ note: 返回df中col只有pk """
    with TimeLog(f"dfutil.{sub_pd_of_pk_by_row.__name__}"):
        #
        df_source_pk = df_source[pk_list]
        #
        df_exclude_pk = df_exclude[pk_list]
        with PandasWarningFalse():
            exclude_col = pd_col_add_prefix("exclude", is_temp=True)
            df_exclude_pk[exclude_col] = 1
        #
        df_merge = df_source_pk.merge(df_exclude_pk, how="left", on=pk_list, suffixes=("", ""))
        #
        df_miss = df_merge[df_merge[exclude_col] != 1]
        df_miss = df_miss.drop(columns=[exclude_col])
    #
    return df_miss


def iter_pd(df: pd.DataFrame,
            iter_func: Callable[[pd.Series], Any],
            pbar_row_desc_func: Callable[[pd.Series], str] = None,
            pbar_row_postfix_func: Callable[[pd.Series], str] = None,
            log_df_desc_func: Callable[[pd.DataFrame], str] = None,
            log_row_desc_func: Callable[[pd.Series], str] = None,
            is_pbar_percent=True,
            is_try_exception=False,
            hint=None):
    """ 遍历df """
    if df is None:
        return

    #
    log(f"{hint}, {log_df_desc_func(df) if log_df_desc_func is not None else ''}")

    #
    pbar_total = len(df)
    pbar_unit = int(pbar_total / 100)
    pbar_unit = 1 if pbar_unit <= 0 else pbar_unit  # ZeroDivisionError: integer division or modulo by zero
    # pbar_desc = pbar_desc_func() if not_empty(pbar_desc_func) else f"iter_df({hint})"
    with tqdm(total=pbar_total) as pbar:
        for i, index in enumerate(df.index):
            #
            row = df.loc[index]

            not_empty(pbar_row_desc_func) and pbar.set_description(pbar_row_desc_func(row))
            not_empty(pbar_row_postfix_func) and pbar.set_postfix_str(pbar_row_postfix_func(row))

            #
            is_progress, pbar_update = ((i % pbar_unit == 0), pbar_unit) if is_pbar_percent else (True, 1)
            #
            is_progress and pbar.update(pbar_update)
            #
            is_progress and not_empty(log_row_desc_func) and log(
                f"{hint}, iter = {i}/{pbar_total}, {log_row_desc_func(row)}"
            )

            #
            if not is_try_exception:
                iter_func(row)
            else:
                # noinspection PyBroadException
                try:
                    iter_func(row)
                except Exception as err:
                    exception(err, f"{hint}")
    #
    return


#############################################

def tqdm_update(pbar, desc_str: str = None, postfix_str: str = None, update_count: int = 1):
    if not_empty(desc_str):
        pbar.set_description(desc_str)
    if not_empty(postfix_str):
        pbar.set_postfix_str(postfix_str)
    #
    pbar.update(update_count)
    return


#############################################

def path_safe(pathfile):
    parent_dir_index = len(pathfile) - pathfile[::-1].index(os.sep)
    parent_dir = pathfile[0:parent_dir_index]
    pathlib.Path(parent_dir).mkdir(parents=True, exist_ok=True)
    # log("....path : " + parent_dir)
    return


def to_path_parent(pathfile):
    """ pathfile 对应的最近上级目录 """

    def __try_index(__prefix, __sep):
        # noinspection PyBroadException
        try:
            return len(__prefix) - __prefix[::-1].index(__sep)
        except Exception as err:
            return 0  # return exception(err, return_value=0)

    # note: "\"和"/"可能混用
    parent_dir_index_slash = __try_index(pathfile, "\\")
    parent_dir_index_backslash = __try_index(pathfile, "/")
    parent_dir_index = max([parent_dir_index_slash, parent_dir_index_backslash])
    #
    parent_dir = pathfile[0:parent_dir_index]
    return parent_dir


def to_path_filename(pathfile):
    """ pathfile 对应的文件名称 """
    # return pathfile[pathfile.rfind(os.sep) + len(os.sep):]
    parent_dir = to_path_parent(pathfile)
    return pathfile[len(parent_dir):]


def create_path(pathfile, is_log):
    # 创建亲代目录，否则会报告错误
    parent_dir = to_path_parent(pathfile)
    pathlib.Path(parent_dir).mkdir(parents=True, exist_ok=True)
    # is_log and log(f"....path : {parent_dir}")  # 不日志太频繁
    return


def is_path_contain_sep(pathfile: str) -> bool:
    return is_str_contain_any(pathfile, ["/", os.sep])


# 自动检查并创建文件目录（使用exist_ok参数）add by hhx 2024.07.29
# 参数: directory_path: 目标目录的路径。
def create_directory(directory_path):
    try:
        os.makedirs(directory_path, exist_ok=True)
        # print(f"目录 '{directory_path}' 已创建或已存在！")
    except OSError as e:
        print(f"创建目录'{directory_path}'时发生错误: {e}")


# 判断文件或目录是否存在 add by hhx 2024.08.16
def is_path_exist(path) -> bool:
    # 方法1
    is_exist = pathlib.Path(path).is_file()
    # 方法2
    # is_exist = os.path.exists(path)
    return is_exist


# 删除文件  add by hhx 2024.11.21
def delete_file(filename):
    if is_path_exist(filename):
        os.remove(filename)
        print(f"文件 {filename} 删除成功！")
    else:
        print(f"文件 {filename} 不存在。")


def copy_file(file_src: str, file_dst: str, is_log=True):
    try:
        create_path(file_src, is_log)
        create_path(file_dst, is_log)
        shutil.copyfile(file_src, file_dst)
        is_log and log(f"....copy : {file_src} > {file_dst}")
    except FileNotFoundError as err:
        warn(f"copy file, {errinfo(err)}, {file_src=}, {file_dst=}")
    except Exception as err:
        exception(err, f"copy file, {file_src=}, {file_dst=}")
    return


def list_path_file_pattern(list_file_path: str, list_file_pattern: str) -> list[str]:
    return [
        x.as_posix()
        for x in pathlib.Path(list_file_path).rglob(list_file_pattern)
        if x.is_file()
    ]


def delete_path_file_pattern(path: str, pattern: str, is_try=False, is_log=True):
    delete_count = 0
    for file in pathlib.Path(path).rglob(pattern):
        delete_count += 1
        if is_try:
            is_log and log(f"....delete : {file}, is_try")
        else:
            is_log_file_missing = False  # True # note: 文件不存在时报告异常，这样不在持续打印成功删除后的日志
            try:
                file.unlink(missing_ok=is_log_file_missing)
                warn(f"....delete : {file}, done")
            except FileNotFoundError as err:
                is_log_file_missing and warn(f"delete file, {errinfo(err)}, {file=}")
            except Exception as err:
                # note: 可能文件已经不存在了（例如multitask），不影响，不要error了，避免影响grep
                warn(err, f"delete file fail, {path=}, {pattern=}")
    # #
    # # file_list 类型是<class 'generator'>，无法 len
    # # (len(file_list) <= 0) and warn(
    # (delete_count <= 0) and log(
    #     f"....delete file empty, {path=}, {pattern=}"
    # )
    #
    return


# def delete_path_file(delete_path_file: str):
#     for pathfile in pathlib.Path(delete_path_file).rglob("*"):
#         warn(f"....delete : {pathfile}")
#         try:
#             pathfile.unlink()
#         except Exception as err:
#             # note: 可能文件已经不存在了（例如multitask），不影响，不要error了，避免影响grep
#             warn(err, f"delete file fail, {delete_file_path=}, {delete_file_pattern=}")
#         return


#############################################


__empty_type_2_validator = {
    int: lambda x: True,  # int
    float: lambda x: not np.isnan(x),  # float：不是nan
    str: lambda x: len(x),  # str：必须有值
    list: lambda x: len(x) and not_empty(x[0]),  # list：note: 至少1个非空元素
    dict: lambda x: len(x),  # dict：至少1个元素
    set: lambda x: len(x),  # set：至少1个元素
    tuple: lambda x: len(x),  # tuple：至少1个元素
    # Row: lambda x: len(x),  # pyodbc查询数据库，处理查询的数据时报错 add by hhx 2025.02.17
    pd.DataFrame: lambda x: len(x),  # df：至少1个元素
    pd.Series: lambda x: len(x),  # ds：至少1个元素
    pd.Index: lambda x: len(x),  # index：至少1个元素
    np.ndarray: lambda x: len(x),  # np：至少1个元素
    np.int64: lambda x: True,  # np: int
    np.int32: lambda x: True,  # np: int
}


def not_empty(v: any) -> bool:
    # 空
    if v is None:
        return False
    if v is pd.NA:  # pandas._libs.missing.NAType
        return False

    # 函数
    if callable(v):
        return True

    # 预定义类型
    for t in __empty_type_2_validator:
        if isinstance(v, t):
            return True if __empty_type_2_validator[t](v) else False

    # note: 没有预定义类型时，退化为判断是否为None
    trace(f"not_empty, {type(v)=} unknown")
    # fatal_exit(f"not_empty, {type(v)=} unknown")
    return v is not None


def all_not_empty(*v_tuplelist) -> bool:
    # 所有元素都非空（任意元素空则False）
    return all(not_empty(v) for v in v_tuplelist)


def all_not_empty_by_list(v_l: list) -> bool:
    # 所有元素都非空（任意元素空则False）
    # note: 空list 时  all 会返回 True，需要排除这种情况
    return False if empty(v_l) else all(not_empty(v) for v in v_l)


def any_not_empty(*v_tuplelist) -> bool:
    # 任意元素非空（所有元素空则False）
    # 不用优化实现，因为调用本方法时v_l都已经被计算了
    return any(not_empty(v) for v in v_tuplelist)


def any_not_empty_by_list(v_l: list) -> bool:
    # 任意元素非空（所有元素空则False）
    # 不用优化实现，因为调用本方法时v_l都已经被计算了
    return False if empty(v_l) else any(not_empty(v) for v in v_l)


def empty(v) -> bool:
    return not not_empty(v)


def all_empty(*v_tuplelist) -> bool:
    # 所有元素都空
    return all(empty(v) for v in v_tuplelist)


def all_empty_by_list(v_l: list) -> bool:
    # 所有元素都空
    return True if empty(v_l) else all(empty(v) for v in v_l)


def any_empty(*v_tuplelist) -> bool:
    # 任意元素为空
    # 不用优化实现，因为调用本方法时v_l都已经被计算了
    return any(empty(v) for v in v_tuplelist)


def any_empty_by_list(v_l: list) -> bool:
    # 任意元素为空
    # 不用优化实现，因为调用本方法时v_l都已经被计算了
    return True if empty(v_l) else any(empty(v) for v in v_l)


def empty_safe(v: Any, default: Any) -> Any:
    return default if empty(v) else v


def none(v) -> bool:
    return v is None


def all_none(*v_tuplelist) -> bool:
    # 所有元素都空
    return all(none(v) for v in v_tuplelist)


def all_none_by_list(v_l: list) -> bool:
    # 所有元素都空
    return True if empty(v_l) else all(none(v) for v in v_l)


def any_none(*v_tuplelist) -> bool:
    # 任意元素为空
    # 不用优化实现，因为调用本方法时v_l都已经被计算了
    return any(none(v) for v in v_tuplelist)


def any_none_by_list(v_l: list) -> bool:
    # 任意元素为空
    # 不用优化实现，因为调用本方法时v_l都已经被计算了
    return True if empty(v_l) else any(none(v) for v in v_l)


def not_none(v) -> bool:
    return v is not None


def all_not_none(*v_tuplelist) -> bool:
    # 所有元素都非空（任意元素空则False）
    return all(not_none(v) for v in v_tuplelist)


def all_not_none_by_list(v_l: list) -> bool:
    # 所有元素都非空（任意元素空则False）
    return False if empty(v_l) else all(not_none(v) for v in v_l)


def any_not_none(*v_tuplelist) -> bool:
    # 任意元素非空（所有元素空则False）
    # 不用优化实现，因为调用本方法时v_l都已经被计算了
    return any(not_none(v) for v in v_tuplelist)


def any_not_none_by_list(v_l: list) -> bool:
    # 任意元素非空（所有元素空则False）
    # 不用优化实现，因为调用本方法时v_l都已经被计算了
    return False if empty(v_l) else any(not_none(v) for v in v_l)


def none_safe(v: Any, default: Any) -> Any:
    return default if v is None else v


# def not_zero(v) -> bool:
#     if v is None:
#         return False
#     if isinstance(v, int) and v != 0:
#         return True
#     if isinstance(v, float) and v != 0:
#         return True
#     return False


def all_zero(*v_tuplelist) -> bool:
    # 所有元素都0
    return all(v == 0 for v in v_tuplelist)


def all_zero_by_list(v_l: list) -> bool:
    # 所有元素都0
    return True if empty(v_l) else all(v == 0 for v in v_l)


def all_not_zero(*v_tuplelist) -> bool:
    # 所有元素都非0
    return all(v != 0 for v in v_tuplelist)


def all_not_zero_by_list(v_l: list) -> bool:
    # 所有元素都非0
    return False if empty(v_l) else all(v != 0 for v in v_l)


def any_not_zero(*v_tuplelist) -> bool:
    # 存在元素非0
    # 不用优化实现，因为调用本方法时v_l都已经被计算了
    return any(v != 0 for v in v_tuplelist)


def any_not_zero_by_list(v_l: list) -> bool:
    # 存在元素非0
    # 不用优化实现，因为调用本方法时v_l都已经被计算了
    return False if empty(v_l) else any(v != 0 for v in v_l)


def all_equal(*v_tuplelist) -> bool:
    return len(set(v_tuplelist)) == 1


def all_equal_by_list(v_l: list) -> bool:
    return False if empty(v_l) else len(set(v_l)) == 1


def len_safe(v) -> int:
    # noinspection PyBroadException
    try:
        return 0 if v is None else len(v)
    except Exception as err:
        return 0


# 删除元组中的None
def remove_none_from_tuple(tup):
    if len_safe(tup) > 0:
        return tuple(x for x in tup if x is not None)
    else:
        return tup


# 删除元组中None后的元组长度
def len_tuple_with_remove_none(tup):
    t = remove_none_from_tuple(tup)
    return len_safe(t)


def var_val(m_file: str, v_name: str, default: Any) -> Any:
    # file 模块 的 name 变量名称 的取值
    # （var 是指 python 文件中定义的变量）
    if empty(v_name):
        return default
    try:
        file = to_file_prefix(m_file)
        return getattr(sys.modules[file], v_name)
    except Exception as err:
        exception(err, f"{var_val.__name__}, {m_file=}, {v_name=}")
        return default


def var_name_list(m_name: str, v_name_prefix: str) -> list[str]:
    # （var 是指 python 文件中定义的变量）
    try:
        sm = sys.modules[m_name]
        return [x for x in dir(sm) if x.startswith(v_name_prefix)]
    except Exception as err:
        exception(err, f"{var_name_list.__name__}, {m_name=}, {v_name_prefix=}")
        return []


def var_val_list(m_name: str, v_name_prefix: str) -> list[Any]:
    # （var 是指 python 文件中定义的变量）
    try:
        sm = sys.modules[m_name]
        return [getattr(sm, x) for x in dir(sm) if x.startswith(v_name_prefix)]
    except Exception as err:
        exception(err, f"{var_val_list.__name__}, {m_name=}, {v_name_prefix=}")
        return []


# 是否字符串类型 note by hhx 2024.10.22
def of_str(v: any) -> bool:
    return False \
        or isinstance(v, str) \
        or False


# 是否字典类型 note by hhx 2024.10.22
def of_dict(v: any) -> bool:
    """ 是不是可以当dict使用 """
    return False \
        or isinstance(v, dict) \
        or False


def of_list(v: any) -> bool:
    """ 是不是可以当list使用 """
    # note: pd.Index：convert_2_list 不能再次转换，可以直接使用，否则 df.loc[index_list] 类似操作报错：KeyError(f"None of [{key}] are in the [{axis_name}]")
    return False \
        or isinstance(v, list) \
        or isinstance(v, np.ndarray) \
        or isinstance(v, pd.Index) \
        or False


def of_tuple(v: any) -> bool:
    """ 是不是可以当list使用 """
    return False \
        or isinstance(v, tuple) \
        or False


def of_pd_to_list(v: any) -> bool:
    """ 是不是具有to_list方法的pd类型从而转换为list """
    return False \
        or isinstance(v, pd.Index) \
        or False


def of_pd_dataframe(v: any) -> bool:
    return False \
        or isinstance(v, pd.DataFrame) \
        or False


def of_pd_series(v: any) -> bool:
    return False \
        or isinstance(v, pd.Series) \
        or False


def of_pd(v: any) -> bool:
    return False \
        or isinstance(v, pd.DataFrame) \
        or isinstance(v, pd.Series) \
        or False


def of_np_ndarray(v: any) -> bool:
    return False \
        or isinstance(v, np.ndarray) \
        or False


def sleep(second: float):
    time.sleep(second)


def is_weekend(date: int, is_log=False) -> bool:
    # 周末（周六，周日）
    return datetime_by_date(date).isoweekday() in [6, 7]


def is_weekend_by(datetime_obj: datetime) -> bool:
    # 周末（周六，周日）
    return datetime_obj.isoweekday() in [6, 7]


def is_monday(date: int, is_log=False) -> bool:
    # 周一
    return datetime_by_date(date).isoweekday() in [1]


def to_monday_begin(date: int) -> int:
    date_begin = date
    date_count = -7
    # return [x for x in date_list if is_monday(x)][0]
    date_list = date_to_list(date_begin, date_count)
    for x in date_list[::-1]:  # 性能：大概率靠近date的应该是周一
        if is_monday(x):
            return x
    return fatal_exit(f"{to_monday_begin.__name__}, check code")


def to_monday_begin_by_list(date_list: list[int]) -> Optional[int]:
    # 可能 date_list 起始日期不是周一，需要向前定位到准确的周一
    if empty(date_list):
        return None
    return to_monday_begin(date_list[0])


def to_week_index_of_year(date: int) -> int:
    # 年度周序号（note: 从 1 起始）
    first_date_of_year = int(date / 100 / 100) * 10000 + 1 * 100 + 1
    return __to_week_index_by(date, first_date_of_year)


def to_week_index_of_month(date: int) -> int:
    # 月度周序号（note: 从 1 起始）
    first_date_of_month = int(date / 100) * 100 + 1
    return __to_week_index_by(date, first_date_of_month)


def __to_week_index_by(date: int, date_first: int) -> int:
    # note: date list 很大时速度很慢，缓存提高性能
    def __calc():
        mm = int(int(date / 100) % 100)

        # note: 防止 0101 不是 monday，需要补足前面的当周日期
        prev_count = 7
        date_begin = date_to(date_first, 0 - prev_count)
        date_count = 0 - (mm * 31) - prev_count

        #
        date_list = [x for x in date_to_list(date, date_count) if x >= date_begin]
        monday_list = [x for x in date_list if is_monday(x)]
        week_index = len(monday_list)

        return week_index

    return CacheUtil.load_cache(
        key=f"{__file__}.{__to_week_index_by.__name__}.{date}.{date_first}",
        init_func=lambda: __calc(),
    )


def __to_monday_begin_by(date: int) -> int:
    yyyy = to_date_year(date)
    mm = to_date_month(date)
    yyyy_prev = yyyy - 1 if mm == 1 else yyyy
    mm_prev = 12 if mm == 1 else mm - 1
    date_list = [
        y * 10000 + m * 100 + d
        for y in unique_list([yyyy_prev, yyyy])
        for m in unique_list([mm_prev, mm])
        for d in range(1, 31 + 1)
    ]
    date_list = [x for x in date_list if x <= date]
    date_2_is_monday = {}
    for d in date_list:
        # noinspection PyBroadException
        try:
            date_2_is_monday[d] = is_monday(d)
        except Exception as err:
            pass

    for d in sorted(date_2_is_monday.keys(), reverse=True):
        if date_2_is_monday[d]:
            return d

    return fatal_exit(f"{__to_monday_begin_by.__name__}, check code")


def in_date_count(date_1: int, date_2: int, date_count_max: int) -> bool:
    """ 是否处于自然日范围内 （note：自然日）"""
    dt_date_1 = __to_datetime_date_by(date_1)
    dt_date_2 = __to_datetime_date_by(date_2)
    return abs((dt_date_2 - dt_date_1).days) <= date_count_max


# note: 提高性能
__date_2_datetime_dict: dict[int, datetime] = {}


def __to_datetime_date_by(int_date: int) -> datetime:
    int_date = int_safe(int_date)
    if int_date not in __date_2_datetime_dict:
        __date_2_datetime_dict[int_date] = datetime_by_date(int_date)
    return __date_2_datetime_dict[int_date]


def timestamp_str(delim="", ms_digit=3) -> str:
    return f"{timestamp_yyyymmdd_str()}{delim}{timestamp_hhmmss_str()}{delim}{timestamp_microsecond_str(ms_digit)}"


def timestamp_yyyymmddhhmmss() -> int:
    # 例如：20210501165107
    return int(__datetime_now().strftime("%Y%m%d%H%M%S"))


def timestamp_yyyymmddhhmmss_by(date_curr: int, time_curr: int) -> int:
    # 例如：20210501165107
    return int("{:0>8d}{:0>6d}".format(date_curr, time_curr))


def timestamp_yyyymmddhhmmss_str() -> str:
    # 例如：20210501165107
    return __datetime_now().strftime("%Y%m%d%H%M%S")


def timestamp_yyyymmdd() -> int:
    # 例如：20210501
    return int(__datetime_now().strftime("%Y%m%d"))


def timestamp_yyyymmdd_str() -> str:
    # 例如：20210501
    return __datetime_now().strftime("%Y%m%d")


def timestamp_hhmm_str() -> str:
    # 例如：1651
    return __datetime_now().strftime("%H%M")


def timestamp_hhmmss_str() -> str:
    # 例如：165107
    return __datetime_now().strftime("%H%M%S")


def timestamp_microsecond_str(digit=3) -> str:
    # 例如：254
    # return __datetime_now().strftime("%f")
    now = time.time()
    microsecond = repr(now).split(".")[1][:digit]
    return microsecond


def timestamp_by_datetime(datetime_obj: datetime = None, timestamp_fmt="%Y%m%d%H%M%S") -> int:
    # 例如：20210501165107
    dt = datetime_obj or __datetime_now()
    return int(dt.strftime(timestamp_fmt))


def timestamp_by_str_of_readable(datetime_str: str, timezone_str: str = None) -> int:
    """例如：2022-04-11 12:34:56 -> 20220411123456"""
    return timestamp_by_str(
        datetime_str, datetime_fmt="%Y-%m-%d %H:%M:%S", timestamp_fmt="%Y%m%d%H%M%S",
        timezone_str=timezone_str
    )


def timestamp_by_str(datetime_str: str,
                     datetime_fmt="%Y-%m-%d %H:%M:%S",
                     timestamp_fmt="%Y%m%d%H%M%S",
                     timezone_str: str = None
                     ) -> int:
    """例如：2022-04-11 12:34:56 -> 20220411123456"""
    datetime_obj = datetime_by_str(datetime_str, datetime_fmt, timezone_str)
    return int(datetime_obj.strftime(timestamp_fmt))


def timestamp_by_count(timestamp: int, second_count: int, timestamp_fmt="%Y%m%d%H%M%S") -> int:
    return timestamp_by_datetime(datetime_to(datetime_by_timestamp(timestamp), second_count), timestamp_fmt)


def timestamp_yyyymmddhhmmss_segment(
        date: int, time_start: int, time_stop: int, segment_count: int, segment_index: int,
        is_log=False
) -> int:
    # 例如：20210501165107 ( start 和 stop 按照 count 等分后取 index 部分的 time，和 date 组合）

    if segment_count <= 0:
        trace(f"segment arg illegal, {segment_count=} <= 0")
        return timestamp_yyyymmddhhmmss_by(date, time_start)

    ts = time_segment(time_start, time_stop, segment_count, segment_index, is_log=is_log)
    return timestamp_yyyymmddhhmmss_by(date, ts)


def timestamp_segment_start(
        timestamp: int, time_start: int, time_stop: int, minute_step: int,
        timestamp_fmt="%Y%m%d%H%M%S",
        is_log=False
) -> int:
    """ 将 timestamp 在 start 和 stop 之间 按照 step 划分为区段后，返回所属区段的开始时间戳 """
    (timestamp_fmt != "%Y%m%d%H%M%S") and fatal_exit(f"unsupported {timestamp_fmt=}")

    date = int(timestamp / 1000000)

    datetime_start, datetime_stop = datetime_by_time(time_start), datetime_by_time(time_stop)
    minute_range = int((datetime_stop - datetime_start).seconds / 60)
    minute_list = [x for x in range(0, minute_range + minute_step, minute_step)]

    datetime_arg = datetime_by_time(int(timestamp % 1000000))
    minute_arg = int((datetime_arg - datetime_start).seconds / 60)
    segment_index = min([np.digitize(minute_arg - minute_step, minute_list), (len(minute_list) - 1)])
    segment_minute = minute_list[segment_index]

    # note: time_to 方法中 second_count 以1作为 base，即表示 time_begin
    return timestamp_yyyymmddhhmmss_by(date, time_to(time_start, segment_minute * 60 + 1))


def timestamp_segment_list(
        timestamp: int, time_start: int, time_stop: int, minute_step: int,
        timestamp_fmt="%Y%m%d%H%M%S",
        is_log=False
) -> list[int]:
    """ 将 timestamp 在 start 和 stop 之间 按照 step 划分为区段后，返回所属区段的所有时戳列表 """
    (timestamp_fmt != "%Y%m%d%H%M%S") and fatal_exit(f"unsupported {timestamp_fmt=}")

    date = int(timestamp / 1000000)

    datetime_start, datetime_stop = datetime_by_time(time_start), datetime_by_time(time_stop)
    minute_range = int((datetime_stop - datetime_start).seconds / 60)
    minute_list = [x for x in range(0, minute_range + minute_step, minute_step)]

    return [
        # note: time_to 方法中 second_count 以1作为 base，即表示 time_begin
        timestamp_yyyymmddhhmmss_by(date, time_to(time_start, segment_minute * 60 + 1))
        for segment_minute in minute_list
        if segment_minute < minute_range
    ]


def timestamp_segment_list_by_date(
        date: int, time_start: int, time_stop: int, minute_step: int,
        timestamp_fmt="%Y%m%d%H%M%S",
        is_log=False
) -> list[int]:
    """ 将 timestamp 在 start 和 stop 之间 按照 step 划分为区段后，返回所属区段的所有时戳列表 """
    (timestamp_fmt != "%Y%m%d%H%M%S") and fatal_exit(f"unsupported {timestamp_fmt=}")

    datetime_start, datetime_stop = datetime_by_time(time_start), datetime_by_time(time_stop)
    minute_range = int((datetime_stop - datetime_start).seconds / 60)
    minute_list = [x for x in range(0, minute_range + minute_step, minute_step)]

    return [
        # note: time_to 方法中 second_count 以1作为 base，即表示 time_begin
        timestamp_yyyymmddhhmmss_by(date, time_to(time_start, segment_minute * 60 + 1))
        for segment_minute in minute_list
        if segment_minute < minute_range
    ]


def timestamp_segment_index(
        timestamp: int, time_start: int, time_stop: int, minute_step: int,
        timestamp_fmt="%Y%m%d%H%M%S",
        is_log=False
) -> int:
    """ 将 timestamp 在 start 和 stop 之间 按照 step 划分为区段后，返回所属区段的 index """
    (timestamp_fmt != "%Y%m%d%H%M%S") and fatal_exit(f"unsupported {timestamp_fmt=}")

    hh = int(timestamp % 1000000 / 10000)
    hh_start, hh_stop = int(time_start / 10000), int(time_stop / 10000)
    hh_index = hh - hh_start

    mm_count = int(60 / minute_step)

    mm_start = int(time_start % 10000 / 100)
    mm_start_index = int(mm_start / minute_step)

    mm = int(timestamp % 1000000 % 10000 / 100)
    mm_index = int(mm / minute_step)

    index = hh_index * mm_count + mm_index - mm_start_index
    return index


def to_date_year(date_curr: int) -> int:
    # 例如：20210501 -> 2021
    return int(date_curr / 10000)


def to_date_month(date_curr: int) -> int:
    # 例如：20210501 -> 5
    return int(date_curr / 100 % 100)


def to_date_year_month(date_curr: int) -> int:
    # 例如：20210501 -> 202105
    return int(date_curr / 100)


def to_date_week_str(date: int, is_return_year_week_index=True, is_return_monday_yyyymmdd=True) -> str:
    # 例如：20210501 -> 2021w18m20210426
    week = ""

    if is_return_year_week_index:
        yyyy = to_date_year(date)
        week += f"{yyyy}w{pad_str_left(str(to_week_index_of_year(date)), 2, '0')}"

    if is_return_monday_yyyymmdd:
        monday = to_monday_begin(date)
        week += f'm{monday}'

    # week += f"(mwi={yyyymm}_{to_week_index_of_month(week_date_begin)})"
    #   if is_return_month_week_index else ""

    #
    return week


def to_date_day(date_curr: int) -> int:
    # 例如：20210501165107 -> 1
    return int(date_curr % 100)


def date_to(date_begin: int, date_count: int) -> int:
    """ 例如：20210501
        note: date_count以1（或者-1）作为base（即表示date_begin），支持正数和负数
    """
    return date_to_skip(date_begin, date_count)


def date_to_skip_weekend(date_begin: int, date_count: int) -> int:
    """ 例如：20210501
        note: date_count以1（或者-1）作为base（即表示date_begin），支持正数和负数
    """
    return date_to_skip(date_begin, date_count, skip_func=lambda datetime_obj: is_weekend_by(datetime_obj))


def date_to_skip(date_begin: int, date_count: int, skip_func: Callable[[datetime], bool] = None) -> int:
    """ 例如：20210501
        note: date_count以1（或者-1）作为base（即表示date_begin），支持正数和负数
        note: skip_func规范：参数 datetime，返回 bool
    """
    days_step = 1 * int(np.sign(date_count))
    dt_begin = datetime.strptime("{:0>8d}".format(int(date_begin)), "%Y%m%d")

    # 不过滤
    is_every_day = skip_func is None
    if is_every_day:
        dt_end = dt_begin + timedelta(days=date_count - days_step)
        return date_by_datetime(dt_end)

    # 过滤
    loop_count, loop_count_max = 1, 999  # note：如果 skip 始终返回True，可能死循环。防止并报错
    #
    not_skip_count = 1
    days = -1 * days_step
    while True:
        days += days_step
        dt_end = dt_begin + timedelta(days=days)
        #
        if not skip_func(dt_end):
            if not_skip_count >= abs(date_count):
                break
            else:
                not_skip_count += 1
        #
        if loop_count >= loop_count_max:
            fatal_exit(f"check: {loop_count=} >= {loop_count_max=}, "
                       f"{date_begin=}, {date_count=}, {skip_func=}")
        loop_count += 1

    return date_by_datetime(dt_end)


def date_to_list(date_begin: int, date_count: int) -> list[int]:
    """ 例如：[20210501,20210502]
        note: date_count以1作为base，即表示date_begin
    """
    return date_to_skip_list(date_begin, date_count)


def date_to_skip_list(date_begin: int, date_count: int, skip_func: Callable[[datetime], bool] = None) -> list[int]:
    """ 例如：[20210501,20210502]
        note: date_count以1作为base，即表示date_begin
        note: skip_func规范：参数 datetime，返回 bool
        todo: impl: 性能：date_list 数据多时很慢
    """
    rl = []
    range_start = 1 if date_count > 0 else date_count  # 可能负数
    range_stop = (date_count + 1) if date_count > 0 else 1  # 可能负数
    for dc in range(range_start, range_stop):
        date = date_to_skip(date_begin, date_count=dc, skip_func=skip_func)
        if date not in rl:
            rl.append(date)
    return rl


def date_now(timezone_str: str = None) -> int:
    """ 指定时区对应的当前日期 """
    tz = __tzinfo(timezone_str)
    dt_now = __datetime_now() \
        .astimezone(tz) \
        .replace(tzinfo=tz)
    return int_safe(dt_now.strftime("%Y%m%d"))


def date_by_datetime(datetime_obj: datetime, default=None, is_fatal_none=False, ) -> int:
    if datetime_obj is not None:
        return int_safe(datetime_obj.strftime("%Y%m%d"))
    return fatal_exit(f"{datetime_obj=} none", return_value=None) if is_fatal_none \
        else warn(f"{date_by_datetime.__name__}, {datetime_obj=} none", return_value=default)


def date_by_timestamp(yyyymmddhhmmss_int: int) -> int:
    return int_safe(yyyymmddhhmmss_int / 1000000)


def date_by_str_of_readable(date_str: str, timezone_str: str = None) -> int:
    """例如：2022-04-11 -> 20220411"""
    return date_by_str(date_str, date_fmt="%Y-%m-%d", timezone_str=timezone_str)


def date_by_str(date_str: str, date_fmt: str, timezone_str: str = None) -> int:
    return date_by_datetime(datetime_by_str(date_str, date_fmt, timezone_str))


def str_date_of_readable(date: int) -> str:
    """例如：20220411 -> 2022-04-11 """
    return str_date(date, date_fmt="%Y-%m-%d")


def str_date(date: int, date_fmt: str) -> str:
    return datetime.strftime(datetime.strptime("{:0>8d}".format(int(date)), "%Y%m%d"), date_fmt)


def date_of_week_monday_yyyymmdd_2_yyyymmdd_list(
        date_list: list[int],
) -> dict[int, list[int]]:
    # 周（ 周一的日期，做为 key ）
    monday = None
    week_2_yyyymmdd_list = {}
    for yyyymmdd in date_list:
        monday = yyyymmdd if is_monday(yyyymmdd) \
            else to_monday_begin_by_list(date_list) if none(monday) \
            else monday
        append_dict_val_list_item(week_2_yyyymmdd_list, monday, yyyymmdd)

    return week_2_yyyymmdd_list


def date_of_week_memo_2_yyyymmdd_list(
        date_list: list[int],
        is_return_year_week_index=True,
        is_return_monday_yyyymmdd=True,
        # is_return_month_week_index=False, note: 每月第几周，意义不大，而且跨月时会将date分割成多个周，不好
) -> dict[str, list[int]]:
    # 周（ key 包括 周一的日期，本年周序号，本月周序号等  ）
    week_2_yyyymmdd_list = {}
    for date in date_list:
        week = to_date_week_str(date,
                                is_return_year_week_index=is_return_year_week_index,
                                is_return_monday_yyyymmdd=is_return_monday_yyyymmdd)
        append_dict_val_list_item(week_2_yyyymmdd_list, week, date)
    return week_2_yyyymmdd_list


def date_of_yyyymm_2_yyyymmdd_list(
        date_list: list[int]
) -> dict[int, list[int]]:
    # 月
    yyyymm_2_yyyymmdd_list = {}
    for date in date_list:
        yyyymm = to_date_year_month(date)
        append_dict_val_list_item(yyyymm_2_yyyymmdd_list, yyyymm, date)
    return yyyymm_2_yyyymmdd_list


def date_of_yyyy_2_yyyymmdd_list(
        date_list: list[int]
) -> dict[int, list[int]]:
    # 年
    yyyy_2_yyyymmdd_list = {}
    for date in date_list:
        yyyy = to_date_year(date)
        append_dict_val_list_item(yyyy_2_yyyymmdd_list, yyyy, date)
    return yyyy_2_yyyymmdd_list


def time_to(time_begin: int, second_count: int) -> int:
    """例如：160758 note: second_count 以1作为 base，即表示 time_begin """
    dt_begin = datetime_by_time(time_begin)
    dt_end = dt_begin + timedelta(seconds=second_count - 1)
    return time_by_datetime(dt_end)


def time_now(timezone_str: str = None) -> int:
    """ 指定时区对应的当前时间 """
    tz = __tzinfo(timezone_str)
    dt_now = __datetime_now() \
        .astimezone(tz) \
        .replace(tzinfo=tz)
    return int_safe(dt_now.strftime("%H%M%S"))


def time_by_datetime(datetime_obj: datetime) -> int:
    return int_safe(datetime_obj.strftime("%H%M%S"))


def time_by_timestamp(yyyymmddhhmmss_int: int) -> int:
    return int_safe(yyyymmddhhmmss_int % 1000000)


def time_segment(time_start, time_stop, segment_count, segment_index, is_log=False) -> int:
    # start 和 stop 按照 count 等分后取 index 部分
    if segment_count <= 0:
        trace(f"segment arg illegal, {segment_count=} <= 0")
        return time_start

    is_log and log(f"{time_segment.__name__}, {time_start=}, {time_stop=}")
    #
    second_total = duration_second_by_hhmmss(time_start, time_stop)
    #
    calc_count = segment_count
    calc_index = min(segment_count, max(0, segment_index))
    second_segment = int(second_total / calc_count * calc_index + 1)
    #
    return time_to(time_start, second_segment)


def epochtime_to(to_date: int, to_time: int, timezone_str: str = None) -> int:
    """ 从1970开始的连续时间数字 """
    tz = __tzinfo(timezone_str)
    dt_to = __datetime_now() \
        .strptime(f"{to_date:0>8d}{to_time:0>6d}", "%Y%m%d%H%M%S") \
        .astimezone(None) \
        .replace(tzinfo=tz)
    return int(dt_to.timestamp())


def datetime_from_epochtime(from_epochtime: float, timezone_str: str = None) -> datetime:
    """ 从1970开始的连续时间数字 """
    tz = __tzinfo(timezone_str)
    dt_from = __datetime_now() \
        .fromtimestamp(from_epochtime) \
        .astimezone(None) \
        .replace(tzinfo=tz)
    return dt_from


def datetime_by_str(datetime_str: str, datetime_fmt="%Y%m%d%H%M%S", timezone_str: str = None) -> datetime:
    tz = __tzinfo(timezone_str)
    return datetime \
        .strptime(datetime_str, datetime_fmt) \
        .astimezone(None) \
        .replace(tzinfo=tz)


def datetime_by_timestamp(timestamp: int, timestamp_fmt="%Y%m%d%H%M%S", timezone_str: str = None) -> datetime:
    # note: float timestamp 会报告错误：ValueError: unconverted data remains: .0
    tz = __tzinfo(timezone_str)
    return datetime \
        .strptime(str(int(timestamp)), timestamp_fmt) \
        .astimezone(None) \
        .replace(tzinfo=tz)


def datetime_by_date(date_curr: int) -> datetime:
    return datetime.strptime("{:0>8d}".format(int(date_curr)), "%Y%m%d")


def datetime_by_time(time_curr: int) -> datetime:
    """例如：160758"""
    return datetime.strptime("{:0>6d}".format(int(time_curr)), "%H%M%S")


def datetime_by_time_str(time_curr: str) -> datetime:
    """例如：160758"""
    return datetime.strptime(time_curr, "%H%M%S")


def datetime_to(datetime_begin: datetime, second_count: int) -> datetime:
    return datetime_begin + timedelta(seconds=second_count)


# 获取过去几天的日期（默认为过去1天，即昨天）
def past_date(past_day=1, fmt: format = ''):
    today = datetime.today()
    yesterday = today - timedelta(days=past_day)
    if len(fmt):
        yesterday = yesterday.strftime(fmt)

    return yesterday


# 获取昨天的日期
def yesterday_date(past_day=1, fmt: format = ''):
    return past_date(past_day, fmt)


# 获取从指定开始日期 向前/后 days_back天 的日期列表
# days_back 向前/后天数
# start_date 开始日期
# fmt 格式化
# is_prev 是否向前，如果为True，则向前获取日期；如果为false，则向后获取日期
def loop_date_str(days_back=0, start_date=datetime.today(), fmt: format = "%Y-%m-%d", is_prev: bool = True):
    # 简单写法
    # date_list = []
    # for i in range(0, days_back):  # range(0, 5) 生成0-5的整数序列
    #     if is_prev:
    #         date_list.append((start_date - timedelta(days=i)).strftime(fmt))
    #     else:
    #         date_list.append((start_date + timedelta(days=i)).strftime(fmt))

    # 串联式写法
    if is_prev:
        date_str_lists = [(start_date - timedelta(days=i)).strftime(fmt) for i in range(0, days_back)]
    else:
        date_str_lists = [(start_date + timedelta(days=i)).strftime(fmt) for i in range(0, days_back)]
    return date_str_lists


# 获取从指定开始日期 向前 days_back天 的日期列表
def loop_dates(days_back=0, start_date=datetime.today(), is_prev: bool = True):
    date_lists = loop_date_str(days_back, start_date, fmt="%Y%m%d", is_prev=is_prev)
    date_int_lists = [int_safe(date_lists[i]) for i in range(0, len(date_lists))]
    return date_int_lists


# 获取从指定 开始日期 到 结束日期 的日期列表
def get_date_list(start_date: int, end_date: int):
    # 设置起始时间
    start_time = datetime_by_date(start_date)
    end_time = datetime_by_date(end_date)

    # 当 当前日期大于结束日期时，循环结束
    date_lists = []
    current_time = start_time
    while current_time <= end_time:
        # print(current_time.strftime('%Y%m%d'))
        date_lists.append(int_safe(current_time.strftime('%Y%m%d')))
        current_time += timedelta(days=1)  # 增加一天

    return date_lists


def is_duration_reach_by_timestamp(from_timestamp: int, to_timestamp: int, delta_second: int,
                                   timezone_str: str = None,
                                   ) -> bool:
    # note: float timestamp 会报告错误：ValueError: unconverted data remains: .0
    return is_duration_reach(
        str(int(from_timestamp)), str(int(to_timestamp)), delta_second,
        datetime_fmt="%Y%m%d%H%M%S", timezone_str=timezone_str
    )


def is_duration_reach(from_datetime_str: str, to_datetime_str: str, delta_second: int,
                      datetime_fmt="%Y%m%d%H%M%S", timezone_str: str = None,
                      ) -> bool:
    dt_from = datetime_by_str(from_datetime_str, datetime_fmt, timezone_str)
    dt_to = datetime_by_str(to_datetime_str, datetime_fmt, timezone_str)
    return (dt_to - dt_from).seconds >= delta_second


def duration_second_now(to_date: int, to_time: int, timezone_str: str = None, is_abs=True) -> int:
    """to到now的时长（秒）（to可能小于now，也可能大于now）（note: 如果abs为False，则可能返回负数）"""
    # note: 不调整的化，会报告错误：TypeError: can't subtract offset-naive and offset-aware datetimes
    tz = __tzinfo(timezone_str)
    dt_to = __datetime_now() \
        .strptime(f"{to_date:0>8d}{to_time:0>6d}", "%Y%m%d%H%M%S") \
        .astimezone(None) \
        .replace(tzinfo=tz)
    dt_now = __datetime_now() \
        .astimezone(tz) \
        .replace(tzinfo=tz)
    second = (dt_now - dt_to).total_seconds() if dt_now > dt_to \
        else (dt_to - dt_now).total_seconds()
    second = -1 * second if not is_abs and dt_now < dt_to else second
    return int(second)


def duration_second_by_hhmmss(from_time: int, to_time: int, is_abs=True) -> int:
    """to到from的时长（秒）（to可能小于from，也可能大于from）（note: 如果abs为False，则可能返回负数）"""
    # note: 不调整的化，会报告错误：
    #       TypeError: can't subtract offset-naive and offset-aware datetimes
    # note: strptime不加yyyymmdd在windows上报错：
    #       File "D:\software\Anaconda3\lib\code.py", line 90, in runcode
    #           exec(code, self.locals)
    #       File "<input>", line 1, in <module>
    #       OSError: [Errno 22] Invalid argument
    d_fake, d_fmt = ("20220101", "%Y%m%d")
    dt_from = __datetime_now() \
        .strptime(f"{d_fake}{from_time:0>6d}", f"{d_fmt}%H%M%S") \
        .astimezone(None)
    dt_to = __datetime_now() \
        .strptime(f"{d_fake}{to_time:0>6d}", f"{d_fmt}%H%M%S") \
        .astimezone(None)
    second = (dt_to - dt_from).total_seconds() if dt_to > dt_from \
        else (dt_from - dt_to).total_seconds()
    second = -1 * second if not is_abs and dt_to < dt_from else second
    return int(second)


def duration_str_by_hhmmss_1(hhmmss_begin: str, hhmmss_end: str) -> str:
    """ 时长, 例如：160758 到 160759"""
    # note: 如果程序中间异常终止，这里会出现对象为 "'NoneType' object is not iterable" 的现象，
    #       原因未知（可能是python解释器的问题：datetime import对象被先删除了）
    try:
        dt_begin = datetime_by_time_str(hhmmss_begin)
        dt_end = datetime_by_time_str(hhmmss_end)
        # note: 如果 end 小于 begin，我们调整1天，认为end是begin的第二天对应的时间，防止出现负值（超过多天情况不考虑）
        dt_end = (dt_end + timedelta(days=1)) if dt_begin > dt_end else dt_end
        return duration_str((dt_end - dt_begin).total_seconds())
    except Exception as err:
        warn(f"{funcname(duration_str_by_hhmmss_1)}, {errinfo(err)}")
        return "duration unknown"


def duration_str_by_hhmmss_2(hhmmss_begin: str, hhmmss_end: str) -> str:
    """ 时长, 例如：160758 到 160759"""
    return f"{hhmmss_begin} -> {hhmmss_end} = {duration_str_by_hhmmss_1(hhmmss_begin, hhmmss_end)}"


def duration_str(second: Union[int, float]) -> str:
    """ 时长 """
    h = second / 60 / 60
    hi = int(second / 60 / 60)
    m = second / 60
    mi = int(second / 60)
    si = int(second)
    if hi > 0:
        hmi = int((si - hi * 60 * 60) / 60)
        hmsi = int(si - hi * 60 * 60 - hmi * 60)
        msi = int(si - mi * 60)
        return f"{hi}h{hmi}m{hmsi}s({h:0>.1f}h), {mi}m{msi}s({m:0>.1f}m), {si}s"
    elif mi > 0:
        msi = int(si - mi * 60)
        return f"{mi}m{msi}s({m:0>.1f}m), {si}s"
    else:
        return f"{si}s"


def float_safe(v: float, default: Optional[float] = 0) -> float:
    return default if np.isnan(v) else v


def to_float(v: any, default: float = np.nan,
             is_trace=True, is_fatal=False, is_log=True) -> float:
    try:
        return float(v)
    except Exception as err:
        msg = f"to_float, {errinfo(err)}, {v=}, {default=}"
        ret = default
        return log_return(msg, ret, is_trace, is_fatal, is_log)


def to_float_segment(v_start: float, v_stop: float, segment_count: int, segment_index: int) -> float:
    int_count = int_safe(segment_count)
    int_index = int_safe(segment_index)
    return v_start if int_index <= 0 \
        else v_stop if int_index >= int_count \
        else v_start + int_index * (v_stop - v_start) / int_count


def is_float_equal(a: float, b: float, equal_diff: float = None, equal_percent: float = None) -> bool:
    abs_diff = abs(a - b)
    #
    if equal_diff is not None:
        return abs_diff <= equal_diff
    #
    if equal_percent is not None:
        is_equal_a = (abs_diff / abs(a) <= equal_percent)
        is_equal_b = (abs_diff / abs(b) <= equal_percent)
        return is_equal_a and is_equal_b
    #
    return abs_diff <= 0.00001


def is_float_zero(v: any) -> bool:
    return to_float(v, default=0) == 0


def is_float_zero_all(*v_tuplelist) -> bool:
    return all(is_float_zero(v) for v in v_tuplelist)


def is_float_zero_all_by_list(v_l: list) -> bool:
    return False if empty(v_l) else all(is_float_zero(v) for v in v_l)


def is_float_zero_any(*v_tuplelist) -> bool:
    return any(is_float_zero(v) for v in v_tuplelist)


def is_float_zero_any_by_list(v_l: list) -> bool:
    return False if empty(v_l) else any(is_float_zero(v) for v in v_l)


def round_float_45(n: float, decimal_count: int = 0) -> float:
    """ note：四舍五入算法
        注意，python round 采用 Banker's rounding（银行家舍入）算法，即四舍六入五取偶。事实上这也是 IEEE 规定的舍入标准。
        因此所有符合 IEEE 标准的语言都应该是采用这一算法的。并且这种银行家舍入算法比四舍五入算法更加精确。
        规则是：四舍六入五考虑，五后非零就进一，五后为零看奇偶，五前为偶应舍去，五前为奇要进一
    """
    fmt = pad_str_right("0.0", decimal_count + 2, "0")  # 2 -> "0.00"
    return float(Decimal(str(n)).quantize(Decimal(fmt), rounding=ROUND_HALF_UP))


def round_float_up(n: float, decimal_count: int = 0) -> float:
    # 向上舍入
    multiplier = 10 ** decimal_count
    return math.ceil(n * multiplier) / multiplier


def round_float_down(n: float, decimal_count: int = 0) -> float:
    # 向下舍入
    multiplier = 10 ** decimal_count
    return math.floor(n * multiplier) / multiplier


def int_safe(v: any, default: Optional[int] = 0) -> int:
    return default if empty(v) else to_int(v, default, is_trace=False, is_log=False)


def to_int(v: any, default: int = 0,
           is_trace=True, is_fatal=False, is_log=False) -> int:
    try:
        return int(v)
    except Exception as err:
        msg = f"{to_int.__name__}, {errinfo(err)}, {v=}, {default=}"
        ret = default
        return log_return(msg, ret, is_trace, is_fatal, is_log)


def is_int(s: str) -> bool:
    return not np.isnan(to_int(s, np.nan, is_trace=False, is_log=False))


def split_int(s: str, delim_char: str, index: int, default: int = 0,
              is_trace=True, is_fatal=False, is_log=False) -> int:
    try:
        return int(s.split(delim_char)[index])
    except Exception as err:
        msg = f"{split_int.__name__}, {errinfo(err)}, {s=}, {delim_char=}, {index=}, {default=}"
        ret = default
        return log_return(msg, ret, is_trace, is_fatal, is_log)


def to_bool(s: str, default: bool = False, is_check_true=True,
            is_trace=True, is_fatal=False, is_log=False) -> bool:
    # note: is_check_true 为 False 表示 s取值只要不是"false" 返回结果就是 True
    # noinspection PyBroadException
    try:
        # return bool(s)
        return s.strip().lower() == "true" if is_check_true else s.strip().lower() != "false"
    except Exception as err:
        msg = f"{to_bool.__name__}, {errinfo(err)}, {s=}, {default=}"
        ret = default
        return log_return(msg, ret, is_trace, is_fatal, is_log)


def to_bool_equal(s: str, str_equal: str = None, default: bool = False,
                  is_trace=True, is_fatal=False, is_log=False) -> bool:
    # note: 取值等于 str_equal 时返回 True （str_equal可以为任意，例如"false"）
    # noinspection PyBroadException
    try:
        # return bool(s)
        return s.lower() == str_equal
    except Exception as err:
        msg = f"{to_bool_equal.__name__}, {errinfo(err)}, {s=}, {default=}"
        ret = default
        return log_return(msg, ret, is_trace, is_fatal, is_log)


def str_safe(v: any, default: Optional[str] = "", is_lower=False, is_trim=False) -> str:
    return default if empty(v) \
        else str(v).strip().lower() if is_lower and is_trim \
        else str(v).lower() if is_lower and not is_trim \
        else str(v).strip() if is_trim \
        else str(v)


def to_str(v: any, default: str = "", is_notnone=True,
           is_trace=True, is_fatal=False, is_log=True) -> str:
    try:
        return default if is_notnone and v is None else str(v)
    except Exception as err:
        msg = f"{to_str.__name__}, {errinfo(err)}, {v=}, {default=}"
        ret = default
        return log_return(msg, ret, is_trace, is_fatal, is_log)


def is_str_split_contain(s: str, delim_char_set: str, t: str, default: bool = False,
                         is_trace=False, is_fatal=False, is_log=False) -> bool:
    """ s 被 delim_char_set 中的 任意 字符 分割后的数组中含有 t """
    try:
        fd = [x for x in delim_char_set][0]  # 取第一个分隔符（用于替换所有分隔符）
        ns = "".join(fd if c in delim_char_set else c for c in s)  # source中可能有多个分隔符
        nt = "".join(fd if c in delim_char_set else c for c in t)  # target中可能有多个分隔符
        return is_whole_sub_list(ns.split(fd), nt.split(fd))
    except Exception as err:
        msg = f"{is_str_split_contain.__name__}, {errinfo(err)}, {s=}, {delim_char_set=}, {t=}, {default=}"
        ret = default
        return log_return(msg, ret, is_trace, is_fatal, is_log)


def is_str_contain_any(s: str, symbol_or_list: Union[str, list[str]]) -> bool:
    item_list = convert_to_list(symbol_or_list)
    return any(s.find(item) >= 0 for item in item_list)


def is_str_suffix(s: str, *symbol_tuple) -> bool:
    return any(s.endswith(f"{x}") for x in symbol_tuple)


def is_str_suffix_by_list(s: str, symbol_or_list: Union[str, list[str]]) -> bool:
    s_l = symbol_or_list if of_list(symbol_or_list) else [symbol_or_list]
    return any(s.endswith(f"{x}") for x in s_l)


def is_str_prefix(s: str, *symbol_tuple) -> bool:
    return any(s.startswith(f"{x}") for x in symbol_tuple) if not_empty(s) else False


def is_str_prefix_by_list(s: str, symbol_or_list: Union[str, list[str]]) -> bool:
    s_l = symbol_or_list if of_list(symbol_or_list) else [symbol_or_list]
    return any(s.startswith(f"{x}") for x in s_l)


def is_str_find(s: str, *symbol_tuple) -> bool:
    return any(s.find(f"{x}") >= 0 for x in symbol_tuple)


def is_str_find_by_list(s: str, symbol_or_list: Union[str, list[str]]) -> bool:
    s_l = symbol_or_list if of_list(symbol_or_list) else [symbol_or_list]
    return any(s.find(f"{x}") >= 0 for x in s_l)


def concat_str_newline(p: str, s: str) -> str:
    return "{}{}".format(f"{p}\n" if p != "" else "", s)


def stress_str(s: str) -> str:
    return f"****{s.upper()}****"


def pad_str_right(s: str, total_len: int, justify_str: str = ".") -> str:
    """ 对齐（支持中文）（靠左边排列，右边补充字符）"""
    byte_len = len(s.encode("GBK"))
    return s + "".ljust(max(0, total_len - byte_len), justify_str)


def pad_str_left(s: str, total_len: int, justify_str: str = ".") -> str:
    """ 对齐（支持中文）（靠右边排列，左边补充字符）"""
    byte_len = len(s.encode("GBK"))
    return "".ljust(max(0, total_len - byte_len), justify_str) + s


def pad_str_left_int(i: int, total_len: int, justify_int: int = 0) -> str:
    """ 对齐（数字）（靠右边排列，左边补充0）"""
    return pad_str_left(str(i), total_len, str(justify_int))


def split_str(s: str, delim_char: str, index: int, default: Optional[str] = "",
              is_trace=False, is_fatal=False, is_log=False) -> str:
    try:
        return str(s.split(delim_char)[index])
    except Exception as err:
        msg = f"{split_str.__name__}, {errinfo(err)}, {s=}, {delim_char=}, {default=}"
        ret = default
        return log_return(msg, ret, is_trace, is_fatal, is_log)


def split_str_to_list(s: str, delim_char_set: str,
                      is_trace=False, is_fatal=False, is_log=False) -> list[str]:
    """ s 被 delim_char_set 中的 任意 字符 分割后的数组 """
    try:
        fd = [x for x in delim_char_set][0]  # 取第一个分隔符（用于替换所有分隔符）
        ns = "".join(fd if c in delim_char_set else c for c in s)  # source中可能有多个分隔符
        return [x for x in ns.split(fd) if len(x)]
    except Exception as err:
        msg = f"{split_str_to_list.__name__}, {errinfo(err)}, {s=}, {delim_char_set=}"
        ret = []
        return log_return(msg, ret, is_trace, is_fatal, is_log)


def split_str_to_tuple2(s: str, delim_char: str, default: Optional[str] = "",
                        is_trace=False, is_fatal=False, is_log=False) -> tuple[str, str]:
    try:
        sl = s.split(delim_char)
        return to_list_str(sl, 0), to_list_str(sl, 1)
    except Exception as err:
        msg = f"{split_str_to_tuple2.__name__}, {errinfo(err)}, {s=}, {delim_char=}, {default=}"
        ret = (default, default)
        return log_return(msg, ret, is_trace, is_fatal, is_log)


def split_str_to_tuple3(s: str, delim_char: str, default: Optional[str] = "",
                        is_trace=False, is_fatal=False, is_log=False) -> tuple[str, str, str]:
    try:
        sl = s.split(delim_char)
        return to_list_str(sl, 0), to_list_str(sl, 1), to_list_str(sl, 2)
    except Exception as err:
        msg = f"{split_str_to_tuple3.__name__}, {errinfo(err)}, {s=}, {delim_char=}, {default=}"
        ret = (default, default, default)
        return log_return(msg, ret, is_trace, is_fatal, is_log)


def split_str_to_tuple4(s: str, delim_char: str, default: Optional[str] = "",
                        is_trace=False, is_fatal=False, is_log=False) -> tuple[str, str, str, str]:
    try:
        sl = s.split(delim_char)
        return to_list_str(sl, 0), to_list_str(sl, 1), to_list_str(sl, 2), to_list_str(sl, 3)
    except Exception as err:
        msg = f"{split_str_to_tuple4.__name__}, {errinfo(err)}, {s=}, {delim_char=}, {default=}"
        ret = (default, default, default, default)
        return log_return(msg, ret, is_trace, is_fatal, is_log)


def is_str_equal_or_empty(s: str, s_compare: Optional[str]) -> bool:
    # note: s如果空，则返回False
    if empty(s):
        return False
    return s == s_compare or empty(s_compare)


def join_str(delim: str, *args_tuple, is_str_none=True, is_str_empty=True):
    """
        is_str_none 为 True 时，args 的 None 会变为非空字符串'None'
        is_str_empty 为 True 时，args 中的 "" 会出现在结果中
    """

    # return delim.join(sub_list_skip_none([
    #     (
    #         delim.join([str_safe(y) for y in x]) if of_list(x)
    #         else delim.join([str_safe(y) for y in x]) if of_tuple(x)
    #         else str(x) if x is not None
    #         else str(x) if x is None and is_str_none
    #         else str(x) if empty(x) and is_str_empty
    #         else None
    #     )
    #     for x in args
    # ]))

    # note: 出现 TypeError: 'NoneType' object is not iterable，原因未知
    # a_l = list(itertools.chain(*args))
    # return delim.join(sub_list_skip_none([
    #     (
    #         str(x) if not_empty(x)
    #         else str(x) if x is None and is_str_none
    #         else str(x) if empty(x) and is_str_empty
    #         else None
    #     )
    #     for x in a_l
    # ]))

    # note: 可能存在调用时 args 为 list 的情况

    def __1(__x):
        return str(__x) if not_empty(__x) \
            else str(__x) if __x is None and is_str_none \
            else str(__x) if __x is not None and empty(__x) and is_str_empty \
            else None

    def __2(__l):
        return delim.join(sub_list_notnone([
            __1(x)
            for x in __l
        ]))

    return delim.join(keep_list_notnone([
        (
            __2(x) if of_list(x)
            else __2(x) if of_tuple(x)
            else __1(x)
        )
        for x in args_tuple
    ]))


def join_str_replace_none(delim: str, none_replace: str, *args_tuple):
    """ args 的 None 会变为指定字符 """
    __item = lambda x: sub_list_notempty([str_safe(y) for y in x])
    return delim.join([
        (
            delim.join(__item(x)) if of_list(x)
            else delim.join(__item(x)) if of_tuple(x)
            else none_replace if x is None
            else str(x)
        )
        for x in args_tuple
    ])


def join_str_notnone(delim: str, *args_tuple):
    """ args 的 None 会变为空字符 """
    __item = lambda x: sub_list_notempty([str_safe(y) for y in x])
    return delim.join([
        (
            delim.join(__item(x)) if of_list(x)
            else delim.join(__item(x)) if of_tuple(x)
            else str(x)
        )
        for x in args_tuple
        if x is not None
    ])


def join_str_exclude_whitespace(delim: str, *args_tuple):
    """ 返回结果中没有空字符（空格等，替换为delim）"""
    __item = lambda x: sub_list_notempty([str_safe(y) for y in x])
    return delim.join([
        (
            delim.join(__item(x)) if of_list(x)
            else delim.join(__item(x)) if of_tuple(x)
            else delim if x is None
            else str(x)
        ).replace(" ", delim)
        for x in args_tuple
    ])


def repeat_str(part: str, count: int) -> str:
    return part.join("" for _ in range(count + 1))


def replace_str_by_char_set(s: str, old_char_set: str, new_str: str) -> str:
    for i in range(len(old_char_set)):
        s = s.replace(old_char_set[i:i + 1], new_str)
    return s


def replace_str_by_str_list(s: str, old_str_list: list[str], new_str: str) -> str:
    for x in old_str_list:
        s = s.replace(x, new_str)
    return s


def sub_str(s: str, prefix: str, default: str = "",
            is_trace=False, is_fatal=False, is_log=False) -> str:
    try:
        return s[len(prefix):]
    except Exception as err:
        msg = f"{sub_str.__name__}, {errinfo(err)}, {s=}, {prefix=}, {default=}"
        ret = default
        return log_return(msg, ret, is_trace, is_fatal, is_log)


def kevstr_key(kevstr: str) -> str:
    """ kevstr: 将 "key=val"（即f"{x=}"）格式的 kev（key equal val）字符串 拆分，返回 key """
    return kevstr.split("=")[0]


def kevstr_key_as_var(kevstr: str, default: str = None) -> str:
    # 通过 f"{x=}" 来获取 "x" 字符串（变量名称）(去掉前面的module名称，如果有的话）
    try:
        prefix = kevstr.partition('=')[0]
        return prefix.partition(".")[-1] if prefix.count(".") > 0 else prefix  # 去掉 module 前缀
    except Exception as err:
        exception(err, f"{kevstr_key_as_var.__name__}, {kevstr=}")
        return default


def kevstr_val(kevstr: str, default="") -> str:
    """ kevstr: 将 "key=val"（即f"{x=}"） 格式的 kev（key equal val）字符串 拆分，返回 val """
    sl = kevstr.split("=")
    return sl[1] if len(sl) > 1 else default


def kevstr_val_as_int(kevstr: str, default=0) -> int:
    """ kevstr: 将 "key=val"（即f"{x=}"） 格式的 kev（key equal val）字符串 拆分，返回 val """
    sl = kevstr.split("=")
    return int(to_float(sl[1])) if len(sl) > 1 else default  # note：截断


def kevstr_val_as_float(kevstr: str, default=0) -> float:
    """ kevstr: 将 "key=val"（即f"{x=}"） 格式的 kev（key equal val）字符串 拆分，返回 val """
    sl = kevstr.split("=")
    return to_float(sl[1]) if len(sl) > 1 else default


def is_list_contain_all(rl: list, item_or_list: Union[list, any]) -> bool:
    """ rl 中含有 所有 item_or_list 的元素（不考虑顺序）"""
    if empty(rl) or empty(item_or_list):
        return False
    if of_list(item_or_list):
        return all(any(r == s for r in rl) for s in item_or_list)
    else:
        return rl.count(item_or_list) > 0


def is_list_contain_any(rl: list, item_or_list: Union[list, any]) -> bool:
    """ rl 中含有 任意 item_or_list 的元素（不考虑顺序）"""
    if empty(rl) or empty(item_or_list):
        return False
    if of_list(item_or_list):
        return any(any(r == s for r in rl) for s in item_or_list)
    else:
        return rl.count(item_or_list) > 0


def is_list_empty_or_contain(rl: list, item: str) -> bool:
    return empty(rl) or (item in rl)


def is_list_equal(list_a: list, list_b: list, is_fatal_notequal: bool = False) -> bool:
    if empty(list_a) and empty(list_b):
        return True
    if empty(list_a) or empty(list_b):
        return False
    if len(list_a) != len(list_b):
        return False
    for i, item in enumerate(list_a):
        item_a = list_a[i]
        item_b = list_b[i]
        if item_a != item_b:
            is_fatal_notequal and fatal_exit(f"check: {item_a=} != {item_b=}, {list_a=}, {list_b=}")
            return False
    return True


def sub_list_by_prefix(rl: list[str], key_prefix_or_list: Optional[Union[str, list[str]]]) -> list[str]:
    """ note: sub_key_prefix 如果 None 则返回 [] """
    prefix_l = key_prefix_or_list if of_list(key_prefix_or_list) else [str(key_prefix_or_list)]
    sl = []
    for key in rl:
        for prefix in prefix_l:
            if key.startswith(prefix) and sl.count(key) <= 0:
                sl.append(key)
    return sl


def sub_list_by_prefix_delim(rl: list[str], delim: str, prefix_delim_count: int) -> list[str]:
    """ delim 的 count 之前 的 子字符串 的 列表"""
    return [
        join_str(delim, split_str_to_list(x, delim)[0:prefix_delim_count])
        for x in rl
    ]


def sub_set_by_prefix_delim(rl: list[str], delim: str, prefix_delim_count: int) -> set[str]:
    """ delim 的 count 之前 的 子字符串 的 集合"""
    return set([
        join_str(delim, split_str_to_list(x, delim)[0:prefix_delim_count])
        for x in rl
    ])


def sub_list_by_suffix(rl: list[str], sub_key_suffix_or_list: Optional[Union[str, list[str]]]) -> list[str]:
    """ note: sub_key_suffix 如果 None 则返回 [] """
    suffix_l = sub_key_suffix_or_list if of_list(sub_key_suffix_or_list) else [str(sub_key_suffix_or_list)]
    sl = []
    for key in rl:
        for suffix in suffix_l:
            if key.endswith(suffix) and sl.count(key) <= 0:
                sl.append(key)
    return sl


def sub_list_notnone(rl: list) -> list:
    return [] if rl is None else [x for x in rl if x is not None]


def sub_list_notempty(rl: list) -> list:
    return [] if rl is None else [x for x in rl if not_empty(x)]


def sub_list_of_int_notzero(rl: list) -> list:
    return [] if rl is None else [x for x in rl if not_empty(x) and (int_safe(x) != 0)]


def sub_list_of_float_notzero(rl: list) -> list:
    return [] if rl is None else [x for x in rl if not_empty(x) and (float_safe(x) != 0)]


def sub_list_exclude(rl: list, exclude_item_or_list: Union[Any, list]) -> list:
    if rl is None:
        return []
    if exclude_item_or_list is None:
        return rl

    # note: 太大的数据量，性能需要优化（20万个tuplelist操作需要15分钟）
    (len(rl) > 10000) and warn(f"dfutil.{sub_list_exclude.__name__}, len large, {len(rl)=}")

    exclude_list = convert_to_list(exclude_item_or_list)
    return [x for x in rl if x not in exclude_list]


def is_sub_list_exclude(rl: list, exclude_l: list) -> bool:
    return not_empty(sub_list_exclude(rl, exclude_l))


def sub_list_intersect(rl: list, item_or_list: Optional[Union[Any, list[Any]]],
                       is_return_result_if_item_empty=True
                       ) -> list:
    """ note: item_or_list 如果 None 则返回 rl """
    if empty(item_or_list):
        return rl if is_return_result_if_item_empty else []
    if of_list(item_or_list):
        return [x for x in rl if x in item_or_list]
    return [x for x in rl if x == item_or_list]


def sub_list_args_intersect(*list_args_tuple) -> list:
    # list_args 的元素类型是 list
    if empty(list_args_tuple):
        return []
    rl = list_args_tuple[0]
    for il in list_args_tuple:
        not of_list(il) and fatal_exit(f"not list, {il=}, {list_args_tuple=}")
        if not_empty(il):
            rl = [x for x in rl if x in il]
    return rl


# def sub_list_intersect(item_list: list) -> list:
#     if empty(item_list):
#         return []
#     rl = []
#     for il in item_list:
#         if not_empty(il):
#             rl = [x for x in rl if x in il]
#     return rl


# def sub_list_union(rl: list, e_or_list) -> list:
#     return merge_list_args_notnone_unique(rl, e_or_list)
#

def is_whole_sub_list(rl: list, whole_sub_list: list) -> bool:
    """ rl 中含有 子列表 sl（note: 注意sl必须完整存在，不能存在隔断）"""
    if not whole_sub_list:
        return True
    if whole_sub_list == rl:
        return True
    if len(whole_sub_list) > len(rl):
        return False
    for i in range(len(rl)):
        if rl[i] == whole_sub_list[0]:
            n = 1
            while (n < len(whole_sub_list)) and (rl[i + n] == whole_sub_list[n]):
                n += 1
            if n == len(whole_sub_list):
                return True
    return False


def convert_to_list(item_or_list: Union[Any, list[Any]]) -> list[Any]:
    # note: 如果命名为 to_list，会让 pycharm 查找使用者时出现很多结果（bug）
    return item_or_list if of_list(item_or_list) else [item_or_list]


def to_list_int(rl: list, index: int, default: int = 0) -> int:
    return int(rl[index]) if index < len(rl) else default


def to_list_bool(rl: list, index: int, default: bool = False) -> bool:
    return bool(rl[index]) if index < len(rl) else default


def to_list_str(rl: list, index: int, default: str = "") -> str:
    return str(rl[index]) if index < len(rl) else default


def to_list_str_char(rl: list, str_index: int, char_index: int, default: str = "") -> str:
    s = str(rl[str_index]) if str_index < len(rl) else ""
    c = s[char_index] if char_index < len(s) else default
    return c


def to_list_by(item_or_list: Union[str, list[str]],
               default: list[str],
               is_check_item_in_default=False,
               ) -> list[str]:
    def __list(item_list):
        if is_check_item_in_default \
                and (item_list is not None) \
                and (is_sub_list_exclude(item_list, default)):
            fatal_exit(f"unsupported {item_or_list=}, {default=}")
        return default if item_list is None else item_list

    def __item(item):
        if is_check_item_in_default \
                and (item is not None) \
                and (item not in default):
            fatal_exit(f"unsupported {item_or_list=}, {default=}")
        return default if item is None else [item]

    return __list(item_or_list) if of_list(item_or_list) else __item(item_or_list)


def to_list_option(item_or_list: Union[Any, list], default: list) -> list:
    return default if empty(item_or_list) \
        else item_or_list if of_list(item_or_list) \
        else [item_or_list]


def append_list(dst_list: list, src_list: list, index: int):
    if index < len(src_list):
        dst_list.append(src_list[index])


def merge_list_list(list_list: list[list], is_notnone=True, is_unique=False) -> list:
    m_l = []
    l_l = [xl for xl in list_list if xl is not None] if is_notnone else list_list
    for i_l in [xl for xl in l_l if xl is not None]:
        #
        # not of_list(i_l) and fatal_exit(f"not list, {i_l=}, {list_list=}")
        i_l = i_l if of_list(i_l) else [i_l]
        #
        for i in [x for x in i_l if not is_notnone or x is not None]:
            is_append = not is_unique or i not in m_l
            is_append and m_l.append(i)
    return m_l


def merge_list_args(*list_args_tuple, is_notnone=True, is_unique=False) -> list:
    # list_args 的元素类型是 list
    return merge_list_list(list(list_args_tuple), is_notnone=is_notnone, is_unique=is_unique)


def merge_list_args_notnone(*list_args_tuple, is_unique=False) -> list:
    # list_args 的元素类型是 list
    return merge_list_list(list(list_args_tuple), is_notnone=True, is_unique=is_unique)


def merge_list_args_notnone_unique(*list_args_tuple) -> list:
    # list_args 的元素类型是 list
    return merge_list_list(list(list_args_tuple), is_notnone=True, is_unique=True)


def keep_list(item_list: list, is_notnone=True, is_unique=False) -> list:
    r_l = []
    i_l = [x for x in item_list if not is_notnone or x is not None]
    for i in i_l:
        is_append = not is_unique or i not in r_l
        is_append and r_l.append(i)
    return r_l


def keep_list_notnone(item_list: list, is_unique=False) -> list:
    return keep_list(item_list, is_notnone=True, is_unique=is_unique)


def unique_list(item_list: list) -> list:
    return list(set(item_list)) if item_list is not None else None


def is_unique_list(item_list: list) -> bool:
    return len(unique_list(item_list)) == len(item_list)


def unique_list_list(list_list: list[list]) -> list:
    return list({join_str("_", rl): rl for rl in list_list}.values()) if list_list is not None else None


def sort_list(item_list: list, is_ascending=True) -> list:
    return sorted(item_list, reverse=not is_ascending) if item_list is not None else None


def count_list_prefix(list_a, list_b):
    """ list相同prefix的数目 """
    c = 0
    for i in range(1, min(len(list_a), len(list_b))):
        if list_a[i] != list_b[i]:
            break
        c += 1
    return c


def check_list_in(rl: list, valid_list: list, is_fatal=True):
    """ l 的 item 必须存在与 valid_l 的 item 中 """
    if any_empty(rl, valid_list):
        return
    legal_list = merge_list_args_notnone_unique(rl, valid_list)
    if len(valid_list) != len(legal_list):
        msg = "list illegal item = {}".format(sub_list_exclude(rl, valid_list))
        if is_fatal:
            fatal_exit(msg)
        else:
            trace(msg)
    return


def return_item_in_list(item: Any, valid_list: list, is_fatal=True) -> Any:
    """ l 的 item 必须存在与 valid_l 的 item 中 """
    if any_empty(item, valid_list):
        return item
    if item not in valid_list:
        msg = f"{item=} not in {valid_list=}"
        if is_fatal:
            fatal_exit(msg)
        else:
            trace(msg)
    return item


def flat_list(item_or_list: Union[Any, list]) -> list:
    """ 将 参数 中的层级 list 全部去除，返回只有一层的list """
    rl = []
    for x in item_or_list:
        if of_list(x):
            rl.extend(flat_list(x))
        else:
            rl.append(x)
    return rl


def init_list(rl: list, *item_tuple) -> list:
    rl.clear()
    rl.extend(list(item_tuple))
    return rl


def pop_dict(d: dict, key: str, is_pop: bool):
    if is_pop:
        d.pop(key)


def adjust_dict_float_zero_to_val(d: Union[dict, pd.Series], k: str, adjust_val) -> float:
    return adjust_val if is_float_zero(d[k]) else d[k]


def adjust_dict_float_zero_to_max(d: Union[dict, pd.Series], k: str, *range_k_l) -> float:
    return max([d[x] for x in range_k_l]) if is_float_zero(d[k]) else d[k]


def adjust_dict_float_zero_to_min(d: Union[dict, pd.Series], k: str, *range_k_l) -> float:
    return min([d[x] for x in range_k_l]) if is_float_zero(d[k]) else d[k]


def to_dict_int(d: dict, key: str, default: int = 0) -> int:
    return to_int(d[key], default) if d is not None and key in d else default


def to_dict_float(d: dict, key: str, default: float = 0) -> float:
    return to_float(d[key]) if key in d else default


def to_dict_bool(d: dict, key: str, default: bool = False) -> bool:
    return bool(d[key]) if key in d else default


def to_dict_str(d: dict, key: str, default: Optional[str] = "") -> str:
    return str(d[key]) if key in d else default


def to_dict_val(d: dict, key: any, default: any = None, is_fatal_miss=False) -> any:
    if is_fatal_miss and d is not None and key not in d:
        fatal_exit(f"unsupported {key=}, {d=}")

    return d[key] if d is not None and key in d else default


def to_dict_val_option(d: dict, key: any,
                       option_d: dict = None, option_key: any = None,
                       default_func: Callable = None, default: any = None) -> any:
    """ note：寻找非空元素的顺序：
            d[key] -> d[option_key] -> option_d[key] -> option_d[option_key] -> default_func() -> default
    """
    val = d[key] if key in d else None
    val = d[option_key] if empty(val) and not_empty(option_key) and option_key in d else val
    val = option_d[key] if empty(val) and not_empty(option_d) and key in option_d else val
    val = option_d[option_key] if empty(val) and not_empty(option_d) and option_key in option_d else val
    val = default_func() if empty(val) and not_empty(default_func) else val
    val = default if empty(val) else val
    return val


def to_dict_val_list_by_key_prefix(d: dict, prefix: Optional[Any]) -> list[Any]:
    """ note: prefix 为 None 则返回所有 key"""
    return [d[x] for x in d if x.startswith(prefix or "")] if d is not None else []


def append_dict_val_list_item(d: dict, key, val_list_item, is_sort=False):
    if key in d:
        val_list = d.get(key)
        val_list.append(val_list_item)
        if is_sort:
            val_list = sorted(val_list)
            d[key] = val_list
    else:
        d[key] = [val_list_item]


def append_dict_check(d: dict, key, val, is_fatal_dup=False):
    """ key 不能存在于 d 中 """
    if key in d:
        if is_fatal_dup:
            fatal_exit("dict contain key = {}".format(key))
        else:
            trace("dict contain key = {}".format(key))
    d[key] = val


def extend_dict_val_list(d: dict, key, val_list):
    if key in d:
        d.get(key).extend(val_list)
    else:
        d[key] = val_list


def update_dict_val_return_old(d: dict, key, init: Any = None, new: Any = None) -> Any:
    old = to_dict_val(d, key, init)
    d[key] = new
    return old


def update_dict_val_dict(d: dict, key, val_dict_key, val_dict_val):
    val_d = d[key] if key in d else {}
    val_d.update({val_dict_key: val_dict_val})
    d[key] = val_d


def update_dict_copy(d: dict, update_d: Optional[dict], prefix: Optional[str], copy_prefix: Optional[str]):
    if update_d is None:
        return

    # 复制相同col
    if prefix is None and copy_prefix is None:
        old_2_new = {k: k for k in d if k in update_d}
        d.update({k: update_d[old_2_new[k]] for k in old_2_new})
        return

    # 无意义
    if prefix is None and copy_prefix is not None:
        return

    # 无意义
    if prefix is not None and copy_prefix is None:
        return

    # 复制prefix的col
    if prefix is not None and copy_prefix is not None:
        old_2_new = {k: k.replace(f"{prefix}", f"{copy_prefix}", 1) for k in d if k in update_d}
        d.update({k: update_d[old_2_new[k]] for k in old_2_new})
        return

    return


def update_dict(d: dict, update_d: dict):
    d.update(update_d)


def update_dict_skip_existed(d: dict, update_d: dict):
    d.update({key: update_d[key] for key in update_d if key not in d})


def update_dict_check_key_in(d: dict, update_d: dict, is_fatal=True):
    """ update_d 的key必须存在与 d 的key中 """
    check_key_list = list(update_d.keys())
    if not is_dict_has_key(d, check_key_list):
        curr_key_list = list(d.keys())
        miss_key_list = sub_list_exclude(check_key_list, curr_key_list)
        msg = f"dict miss key, {miss_key_list=}, {check_key_list=}, {curr_key_list=}"
        is_fatal and fatal_exit(msg)
        not is_fatal and trace(msg)
    d.update(update_d)


def update_dict_check_not_dup(d: dict, update_d: dict, is_fatal=True):
    """ update_d 的key必须不存在于 d 的key中 """
    check_key_list = list(update_d.keys())
    if any((x in d) for x in check_key_list):
        curr_key_list = list(d.keys())
        msg = f"dict dup key, {check_key_list=}, {curr_key_list=}"
        is_fatal and fatal_exit(msg)
        not is_fatal and trace(msg)
    d.update(update_d)


# 将tuple[Any]改为tuple[Any, ...] modify by hhx 2024.07.23
def sub_val_tuple(d: dict[str, Any], sub_key_list: list[str]) -> tuple[Any, ...]:
    return tuple(d[key] for key in sub_key_list if key in d)


def sub_dict(d: dict[str, Any], sub_key_list: list[str]) -> dict[str, Any]:
    return {key: d[key] for key in sub_key_list if key in d}


def sub_dict_by_prefix(d: dict[str, Any], sub_key_prefix_or_list: Union[str, list[str]]) -> dict[str, Any]:
    """ note: sub_key_prefix 如果 None 则返回 {} """
    skl = sub_key_prefix_or_list if of_list(sub_key_prefix_or_list) else [str(sub_key_prefix_or_list)]
    rd = {}
    for sub_key_prefix in skl:
        rd.update({key: d[key] for key in d if key.startswith(sub_key_prefix)})
    return rd


def sub_dict_by_suffix(d: dict[str, Any], sub_key_suffix_or_list: Union[str, list[str]]) -> dict[str, Any]:
    """ note: sub_key_suffix 如果 None 则返回 {} """
    skl = sub_key_suffix_or_list if of_list(sub_key_suffix_or_list) else [str(sub_key_suffix_or_list)]
    rd = {}
    for sub_key_suffix in skl:
        rd.update({key: d[key] for key in d if key.endswith(sub_key_suffix)})
    return rd


def sub_dict_of_pd_row(row: pd.Series, sub_key_list: list[str]) -> dict[str, Any]:
    return {key: row[key] for key in sub_key_list if key in row.index.to_list()}


def sub_dict_notnone(d: dict[str, Any]) -> dict[str, Any]:
    return {key: d[key] for key in d if key is not None}


def sub_dict_exclude_key_empty_or_val_empty(d: dict[str, Any]) -> dict[str, Any]:
    # key 和 val 都不空
    return {key: d[key] for key in d if (not_empty(key) and not_empty(d[key]))}


def sub_dict_exclude_not_int_key(d: dict[str, Any]) -> dict[str, Any]:
    """ 去除 非int """
    return {key: d[key] for key in d if f"{to_int(key)}" == key}


def sub_dict_exclude_key_prefix(d: dict[str, Any], exclude_key_prefix: str) -> dict[str, Any]:
    return {key: d[key] for key in d if not key.startswith(exclude_key_prefix)}


def is_dict_has_key(d: dict[str, Any], sub_key_or_list: Union[str, list[str]]) -> bool:
    sub_key_list = sub_key_or_list if of_list(sub_key_or_list) else [sub_key_or_list]
    exist_key_list = sorted(sub_dict(d, sub_key_list).keys())
    check_key_list = sorted(sub_key_list)
    if len(exist_key_list) != len(check_key_list):
        return False
    for i in range(0, len(exist_key_list)):
        if exist_key_list[i] != check_key_list[i]:
            return False
    return True


def is_dict_has_val(d: dict[str, Any], sub_d: dict[str, Any]) -> bool:
    for k in d:
        if k not in sub_d:
            return False
        if d[k] != sub_d[k]:
            return False
    return True


# 将参数tuple改为tuple[str, str] modify by hhx 2024.07.23
def convert_dict_to_kvlist(d: dict) -> list[tuple[str, str]]:
    # kvlist = pairlist = tuplelist( tuple item len = 2 )
    return [(x, d[x]) for x in d] if not_empty(d) else None


def to_dictlist_key_list(dl: list[dict[str, Any]]) -> list[str]:
    return unique_list(merge_list_list([list(d.keys()) for d in dl]))


def to_dictlist_val_list(dl: list[dict[str, Any]], key: str) -> list[Any]:
    return [d[key] for d in dl if key in d]


def to_dictlist_val_list_all(dl: list[dict[str, Any]]) -> list[Any]:
    return merge_list_list([list(d.values()) for d in dl])


def is_dictlist_has_key(dl: list[dict[str, Any]], sub_key_list: list[str]) -> bool:
    if any_empty(dl, sub_key_list):
        return False
    for d in dl:
        if not is_dict_has_key(d, sub_key_list):
            return False
    return True


def update_dictlist(dl: list[dict[str, Any]], update_dl: list[dict[str, Any]], equal_key: str):
    for d in dl:
        key = d[equal_key]
        for update_d in update_dl:
            if key == update_d[equal_key]:
                d.update({k: update_d[k] for k in update_d if k in d})
    return


def normalize_dictlist(dl: list[dict], key: str, normalize_sum: float = 1):
    # dl 中 所有 d 的 key 的 val 取值归一化（和为1）# note: 如果原始取值和为0，则结果也为0
    __adjust = lambda v: (normalize_sum * v / s)
    s = sum(d[key] for d in dl)
    for d in dl:
        d[key] = 0 if s <= 0 else __adjust(d[key])
        d[key] = normalize_sum if d[key] > normalize_sum else d[key]  # note：结果float可能超过上限，例如 3.000000000004 > 3
    return


def to_bin_fmt_str(bin_sep_list, bin_sep_index,
                   template_out_left, template_in, template_out_right, val_formatter) -> str:
    if bin_sep_index == 0:
        return template_out_left.format(
            sep_index=bin_sep_index,
            val_left=None,
            val_right=val_formatter(bin_sep_list[bin_sep_index]),
        )
    elif bin_sep_index < len(bin_sep_list):
        return template_in.format(
            sep_index=bin_sep_index,
            val_left=val_formatter(bin_sep_list[bin_sep_index - 1]),
            val_right=val_formatter(bin_sep_list[bin_sep_index]),
        )
    else:
        return template_out_right.format(
            sep_index=bin_sep_index,
            val_left=val_formatter(bin_sep_list[len(bin_sep_list) - 1]),
            val_right=None,
        )


def to_idx_len_str_of_bin_fmt_1(
        bin_sep_list, bin_val,
        bin_str_if_nan,
        template_out_left, template_in, template_out_right,
        val_formatter=lambda x: x,
) -> [int, int, str]:
    """ nan 的序号 -1，len 不包括 nan，包含bin最右边取值 """
    bin_sep_list_adjust = bin_sep_list + [bin_sep_list[-1] + 0.001]
    sep_len = len(bin_sep_list_adjust)

    # note: 新股会出现指标nan，特殊分类
    if np.isnan(bin_val):
        sep_idx = -1
        bin_str = bin_str_if_nan
    else:
        sep_idx = np.digitize(bin_val, bins=bin_sep_list_adjust)
        if sep_idx == 0:
            bin_str = template_out_left.format(
                sep_index=sep_idx,
                val_left=None,
                val_right=val_formatter(bin_sep_list_adjust[sep_idx]),
            )
        elif sep_idx < sep_len:
            bin_str = template_in.format(
                sep_index=sep_idx,
                val_left=val_formatter(bin_sep_list_adjust[sep_idx - 1]),
                val_right=val_formatter(bin_sep_list_adjust[sep_idx]),
            )
        else:
            bin_str = template_out_right.format(
                sep_index=sep_idx,
                val_left=val_formatter(bin_sep_list_adjust[sep_len - 1]),
                val_right=None,
            )
    #
    return sep_idx, sep_len + 1, bin_str


def to_idx_len_str_of_bin_fmt_2(
        bin_sep_list, bin_val,
        bin_str_if_nan,
        template_out_left, template_in, template_out_right,
        val_formatter=lambda x: x,
) -> [int, int, str]:
    """ nan 的序号 -1，len 不包括 nan, **不**包含bin最右边取值 """
    sep_len = len(bin_sep_list)

    # note: 新股会出现指标nan，特殊分类
    if np.isnan(bin_val):
        sep_idx = -1
        bin_str = bin_str_if_nan
    else:
        sep_idx = np.digitize(bin_val, bins=bin_sep_list)
        if sep_idx == 0:
            bin_str = template_out_left.format(
                sep_index=sep_idx,
                val_left=None,
                val_right=val_formatter(bin_sep_list[sep_idx]),
            )
        elif sep_idx < sep_len:
            bin_str = template_in.format(
                sep_index=sep_idx,
                val_left=val_formatter(bin_sep_list[sep_idx - 1]),
                val_right=val_formatter(bin_sep_list[sep_idx]),
            )
        else:
            bin_str = template_out_right.format(
                sep_index=sep_idx,
                val_left=val_formatter(bin_sep_list[sep_len - 1]),
                val_right=None,
            )

    return sep_idx, sep_len + 1, bin_str


def to_idx_len_str_of_bin_fmt_2_5(
        bin_sep_list, bin_val,
        bin_str_if_nan,
        template_out_left, template_in_left, template_in, template_in_right, template_out_right,
        val_formatter=lambda x: x,
) -> [int, int, str]:
    """ nan 的序号 -1，len 不包括 nan： sep 是数值范围, **不**包含bin最右边取值 """
    sep_len = len(bin_sep_list)

    # note: 新股会出现指标nan，特殊分类
    if np.isnan(bin_val):
        sep_idx = -1
        bin_str = bin_str_if_nan
    else:
        # 将sep按照0划分为3个部分：out_left（0左边第2个sep以及更左），in（0左右各1个sep），out_right（0右边第2个sep以及更右）
        # bin_sep_list 例如：[-3,-2,  |  -1,1,  | 2,3]
        zero_idx = np.digitize(0, bins=bin_sep_list)  # 例如：3
        zero_idx <= 0 and trace(f"no zero in sep, {bin_sep_list}")
        left_idx = zero_idx - 1  # 例如：2
        right_idx = zero_idx + 1  # 例如：4

        sep_idx = np.digitize(bin_val, bins=bin_sep_list)
        if sep_idx == 0:
            bin_str = template_out_left.format(
                sep_index=sep_idx,
                val_left=None,
                val_right=val_formatter(bin_sep_list[sep_idx]) if sep_idx < sep_len else None,
            )
        elif sep_idx <= left_idx:
            bin_str = template_in_left.format(
                sep_index=sep_idx,
                val_left=val_formatter(bin_sep_list[sep_idx - 1]) if sep_idx >= 1 else None,
                val_right=val_formatter(bin_sep_list[sep_idx]) if sep_idx < sep_len else None,
            )
        elif (sep_idx <= right_idx) \
                and (bin_val < bin_sep_list[right_idx - 1]):  # right_idx 可能等于 len
            bin_str = template_in.format(
                sep_index=sep_idx,
                val_left=val_formatter(bin_sep_list[sep_idx - 1]) if sep_idx >= 1 else None,
                val_right=val_formatter(bin_sep_list[sep_idx]) if sep_idx < sep_len else None,
            )
        elif sep_idx < sep_len:
            bin_str = template_in_right.format(
                sep_index=sep_idx,
                val_left=val_formatter(bin_sep_list[sep_idx - 1]) if sep_idx >= 1 else None,
                val_right=val_formatter(bin_sep_list[sep_idx]) if sep_idx < sep_len else None,
            )
        else:
            bin_str = template_out_right.format(
                sep_index=sep_idx,
                val_left=val_formatter(bin_sep_list[sep_len - 1]),
                val_right=None,
            )

    return sep_idx, sep_len + 1, bin_str


def slice_max(raw_obj, len_max: int, slice_str: str, is_log: bool = False):
    is_log and log("slice = {}".format(slice_str))

    # x:y:z，x起始位置（缺省0），y结束位置（缺省结尾），z从起始位置到结束位置遍历的步长（缺省1）
    slice_begin = split_int(slice_str, ":", 0, 0, is_trace=False, is_log=False)
    slice_step = split_int(slice_str, ":", 2, 1, is_trace=False, is_log=False)
    slice_end = split_int(slice_str, ":", 1, len(raw_obj), is_trace=False, is_log=False)
    slice_end = (slice_begin + len_max) if (slice_end - slice_begin > len_max) else slice_end

    return raw_obj[slice_begin:slice_end:slice_step]


def scale(val, val_min, val_max, scale_min, scale_max):
    """ 缩放公式：x = (y-a1)/(a2-a1)*(b2-b1)+b1 """
    not_valid(val_max != val_min) and trace(
        f"{val=}", f"{val_min=}", f"{val_max=}", f"{scale_min=}", f"{scale_max=}")
    return (val - val_min) / (val_max - val_min) * (scale_max - scale_min) + scale_min


def limit(val, limit_l, limit_h, offset=0, is_limit=True):
    """ 调整到范围内 """
    return max(limit_l - offset, min(limit_h + offset, val)) if is_limit else val


def rand_not_overlap(rand_list: list, rand_base: float,
                     rand_scale_1: float = 1, rand_scale_2: float = 1, diff_min: float = 1,
                     ) -> float:
    """生成不覆盖的随机值"""
    if len(rand_list) <= 0:
        rand_list.append(0)

    v = rand_list[0]

    # 防止始终找不到
    for i in range(0, 2):
        rand_scale = rand_scale_1 if i == 0 else rand_scale_2  # 第一次找不到时，再尝试第二次放大范围
        count_max = 99
        count = 0
        while (count < count_max) and len([1 for x in rand_list if abs(v - x) <= diff_min]):
            v = float(rand_base) + rand_scale * np.random.rand() * (1 if np.random.rand() > 0.5 else -1)
            count = count + 1
        if count >= count_max:
            warn(f"rand_not_overlap fail, loop {i}")

    rand_list.append(v)

    return v


def to_diff(val_a, val_b) -> float:
    """ 相减 """
    # note: 支持nan运算
    return val_a - val_b


def to_divide(val_n: float, val_d: float,
              default_n0d0: float = 0,
              default_n0d1: float = 0,
              default_n1d0: float = 0,
              is_log=False
              ) -> float:
    """ 相除 n/d（分子 numerator, 分母 denominator）"""
    # note: 支持nan运算

    # todo: impl: 报错：RuntimeWarning: invalid value encountered in double_scalars
    is_log and log(f"{to_divide.__name__}, {val_n=}, {val_d=}")

    return default_n0d0 if ((val_n == 0) and (val_d == 0 or val_d is np.nan)) \
        else default_n0d1 if ((val_n == 0) and (val_d != 0)) \
        else default_n1d0 if ((val_n != 0) and (val_d == 0 or val_d is np.nan)) \
        else (val_n / val_d)  # if (a != 0) and (b != 0)


def to_ratio(val_n: float, val_d: float, is_log=False) -> float:
    """ 比率 """
    return to_divide(val_n, val_d, is_log=is_log)


def to_percent(val_r: float) -> float:
    """ 百分比 """
    # note: 支持nan运算
    return val_r * 100


# 将百分数字符串转为float浮点类型 add by hhx 2024.10.22
def percent_string_to_float(percent_str):
    if percent_str.endswith('%'):
        percent_str = percent_str.rstrip('%')  # 移除尾部的百分号
        return float(percent_str) / 100.0
    else:
        raise ValueError("The input string is not a valid percentage format.")


def to_diff_ratio_of_a(val_a, val_b) -> float:
    """ ( val_a - val_b ) / val_a （分子 numerator, 分母 denominator） """
    # note: 支持nan运算
    return to_diff_ratio_by(val_a, val_b, val_a, None)


def to_diff_ratio_of_b(val_a, val_b) -> float:
    """ ( val_a - val_b ) / val_b （分子 numerator, 分母 denominator） """
    # note: 支持nan运算
    return to_diff_ratio_by(val_a, val_b, val_b, None)


def to_diff_ratio_of_max(val_a, val_b) -> float:
    """ 差值占较大值的比率（分子 numerator, 分母 denominator） """
    # note: 支持nan运算
    # 符号由差值决定
    val_diff = val_a - val_b
    val_denominator = np.max(np.array([val_a, val_b]))
    return np.sign(val_diff) * abs(val_diff / val_denominator) if val_denominator != 0 else 0


def to_diff_ratio_by(val_a, val_b, val_denominator, diff_as_equal=None) -> float:
    """ 差值占参数值的比率（分子 numerator, 分母 denominator） """
    # note: 支持nan运算
    if val_denominator == 0:
        return 0
    # nan
    if diff_as_equal is not None and np.isnan(diff_as_equal):
        return np.NaN
    # 差值特定范围内认为没有差值
    val_diff = val_a - val_b
    if diff_as_equal is not None and abs(val_diff) <= abs(diff_as_equal):
        return 0
    # 符号由差值决定
    return np.sign(val_diff) * abs(val_diff / val_denominator)


def to_diff_percent_of_max(val_a, val_b) -> float:
    """ 差值占较大值的百分比（分子 numerator, 分母 denominator） """
    # note: 支持nan运算
    return to_diff_ratio_of_max(val_a, val_b) * 100


def to_diff_percent_by(val_a, val_b, val_denominator, diff_as_equal=None) -> float:
    """ 差值占参数值的百分比（分子 numerator, 分母 denominator） """
    # note: 支持nan运算
    return to_diff_ratio_by(val_a, val_b, val_denominator, diff_as_equal=diff_as_equal) * 100


def calc_weight_2(r1: float, r2: float) -> float:
    """ 按照 ratio 顺序返回结算后的权重值，保证前面的ratio权重大于后面的ratio
        ratio 取值 -1～1 之间
    """
    not all(is_valid(-1 <= r <= 1) for r in [r1, r2]) and fatal_exit(
        f"ratio must be decimal, {r1=}, {r2=}, "
    )

    unit = 1000
    __int = lambda r: int(r)
    __normalize = lambda r: (r + 1) / 2
    return 0 \
        + __int(__normalize(r1) * unit * unit) \
        + __int(__normalize(r2) * unit) \
        + 0


def calc_weight_3(r1: float, r2: float, r3: float) -> float:
    """ 按照 ratio 顺序返回结算后的权重值，保证前面的ratio权重大于后面的ratio
        ratio 取值 -1～1 之间
    """
    not all(is_valid(-1 <= r <= 1) for r in [r1, r2, r3]) and fatal_exit(
        f"ratio must be decimal, {r1=}, {r2=}, {r3=}, "
    )

    unit = 1000
    __int = lambda r: int(r)
    __normalize = lambda r: (r + 1) / 2
    return 0 \
        + __int(__normalize(r1) * unit * unit * unit) \
        + __int(__normalize(r2) * unit * unit) \
        + __int(__normalize(r3) * unit) \
        + 0


def calc_weight_4(r1: float, r2: float, r3: float, r4: float) -> float:
    """ 按照 ratio 顺序返回结算后的权重值，保证前面的ratio权重大于后面的ratio
        ratio 取值 -1～1 之间
    """
    not all(is_valid(-1 <= r <= 1) for r in [r1, r2, r3, r4]) and fatal_exit(
        f"ratio must be decimal, {r1=}, {r2=}, {r3=}, {r4=}, "
    )

    unit = 1000
    __int = lambda r: int(r)
    __normalize = lambda r: (r + 1) / 2
    return 0 \
        + __int(__normalize(r1) * unit * unit * unit * unit) \
        + __int(__normalize(r2) * unit * unit * unit) \
        + __int(__normalize(r3) * unit * unit) \
        + __int(__normalize(r4) * unit) \
        + 0


def to_file_prefix(f: str) -> str:
    return os.path.basename(f).split(".")[0]


def to_file_process(f: str) -> str:
    return f"{os.path.basename(f).split('.')[0]}[{os.getpid()}]"


def to_info_process(s: str) -> str:
    return f"{s}[{os.getpid()}]"


def name_to_desc(n: Union[Callable, str]) -> str:
    """ 去掉下划线"""
    name = n.__name__ if callable(n) else str(n)
    return name.replace("_", " ") if not_empty(name) else ""


def bool_to_desc(b: bool, hint_if_true) -> str:
    return hint_if_true if b else f"not_{hint_if_true}"


def name_safe(n: Union[Callable, str]) -> str:
    return n.__name__ if callable(n) else str(n) if n is not None else ""


def errname(err: BaseException) -> str:
    s = type(err).__name__
    s = s.replace("Error", "ERR")  # note: 为了防止我们grep error是显示warn中的信息，例如FileNotFoundError
    return s


def errinfo(err: BaseException) -> str:
    s = repr(err)
    s = s.replace("Error", "ERR")  # note: 为了防止我们grep error是显示warn中的信息，例如FileNotFoundError
    return s


# note: 命名参数必须放到后面，否则报错：TypeError: argname() got multiple values for argument
def argname(*args_tuple, left="", right="", delim="", is_log=False) -> str:
    """ 参数 """
    name = f"{left if len(args_tuple) else ''}" \
           f"{delim.join(str(x) for x in args_tuple) if len(args_tuple) else ''}" \
           f"{right if len(args_tuple) else ''}"
    is_log and log(name)
    return name


# note: 命名参数必须放到后面，否则报错：TypeError: argname() got multiple values for argument
def funcname(func: Union[str, Callable], *args_tuple, is_log=False) -> str:
    """ 函数（名称，参数） """
    name = f"{func.__name__ if callable(func) else str(func) if not_empty(func) else ''}" \
           f"{argname(left='(', right=')', delim=',', *args_tuple)}"
    is_log and log(name)
    return name


# note: 命名参数必须放到后面，否则报错：TypeError: argname() got multiple values for argument
def objectname(cls, *args_tuple, is_log=False) -> str:
    """ 类对象（类，属性）"""
    name = f"{cls.__name__}" \
           f"{argname(left='{', right='}', delim=',', *args_tuple)}"
    is_log and log(name)
    return name


# note: 命名参数必须放到后面，否则报错：TypeError: argname() got multiple values for argument
def methodname(obj, func: Union[str, Callable], *args_tuple, is_log=False) -> str:
    """ 类方法（对象，函数名称，函数参数）"""
    name = f"{obj}.{funcname(func, *args_tuple, is_log=False)}"
    is_log and log(name)
    return name


def clazzname(cls_or_name):
    return cls_or_name if of_str(cls_or_name) else cls_or_name.__name__


def object_2_clazzname(obj):
    return obj.__class__.__name__


# 装饰函数
def decorator_rename(new_name):
    def inner(f):
        f.__name__ = new_name
        return f

    return inner


# 发送邮件
def send_email(
        smtp_server: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        sender_email: str,
        receiver_email_list: list[str],
        subject_text: str = None,
        body_text: str = None,
        body_html: str = None,
        attach_file_list: list[str] = None,
        is_log=False,
):
    fn = send_email.__name__

    is_log and log(f"{fn}, {smtp_server=}, {smtp_username=}, {sender_email=}")

    if any_empty(smtp_server, smtp_port, smtp_username, smtp_password):
        warn(f"{fn}, smtp arg empty")
        return
    if any_empty(sender_email, receiver_email_list):
        warn(f"{fn}, sender or receiver arg empty")
        return

    msg = email.mime.multipart.MIMEMultipart()

    msg['From'] = email.header.Header(sender_email, __the_smtp_encoding)

    msg['To'] = email.header.Header(email.utils.COMMASPACE.join(receiver_email_list), __the_smtp_encoding)

    msg['Subject'] = email.header.Header(empty_safe(
        subject_text, f"({timestamp_str()})"
    ), __the_smtp_encoding)

    # msg.attach(email.mime.text.MIMEText(empty_safe(
    #     body_text, "(empty)"
    # ), 'plain', __the_smtp_encoding))

    body_str = f"{body_text or ''}{body_html or ''}"
    msg.attach(email.mime.text.MIMEText(empty_safe(
        body_str, "(empty)"
    ), 'html', __the_smtp_encoding))

    for file in attach_file_list or []:
        if os.path.isfile(empty_safe(file, "")):
            with open(file, "rb") as file_handler:
                part = email.mime.application.MIMEApplication(
                    file_handler.read(),
                    Name=os.path.basename(file)
                )
            # After the file is closed
            part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(file)
            msg.attach(part)

    is_log and log(f"{fn}, before ")

    # noinspection PyBroadException
    try:
        # 修改默认的 SSL 上下文以适应某些网络环境
        import ssl
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        mailer = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) if __the_smtp_ssl \
            else smtplib.SMTP(smtp_server, port=smtp_port)
        mailer.set_debuglevel(__the_smtp_debuglevel)
        mailer.login(smtp_username, smtp_password)
        mailer.send_message(msg, sender_email, receiver_email_list)
        mailer.quit()
    except Exception as err:
        log(f"邮件发送失败(非致命错误): {err}")
        # exception(err, f"{fn}")

    is_log and log(f"{fn}, afterr ")

    #
    return


# 使用bs邮箱发送邮件
def send_email_with_bs(receiver_email_list: list[str],
                       subject_text: str = None,
                       body_text: str = None,
                       attach_file_list: list[str] = None,
                       is_send=True):
    if is_send:
        send_email('smtp.gmail.com', 587, 'yandicheng880@gmail.com',
           'ohapvhjdqhxtnplu', 'yandicheng880@gmail.com',

                   receiver_email_list,
                   subject_text, body_text, '',
                   attach_file_list, True)


def sound_coin(count=1):
    # 金币声音
    try:
        for _ in range(0, count):
            beepy.beep(sound="coin")
    except Exception as err:
        trace(f"{sound_coin.__name__}, {errinfo(err)}")


def check_var_exist_or_exist(m_file: str, var_prefix: str):
    try:
        sm = sys.modules[m_file]
        for field in [x for x in dir(sm) if x.startswith(var_prefix)]:
            valid_or_exit(not_empty(getattr(sm, field)), f"{field=} empty")
    except Exception as err:
        exception_exit(err, f"{check_var_exist_or_exist.__name__}, {m_file=}, {var_prefix=}")
    return


def check_notin_key_list(row_or_dict: Union[pd.Series, dict], key_list: list[str],
                         is_trace=True, is_error=False, is_fatal=False):
    notin_k_l = [key for key in key_list if key not in row_or_dict]
    not_empty(notin_k_l) and is_trace and trace(f"col not in row_or_dict, {notin_k_l=}, {row_or_dict=}")
    not_empty(notin_k_l) and is_error and error(f"col not in row_or_dict, {notin_k_l=}, {row_or_dict=}")
    not_empty(notin_k_l) and is_fatal and fatal_exit(f"col not in row_or_dict, {notin_k_l=}, {row_or_dict=}")
    return


def exec_try(exec_func: Callable[[], Any], default=None,
             try_call_count=1, try_interval_second=0,
             hint=None,
             is_log=False
             ) -> Any:
    """ 报错时重复执行 """
    is_exception, func_return_obj, func_call_count = True, default, 0
    while is_exception and func_call_count < try_call_count:
        # noinspection PyStatementEffect
        func_call_count += 1
        try:
            is_exception, func_return_obj = False, exec_func()
            # is_log and of_pd(func_return_obj) and log_pd(
            #     f"{name_safe(hint)}, {func_call_count=}, func_return_obj=", func_return_obj
            # )
            # is_log and not of_pd(func_return_obj) and log(
            #     f"{name_safe(hint)}, {func_call_count=}, {func_return_obj=}"
            # )
            # is_log and log(f"{exec_try.__name__}, {name_safe(hint)}, {func_call_count=}")
        except Exception as err:
            is_exception, func_return_obj = True, default
            is_log and exception(err, f"{name_safe(hint)}, {func_call_count=}")
            sleep(try_interval_second)  # 防止过快的请求频率
    #
    valid_or_exit(func_call_count > 0,
                  f"check: {func_call_count=} > 0, {try_call_count=}, {try_interval_second=}")
    return func_return_obj


def get_hs300_code1():
    return '399300'


def get_hs300_code2():
    return '000300'


# 判断是否沪深300 指数（其中'399300'和'000300'的innerCode分别为3146 和 3145）
def is_hs300(target) -> bool:
    if (target == get_hs300_code1()) or (target == get_hs300_code2()):
        return True
    else:
        return False


# 是否 无有效地量化股票代码（其中399300和000300为沪深300 指数） add by hhx 2024.08.09
def is_invalid_quantization_stock(target) -> bool:
    if not (target.startswith('60')
            or target.startswith('00')
            or target.startswith('30')
            or target.startswith('68')
            or is_hs300(target)):
        return True
    else:
        return False


# 获取指定目录下所有文件列表 add by hhx 2024.08.09
# path 指定目录
# filter_str 需要过滤的文件名标识
def get_all_files(path='', filter_str='') -> list:
    filelist = []
    target_path = path
    is_exist = pathlib.Path(target_path).is_dir()
    if not is_exist:
        return filelist

    files = os.listdir(str(target_path))
    for file in files:
        file_path = os.path.join(target_path, file)  # f"{path}/{file}"
        if os.path.isdir(file_path):
            filelist = get_all_files(str(file_path))
        else:
            if len(filter_str) > 0:
                if filter_str in file:  # file_path 改为 file，判断文件名中是否包含过滤字符串
                    filelist.append(file_path)
            else:
                filelist.append(file_path)

    return filelist


#############################################

# 基类（常用方法定义）
class Base:
    """ 基类（常用方法定义）"""

    def __repr__(self):
        return self.objectname()

    # note: 经常用于 __repr__，因此缺省不log
    def objectname(self, *obj_attrs, is_log=False) -> str:
        return objectname(self.__class__, *obj_attrs, is_log=is_log)

    def methodname(self, func: Union[str, Callable], *func_args_tuple, is_log=False) -> str:
        return methodname(repr(self), func, *func_args_tuple, is_log=is_log)

    def impl(self, method_func: Union[str, Callable], return_value):
        return impl_exit(self.methodname(method_func), return_value)


# 空（适配必须要代码的地方，例如tqdm的with ）
class Nope(Base):
    """ 空（适配必须要代码的地方，例如tqdm的with ） """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # note: 对于异常这里不处理，直接抛出
        return False


# 代码块
class CodeBlock(Base):
    """ 代码块（需要缩紧形成block便于阅读，并在特定时刻执行动作）"""

    def __init__(self,
                 hint: str = None,
                 act_func: Callable[[str], Any] = None,
                 act_enter_func: Callable[[str], Any] = None,
                 act_exit_func: Callable[[str], Any] = None,
                 act_del_func: Callable[[str], Any] = None,
                 ):
        self.hint = hint
        self.act_func = act_func
        self.act_enter_func = act_enter_func
        self.act_exit_func = act_exit_func
        self.act_del_func = act_del_func
        return

    def __del__(self):
        fn = funcname(self.__del__)
        not_empty(self.hint) and log(f"{self.hint}, {fn}")
        self.act_func and self.act_func(f"{fn}")
        self.act_del_func and self.act_del_func(f"{fn}")
        return self

    def __enter__(self):
        fn = funcname(self.__enter__)
        not_empty(self.hint) and log(f"{self.hint}, {fn}")
        self.act_func and self.act_func(f"{fn}")
        self.act_enter_func and self.act_enter_func(f"{fn}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        fn = funcname(self.__exit__)
        not_empty(self.hint) and log(f"{self.hint}, {fn}")
        self.act_func and self.act_func(f"{fn}")
        self.act_exit_func and self.act_exit_func(f"{fn}")
        # note: 对于异常这里不处理，直接抛出
        return False


# 日志时间开始与结束
class TimeLog(Base):
    """ 日志时间开始与结束
        note: 如果以Guard模式使用，必须赋值给一个变量，例如
            # noinspection PyUnusedLocal
            timelog = dfutil.TimeLog(dfutil.name_to_desc(extract_bin))
    """

    def __init__(self, tag="",
                 is_show_begin_end=True, is_show_enter_exit=False,
                 is_line_begin_as_main=False, is_line_end_as_main=False,
                 ):
        self.tag = tag
        self.is_show_begin = is_show_begin_end
        self.is_show_end = is_show_begin_end
        self.is_show_enter = is_show_enter_exit
        self.is_show_exit = is_show_enter_exit
        self.is_main_begin = is_line_begin_as_main
        self.is_main_end = is_line_end_as_main

        self.hms_begin = timestamp_hhmmss_str()
        self.hms_end = None
        self.is_show_begin and log(
            f"{self.tag}, "
            f"time begin, "
            f"{self.hms_begin} "
            f"{the_line_main if self.is_main_begin else the_line_func}")

        return

    def __repr__(self):
        # note: 简化日志调用（例如，f"{timelog}"）
        return self.tag  # self.objectname()

    def __del__(self):
        self.hms_end = timestamp_hhmmss_str()
        duration = duration_str_by_hhmmss_2(self.hms_begin, self.hms_end)
        self.is_show_end and log(
            f"{self.tag}, "
            f"time enddd, "
            f"{duration} "
            f"{the_line_main if self.is_main_end else the_line_func}")
        return

    def __enter__(self):
        self.is_show_enter and log(
            f"{TimeLog.__name__}, __enter__"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.is_show_exit and log(
            f"{TimeLog.__name__}, __exit__"
        )
        # note: 对于异常这里不处理，直接抛出
        return False


#
class FlagSwitch(Base):
    """ 用于保存最近设置的 flog 取值，以便 set | reset """

    def __init__(self, is_log=False):
        self.is_log = is_log
        self.flag_2_val = {}
        return

    def set_flag_list(self, module_name, flag_prefix_list: list[str], flag_val: bool):
        for flag_prefix in flag_prefix_list:
            self.set_flag(module_name, flag_prefix, flag_val)

    def set_flag(self, module_name, flag_prefix: str, flag_val: bool):
        sm = sys.modules[module_name]
        if not len(self.flag_2_val):
            self.flag_2_val.update({
                flag: getattr(sm, flag)
                for flag in dir(sm)
                if flag.startswith(flag_prefix)
            })
        for flag in self.flag_2_val:
            setattr(sm, flag, flag_val)
        return

    def reset_flag(self, module_name):
        sm = sys.modules[module_name]
        for flag in self.flag_2_val:
            setattr(sm, flag, self.flag_2_val[flag])
        return


#
class Key2FuncInvoke(Base):
    """ 针对 {key:func} 配置，根据参数 key，选择对应的 func 并进行调用 """

    def __init__(self, key_2_func: dict[str, Callable[[Any], Any]], ):
        self.key_2_func = key_2_func
        return

    def call_a0(self, key: str, hint=None, default=None, is_fatal_miss=False) -> Optional[Any]:
        """ 0 argument ( default 定义返回值数目）"""
        func = to_dict_val(self.key_2_func, key)
        is_fatal_miss and empty(func) and unsupported_exit(f"{name_safe(hint)}, {key=}")
        empty(func) and warn(f"{name_safe(hint)}, func empty, {key=}")
        return default if empty(func) else func()

    def call_a1(self, key: str, arg: Optional[Any], hint=None, default=None, is_fatal_miss=False) -> Optional[Any]:
        """ 1 argument ( default 定义返回值数目）"""
        func = to_dict_val(self.key_2_func, key)
        is_fatal_miss and empty(func) and unsupported_exit(f"{name_safe(hint)}, {key=}")
        empty(func) and warn(f"{name_safe(hint)}, func empty, {key=}")
        return default if empty(func) else func(arg)

    # noinspection PyPep8Naming
    def try_a0(self, key: str, default=None, hint=None, desc=None,
               is_fatal_miss=False,
               is_pandas_warning_false=False,
               is_exception_warn_IndexError=False,
               is_exception_warn_SyntaxError=False,
               is_exception_warn_KeyError=False,
               is_exception_exit=False) -> Optional[tuple[Any, Any]]:
        """ 0 argument ( default 定义返回值数目）"""
        # note: akshare问题，1.8版本会报告错误：
        #       venv/lib/python3.9/site-packages/akshare/stock/stock_us_sina.py:196: SettingWithCopyWarning:
        #       A value is trying to be set on a copy of a slice from a DataFrame
        #       See the caveats in the documentation: https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
        with PandasWarningFalse() if is_pandas_warning_false else Nope():
            try:
                return self.call_a0(key, hint, default=default, is_fatal_miss=is_fatal_miss)
            except Exception as err:
                self.__handle_exception(
                    err, hint, desc,
                    is_exception_exit,
                    is_exception_warn_IndexError,
                    is_exception_warn_KeyError,
                    is_exception_warn_SyntaxError
                )
        return default

    # noinspection PyPep8Naming
    def try_a1(self, key: str, arg: Optional[Any], default=None, hint=None, desc=None,
               is_fatal_miss=False,
               is_pandas_warning_false=False,
               is_exception_warn_IndexError=False,
               is_exception_warn_SyntaxError=False,
               is_exception_warn_KeyError=False,
               is_exception_exit=False) -> Optional[tuple[Any, Any]]:
        """ 1 argument ( default 定义返回值数目）"""
        # note: akshare问题，1.8版本会报告错误：
        #       venv/lib/python3.9/site-packages/akshare/stock/stock_us_sina.py:196: SettingWithCopyWarning:
        #       A value is trying to be set on a copy of a slice from a DataFrame
        #       See the caveats in the documentation: https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
        with PandasWarningFalse() if is_pandas_warning_false else Nope():
            try:
                return self.call_a1(key, arg, hint, default=default, is_fatal_miss=is_fatal_miss)
            except Exception as err:
                self.__handle_exception(
                    err, hint, desc,
                    is_exception_exit,
                    is_exception_warn_IndexError,
                    is_exception_warn_KeyError,
                    is_exception_warn_SyntaxError
                )
        return default

    # noinspection PyPep8Naming
    def __handle_exception(self, err: Exception, hint, desc,
                           is_exception_exit,
                           is_exception_warn_IndexError,
                           is_exception_warn_KeyError,
                           is_exception_warn_SyntaxError):
        # 如果某个标的代码不存在（例如新股），akshare会报错，我们跳过它继续
        # 其它错误报错或者退出（例如无法连接）
        if is_exception_warn_IndexError and type(err) == IndexError:
            warn(f"{name_safe(hint)}, {desc}, {errinfo(err)}")
        elif is_exception_warn_SyntaxError and type(err) == SyntaxError:
            warn(f"{name_safe(hint)}, {desc}, {errinfo(err)}")
        elif is_exception_warn_KeyError and type(err) == KeyError:
            warn(f"{name_safe(hint)}, {desc}, {errinfo(err)}")
        elif is_exception_exit:
            exception_exit(err, f"{name_safe(hint)}, {desc}")
        else:
            exception(err, f"{name_safe(hint)}, {desc}")


#
class Prefix2FuncInvoke(Base):
    """ 针对 {prefix:func} 配置，根据参数 name 通过选择最长的 prefix，选择对应的 func 并进行调用 """

    def __init__(self, prefix_2_func: dict[str, Callable[[Any], Any]], ):
        self.prefix_2_func = prefix_2_func
        return

    def call_a0(self, name: str, default=None, hint=None, is_fatal_miss=False) -> Optional[Any]:
        """ 0 argument ( default 定义返回值数目）"""
        func = self._to_func(name, hint, is_fatal_miss)
        return default if empty(func) else func()

    def call_a1(self, name: str, arg: Optional[Any], default=None, hint=None, is_fatal_miss=False) -> Optional[Any]:
        """ 1 argument ( default 定义返回值数目）"""
        func = self._to_func(name, hint, is_fatal_miss)
        return default if empty(func) else func(arg)

    def _to_func(self, name, hint, is_fatal_miss):
        func = to_dict_val(
            self.prefix_2_func, self._greedy_prefix(name), None, is_fatal_miss=is_fatal_miss
        )
        is_fatal_miss and empty(func) and unsupported_exit(
            f"{name_safe(hint)}, {name=}, {self.prefix_2_func.keys()=}"
        )
        empty(func) and warn(f"{name_safe(hint)}, func empty, {name=}")
        return func

    def _greedy_prefix(self, name):
        # 最大长度匹配（如果长度相同，则选择第一个长度的）
        prefix_list = [prefix for prefix in self.prefix_2_func if name.startswith(prefix)]
        max_prefix, max_len = None, 0
        for prefix in prefix_list:
            if len(prefix) > max_len:
                max_prefix, max_len = prefix, len(prefix)
        return max_prefix


#
class AttributeDict(dict):
    """ 通过 属性 方式使用 dict """

    __slots__ = ()
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


#
class WorkflowAction(Base):
    """ 工作流动作判别 """

    def __init__(self, action_list: list[str]):
        # note: 没有任何参数表示执行workflow，意味着，或者得到更新后的数据从而继续，或者退出等待下次重新判断
        self._action_list = action_list
        self._action = None
        return

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # note: 对于异常这里不处理，直接抛出
        return False

    def action(self):
        return self._action

    def start(self) -> bool:
        # 缺省进入工作流
        return empty(self._action_list)

    def need(self, action) -> bool:
        # 处于工作流中，或者，特别指定
        self._action = action
        return is_list_empty_or_contain(self._action_list, action)

    def special(self, action) -> bool:
        # 不属于工作流（需要特别指定）
        self._action = action
        return is_list_contain_all(self._action_list, action)


# 数据空间定义
class ValueSpace(Base):
    """  数据空间定义 """

    def __init__(self, is_log=False):
        self.is_log = is_log
        return

    def to_space_str_list(self, col_len: int, val_list: list[str], join_delim: str = "") -> list[str]:
        fn = f"{self.to_space_str_list.__name__}"

        self.is_log and log(f"{fn}, space create begin, ....")
        col = "_"  # 内部字段，无意义
        df_space = pd.DataFrame(columns={col})
        for _ in range(0, col_len):
            df_col = pd.DataFrame(val_list, columns=[col])
            df_space = df_col if empty(df_space) else df_space.merge(df_col, how="cross")  # 笛卡尔积
            self.is_log and log(f"{fn}, {col = }, len curr = {len(df_col)}, len total = {len(df_space)}")
        self.is_log and log(f"{fn}, space create enddd, len total = {len(df_space)}")

        return df_space.apply(
            lambda x: join_delim.join(x),
            axis=1
        ).to_list()

    def to_space_tuple_list(self,
                            val_list: list[Any],
                            placeholder_val: Any = None,
                            is_unique_exclude_placeholder=True,
                            ) -> list[tuple[Any]]:
        """ 返回组合元素列表
            placeholder_val 表示是否需要在结果中 包括 无意义的取值（例如，对结果处理时希望排除掉某些元素）
            is_unique 表示是否某组结果中的所有元素都必须不同
        """
        fn = f"{self.to_space_tuple_list.__name__}"

        space_col_len = len(val_list)
        space_val_list = val_list + ([placeholder_val] if placeholder_val is not None else [])

        self.is_log and log(f"{fn}, space create begin, ....")
        col = "_"  # 内部字段，无意义
        df_space = pd.DataFrame(columns={col})
        for _ in range(0, space_col_len):
            df_col = pd.DataFrame(space_val_list, columns=[col])
            df_space = df_col if empty(df_space) else df_space.merge(df_col, how="cross")  # 笛卡尔积
            self.is_log and log(f"{fn}, {col = }, len curr = {len(df_col)}, len total = {len(df_space)}")
        self.is_log and log(f"{fn}, space create enddd, len total = {len(df_space)}")

        def __unique(t: tuple):
            compare_t = [x for x in t if x != placeholder_val]
            return len(set(compare_t)) == len(compare_t)

        # noinspection PyTypeChecker
        tuplelist = [
            x for x in (df_space.apply(tuple, axis=1).to_list())
            if False
               or (not is_unique_exclude_placeholder)
               or (is_unique_exclude_placeholder and __unique(x))
        ]
        self.is_log and log(f"{fn}, {is_unique_exclude_placeholder=}, {len(tuplelist)=}")
        return tuplelist


# 数据空间定义
# range_dict 必须具有如下的key属性： key, min, max, offset
class RangeSpace(Base):
    """ 数据空间定义
        range_dict 必须具有如下的key属性： key, min, max, offset
    """

    def __init__(self, is_log=False):
        self.is_log = is_log
        self.range_dictlist: list[dict[str, Any]] = []
        return

    def check_range(self,
                    key_prefix_list: list[str] = None,
                    val_min_range: [float, float] = None,
                    val_max_range: [float, float] = None,
                    val_offset_range: [float, float] = None):

        def __prefix(__prefix_list, __key):
            kl = [x[__key] for x in self.range_dictlist]
            __prefix_list is not None and valid_or_exit(
                len(sub_list_by_prefix(kl, __prefix_list)) == len(kl),
                f"check: '{__key}' prefix illegal, {__prefix_list=}, {self.range_dictlist=}")

        def __range(__range_tuple, __key):
            __range_tuple is not None and valid_or_exit(
                __range_tuple[0] <= min([x[__key] for x in self.range_dictlist]),
                f"check: '{__key}' min overflow, {__range_tuple=}, {self.range_dictlist=}")
            __range_tuple is not None and valid_or_exit(
                max([x[__key] for x in self.range_dictlist]) <= __range_tuple[1],
                f"check: '{__key}' max overflow, {__range_tuple=}, {self.range_dictlist=}")

        __prefix(key_prefix_list, "key")
        __range(val_min_range, "min")
        __range(val_max_range, "max")
        __range(val_offset_range, "offset")

        return self  # chain 操作

    def adjust_range_min(self,
                         key_substr_or_list: Union[str, list[str]], val_min: float):
        key_substr_list = convert_to_list(key_substr_or_list)
        for d in self.range_dictlist:
            if all(is_str_contain_any(d["key"], key_substr) for key_substr in key_substr_list):
                d["min"] = val_min

        return self  # chain 操作

    def adjust_range_max(self,
                         key_substr: str, val_max: float):
        for d in self.range_dictlist:
            if is_str_contain_any(d["key"], key_substr):
                d["max"] = val_max

        return self  # chain 操作

    def append_range(self,
                     key: str, val_min: float, val_max: float, val_offset: float,
                     df_range: pd.DataFrame = None
                     ):
        """ range_dict 必须具有如下的key属性： key, min, max, offset """
        self.range_dictlist.append({
            "key": key,
            "min": val_min if df_range is None else max(val_min, df_range.eval(key).min()),
            "max": val_max if df_range is None else min(val_max, df_range.eval(key).max()),
            "offset": val_offset,
        })

        return self  # chain 操作

    def append_range_segment(self,
                             key: str,
                             val_min_max_offset_list: list[tuple[float, float, float]],
                             df_range: pd.DataFrame = None):
        """ range_dict 必须具有如下的key属性： key, min, max, offset （允许不同的 min/max/offset 组合）"""
        dl = []
        for v_min, v_max, v_offset in val_min_max_offset_list:
            dl.append({
                "min": v_min if df_range is None else max(v_min, df_range.eval(key).min()),
                "max": v_max if df_range is None else min(v_max, df_range.eval(key).max()),
                "offset": v_offset,
            })
        self.range_dictlist.append({
            "key": key,
            "min_max_offset_list": dl
        })

        return self  # chain 操作

    def create_range_df(self) -> pd.DataFrame:
        """ range_dict 必须具有如下的key属性： key, min, max, offset """
        fn = self.create_range_df.__name__

        self.is_log and log(f"{fn}, space create start, ....")

        self.is_log and log(f"{fn}, {self.range_dictlist=}")

        def __dict2list(__d):
            return [
                x for x in np.arange(
                    __d["min"],
                    __d["max"] + 0.0000001,  # __d["max"] + __d["offset"], # note: max要稍大于min，否则无值
                    __d["offset"]
                )]

        df_space = pd.DataFrame(columns=[x["key"] for x in self.range_dictlist])
        for range_dict in self.range_dictlist:
            key = range_dict["key"]

            val_list = []
            if "min_max_offset_list" in range_dict:
                for val_min_max_offset in range_dict["min_max_offset_list"]:
                    val_list.extend(__dict2list(val_min_max_offset))
                self.is_log and log(f"{fn}, min_max_offset_list, {key=}, {val_list=}")
            else:
                val_list.extend(__dict2list(range_dict))

            #
            df_key = pd.DataFrame(val_list, columns=[key])
            df_space = df_key if empty(df_space) else df_space.merge(df_key, how="cross")  # 笛卡尔积
            self.is_log and log(f"{fn}, {key=}, len curr = {pd_len_row(df_key)}, len total = {pd_len_row(df_space)}")

        df_space.reset_index(drop=True, inplace=True)
        self.is_log and log(f"{fn}, space create enddd, len total = {pd_len_row(df_space)}")

        return df_space


# 对象缓存
class ObjectCache(Base):
    """ 对象缓存
    """

    def __init__(self, is_log=False):
        self._is_log: bool = is_log
        self._cache: dict[str, Optional[Any]] = dict()
        return

    def enable_log(self,
                   is_log):
        self._is_log = is_log

    def load_cache(self,
                   key: str,
                   init_func: Callable[[], Any],
                   is_log=False,
                   ) -> Optional[Any]:
        val = self._cache[key] if key in self._cache else None

        if val is not None:
            self._is_log and is_log and log(f"....cache : gettt, {key}")

        if val is None:
            with TimeLog(f"....cache : initt, {key}") if self._is_log and is_log else Nope():
                val = init_func()

            self._cache[key] = val
            self._is_log and is_log and log(f"....cache : settt, {key}")

        return val

    def clear_cache(self,
                    key: str,
                    is_log=False):
        self._cache[key] = None
        self._is_log and is_log and log(f"....cache : clear, {key}")

    def purge_cache(self,
                    key: str,
                    init_func: Callable[[], Any],
                    clear_val: Any,
                    is_log=False,
                    ):
        val = self.load_cache(key=key, init_func=init_func, is_log=is_log)
        if val == clear_val:
            warn(f"....cache : purge, {key}, {val=} == {clear_val=}, clear")
            self.clear_cache(key=key, is_log=is_log)

    def set_cache(self,
                  key: str,
                  set_func: Callable[[], Any],
                  is_log=False,
                  ) -> Optional[Any]:
        self.clear_cache(key=key, is_log=is_log)
        return self.load_cache(key=key, init_func=set_func, is_log=is_log)


# 通用缓存
class CacheUtil(Base):
    """ 通用缓存
        note: static 使用 使用上比较简单，不需要创建对象
    """
    _cache: dict[str, Optional[Any]] = dict()
    _is_log: bool = False

    @staticmethod
    def show_log(is_log):
        CacheUtil._is_log = is_log

    @staticmethod
    def reset_cache_of_key(key: str,
                           is_log=False):
        if CacheUtil._cache is not None:
            CacheUtil._cache[key] = None
            is_log and log(f"....cache : reset, {key}")

    @staticmethod
    def reset_cache_of_all(hint: str = None,
                           is_log=False):
        if CacheUtil._cache is not None:
            CacheUtil._cache.clear()
            is_log and log(f"....cache : reset all, {hint}")

    @staticmethod
    def load_cache(key: str,
                   init_func: Callable[[], Any],
                   is_log=False,
                   ) -> Optional[Any]:
        val = CacheUtil._cache[key] if key in CacheUtil._cache else None

        if val is not None:
            CacheUtil._is_log_cache(is_log) and log(f"....cache : gettt, {key}")

        if val is None:
            with TimeLog(f"....cache : initt, {key}") if CacheUtil._is_log_cache(is_log) else Nope():
                val = init_func()

            CacheUtil._cache[key] = val
            CacheUtil._is_log_cache(is_log) and log(f"....cache : settt, {key}")

        return val

    @staticmethod
    def clear_cache(key: str,
                    is_log=False):
        CacheUtil._cache[key] = None
        CacheUtil._is_log_cache(is_log) and log(f"....cache : clear, {key}")

    @staticmethod
    def purge_cache(key: str,
                    init_func: Callable[[], Any],
                    clear_val: Any,
                    is_log=False,
                    ):
        val = CacheUtil.load_cache(key=key, init_func=init_func, is_log=is_log)
        if val == clear_val:
            warn(f"....cache : purge, {key}, {val=} == {clear_val=}, clear")
            CacheUtil.clear_cache(key=key, is_log=is_log)

    @staticmethod
    def set_cache(key: str,
                  init_func: Callable[[], Any],
                  is_log=False,
                  ) -> Optional[Any]:
        CacheUtil.clear_cache(key=key, is_log=is_log)
        return CacheUtil.load_cache(key=key, init_func=init_func, is_log=is_log)

    @staticmethod
    def _is_log_cache(is_log):
        return CacheUtil._is_log or is_log


# pandas数据缓存
class PandasCacheUtil(Base):
    """ pandas数据缓存
        note: static 使用 使用上比较简单，不需要创建对象
    """
    _is_log: bool = False

    @staticmethod
    def show_log(is_log):
        PandasCacheUtil._is_log = is_log

    @staticmethod
    def reset_cache_of_key(cache: dict[str, Optional[pd.DataFrame]],
                           key: str,
                           is_log=False):
        if cache is not None:
            cache[key] = None
            PandasCacheUtil._is_log_cache(is_log) and log(f"....cache : reset, {key}")

    @staticmethod
    def reset_cache_of_all(cache: dict[str, Optional[pd.DataFrame]],
                           hint: str,
                           is_log=False):
        if cache is not None:
            cache.clear()
            PandasCacheUtil._is_log_cache(is_log) and log(f"....cache : reset all, {hint}")

    @staticmethod
    def load_cache(cache: dict[str, Optional[pd.DataFrame]],
                   key: str,
                   read_func: Callable[[], Optional[pd.DataFrame]],
                   is_cache=True, is_cache_copy=True,
                   is_log=False,
                   ) -> Optional[pd.DataFrame]:
        df = None

        if is_cache and cache is not None:
            df_cache = cache[key] if key in cache else None
            if df_cache is not None:
                df = df_cache.copy() if is_cache_copy else df_cache  # note: copy 可能性能瓶颈
                PandasCacheUtil._is_log_cache(is_log) and log(f"....cache : gettt, {key}")

        if df is None:
            with TimeLog(f"....cache : readd, {key}") if PandasCacheUtil._is_log_cache(is_log) else Nope():
                df = read_func()

            if is_cache and cache is not None:
                cache[key] = df.copy() if df is not None else None  # copy 防止被更改
                PandasCacheUtil._is_log_cache(is_log) and log(f"....cache : settt, {key}")

        return df

    @staticmethod
    def clear_cache(cache: dict[str, Optional[pd.DataFrame]],
                    key: str,
                    write_func: Callable[[], Optional[bool]],
                    is_log=False):
        with TimeLog(f"....cache : write, {key}") if PandasCacheUtil._is_log_cache(is_log) else Nope():
            write_func()

        if cache is not None:
            cache[key] = None
            PandasCacheUtil._is_log_cache(is_log) and log(f"....cache : clear, {key}")

    @staticmethod
    def _is_log_cache(is_log):
        return PandasCacheUtil._is_log and is_log


# 屏蔽 pandas 无意义的警告
class PandasWarningFalse(Base):
    """ 屏蔽 pandas 无意义的警告
        note: 例如：
            value is trying to be set on a copy of a slice from a DataFrame.
    """

    def __init__(self, is_log=False):
        self.is_log = is_log
        return

    def __del__(self):
        return

    def __enter__(self):
        fn = funcname(self.__enter__)
        hint = PandasWarningFalse.__name__
        self.is_log and log(f"{hint}, {fn}")
        set_pd_option_warn()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        fn = funcname(self.__exit__)
        hint = PandasWarningFalse.__name__
        self.is_log and log(f"{hint}, {fn}")
        reset_pd_option()
        # note: 对于异常这里不处理，直接抛出
        return False


#
class FileCsv(Base):
    """ csv 文件处理 """

    @staticmethod
    def read(pathfile, sep, dtype, usecols, nrows, is_t, csv_encoding) -> pd.DataFrame:
        # note：sep为Null告警：
        #       ParserWarning: Falling back to the 'python' engine because the 'c' engine does not support sep=None with delim_whitespace=False;
        #       you can avoid this warning by specifying engine='python'.
        if sep is None:
            if is_t:
                return pd.read_csv(pathfile, dtype=dtype, usecols=usecols, nrows=nrows, encoding=csv_encoding,
                                   index_col=0, header=0)
            else:
                return pd.read_csv(pathfile, dtype=dtype, usecols=usecols, nrows=nrows, encoding=csv_encoding)
        else:
            if is_t:
                return pd.read_csv(pathfile, sep=sep, dtype=dtype, usecols=usecols, nrows=nrows, encoding=csv_encoding,
                                   index_col=0, header=0)
            else:
                return pd.read_csv(pathfile, sep=sep, dtype=dtype, usecols=usecols, nrows=nrows, encoding=csv_encoding)

    @staticmethod
    def write(df: pd.DataFrame, pathfile, is_t, is_format, csv_float_format, csv_encoding, mode='w'):
        if is_format:
            if is_t:
                df.transpose().to_csv(pathfile, index=True, float_format=csv_float_format, encoding=csv_encoding,
                                      mode=mode)
            else:
                """
                添加mode参数：mode参数用于指定文件的打开模式 modify by hhx 2024.08.01
                ‌其中'a'表示追加模式，‌意味着如果文件已经存在，‌新的数据将被追加到文件的末尾，‌而不是覆盖原有的内容；
                   'w'表示重新写入，会覆盖原来的内容
                """
                df.to_csv(pathfile, index=False, float_format=csv_float_format, encoding=csv_encoding, mode=mode)
        else:
            if is_t:
                df.transpose().to_csv(pathfile, index=True, encoding=csv_encoding, mode=mode)
            else:
                df.to_csv(pathfile, index=False, encoding=csv_encoding, mode=mode)
        return


#
class FilePkl(Base):
    """ pkl 文件处理 """

    @staticmethod
    def read(pathfile) -> pd.DataFrame:
        return pd.read_pickle(pathfile)  # note: 此时 dtype/usecols 无效

    @staticmethod
    def write(df, pathfile):
        df.to_pickle(pathfile)
        return


#
class FileJbl(Base):
    """ jbl 文件处理 """

    @staticmethod
    def read(pathfile) -> Any:
        return joblib.load(pathfile)

    @staticmethod
    def write(obj, pathfile):
        joblib.dump(obj, pathfile)
        return


# Pandas文件操作
class PandasFile(Base):
    """ Pandas文件操作
        note：压缩格式比较（倍数基准为pkl）
            保存时间(从小到大)   : zip(5x), z(7x), bz2(30~40x，很慢), gz(8~50x，很慢), xz(太很慢)
            读取时间(从小到大)   : zip(2x), z(3x), gz(2~4x), bz2(9~20x, 很慢),
            磁盘空间(从小到大)   : bz2(0.22x), gz(0.27x), zip(0.27x), z(0.3~0.5x)
            pkl 支持           : zip, gz, bz2, xz,
            jbl 支持           : z, gz, bz2, xz, lzma,
            csv 支持           : zip, gz, bz2, xz,
        举例：df_good_filter
            write pkl(6s, 650mb)   : zip(35s, 179mb), bz2(186s, 146mb), gz(334s, 177mb),
                  jbl(19s, 1320mb) : z(43s, 382mb), gz(49s, 381mb), bz2(250s, 294mb), xz(1670s, 162mb), lzma(1880s, 162mb),
                  csv(253s, 629mb) : zip(274s, 162mb), bz2(361s, 133mb), gz(425s, 160mb), xz(935s, 72mb),
            read  pkl(5s, 650mb)   : zip(9s, 179mb), gz(10s, 177mb), bz2(45s, 146mb),
                  jbl(8s, 1320mb)  : z(16s, 382mb), gz(19s, 381mb), lzma(64s, 162mb), xz(70s, 162mb), bz2(109s, 294mb),
                  csv(52s, 629mb)  : zip(51s, 162mb), gz(54s, 160mb), xz(70s, 72mb), bz2(98s, 133mb),
    """

    def __init__(self,
                 csv_encoding=None,
                 csv_float_format=None,
                 is_log_func: Callable[[], bool] = None,
                 is_warn_file_not_found_func: Callable[[], bool] = None,
                 is_error_file_not_found_func: Callable[[], bool] = None,
                 check_dvalue_func: Callable[[pd.DataFrame, str], None] = None,
                 ):
        self.csv_encoding = csv_encoding
        self.csv_float_format = csv_float_format
        self.is_log_func = is_log_func
        self.is_warn_file_not_found_func = is_warn_file_not_found_func
        self.is_error_file_not_found_func = is_error_file_not_found_func
        self.check_dvalue_func = check_dvalue_func
        return

    # noinspection PyMethodMayBeStatic
    def _is_log_file(self, is_log):
        return False if not is_log \
            else self.is_log_func() if self.is_log_func \
            else True

    # noinspection PyMethodMayBeStatic
    def _is_warn_file_not_found(self, is_warn_file_not_found):
        return False if not is_warn_file_not_found \
            else self.is_warn_file_not_found_func() if self.is_warn_file_not_found_func \
            else True

    # noinspection PyMethodMayBeStatic
    def _is_error_file_not_found(self, is_error_file_not_found):
        return False if not is_error_file_not_found \
            else self.is_error_file_not_found_func() if self.is_error_file_not_found_func \
            else True

    # ================================================================

    # noinspection PyMethodMayBeStatic
    def _to_file_suffix_list(self,
                             is_file_hdf=False,  # todo: hdf文件总是报错
                             is_file_csv=False, is_file_csvzip=False, is_file_csvbz2=False, is_file_csvgz=False,
                             is_file_pkl=False, is_file_pklzip=False, is_file_pklbz2=False, is_file_pklgz=False,
                             is_file_jbl=False, is_file_jblz=False, is_file_jblgz=False,
                             ) -> list[str]:
        return sub_list_notnone([
            ".hdf" if is_file_hdf else None,
            ".jbl" if is_file_jbl else None,
            ".jbl.z" if is_file_jblz else None,
            ".jbl.gz" if is_file_jblgz else None,
            ".pkl" if is_file_pkl else None,
            ".pkl.zip" if is_file_pklzip else None,
            ".pkl.gz" if is_file_pklgz else None,
            ".pkl.bz2" if is_file_pklbz2 else None,
            ".csv" if is_file_csv else None,
            ".csv.zip" if is_file_csvzip else None,
            ".csv.gz" if is_file_csvgz else None,
            ".csv.bz2" if is_file_csvbz2 else None,
        ])

    # noinspection PyMethodMayBeStatic
    def _to_file_list(self, prefix: str,
                      is_file_hdf=False,  # todo: hdf文件总是报错
                      is_file_csv=False, is_file_csvzip=False, is_file_csvbz2=False, is_file_csvgz=False,
                      is_file_pkl=False, is_file_pklzip=False, is_file_pklbz2=False, is_file_pklgz=False,
                      is_file_jbl=False, is_file_jblz=False, is_file_jblgz=False,
                      ) -> list[str]:
        return [f"{prefix}{suffix}" for suffix in self._to_file_suffix_list(
            is_file_hdf,
            is_file_csv, is_file_csvzip, is_file_csvbz2, is_file_csvgz,
            is_file_pkl, is_file_pklzip, is_file_pklbz2, is_file_pklgz,
            is_file_jbl, is_file_jblz, is_file_jblgz
        )]

    # noinspection PyMethodMayBeStatic
    def _is_file_prefix_exist(self, prefix,
                              is_log=True):
        for pathfile in self._to_file_list(
                prefix,
                is_file_hdf=True,
                is_file_csv=True, is_file_csvzip=True, is_file_csvbz2=True, is_file_csvgz=True,
                is_file_pkl=True, is_file_pklzip=True, is_file_pklbz2=True, is_file_pklgz=True,
                is_file_jbl=True, is_file_jblz=True, is_file_jblgz=True,
        ):
            is_exist = pathlib.Path(pathfile).is_file()
            self._is_log_file(is_log) and is_exist and log(f"....exist : {pathfile}")  # 太多不存在文件
            if is_exist:
                return True
        #
        self._is_log_file(is_log) and warn(f"....exist : {prefix=}, False")
        return False

    # noinspection PyMethodMayBeStatic
    def _is_file_exist(self, pathfile,
                       is_log=True):
        is_exist = pathlib.Path(pathfile).is_file()
        self._is_log_file(is_log) and is_exist and log(f"....exist : {pathfile}")  # 太多不存在文件
        if is_exist:
            return True
        return False

    # noinspection PyMethodMayBeStatic
    def _is_file_prefix_multi_suffix(self, prefix,
                                     is_log=True):
        # note：对于同种类型的文件，只能存在一种格式，否则可能是旧数据新数据同时存在，需要手工调整（例如 jbl.gz 和 jbl.zip ）
        m_l_l = self._to_filepath_listlist_of_prefix_multi_suffix(prefix, is_log)
        if len(m_l_l) > 0:
            return error(f"....multi : {prefix=}, {m_l_l}", return_value=True)
        return False

    # noinspection PyMethodMayBeStatic
    def _to_filepath_listlist_of_prefix_multi_suffix(self, prefix,
                                                     is_log=True) -> list[list[str]]:
        # note：对于同种类型的文件，只能存在一种格式，否则可能是旧数据新数据同时存在，需要手工调整（例如 jbl.gz 和 jbl.zip ）
        def __multi(__l, __hdf=False, __csv=False, __pkl=False, __jbl=False):
            e_l = [pathfile for pathfile in
                   self._to_file_list(
                       prefix,
                       is_file_hdf=__hdf,
                       is_file_csv=__csv, is_file_csvzip=__csv, is_file_csvbz2=__csv, is_file_csvgz=__csv,
                       is_file_pkl=__pkl, is_file_pklzip=__pkl, is_file_pklbz2=__pkl, is_file_pklgz=__pkl,
                       is_file_jbl=__jbl, is_file_jblz=__jbl, is_file_jblgz=__jbl,
                   ) if pathlib.Path(pathfile).is_file()]
            if len(e_l) > 1:
                __l.append(e_l)
            return

        r_l = []
        __multi(r_l, True, False, False, False)
        __multi(r_l, False, True, False, False)
        __multi(r_l, False, False, True, False)
        __multi(r_l, False, False, False, True)
        return r_l

    def _rename_file_of_multi_suffix_to_suffix_timestamp(self, prefix: str,
                                                         is_log=True):
        # note：对于同种类型的文件，只能存在一种格式，否则可能是旧数据新数据同时存在，重新命名为不同时刻的文件，防止覆盖
        pathfile_listlist = self._to_filepath_listlist_of_prefix_multi_suffix(prefix, is_log)
        for pathfile_list in pathfile_listlist:
            second_2_pathfile = {os.path.getmtime(x): x for x in pathfile_list}
            # note: 如果时间戳相同，则需要手工调整
            len(second_2_pathfile) != len(pathfile_list) and fatal_exit(
                f"rename, modify time same, check, {pathfile_list=}"
            )
            #
            rename_second_2_pathfile = {
                x: second_2_pathfile[x]
                for x in (sorted(second_2_pathfile.keys(), reverse=True)[1:])
            }
            for second in rename_second_2_pathfile:
                timestamp = timestamp_by_datetime(datetime_from_epochtime(second))
                pathfile = rename_second_2_pathfile[second]
                new_pathfile = f"{pathfile}.{timestamp}"
                try:
                    pathlib.Path(pathfile).rename(new_pathfile)
                    # self._is_log_file(is_log) and log(f"....rename : {pathfile} -> {new_pathfile}")
                    info(f"....rename : {pathfile} -> {new_pathfile}")
                except FileNotFoundError as err:
                    warn(f"rename file, {errinfo(err)}, {pathfile=} -> {new_pathfile}")
                except Exception as err:
                    exception(err, f"rename file, {pathfile=} -> {new_pathfile}")
        return

    # noinspection PyMethodMayBeStatic
    def _try_prefix_suffix(self, pathfile, prefix, suffix) -> [str, bool]:
        # 如果prefix为空，则尝试分解prefix和suffix
        if not_empty(prefix):
            return prefix, False
        is_suffix = pathfile.endswith(suffix)
        prefix = pathfile[0:pathfile.index(suffix)] if is_suffix else ""
        return prefix, is_suffix

    # ================================================================

    def _check_read(self, df_or_obj, prefix_or_path, is_check, is_log, is_error_none, is_warn_none
                    ) -> bool:
        if df_or_obj is None and is_error_none:
            return error(f"read file, df none, ignore, {prefix_or_path=}", return_value=False)
        if df_or_obj is None and is_warn_none:
            return warn(f"read file, df none, ignore, {prefix_or_path=}", return_value=False)
        if df_or_obj is not None and is_check:
            not self.check_dvalue_func and fatal_exit(f"read file, check but check_dvalue_func none")
            self.check_dvalue_func(df_or_obj, prefix_or_path)
        #
        return True

    def _check_write(self, df_or_obj, prefix_or_path, is_check, is_log, is_error_none, is_warn_none
                     ) -> bool:
        if df_or_obj is None and is_error_none:
            return error(f"write file, df_or_obj none, ignore, {prefix_or_path=}", return_value=False)
        if df_or_obj is None and is_warn_none:
            return warn(f"write file, df_or_obj none, ignore, {prefix_or_path=}", return_value=False)
        if df_or_obj is not None and is_check:
            not self.check_dvalue_func and fatal_exit(f"write file, check but check_dvalue_func none")
            not of_pd_dataframe(df_or_obj) and warn(f"write file, check but not pd.DataFrame, {type(df_or_obj)=}")
            of_pd_dataframe(df_or_obj) and self.check_dvalue_func(df_or_obj, prefix_or_path)
        #
        create_path(prefix_or_path, is_log)
        return True

    # ================================================================

    def _copy_file(self, prefix_src: str, prefix_dst: str,
                   is_file_hdf=False,  # todo: hdf文件总是报错
                   is_file_csv=False, is_file_csvzip=False, is_file_csvbz2=False, is_file_csvgz=False,
                   is_file_pkl=False, is_file_pklzip=False, is_file_pklbz2=False, is_file_pklgz=False,
                   is_file_jbl=False, is_file_jblz=False, is_file_jblgz=False,
                   is_log=True, is_log_file_missing=False,
                   ):
        if not any([is_file_hdf,
                    is_file_csv, is_file_csvzip, is_file_csvbz2, is_file_csvgz,
                    is_file_pkl, is_file_pklzip, is_file_pklbz2, is_file_pklgz,
                    is_file_jbl, is_file_jblz, is_file_jblgz,
                    ]):
            trace("copy file, file type none")

        create_path(prefix_src, is_log)
        create_path(prefix_dst, is_log)
        for suffix in self._to_file_suffix_list(
                is_file_hdf,
                is_file_csv, is_file_csvzip, is_file_csvbz2, is_file_csvgz,
                is_file_pkl, is_file_pklzip, is_file_pklbz2, is_file_pklgz,
                is_file_jbl, is_file_jblz, is_file_jblgz
        ):
            source = prefix_src + suffix
            target = prefix_dst + suffix
            try:
                shutil.copyfile(source, target)
                self._is_log_file(is_log) and log(f"....copy : {source} > {target}")
            except FileNotFoundError as err:
                is_log_file_missing and warn(f"copy file, {errinfo(err)}, {prefix_src=}, {prefix_dst=}")
            except Exception as err:
                exception(err, f"copy file, {prefix_src=}, {prefix_dst=}")
        #
        return

    # noinspection PyMethodMayBeStatic
    def _copy_file_direct(self, file_src: str, file_dst: str,
                          is_log=True,
                          ):
        copy_file(file_src, file_dst, self._is_log_file(is_log))
        return

    # ================================================================

    def _delete_file(self, prefix: str,
                     is_file_hdf=False,  # todo: hdf文件总是报错
                     is_file_csv=False, is_file_csvzip=False, is_file_csvbz2=False, is_file_csvgz=False,
                     is_file_pkl=False, is_file_pklzip=False, is_file_pklbz2=False, is_file_pklgz=False,
                     is_file_jbl=False, is_file_jblz=False, is_file_jblgz=False,
                     is_log=True,
                     ):
        if not any([is_file_hdf,
                    is_file_csv, is_file_csvzip, is_file_csvbz2, is_file_csvgz,
                    is_file_pkl, is_file_pklzip, is_file_pklbz2, is_file_pklgz,
                    is_file_jbl, is_file_jblz, is_file_jblgz,
                    ]):
            trace("delete file, file type none")

        for pathfile in self._to_file_list(
                prefix,
                is_file_hdf,
                is_file_csv, is_file_csvzip, is_file_csvbz2, is_file_csvgz,
                is_file_pkl, is_file_pklzip, is_file_pklbz2, is_file_pklgz,
                is_file_jbl, is_file_jblz, is_file_jblgz
        ):
            is_log_file_missing = False  # True # note: 文件不存在时报告异常，这样不在持续打印成功删除后的日志
            try:
                pathlib.Path(pathfile).unlink(missing_ok=is_log_file_missing)
                warn(f"....delete : {pathfile}")
            except FileNotFoundError as err:
                is_log_file_missing and warn(f"delete file, {errinfo(err)}, {pathfile=}")
            except Exception as err:
                exception(err, f"delete file, {pathfile=}")
        #
        return

    # ================================================================

    def write_file(self, df: pd.DataFrame, prefix: str,
                   is_file_hdf=False,  # todo: hdf文件总是报错
                   is_file_csv=False, is_file_csvzip=False, is_file_csvbz2=False, is_file_csvgz=False,
                   is_file_pkl=False, is_file_pklzip=False, is_file_pklbz2=False, is_file_pklgz=False,
                   is_file_jbl=False, is_file_jblz=False, is_file_jblgz=False,
                   is_log=True, is_t=False, is_check=True, is_format=True,
                   ) -> bool:
        if not any([is_file_hdf,
                    is_file_csv, is_file_csvzip, is_file_csvbz2, is_file_csvgz,
                    is_file_pkl, is_file_pklzip, is_file_pklbz2, is_file_pklgz,
                    is_file_jbl, is_file_jblz, is_file_jblgz,
                    ]):
            fatal_exit(f"write file, file type none")

        # 检查数据格式
        if not self._check_write(df, prefix, is_check, is_log, is_error_none=True, is_warn_none=True):
            return False

        # 后面不在check了，提高性能
        is_check = False

        # note: 按照合理的顺序排列，减少检索时间
        is_file_jblz and self.write_file_jbl(df, prefix, ".jbl.z", is_log, is_check)
        is_file_jbl and self.write_file_jbl(df, prefix, ".jbl", is_log, is_check)
        is_file_jblgz and self.write_file_jbl(df, prefix, ".jbl.gz", is_log, is_check)
        is_file_pklzip and self.write_file_pkl(df, prefix, ".pkl.zip", is_log, is_check)
        is_file_pkl and self.write_file_pkl(df, prefix, ".pkl", is_log, is_check)
        is_file_pklgz and self.write_file_pkl(df, prefix, ".pkl.gz", is_log, is_check)
        is_file_pklbz2 and self.write_file_pkl(df, prefix, ".pkl.bz2", is_log, is_check)
        is_file_csvzip and self.write_file_csv(df, prefix, ".csv.zip", is_log, is_t, is_format, is_check)
        is_file_csv and self.write_file_csv(df, prefix, ".csv", is_log, is_t, is_format, is_check)  # note: 1g文件太慢
        is_file_csvgz and self.write_file_csv(df, prefix, ".csv.gz", is_log, is_t, is_format, is_check)
        is_file_csvbz2 and self.write_file_csv(df, prefix, ".csv.bz2", is_log, is_t, is_format, is_check)
        # is_file_hdf and self._write_file_hdf(df, prefix, ".hdf", is_log)

        self._rename_file_of_multi_suffix_to_suffix_timestamp(prefix, is_log)

        #
        return True  # df

    # def _write_file_hdf(self, df, prefix, suffix, is_log) -> bool:
    #     # todo: 总是报错：ImportError: Missing optional dependency 'tables'.  Use pip or conda to install tables.
    #     # format='fixed'
    #     pathfile = prefix + suffix
    #     self._is_log_file(is_log) and log(f"....write : {pathfile}")
    #     with TimeLog(f"write {pathfile}") if self._is_log_file(is_log) else Nope():
    #         df.to_hdf(pathfile, 'df')
    #     return True

    def write_file_jbl(self, obj, prefix, suffix,
                       is_log, is_check=True) -> bool:
        pathfile = prefix + suffix
        __write = lambda: FileJbl.write(obj, pathfile)
        return self._write_file_impl(
            write_func=__write, df_or_obj=obj, pathfile=pathfile, hint=None,
            is_log=is_log, is_check=is_check
        )

    def write_file_jbl_direct(self, obj, pathfile,
                              is_log, is_check=True) -> bool:
        __write = lambda: FileJbl.write(obj, pathfile)
        return self._write_file_impl(
            write_func=__write, df_or_obj=obj, pathfile=pathfile, hint=None,
            is_log=is_log, is_check=is_check
        )

    def write_file_jbl_return_file(self, obj, path_prefix, file_prefix, suffix,
                                   is_log, is_check=True) -> str:
        file = file_prefix + suffix
        pathfile = path_prefix + "/" + file
        __write = lambda: FileJbl.write(obj, pathfile)
        result = self._write_file_impl(
            write_func=__write, df_or_obj=obj, pathfile=pathfile, hint=None,
            is_log=is_log, is_check=is_check
        )
        return file

    def write_file_pkl(self, df, prefix, suffix,
                       is_log, is_check=True) -> bool:
        pathfile = prefix + suffix
        __write = lambda: FilePkl.write(df, pathfile)
        return self._write_file_impl(
            write_func=__write, df_or_obj=df, pathfile=pathfile, hint=None,
            is_log=is_log, is_check=is_check
        )

    def write_file_pkl_direct(self, df, pathfile,
                              is_log, is_check=True) -> bool:
        __write = lambda: FilePkl.write(df, pathfile)
        return self._write_file_impl(
            write_func=__write, df_or_obj=df, pathfile=pathfile, hint=None,
            is_log=is_log, is_check=is_check
        )

    def write_file_pkl_return_file(self, df, path_prefix, file_prefix, suffix,
                                   is_log, is_check=True) -> str:
        file = file_prefix + suffix
        pathfile = path_prefix + "/" + file
        __write = lambda: FilePkl.write(df, pathfile)
        result = self._write_file_impl(
            write_func=__write, df_or_obj=df, pathfile=pathfile, hint=None,
            is_log=is_log, is_check=is_check
        )
        return file

    def write_file_csv(self, df: pd.DataFrame, prefix, suffix,
                       is_log=True, is_t=False, is_format=True, is_check=True, encoding=None, mode='w') -> bool:
        pathfile = prefix + suffix
        __write = lambda: \
            FileCsv.write(df, pathfile, is_t, is_format, self.csv_float_format, encoding or self.csv_encoding,
                          mode=mode)
        return self._write_file_impl(
            write_func=__write, df_or_obj=df, pathfile=pathfile, hint=None,
            is_log=is_log, is_check=is_check
        )

    def write_file_csv_direct(self, df: pd.DataFrame, pathfile: str,
                              hint=None,
                              is_log=True, is_t=False, is_format=True, is_check=True, encoding=None, ) -> bool:
        __write = lambda: \
            FileCsv.write(df, pathfile, is_t, is_format, self.csv_float_format, encoding or self.csv_encoding)
        return self._write_file_impl(
            write_func=__write, df_or_obj=df, pathfile=pathfile, hint=hint,
            is_log=is_log, is_check=is_check
        )

    def write_file_csv_return_file(self, df: pd.DataFrame, path_prefix, file_prefix, suffix,
                                   is_log=True, is_t=False, is_format=True, is_check=True, encoding=None, ) -> str:
        file = file_prefix + suffix
        pathfile = path_prefix + "/" + file
        __write = lambda: \
            FileCsv.write(df, pathfile, is_t, is_format, self.csv_float_format, encoding or self.csv_encoding)
        result = self._write_file_impl(
            write_func=__write, df_or_obj=df, pathfile=pathfile, hint=None,
            is_log=is_log, is_check=is_check
        )
        return file

    def _write_file_impl(self, write_func: Callable, df_or_obj: Any, pathfile, hint,
                         is_log, is_check, ) -> bool:
        # 检查数据格式
        if not self._check_write(df_or_obj, pathfile, is_check, is_log, is_error_none=False, is_warn_none=True):
            return False

        #
        self._is_log_file(is_log) and log(f"....write : {pathfile}", f", {hint}" if hint is not None else "")
        # create_path(pathfile, is_log)
        with TimeLog(f"write {pathfile}") if self._is_log_file(is_log) else Nope():
            write_func()

        #
        return True

    # ================================================================

    def read_file(self, prefix: str, dtype=None, usecols=None, nrows=None,
                  is_file_hdf=False,  # todo: hdf文件总是报错
                  is_file_csv=True, is_file_csvzip=True, is_file_csvbz2=True, is_file_csvgz=True,
                  is_file_pkl=True, is_file_pklzip=True, is_file_pklbz2=True, is_file_pklgz=True,
                  is_file_jbl=True, is_file_jblz=True, is_file_jblgz=True,
                  is_log=True,
                  is_check=True, is_error_filenotfound=True, is_warn_filenotfound=True,
                  ) -> Optional[pd.DataFrame]:
        """
        """
        if not any([is_file_hdf,
                    is_file_csv, is_file_csvzip, is_file_csvbz2, is_file_csvgz,
                    is_file_pkl, is_file_pklzip, is_file_pklbz2, is_file_pklgz,
                    is_file_jbl, is_file_jblz, is_file_jblgz,
                    ]):
            fatal_exit("read file, file type none")

        if self._is_file_prefix_multi_suffix(prefix):
            fatal_exit(f"read file, exist old and new, check, {prefix=}")

        df = None

        __read = lambda __is: __is and df is None
        __jbl = lambda __suffix, __is: \
            self.read_file_jbl(prefix, __suffix, is_log) if __read(__is) else df
        __pkl = lambda __suffix, __is: \
            self.read_file_pkl(prefix, __suffix, is_log) if __read(__is) else df
        __csv = lambda __suffix, __is: \
            self.read_file_csv(prefix, __suffix, dtype, usecols, nrows, False, is_log) if __read(__is) else df

        # note: 按照如下优先级读取（jbl.z比jbl常用，pkl.zip比pkl常用，csv比csv.zip常用）
        df = __jbl(".jbl.z", is_file_jblz)
        df = __jbl(".jbl", is_file_jbl)
        df = __jbl(".jbl.gz", is_file_jblgz)
        df = __pkl(".pkl.zip", is_file_pklzip)
        df = __pkl(".pkl", is_file_pkl)
        df = __pkl(".pkl.gz", is_file_pklgz)
        df = __pkl(".pkl.bz2", is_file_pklbz2)
        df = __csv(".csv", is_file_csv)
        df = __csv(".csv.zip", is_file_csvzip)
        df = __csv(".csv.gz", is_file_csvgz)
        df = __csv(".csv.bz2", is_file_csvbz2)
        # df = self._read_file_hdf(prefix, ".hdf", is_log) if __read(is_file_hdf) else df

        # 检查数据格式
        if not self._check_read(df, prefix, is_check, is_log, is_error_filenotfound, is_warn_filenotfound):
            df = None

        # note: 不能退出，在detect signal时indicator可能不存在，因为akshare没有数据，正常的
        # # note：无法加载文件，是程序逻辑的问题，可能是sh执行顺序（例如要先signal在stats），报错退出
        # fatal_and_exit(f"no file, {prefix=}")
        return df

    def read_file_direct(self, pathfile: str, dtype=None, usecols=None, nrows=None,
                         is_log=True,
                         is_check=True, is_error_filenotfound=True, is_warn_filenotfound=True,
                         ) -> Optional[pd.DataFrame]:

        prefix = ""
        prefix, is_file_hdf = self._try_prefix_suffix(pathfile, prefix, ".hdf")
        prefix, is_file_jbl = self._try_prefix_suffix(pathfile, prefix, ".jbl")
        prefix, is_file_jblz = self._try_prefix_suffix(pathfile, prefix, ".jbl.z")
        prefix, is_file_jblgz = self._try_prefix_suffix(pathfile, prefix, ".jbl.gz")
        prefix, is_file_pkl = self._try_prefix_suffix(pathfile, prefix, ".pkl")
        prefix, is_file_pklzip = self._try_prefix_suffix(pathfile, prefix, ".pkl.zip")
        prefix, is_file_pklgz = self._try_prefix_suffix(pathfile, prefix, ".pkl.gz")
        prefix, is_file_pklbz2 = self._try_prefix_suffix(pathfile, prefix, ".pkl.bz2")
        prefix, is_file_csv = self._try_prefix_suffix(pathfile, prefix, ".csv")
        prefix, is_file_csvzip = self._try_prefix_suffix(pathfile, prefix, ".csv.zip")
        prefix, is_file_csvgz = self._try_prefix_suffix(pathfile, prefix, ".csv.gz")
        prefix, is_file_csvbz2 = self._try_prefix_suffix(pathfile, prefix, ".csv.bz2")

        return self.read_file(
            prefix, dtype=dtype, usecols=usecols, nrows=nrows,
            is_file_hdf=is_file_hdf,
            is_file_csv=is_file_csv,
            is_file_csvzip=is_file_csvzip,
            is_file_csvbz2=is_file_csvbz2,
            is_file_csvgz=is_file_csvgz,
            is_file_pkl=is_file_pkl,
            is_file_pklzip=is_file_pklzip,
            is_file_pklbz2=is_file_pklbz2,
            is_file_pklgz=is_file_pklgz,
            is_file_jbl=is_file_jbl,
            is_file_jblz=is_file_jblz,
            is_file_jblgz=is_file_jblgz,
            is_log=is_log,
            is_check=is_check,
            is_error_filenotfound=is_error_filenotfound,
            is_warn_filenotfound=is_warn_filenotfound,
        )

    def read_file_jbl(self, prefix, suffix,
                      is_log=True, is_error_filenotfound=False, is_warn_filenotfound=False
                      ) -> Optional[Any]:
        pathfile = prefix + suffix
        __read = lambda: FileJbl.read(pathfile)
        return self.__read_file_impl(
            read_func=__read, filetype="jbl", pathfile=pathfile, hint=None,
            is_log=is_log, is_error_filenotfound=is_error_filenotfound, is_warn_filenotfound=is_warn_filenotfound,
        )

    def read_file_jbl_direct(self, pathfile,
                             is_log=True, is_error_filenotfound=False, is_warn_filenotfound=False
                             ) -> Optional[Any]:
        __read = lambda: FileJbl.read(pathfile)
        return self.__read_file_impl(
            read_func=__read, filetype="jbl", pathfile=pathfile, hint=None,
            is_log=is_log, is_error_filenotfound=is_error_filenotfound, is_warn_filenotfound=is_warn_filenotfound,
        )

    def read_file_pkl(self, prefix, suffix,
                      is_log=True, is_error_filenotfound=False, is_warn_filenotfound=False
                      ) -> Optional[pd.DataFrame]:
        pathfile = prefix + suffix
        __read = lambda: FilePkl.read(pathfile)  # note: 此时 dtype/usecols 无效
        return self.__read_file_impl(
            read_func=__read, filetype="pkl", pathfile=pathfile, hint=None,
            is_log=is_log, is_error_filenotfound=is_error_filenotfound, is_warn_filenotfound=is_warn_filenotfound,
        )

    def read_file_csv(self, prefix, suffix, dtype, usecols, nrows, is_t=False,
                      is_log=True, is_error_filenotfound=False, is_warn_filenotfound=False, encoding=None,
                      ) -> Optional[pd.DataFrame]:
        pathfile = prefix + suffix
        __read = lambda: \
            FileCsv.read(pathfile, None, dtype, usecols, nrows, is_t, encoding or self.csv_encoding)
        return self.__read_file_impl(
            read_func=__read, filetype="csv", pathfile=pathfile, hint=f"{nrows=}",
            is_log=is_log, is_error_filenotfound=is_error_filenotfound, is_warn_filenotfound=is_warn_filenotfound,
        )

    def read_file_csv_direct(self, pathfile, dtype=None, usecols=None, nrows=None, is_t=False,
                             is_log=True, is_error_filenotfound=False, is_warn_filenotfound=False, encoding=None,
                             ) -> Optional[pd.DataFrame]:
        __read = lambda: \
            FileCsv.read(pathfile, None, dtype, usecols, nrows, is_t, encoding or self.csv_encoding)
        return self.__read_file_impl(
            read_func=__read, filetype="csv", pathfile=pathfile, hint=None,
            is_log=is_log, is_error_filenotfound=is_error_filenotfound, is_warn_filenotfound=is_warn_filenotfound,
        )

    def read_file_tsv_direct(self, pathfile, is_t=False,
                             is_log=True, is_error_filenotfound=False, is_warn_filenotfound=False, encoding=None,
                             ) -> Optional[pd.DataFrame]:
        __read = lambda: \
            FileCsv.read(pathfile, "\t", None, None, None, is_t, encoding or self.csv_encoding)
        return self.__read_file_impl(
            read_func=__read, filetype="tsv", pathfile=pathfile, hint=None,
            is_log=is_log, is_error_filenotfound=is_error_filenotfound, is_warn_filenotfound=is_warn_filenotfound,
        )

    def __read_file_impl(self, read_func: Callable, filetype: str, pathfile: str, hint=None,
                         is_log=True, is_error_filenotfound=False, is_warn_filenotfound=False,
                         ) -> Optional[Any]:
        try:
            self._is_log_file(is_log) and log(f"....readd : {pathfile}", f", {hint}" if hint is not None else "")
            with TimeLog(f"readd {pathfile}") if self._is_log_file(is_log) else Nope():
                return read_func()
        except FileNotFoundError as err:
            # 可能没有文件
            self._is_error_file_not_found(is_error_filenotfound) and error(
                f"read {filetype}, {errinfo(err)}, {pathfile=}")
            self._is_warn_file_not_found(is_warn_filenotfound) and warn(
                f"read {filetype}, {errinfo(err)}, {pathfile=}")
        # except pd_errors.EmptyDataError as err:
        #     # note：屏蔽掉空文件报错：pandas.errors.EmptyDataError: No columns to parse from file
        #     exception(err, f"{pathfile=}")
        except ValueError as err:
            # todo: impl: 多进程时pandas可能对存在的文件报错EmptyData原因未知。如果exit会导致joblib停止
            # # 无法解析，可能格式转换有问题，退出执行进行调试
            # exception_exit(err, f"{pathfile=}")
            exception(err, f"{pathfile=}")
        except Exception as err:
            exception(err, f"{pathfile=}")
        return None


# 多任务
class MultiTask(Base):
    """ 多任务
        note: 测试看，4核mac机器最多用2核，以mp0为基准，mp2是mp0的一半多一点，mp4/mp6都与mp2差不多（还稍多一点）
    """

    @staticmethod
    def desc(msg, task_index, task_count):
        return f"{msg}_{task_index}/{task_count}_{os.getpid()}"

    def join_1(self,
               hint: str, task_count: int,
               process_func: Callable[[list], None], arg_list: list):
        name = self.methodname(self.join_1, hint, task_count)
        # noinspection PyUnusedLocal
        timelog = TimeLog(name)

        log(f"{name}, create pool")
        pool = multiprocessing.Pool(processes=task_count)
        for index in range(task_count):
            log(f"{name}, apply_async, {index}/{task_count}")
            result = pool.apply_async(process_func, arg_list)
        pool.close()
        log(f"{name}, join start")
        pool.join()
        log(f"{name}, join stop")

        #
        return

    def distribute_join(self,
                        task_hint, task_count: int,
                        remote_func: Callable[[dict, dict, list[dict]], Any],
                        local_fixed_arg_dict_func: Callable[[], dict],
                        local_distributable_arg_dictlist_func: Callable[[], list[dict]],
                        is_task_thread=False,
                        is_dispatch_zigzag=False,
                        is_backend_ray=False,
                        is_log=True,
                        ) -> list[Any]:
        """ 多进程分发，每个远端进程remote有3个参数：
            1：进程参数（dict）：task_index
            2：自定义fixed固定参数（dict）
            3：从自定义distributable可分配参数列表中选择的部分参数（list[dict]）
        """
        name = self.methodname(self.distribute_join, task_hint, task_count)

        # note: 需要先单独启动 ray cluster
        def __ray():
            log(f"{name}, use joblib backend ray, {the_elem_part}")
            #
            register_ray()
            #
            # note: 不能init多次，否则报错：
            #       RuntimeError: Maybe you called ray.init twice by accident?
            #       This error can be suppressed by passing in 'ignore_reinit_error=True'
            #       or by calling 'ray.shutdown()' prior to 'ray.init()'.
            ray.init(address="auto", ignore_reinit_error=True)
            #
            return

        # note: multiprocessing 不稳定
        is_joblib = True

        if is_joblib:
            #
            is_backend_ray and __ray()
            #
            with joblib.parallel_backend('ray') if is_backend_ray else CodeBlock():
                return self.distribute_join_by_joblib(
                    task_hint, task_count,
                    remote_func,
                    local_fixed_arg_dict_func,
                    local_distributable_arg_dictlist_func,
                    is_task_thread,
                    is_dispatch_zigzag,
                    is_log=is_log,
                )
        else:
            return self.distribute_join_by_multiprocessing(
                task_hint, task_count,
                remote_func,
                local_fixed_arg_dict_func,
                local_distributable_arg_dictlist_func,
                is_log=is_log,
            )

    def distribute_join_by_multiprocessing(self,
                                           task_hint, task_count: int,
                                           remote_func: Callable[[dict, dict, list[dict]], Any],
                                           local_fixed_arg_dict_func: Callable[[], dict],
                                           local_distributable_arg_dictlist_func: Callable[[], list[dict]],
                                           is_log=True,
                                           ) -> list[Any]:

        name = self.methodname(self.distribute_join_by_multiprocessing, task_hint, task_count)

        mpm = multiprocessing.Manager()

        # note: 保证local func只被调用一次
        log(f"{name}, call local_fixed_arg_dict_func")
        fixed_arg_dict = local_fixed_arg_dict_func()
        log(f"{name}, {len(fixed_arg_dict)=}")
        is_log and log(f"{name}, {fixed_arg_dict=}")
        arg_mpdict = mpm.dict(fixed_arg_dict)
        log(f"{name}, {len(arg_mpdict)=}")

        # note: 保证local func只被调用一次
        log(f"{name}, call local_distributable_arg_dictlist_func")
        distributable_arg_dictlist = local_distributable_arg_dictlist_func()
        log(f"{name}, {len(distributable_arg_dictlist)=}")
        is_log and log(f"{name}, {distributable_arg_dictlist=}")
        arg_mpdict_mplist = mpm.list([mpm.dict(x) for x in distributable_arg_dictlist])
        log(f"{name}, {len(arg_mpdict_mplist)=}")

        #
        log(f"{name}, multi task, want, {task_count=}")
        task_count = min(len(arg_mpdict_mplist), task_count)
        log(f"{name}, multi task, real, {task_count=}")

        #
        log(f"{name}, create dispatch arg sequence")
        dispatch_arg_dict_sequence, dispatch_arg_dictlist_sequence = self._dispatch_task_sequence(
            name, arg_mpdict, arg_mpdict_mplist, task_count,
            task_dispatch_step=1, is_dispatch_zigzag=False, is_log=is_log)
        dispatch_task_count = len(dispatch_arg_dict_sequence)
        log(f"{name}, {dispatch_task_count=}")

        #
        valid_or_exit(sum(len(x) for x in dispatch_arg_dictlist_sequence) == len(arg_mpdict_mplist),
                      f"{name}, arg mpdict size diff")

        #
        with TimeLog(f"{name}"):
            # note: multiprocessing 无法 ctrl+c 终止所有进程
            #       解决参见 https://stackoverflow.com/questions/11312525/catch-ctrlc-sigint-and-exit-multiprocesses-gracefully-in-python/35134329#35134329
            log(f"{name}, create task pool")
            original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
            with multiprocessing.Pool(processes=task_count) as pool:
                signal.signal(signal.SIGINT, original_sigint_handler)
                #
                log(f"{name}, exec, wait result")
                try:
                    result_list = [result.get() for result in [
                        pool.apply_async(
                            remote_func, (
                                {"task_index": i, "task_count": dispatch_task_count, },
                                dispatch_arg_dict_sequence[i],
                                dispatch_arg_dictlist_sequence[i],
                            )
                        )
                        for i in range(dispatch_task_count)
                    ]]
                    log(f"{name}, {len(result_list)=}")  # note: result可能很长，不在打印内容
                except KeyboardInterrupt as err:
                    info(f"{name}, {errinfo(err)}, user termination")
                    pool.terminate()
                else:
                    log(f"{name}, normal termination")
                    pool.close()
                #
                # note: 程序结束报错：UserWarning: resource_tracker: There appear to be 26 leaked semaphore objects to clean up at shutdown
                #       解决方法：忽略： export PYTHONWARNINGS='ignore:semaphore_tracker:UserWarning'
                #       或者：增加如下代码
                pool.join()

        #
        return result_list

    def distribute_join_by_joblib(self,
                                  task_hint, task_count: int,
                                  remote_func: Callable[[dict, dict, list[dict]], Any],
                                  local_fixed_arg_dict_func: Callable[[], dict],
                                  local_distributable_arg_dictlist_func: Callable[[], list[dict]],
                                  is_task_thread=False,
                                  is_dispatch_zigzag=False,
                                  is_log=True,
                                  ) -> list[Any]:
        jb_verbose = 99
        jb_batch_size = "auto"
        jb_prefer = "threads" if is_task_thread else "processes"
        name = self.methodname(self.distribute_join_by_joblib, task_hint, task_count, jb_prefer)

        # note: 保证local func只被调用一次
        log(f"{name}, call local_fixed_arg_dict_func")
        fixed_arg_dict = local_fixed_arg_dict_func()
        log(f"{name}, {len(fixed_arg_dict)=}")
        is_log and log(f"{name}, {fixed_arg_dict=}")

        # note: 保证local func只被调用一次
        log(f"{name}, call local_distributable_arg_dictlist_func")
        distributable_arg_dictlist = local_distributable_arg_dictlist_func()
        log(f"{name}, {len(distributable_arg_dictlist)=}")
        is_log and log(f"{name}, {distributable_arg_dictlist=}")

        log(f"{name}, create dispatch arg sequence")
        dispatch_arg_dict_sequence, dispatch_arg_dictlist_sequence = self._dispatch_task_sequence(
            name, fixed_arg_dict, distributable_arg_dictlist, task_count,
            is_dispatch_zigzag=is_dispatch_zigzag, is_log=is_log)
        dispatch_task_count = len(dispatch_arg_dict_sequence)
        log(f"{name}, {dispatch_task_count=}")

        #
        with TimeLog(f"{name}"):
            result_list = joblib.Parallel(
                n_jobs=task_count, prefer=jb_prefer, verbose=jb_verbose, batch_size=jb_batch_size,
            )(
                joblib.delayed(remote_func)(
                    {"task_index": i, "task_count": dispatch_task_count, },
                    dispatch_arg_dict_sequence[i],
                    dispatch_arg_dictlist_sequence[i],
                )
                for i in range(dispatch_task_count)
            )
            log(f"{name}, {len(result_list)=}, {type(result_list)=}")  # note: result可能很长，不在打印内容

        #
        return result_list

    # noinspection PyMethodMayBeStatic
    def _dispatch_task_sequence(self, msg, fixed_arg_dict, distributable_arg_dictlist,
                                task_count, task_dispatch_step=None,
                                is_dispatch_zigzag=False,
                                is_log=False,
                                ) -> [list, list]:

        dispatch_count = len(distributable_arg_dictlist)

        # note: 单个进程执行数据太少的化，调度成本变高

        dispatch_index_list, adjacent_count_list = \
            self._dispatch_using_zigzag(msg, task_count, dispatch_count) if is_dispatch_zigzag \
                else self._dispatch_using_same(msg, task_count, dispatch_count, task_dispatch_step)
        valid_or_exit(len(dispatch_index_list) == len(adjacent_count_list),
                      f"{msg}, index and count len diff, {dispatch_index_list=}, {adjacent_count_list=}")
        # valid_or_exit(len(dispatch_index_list) == task_count * task_count + 1,
        #               f"{hint}, index len != power(task_count)+1, {len(dispatch_index_list)=}, {task_count=}")

        task_arg_dict_sequence = []
        task_arg_dictlist_sequence = []
        for i, dispatch_index in enumerate(dispatch_index_list):
            dispatch_count = adjacent_count_list[i]
            sequence = distributable_arg_dictlist[dispatch_index:(dispatch_index + dispatch_count)]
            if len(sequence) > 0:
                task_arg_dict_sequence.append(fixed_arg_dict.copy())
                task_arg_dictlist_sequence.append(sequence)

        log(f"{msg}, {len(task_arg_dict_sequence)=}, {len(task_arg_dictlist_sequence)=}, ")
        is_log and log(f"{msg}, {task_arg_dict_sequence=}")
        is_log and log(f"{msg}, {task_arg_dictlist_sequence=}")

        return task_arg_dict_sequence, task_arg_dictlist_sequence

    def _dispatch_using_same(self, hint, task_count, dispatch_count, task_dispatch_step=None, ):
        name = self.methodname(self._dispatch_using_same, hint, task_count, dispatch_count, task_dispatch_step)

        dispatch_step = task_dispatch_step \
            if task_dispatch_step is not None \
            else max(1, dispatch_count // task_count // task_count)  # 1
        dispatch_index_list = []
        dispatch_index_list.extend([x for x in range(0, dispatch_count + 1, dispatch_step)])
        dispatch_index_list[-1] = dispatch_count
        adjacent_count_list = self._to_adjacent_count_list(dispatch_index_list, dispatch_count)

        log(f"{name}, {dispatch_index_list=}, {adjacent_count_list=}")
        return dispatch_index_list, adjacent_count_list

    def _dispatch_using_zigzag(self, hint, task_count, dispatch_count):
        """ note：每个task可能在开始时读取文件并在结尾时写入文件，此时如果同时进行，会导致磁盘阻塞。
                通过划分大小不同的task执行数据，让中间的cpu时长不一致，并导致task的开始和结束时间交错，从而不会同时执行磁盘操作
            交错算法：
                每个 dispatch 由多个 task 组成，
                每个 task 由数目相同的多个 segment 组成，
                每个 segment 的数据长度不一致，但是单位数据长度的倍数，
                假设 每个 task 总共可以划分为 n 个 单位数据，而这些 segment 的 单位数据个数 构成等差数列，而 x 为单位数据的大小，则
                    1/x + 2/x + ... + n/x = n
                    1 + 2 + ... + n = nx
                    x = (1 + 2 + ... + n ) / n
        """
        name = self.methodname(self._dispatch_using_zigzag, hint, task_count, dispatch_count)

        task_step = max(1, dispatch_count // task_count)

        segment_total = sum(range(1, task_count + 1))
        # segment_divide = segment_total / task_count
        segment_count_list = []
        for j in range(1, task_count + 1):
            count = (task_step / segment_total) * j
            segment_count_list.append(count)
        # log(f"{name}, {task_step=}, {segment_total=}, {segment_divide=}, {segment_count_list=}")

        dispatch_index_list = [0]
        for i in range(0, task_count):
            start = i * task_step
            # 奇数偶数 task 对应序号的 segment 的单元数据个数累加起来，应该大致相同，从而保证总执行时间最小
            dispatch_step_list = sorted(segment_count_list, reverse=(i % 2 != 0))
            dispatch_index_list.extend([int(start + x) for x in np.cumsum(dispatch_step_list)])
        dispatch_index_list[-1] = dispatch_count
        adjacent_count_list = self._to_adjacent_count_list(dispatch_index_list, dispatch_count)
        log(f"{name}, {dispatch_index_list=}, {adjacent_count_list=}")

        return dispatch_index_list, adjacent_count_list

    @staticmethod
    def _to_adjacent_count_list(dispatch_index_list, dispatch_count):
        adjacent_count_list = \
            [
                dispatch_index_list[x] - dispatch_index_list[x - 1]
                for x in range(1, len(dispatch_index_list))
            ] + [
                dispatch_count - dispatch_index_list[-1]  # 最后一个index和总长度相同，增加它为了保持和index_list长度一致
            ]
        return adjacent_count_list


#
class Memory(joblib.Memory):
    """  缓存 """

    def __init__(self, location=None, backend='local', cachedir=None,
                 mmap_mode=None, compress=False, verbose=1, bytes_limit=None,
                 backend_options=None,
                 enable_cache_func=None, is_log=True,
                 ):
        super().__init__(location, backend, cachedir,
                         mmap_mode, compress, verbose, bytes_limit,
                         backend_options)
        self._enable_cache_func = enable_cache_func
        self._is_log = is_log
        return

    @property
    def enable_cache(self):
        return self._enable_cache_func() if self._enable_cache_func is not None else False

    # ================================================================

    def cache(self, func=None, ignore=None, verbose=None, mmap_mode=False):
        if self.enable_cache:
            return super().cache(func, ignore, verbose, mmap_mode)

        # note：有些cache很占据磁盘，这样性能可能反而降低，例如trigger_trade中valid|enter|exit方法，simu时达到50万个文件
        # todo: impl: 哪种性能更高？这里创建了内部函数

        if func is None:
            return functools.partial(self.cache, ignore=ignore, verbose=verbose, mmap_mode=mmap_mode)

        self._is_log and log(f"{methodname(self, self.cache, func)}, ignore")

        def __inner(*args, **kwargs):
            __inner.__name__ = func.__name__
            return func(*args, **kwargs)

        return __inner

    # ================================================================

    def clear(self, warn=True):
        # note: 可能报错：FileNotFoundError: [WinError 3] xxx: xxx
        # note: 可能报错：OSError: [WinError 145] 目录不是空的。: xxx
        try:
            return super().clear(warn)
        except Exception as err:
            exception(err, f"{methodname(self, self.clear)}")

    # ================================================================

    def reduce_size(self):
        return super().reduce_size()

    def eval(self, func, *args, **kwargs):
        return super().eval(func, *args, **kwargs)

    # ================================================================


# 股票技术指标
class Stock(Base):
    # 计算ema（df收盘价按照日期为顺序，日期从以前到现在，即第一行为以前）
    # df为收盘价列表，n为几日，比如9/12/26
    @staticmethod
    def calc_ema(df, n):
        col_name = f'ema{n}'
        for i in range(len(df)):
            if i == 0:
                df.loc[i, col_name] = df.loc[i, 'close']
                # df.loc[i, 'ema'] = ((n - 1) * 22.9810077 + 2 * df.loc[i, 'close']) / (n + 1)
            if i > 0:
                df.loc[i, col_name] = ((n - 1) * df.loc[i - 1, col_name] + 2 * df.loc[i, 'close']) / (n + 1)
        ema = list(df[col_name])
        return ema

    # 计算ema（df收盘价按照日期为倒序，日期从现在到以前，即第一行为现在）
    # df为收盘价列表，n为几日，比如9/12/26
    @staticmethod
    def calc_ema_reverse_order(df, n):
        col_name = f'ema{n}'
        i = len(df) - 1
        while i >= 0:
            if i == len(df) - 1:
                df.loc[i, col_name] = df.loc[i, 'close']
            else:
                df.loc[i, col_name] = ((n - 1) * df.loc[i + 1, col_name] + 2 * df.loc[i, 'close']) / (n + 1)

            i -= 1

        ema = list(df[col_name])
        return ema

    # 计算bbi指标
    @staticmethod
    def calculate_bbi(df: pd.DataFrame, n1=3, n2=6, n3=12, n4=24) -> pd.DataFrame:
        """
        计算Bull and Bear Index (BBI)，一种技术分析指标，用于识别市场趋势。
        参数:
        df (pd.DataFrame): 包含至少'close'列的DataFrame，代表收盘价。
        N1, N2, N3, N4 (int): 分别代表四个不同周期的简单移动平均线(SMA)的窗口大小。
        返回:
        pd.DataFrame: 包含BBI值的DataFrame。
        """
        # 创建一个df的副本以避免修改原始数据
        data = df.copy()

        # 计算四个不同周期的简单移动平均线
        data['ma_' + str(n1)] = data['close'].rolling(n1).mean().shift(-(n1 - 1))
        data['ma_' + str(n2)] = data['close'].rolling(n2).mean().shift(-(n2 - 1))
        data['ma_' + str(n3)] = data['close'].rolling(n3).mean().shift(-(n3 - 1))
        data['ma_' + str(n4)] = data['close'].rolling(n4).mean().shift(-(n4 - 1))

        # 计算BBI，即这四个SMA的均值
        data['bbi'] = (data['ma_' + str(n1)] + data['ma_' + str(n2)] +
                       data['ma_' + str(n3)] + data['ma_' + str(n4)]) / 4

        return data['bbi']

#############################################
# --- compatibility helper for old callers (databaseutil.py) ---
def get_date_from_now(day_count: int, end_date: int) -> int:
    """
    Backward N days from end_date.
    Args:
        day_count: how many days to go back (int)
        end_date: YYYYMMDD (int)
    Returns:
        YYYYMMDD (int)
    """
    from datetime import datetime, timedelta

    if end_date is None:
        raise ValueError("end_date is None")

    s = str(end_date)
    if len(s) != 8 or not s.isdigit():
        raise ValueError(f"end_date must be YYYYMMDD int, got: {end_date}")

    dt = datetime.strptime(s, "%Y%m%d")
    dt2 = dt - timedelta(days=int(day_count))
    return int(dt2.strftime("%Y%m%d"))
