"""
download_hs300.py
下载沪深300指数日度行情数据，并按现有CSV格式保存
支持多个数据源自动切换：akshare(新浪) → akshare(腾讯) → 网易财经HTTP → 手动导入

使用前请先安装: pip install akshare

用法:
    python download_hs300.py
    python download_hs300.py --start 20240101 --end 20240131
    python download_hs300.py --source sina
    python download_hs300.py --source manual --manual-file hs300_data.csv
"""
import argparse
import os
import sys
import time
from datetime import datetime
import sqlite3
import databaseutil
import project_paths

import numpy as np
import pandas as pd


# ===================== 配置区 =====================
INNER_CODE_1 = "399300"
INNER_CODE_2 = "000300"

OUTPUT_DIR = str(project_paths.get_market_quote_dir())

STOCK_NAME = "沪深300"
# ===================== 配置区结束 =====================


# ==================== 数据源 ====================

def download_from_eastmoney(start_date: str, end_date: str) -> pd.DataFrame:
    """数据源1: akshare 东方财富"""
    import akshare as ak
    print("  📡 尝试: 东方财富 (index_zh_a_hist)...")
    df = ak.index_zh_a_hist(
        symbol="000300", period="daily",
        start_date=start_date, end_date=end_date
    )
    return df


def download_from_sina(start_date: str, end_date: str) -> pd.DataFrame:
    """数据源2: akshare 新浪"""
    import akshare as ak
    print("  📡 尝试: 新浪 (stock_zh_index_daily)...")
    df = ak.stock_zh_index_daily(symbol="sh000300")
    if df is not None and not df.empty:
        df['日期'] = pd.to_datetime(df['date'])
        sd = pd.to_datetime(start_date, format='%Y%m%d')
        ed = pd.to_datetime(end_date, format='%Y%m%d')
        df = df[(df['日期'] >= sd) & (df['日期'] <= ed)]
        df = df.rename(columns={
            'open': '开盘', 'high': '最高', 'low': '最低',
            'close': '收盘', 'volume': '成交量'
        })
        if '成交额' not in df.columns:
            df['成交额'] = 0.0
    return df


def download_from_tencent(start_date: str, end_date: str) -> pd.DataFrame:
    """数据源3: akshare 腾讯"""
    import akshare as ak
    print("  📡 尝试: 腾讯 (stock_zh_index_daily_tx)...")
    df = ak.stock_zh_index_daily_tx(symbol="sh000300")
    if df is not None and not df.empty:
        df['日期'] = pd.to_datetime(df['date'])
        sd = pd.to_datetime(start_date, format='%Y%m%d')
        ed = pd.to_datetime(end_date, format='%Y%m%d')
        df = df[(df['日期'] >= sd) & (df['日期'] <= ed)]
        df = df.rename(columns={
            'open': '开盘', 'high': '最高', 'low': '最低',
            'close': '收盘', 'volume': '成交量'
        })
        if '成交额' not in df.columns:
            df['成交额'] = 0.0
    return df


