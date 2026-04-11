#!/usr/bin/env python3
# coding=utf-8
"""
分批下载行业数据脚本 - fix_industry_data_batch.py

特点：
1. 支持断点续传：自动跳过已下载的行业
2. 分批下载：每批10个行业，避免频率限制
3. 进度保存：记录下载进度，随时可以继续

使用方法：
python fix_industry_data_batch.py --batch-size 10 --start-index 0

作者：Manus AI
日期：2026-01-26
"""

import akshare as ak
import sqlite3
import time
from datetime import datetime
import os
import sys
import argparse

from project_paths import get_db_path as get_project_db_path


def get_db_path():
    """获取数据库路径"""
    return str(get_project_db_path())


def create_tables(conn):
    """创建表结构"""
    cursor = conn.cursor()
    
    # stock_industry 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_industry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            stock_name TEXT,
            second_industry_code TEXT,
            second_industry_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(stock_code)
        )
    """)
    
    # industry_quote 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS industry_quote (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            industry_code TEXT NOT NULL,
            industry_name TEXT,
            trade_date TEXT NOT NULL,
            open_price REAL,
            close_price REAL,
            high_price REAL,
            low_price REAL,
            volume REAL,
            turnover REAL,
            amplitude REAL,
            change_pct REAL,
            change_amount REAL,
            turnover_rate REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(industry_code, trade_date)
        )
    """)
    
    conn.commit()


def get_industry_list():
    """获取行业列表"""
    try:
        df = ak.stock_board_industry_name_em()
        return df
    except Exception as e:
        print(f"❌ 获取行业列表失败: {e}")
        return None


def get_downloaded_industries(conn):
    """获取已下载的行业"""
    cursor = conn.cursor()
    
    # 获取已有成分股的行业
    cursor.execute("""
        SELECT DISTINCT second_industry_code, second_industry_name 
        FROM stock_industry
    """)
    downloaded_cons = {row[0]: row[1] for row in cursor.fetchall()}
    
    # 获取已有行情的行业
    cursor.execute("""
        SELECT DISTINCT industry_code, industry_name 
        FROM industry_quote
    """)
    downloaded_quote = {row[0]: row[1] for row in cursor.fetchall()}
    
    return downloaded_cons, downloaded_quote


