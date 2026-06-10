"""
logutil.py
qlsignalNew_20240808
Created by huanghx on 2024/8/8
Copyright © 2024 huanghx. All rights reserved.

FIXED: 修复多进程环境下的日志文件权限问题
"""
import logging
import os
from logging.handlers import RotatingFileHandler
try:
    import colorlog
except ImportError:
    colorlog = None

import dfutil

"""
初始化配置（可以通过设置不同的级别，来控制打印不同级别的日志，其中DEBUG级别最低，CRITICAL级别最高）
每个级别对应的数字值为 CRITICAL: 50, ERROR: 40, WARNING: 30, INFO: 20, DEBUG: 10, NOTSET: 0.

debug： 所有详细信息，用于调试。
info：一些关键跳转，证明软件正常运行的日志。
warning：表明发生了一些意外，软件无法处理，但是依然能正常运行。
error：由于一些严重问题，软件不能正常执行一些功能，但是依然能运行。
critical/fatal：非常严重的错误，软件已经不能继续运行了。

Python 中日志的默认等级是 WARNING，DEBUG 和INFO级别的日志将不会得到显示
"""


class Log:
    def __init__(self, name=None, log_level=logging.DEBUG):
        # 获取logger对象
        self.logger = logging.getLogger(name)

        # 避免重复打印日志
        self.logger.handlers = []

        # 指定最低日志级别：（critical > error > warning > info > debug）
        self.logger.setLevel(log_level)

        # 日志格化字符串
        console_fmt = ('%(log_color)s%(asctime)s-%(threadName)s-%(filename)s-[line:%(lineno)d]-%(levelname)s: %('
                       'message)s')
        file_fmt = '%(asctime)s-%(threadName)s-%(filename)s-[line:%(lineno)d]-%(levelname)s: %(message)s'

        # 控制台输出不同级别日志颜色设置
        color_config = {
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'purple',
        }

        if colorlog:
            console_formatter = colorlog.ColoredFormatter(fmt=console_fmt, log_colors=color_config)
        else:
            console_formatter = logging.Formatter(fmt=file_fmt)
        
        file_formatter = logging.Formatter(fmt=file_fmt)

        # 输出到控制台
        console_handler = logging.StreamHandler()

        """
        输出到文件：使用 RotatingFileHandler 替代 TimedRotatingFileHandler
        
        修复说明：
        1. TimedRotatingFileHandler 在多进程环境下不安全，会导致文件锁冲突
        2. RotatingFileHandler 按文件大小滚动，在多进程环境下更稳定
        3. maxBytes=10*1024*1024 表示单个日志文件最大10MB
        4. backupCount=10 表示保留10个备份文件
        
        如果仍需要按日期滚动，建议：
        - 使用 ConcurrentLogHandler (需要安装 concurrent-log-handler)
        - 或者为每个进程创建独立的日志文件
        """
        log_dir = 'logs'
        dfutil.create_directory(log_dir)
        log_path = os.path.join(log_dir, 'myapp.log')
        
        # 使用 RotatingFileHandler 替代 TimedRotatingFileHandler
        # 按文件大小滚动，避免多进程文件锁冲突
        # FIX: Windows下多进程仍然会产生PermissionError [WinError 32]，尝试使用ConcurrentRotatingFileHandler或PID分离
        try:
            from concurrent_log_handler import ConcurrentRotatingFileHandler
            file_handler = ConcurrentRotatingFileHandler(
                log_path, 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=10,
                encoding="UTF-8"
            )
        except ImportError:
            # 如果没有安装concurrent_log_handler，则使用带PID的文件名避免冲突
            # 这种方式会生成多个日志文件，但能彻底解决权限占用问题
            pid = os.getpid()
            # 只有主进程使用myapp.log，子进程使用myapp_pid.log (简单起见全都带PID或者检测是否为主进程)
            # 为了稳健，如果发生冲突，通常意味着多实例或多进程，直接加上PID最安全
            # 但为了保持主日志整洁，可以尝试检测
            import multiprocessing
            if multiprocessing.current_process().name == 'MainProcess':
                # 主进程尝试使用主文件，如果被占用则加PID
                try:
                    # 简单的测试打开，如果失败说明被占
                    with open(log_path, 'a'): pass
                except PermissionError:
                    log_path = os.path.join(log_dir, f'myapp_{pid}.log')
            else:
                log_path = os.path.join(log_dir, f'myapp_{pid}.log')

            file_handler = RotatingFileHandler(
                log_path, 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=10,
                encoding="UTF-8"
            )

        # 设置日志格式
        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(file_formatter)

        # 处理器设置日志级别，不同处理器可各自设置级别，默认使用logger日志级别
        # console_handler.setLevel(logging.WARNING)
        file_handler.setLevel(logging.ERROR)  # 只有error和critical级别才会写入日志文件

        # logger添加处理器
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    # 注意：这里不能加上"args, kwargs"参数，否则每次打印日志时，都会出现一堆红色日志
    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)


if __debug__:
    # debug模式下，默认设置DEBUG级别日志
    log = Log(name='log.txt')
else:
    # release模式下，设置ERROR级别日志
    log = Log(name='log.txt', log_level=logging.ERROR)