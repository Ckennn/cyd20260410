"""
tradedateutil.py
qlsignalNew_20240808
Created by huanghx on 2024/8/12
Copyright © 2024 huanghx. All rights reserved.
"""
import requests
import json
# import requests.packages.urllib3.util.ssl_
import os
import time

# from chinese_calendar import is_workday # 3.12版本的python才有这个库 delete by hhx 2025.01.23
from datetime import datetime, timedelta

import dfutil
import logutil
import qldef

# requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL'  # 防止SSL限制


# 方法2：判断所给日期是否为交易日
def is_trade_date(date_str):
    year = time.strftime('%Y', time.localtime(time.time()))
    save_file_path = qldef.file_cache_path + year + "_trade_date.txt"

    if os.path.isfile(save_file_path):
        # 如果交易日期文件存在时，则读取该文件，并判断日期是否能在文件中存在，如果存在则为交易日，否则非交易日
        with open(save_file_path, 'a+') as f:
            f.seek(0)
            lines = f.readlines()
            if date_str in lines:
                return True
            else:
                return False
    else:
        # 如果交易日期文件不存在，则重新下载交易日期 并 保存文件（每年一次）
        logutil.log.debug(f"无本地{save_file_path}文件，进行下载")
        is_success = False
        for _month_i in range(12):
            is_success = get_trading_date_request(year, _month_i, save_file_path)

        if is_success:
            return is_trade_date(date_str)


# 通过爬虫抓取深交所的交易日历
# _year_i: 年份
# _month_i：月份
# save_file_path：保存日历文件名
def get_trading_date_request(_year_i, _month_i, save_file_path):
    """
    通过爬虫抓取深交所的交易日历
    month_date: 日期，例 2020-01、2022-12
    """
    month_date = "{}-{}".format(_year_i, _month_i + 1)
    target_url = "http://www.szse.cn/api/report/exchange/onepersistenthour/monthList?month={}".format(month_date)
    send_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"}
    time.sleep(2)  # 限制频率
    req = requests.get(target_url, headers=send_headers)
    if req.status_code == 200:
        if (req is not None) & (len(req.text) > 0):
            json_state = json.loads(req.text)
            for dict_value in json_state['data']:
                # 保存结果：工作日非交易日
                date_str = dict_value['jyrq']
                if dict_value['jybz'] == "1":
                    with open(save_file_path, 'a') as file:
                        file.write(date_str)
                        file.write("\n")

            return True
        else:
            return False
    else:
        return False


# 方法2：判断所给日期是否为交易日
def isTradeDay(date_str, fmt: format = '%Y-%m-%d'):
    date_time = datetime.strptime(date_str, fmt).date()
    # if is_workday(date_time): # 3.12版本的python才有这个库 delete by hhx 2025.01.23
    if datetime.isoweekday(date_time) < 6:
        return True

    return False


# 获取指定日期的前/后几个交易日期（可以设置是否包括start_date）
# start_date: 指定开始日期
# trade_days：前/后 几个交易日期数
# is_prev：是否前几个交易日（默认是前，传False：表示后几个交易日期）
# is_include_start_date：是否包含指定开始日期（默认包括，传False，则不包括）
def get_trade_dates(start_date: int, trade_days_count: int, is_prev: bool = True, is_include_start_date: bool = True):
    trade_dates = []

    # 默认为30，因为一般不会出现连续30个非交易日
    days_back = 30

    start_date_time = dfutil.datetime_by_date(start_date)
    datetime_off = timedelta(0)
    if not is_include_start_date:
        # 如果不包括指定开始日期，则需要+/- 1
        datetime_off = timedelta(1)

    if is_prev:
        start_date_time = start_date_time - datetime_off
    else:
        start_date_time = start_date_time + datetime_off

    date_list = dfutil.loop_dates(days_back=days_back, start_date=start_date_time, is_prev=is_prev)
    for date_int in date_list:
        if isTradeDay(str(date_int), "%Y%m%d"):
            trade_dates.append(date_int)
            if len(trade_dates) >= trade_days_count:
                break

    return trade_dates


if __name__ == '__main__':
    # time_str为需要判断的日期，默认为当天
    # date_str = time.strftime('%Y-%m-%d', time.localtime(time.time())) + '\n'
    # res = is_trade_date(date_str)
    # if res:
    #     logutil.log.debug("当天是交易日")

    # date = '2023-04-1'
    # date = datetime.strptime(date, '%Y-%m-%d').date()
    # print(isTradeDay(date))
    # print(isTradeDay(datetime.now()))

    today = 20240812
    get_trade_dates(today, 3)