def download_industry_constituents(industry_name, max_retries=3):
    """下载行业成分股（带重试）"""
    for attempt in range(max_retries):
        try:
            df = ak.stock_board_industry_cons_em(symbol=industry_name)
            return df
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 3
                print(f"   ⚠️ 获取失败，{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"   ❌ 获取成分股失败: {e}")
                return None


def download_industry_hist(industry_name, start_date="20040101", max_retries=3):
    """下载行业历史行情（带重试）"""
    end_date = datetime.now().strftime("%Y%m%d")
    
    for attempt in range(max_retries):
        try:
            df = ak.stock_board_industry_hist_em(
                symbol=industry_name,
                period="日k",
                start_date=start_date,
                end_date=end_date,
                adjust=""
            )
            return df
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 3
                print(f"   ⚠️ 获取失败，{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"   ❌ 获取行情失败: {e}")
                return None


def import_batch_constituents(conn, industry_list_df, start_index, batch_size, downloaded_cons):
    """分批导入成分股"""
    cursor = conn.cursor()
    end_index = min(start_index + batch_size, len(industry_list_df))
    
    success_count = 0
    fail_count = 0
    total_stocks = 0
    
    print(f"\n{'='*80}")
    print(f"导入成分股：行业 {start_index+1}-{end_index} / {len(industry_list_df)}")
    print(f"{'='*80}")
    
    for idx in range(start_index, end_index):
        row = industry_list_df.iloc[idx]
        industry_name = row['板块名称']
        industry_code = row['板块代码']
        
        # 检查是否已下载
        if industry_code in downloaded_cons:
            print(f"\n[{idx+1}/{len(industry_list_df)}] {industry_name} ({industry_code})")
            print(f"   ⏭️  已下载，跳过")
            continue
        
        print(f"\n[{idx+1}/{len(industry_list_df)}] {industry_name} ({industry_code})")
        
        # 下载成分股
        df_cons = download_industry_constituents(industry_name)
        if df_cons is None or len(df_cons) == 0:
            print(f"   ⚠️ 无成分股数据")
            fail_count += 1
            continue
        
        print(f"   ✅ 获取 {len(df_cons)} 只成分股")
        
        # 插入数据库
        inserted = 0
        for _, stock_row in df_cons.iterrows():
            stock_code = stock_row['代码']
            stock_name = stock_row['名称']
            
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO stock_industry 
                    (stock_code, stock_name, second_industry_code, second_industry_name)
                    VALUES (?, ?, ?, ?)
                """, (stock_code, stock_name, industry_code, industry_name))
                inserted += 1
                total_stocks += 1
            except Exception as e:
                print(f"   ❌ 插入失败 {stock_code}: {e}")
        
        conn.commit()
        print(f"   ✅ 已插入 {inserted} 只股票")
        success_count += 1
        
        # 避免请求过快
        time.sleep(2.0)
    
    print(f"\n✅ 本批次完成：成功 {success_count} 个，失败 {fail_count} 个，共 {total_stocks} 只股票")
    return success_count, fail_count


def import_batch_quotes(conn, industry_list_df, start_index, batch_size, downloaded_quote):
    """分批导入行情"""
    cursor = conn.cursor()
    end_index = min(start_index + batch_size, len(industry_list_df))
    
    success_count = 0
    fail_count = 0
    total_records = 0
    
    print(f"\n{'='*80}")
    print(f"导入行情：行业 {start_index+1}-{end_index} / {len(industry_list_df)}")
    print(f"{'='*80}")
    
    for idx in range(start_index, end_index):
        row = industry_list_df.iloc[idx]
        industry_name = row['板块名称']
        industry_code = row['板块代码']
        
        # 检查是否已下载
        if industry_code in downloaded_quote:
            print(f"\n[{idx+1}/{len(industry_list_df)}] {industry_name} ({industry_code})")
            print(f"   ⏭️  已下载，跳过")
            continue
        
        print(f"\n[{idx+1}/{len(industry_list_df)}] {industry_name} ({industry_code})")
        
        # 下载行情
        df = download_industry_hist(industry_name)
        if df is None or len(df) == 0:
            print(f"   ⚠️ 无行情数据")
            fail_count += 1
            continue
        
        print(f"   ✅ 获取 {len(df)} 条行情记录")
        
        # 重命名列
        df = df.rename(columns={
            '日期': 'trade_date',
            '开盘': 'open_price',
            '收盘': 'close_price',
            '最高': 'high_price',
            '最低': 'low_price',
            '成交量': 'volume',
            '成交额': 'turnover',
            '振幅': 'amplitude',
            '涨跌幅': 'change_pct',
            '涨跌额': 'change_amount',
            '换手率': 'turnover_rate'
        })
        
        df['industry_code'] = industry_code
        df['industry_name'] = industry_name
        
        # 插入数据库
        inserted = 0
        for _, quote_row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO industry_quote 
                    (industry_code, industry_name, trade_date, open_price, close_price,
                     high_price, low_price, volume, turnover, amplitude, change_pct,
                     change_amount, turnover_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    industry_code, industry_name, quote_row['trade_date'],
                    quote_row.get('open_price'), quote_row.get('close_price'),
                    quote_row.get('high_price'), quote_row.get('low_price'),
                    quote_row.get('volume'), quote_row.get('turnover'),
                    quote_row.get('amplitude'), quote_row.get('change_pct'),
                    quote_row.get('change_amount'), quote_row.get('turnover_rate')
                ))
                inserted += 1
                total_records += 1
            except Exception as e:
                print(f"   ❌ 插入失败: {e}")
        
        conn.commit()
        print(f"   ✅ 已插入 {inserted} 条行情记录")
        success_count += 1
        
        # 避免请求过快
        time.sleep(2.0)
    
    print(f"\n✅ 本批次完成：成功 {success_count} 个，失败 {fail_count} 个，共 {total_records} 条记录")
    return success_count, fail_count


def print_progress(conn):
    """打印进度"""
    cursor = conn.cursor()
    
    # stock_industry 统计
    cursor.execute("SELECT COUNT(DISTINCT second_industry_code) FROM stock_industry")
    cons_industries = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM stock_industry")
    total_stocks = cursor.fetchone()[0]
    
    # industry_quote 统计
    cursor.execute("SELECT COUNT(DISTINCT industry_code) FROM industry_quote")
    quote_industries = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM industry_quote")
    total_quotes = cursor.fetchone()[0]
    
    print(f"\n{'='*80}")
    print(f"当前进度")
    print(f"{'='*80}")
    print(f"成分股：{cons_industries}/86 个行业，{total_stocks} 只股票")
    print(f"行情：{quote_industries}/86 个行业，{total_quotes} 条记录")
    print(f"{'='*80}")


def main():
    parser = argparse.ArgumentParser(description='分批下载行业数据')
    parser.add_argument('--batch-size', type=int, default=10, help='每批下载的行业数量')
    parser.add_argument('--start-index', type=int, default=0, help='起始行业索引（从0开始）')
    parser.add_argument('--type', choices=['cons', 'quote', 'both'], default='both',
                       help='下载类型：cons=成分股, quote=行情, both=两者')
    
    args = parser.parse_args()
    
    print("="*80)
    print("分批下载行业数据工具")
    print("="*80)
    print(f"批次大小: {args.batch_size} 个行业")
    print(f"起始索引: {args.start_index}")
    print(f"下载类型: {args.type}")
    print()
    
    # 连接数据库
    db_path = get_db_path()
    print(f"数据库路径: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    conn = sqlite3.connect(db_path)
    
    # 创建表结构
    create_tables(conn)
    print("✅ 表结构检查完成\n")
    
    # 获取行业列表
    print("正在获取行业列表...")
    industry_list_df = get_industry_list()
    if industry_list_df is None:
        print("❌ 无法获取行业列表")
        conn.close()
        return
    
    print(f"✅ 共 {len(industry_list_df)} 个行业\n")
    
    # 获取已下载的行业
    downloaded_cons, downloaded_quote = get_downloaded_industries(conn)
    print(f"已下载成分股: {len(downloaded_cons)} 个行业")
    print(f"已下载行情: {len(downloaded_quote)} 个行业\n")
    
    # 下载成分股
    if args.type in ['cons', 'both']:
        success, fail = import_batch_constituents(
            conn, industry_list_df, args.start_index, args.batch_size, downloaded_cons
        )
    
    # 下载行情
    if args.type in ['quote', 'both']:
        success, fail = import_batch_quotes(
            conn, industry_list_df, args.start_index, args.batch_size, downloaded_quote
        )
    
    # 打印进度
    print_progress(conn)
    
    # 计算下一批次
    next_index = args.start_index + args.batch_size
    if next_index < len(industry_list_df):
        print(f"\n💡 继续下载下一批次（30分钟后）：")
        print(f"   python fix_industry_data_batch.py --start-index {next_index} --batch-size {args.batch_size}")
    else:
        print(f"\n🎉 所有行业已处理完成！")
    
    conn.close()


if __name__ == "__main__":
    main()