def download_from_163(start_date: str, end_date: str) -> pd.DataFrame:
    """数据源4: 网易财经直接HTTP"""
    import requests
    print("  📡 尝试: 网易财经 (HTTP直接下载)...")
    url = (
        f"http://quotes.money.163.com/service/chddata.html"
        f"?code=0000300&start={start_date}&end={end_date}"
        f"&fields=TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.encoding = 'gb2312'

    if resp.status_code == 200 and len(resp.text) > 100:
        from io import StringIO
        df = pd.read_csv(StringIO(resp.text))
        col_map = {}
        for col in df.columns:
            c = col.strip()
            if c in ['日期']: col_map[col] = '日期'
            elif c in ['收盘价', 'TCLOSE']: col_map[col] = '收盘'
            elif c in ['最高价', 'HIGH']: col_map[col] = '最高'
            elif c in ['最低价', 'LOW']: col_map[col] = '最低'
            elif c in ['开盘价', 'TOPEN']: col_map[col] = '开盘'
            elif c in ['成交量', 'VOTURNOVER']: col_map[col] = '成交量'
            elif c in ['成交金额', 'VATURNOVER']: col_map[col] = '成交额'
        df = df.rename(columns=col_map)
        if '日期' in df.columns:
            df['日期'] = pd.to_datetime(df['日期'])
        return df
    return None


def load_from_manual_file(filepath: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    数据源5: 从手动下载的CSV文件导入
    支持从东方财富/同花顺/新浪/通达信等导出的CSV
    """
    print(f"  📂 从本地文件导入: {filepath}")
    if not os.path.isfile(filepath):
        print(f"  ❌ 文件不存在: {filepath}")
        return None

    # 尝试多种编码
    for encoding in ['utf-8', 'gb2312', 'gbk', 'utf-8-sig']:
        try:
            df = pd.read_csv(filepath, encoding=encoding)
            break
        except:
            continue
    else:
        print("  ❌ 无法读取文件，请检查编码")
        return None

    print(f"  原始列名: {list(df.columns)}")

    col_map = {}
    for col in df.columns:
        cl = col.lower().strip()
        if cl in ['日期', 'date', '时间', 'datetime', 'trade_date']: col_map[col] = '日期'
        elif cl in ['开盘', 'open', '开盘价', '今开']: col_map[col] = '开盘'
        elif cl in ['最高', 'high', '最高价']: col_map[col] = '最高'
        elif cl in ['最低', 'low', '最低价']: col_map[col] = '最低'
        elif cl in ['收盘', 'close', '收盘价', '今收']: col_map[col] = '收盘'
        elif cl in ['成交量', 'volume', 'vol']: col_map[col] = '成交量'
        elif cl in ['成交额', 'amount', 'turnover']: col_map[col] = '成交额'

    df = df.rename(columns=col_map)
    df['日期'] = pd.to_datetime(df['日期'])

    sd = pd.to_datetime(start_date, format='%Y%m%d')
    ed = pd.to_datetime(end_date, format='%Y%m%d')
    df = df[(df['日期'] >= sd) & (df['日期'] <= ed)]

    if '成交额' not in df.columns:
        df['成交额'] = 0.0

    return df


# ==================== 核心逻辑 ====================

def download_with_retry(func, start_date, end_date, max_retries=2, delay=3):
    """带重试的下载"""
    for attempt in range(max_retries):
        try:
            df = func(start_date, end_date)
            if df is not None and not df.empty:
                return df
            print(f"  ⚠️ 返回数据为空")
        except Exception as e:
            err_name = type(e).__name__
            # 简短打印错误，不打印完整堆栈
            print(f"  ❌ 失败 ({err_name}): {str(e)[:80]}")
            if attempt < max_retries - 1:
                print(f"  ⏳ {delay}秒后重试...")
                time.sleep(delay)
    return None


def download_hs300_data(start_date, end_date, source='auto', manual_file=None):
    """下载沪深300数据，多数据源自动切换"""
    print(f"📥 下载沪深300指数数据 ({start_date} ~ {end_date})...\n")

    if source == 'manual':
        if not manual_file:
            print("❌ --source manual 需配合 --manual-file 使用")
            sys.exit(1)
        df = load_from_manual_file(manual_file, start_date, end_date)
        if df is not None and not df.empty:
            print(f"  ✅ 导入 {len(df)} 条记录\n")
            return df
        sys.exit(1)

    # 数据源优先级: 新浪 → 腾讯 → 网易 → 东方财富
    # (东方财富放最后，因为它最容易被封)
    sources = [
        ('新浪', download_from_sina),
        ('腾讯', download_from_tencent),
        ('网易财经', download_from_163),
        ('东方财富', download_from_eastmoney),
    ]

    if source != 'auto':
        source_map = {
            'eastmoney': ('东方财富', download_from_eastmoney),
            'sina': ('新浪', download_from_sina),
            'tencent': ('腾讯', download_from_tencent),
            '163': ('网易财经', download_from_163),
        }
        if source in source_map:
            # 指定源放最前
            item = source_map[source]
            sources = [item] + [s for s in sources if s[0] != item[0]]

    for name, func in sources:
        df = download_with_retry(func, start_date, end_date)
        if df is not None and not df.empty:
            print(f"  ✅ [{name}] 成功! {len(df)} 条记录\n")
            return df
        print(f"  ⚠️ [{name}] 失败，换下一个...\n")

    # 全部失败
    print("=" * 60)
    print("❌ 所有自动数据源均失败！")
    print()
    print("请使用手动方式:")
    print("  1. 浏览器打开 https://quote.eastmoney.com/zs000300.html")
    print("  2. 下载历史日K数据CSV")
    print("  3. 运行:")
    print("     python download_hs300.py --source manual --manual-file 下载的文件.csv")
    print("=" * 60)
    sys.exit(1)


def format_raw_data(df: pd.DataFrame) -> pd.DataFrame:
    """格式化为系统CSV格式"""
    result = pd.DataFrame()
    result['inner_code'] = INNER_CODE_1
    result['stock_name'] = STOCK_NAME
    result['date'] = pd.to_datetime(df['日期']).dt.strftime('%Y%m%d').astype(int)
    result['open'] = pd.to_numeric(df['开盘'], errors='coerce').values
    result['high'] = pd.to_numeric(df['最高'], errors='coerce').values
    result['low'] = pd.to_numeric(df['最低'], errors='coerce').values
    result['close'] = pd.to_numeric(df['收盘'], errors='coerce').values
    result['volume'] = pd.to_numeric(df['成交量'], errors='coerce').astype(float).values
    result['turnover'] = pd.to_numeric(df.get('成交额', 0), errors='coerce').astype(float).values
    result['trade_status'] = 1
    result['prev_close'] = result['close'].shift(1).values
    result['amount'] = result['turnover']
    result = result.dropna(subset=['close']).reset_index(drop=True)
    return result


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算技术指标"""
    df = df.sort_values('date', ascending=True).reset_index(drop=True)
    close = df['close']
    volume = df['volume']

    df['ema(11)'] = close.ewm(span=11, adjust=False).mean()
    df['ema(22)'] = close.ewm(span=22, adjust=False).mean()

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    df['macddif(12,26,9)'] = dif
    df['macddea(12,26,9)'] = dea
    df['macdbar(12,26,9)'] = 2 * (dif - dea)

    ma3 = close.rolling(3).mean()
    ma6 = close.rolling(6).mean()
    ma12 = close.rolling(12).mean()
    ma24 = close.rolling(24).mean()
    df['bbi(3,6,12,24)'] = (ma3 + ma6 + ma12 + ma24) / 4

    for p in [5, 10, 20, 30, 60, 120, 250]:
        df[f'ma({p})'] = close.rolling(p).mean()
    for p in [3, 5, 10, 20]:
        df[f'mavol({p})'] = volume.rolling(p).mean()

    df = df.sort_values('date', ascending=False).reset_index(drop=True)
    return df


def save_csv(df, output_dir, filename):
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    df.to_csv(filepath, index=False)
    print(f"  ✅ {filepath}  ({len(df)}行)")
    return filepath


def save_to_sqlite(df):
    """保存到SQLite数据库"""
    print(f"\n💾 保存到SQLite数据库: {databaseutil.DB_PATH}")
    
    if not os.path.exists(databaseutil.DB_PATH):
        print(f"  ❌ 数据库文件不存在: {databaseutil.DB_PATH}")
        return

    try:
        conn = sqlite3.connect(databaseutil.DB_PATH)
        cursor = conn.cursor()
        
        # 准备数据
        # 确保列名匹配 daily_quote 表
        # stock_code, stock_name, trade_date, open_price, high_price, low_price, close_price, volume, turnover
        
        count = 0
        for _, row in df.iterrows():
            trade_date = str(row['date']) # 确保是字符串
            
            # 检查是否存在
            cursor.execute(
                "SELECT 1 FROM daily_quote WHERE stock_code=? AND trade_date=?",
                (str(row['inner_code']), trade_date)
            )
            exists = cursor.fetchone()
            
            if not exists:
                sql = """
                INSERT INTO daily_quote 
                (stock_code, stock_name, trade_date, open_price, high_price, low_price, close_price, volume, turnover)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(sql, (
                    str(row['inner_code']),
                    row['stock_name'],
                    trade_date,
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    row['volume'],
                    row['turnover']
                ))
                count += 1
                
        conn.commit()
        conn.close()
        print(f"  ✅ 成功插入/更新 {count} 条记录")
        
    except Exception as e:
        print(f"  ❌ 保存到数据库失败: {e}")


def main():
    parser = argparse.ArgumentParser(description='下载沪深300指数日度行情数据')
    parser.add_argument('--start', type=str, default='20200101')
    parser.add_argument('--end', type=str, default=datetime.now().strftime('%Y%m%d'))
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR)
    parser.add_argument('--source', type=str, default='auto',
                        choices=['auto', 'eastmoney', 'sina', 'tencent', '163', 'manual'])
    parser.add_argument('--manual-file', type=str, default=None,
                        help='手动CSV文件路径 (配合 --source manual)')
    args = parser.parse_args()

    print("=" * 60)
    print("沪深300指数数据下载工具")
    print("=" * 60)
    print(f"  代码: {INNER_CODE_1} / {INNER_CODE_2}")
    print(f"  日期: {args.start} ~ {args.end}")
    print(f"  数据源: {args.source}")
    print(f"  输出: {args.output_dir}")
    print("=" * 60)
    print()

    raw_df = download_hs300_data(args.start, args.end, args.source, args.manual_file)

    print("🔄 格式化数据...")
    formatted_df = format_raw_data(raw_df)

    print("📊 计算技术指标...")
    final_df = calculate_all_indicators(formatted_df)

    print("\n💾 保存文件:")
    for code in [INNER_CODE_1, INNER_CODE_2]:
        df_out = final_df.copy()
        df_out['inner_code'] = code
        save_csv(df_out, args.output_dir, f"zh_{code}_hs300.csv")
        # 同时保存到数据库
        save_to_sqlite(df_out)

    print(f"\n{'=' * 60}")
    print("✅ 完成！")
    print(f"{'=' * 60}")
    print(f"\n📋 数据预览:")
    print(final_df[['date', 'open', 'high', 'low', 'close', 'volume']].head(5).to_string())


if __name__ == '__main__':
    main()
