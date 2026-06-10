#!/usr/bin/env python3
# coding=utf-8
"""
数据初始化脚本 - data_initializer.py

功能：
1. 从AKShare批量下载A股、科创板历史行情数据
2. 下载申万行业板块指数数据
3. 下载股票行业分类数据
4. 存储到本地SQLite数据库

作者：Manus AI
日期：2026-01-14
"""

import akshare as ak
import sqlite3
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Optional, List
import logging
import os
import sys
from tqdm import tqdm

from project_paths import get_db_path


class DataInitializer:
    """数据初始化器"""
    
    def __init__(self, db_path: str = None, start_date: str = "20150101"):
        """
        初始化
        
        Args:
            db_path: SQLite数据库文件路径
            start_date: 数据起始日期（格式：YYYYMMDD）
        """
        if db_path is None:
            self.db_path = str(get_db_path())
        else:
            self.db_path = db_path
        self.start_date = start_date
        self.end_date = datetime.now().strftime("%Y%m%d")
        
        # 配置日志
        self._setup_logging()
        
        # 初始化数据库连接
        self.conn = None
        
        # 统计信息
        self.stats = {
            'total_stocks': 0,
            'success_stocks': 0,
            'failed_stocks': 0,
            'total_records': 0,
            'start_time': None,
            'end_time': None
        }
    
    def _setup_logging(self):
        """配置日志"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(f'data_init_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def connect_db(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.logger.info(f"成功连接数据库: {self.db_path}")
        except Exception as e:
            self.logger.error(f"连接数据库失败: {e}")
            raise
    
    def close_db(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.logger.info("数据库连接已关闭")
    
    def create_tables(self):
        """创建数据库表结构"""
        self.logger.info("开始创建数据库表结构...")
        
        cursor = self.conn.cursor()
        
        # 1. 股票日度行情表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_quote (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
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
                UNIQUE(stock_code, trade_date)
            )
        """)
        
        # 2. 股票基本信息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_info (
                stock_code TEXT PRIMARY KEY,
                stock_name TEXT,
                market TEXT,
                list_date TEXT DEFAULT NULL,
                industry TEXT,
                industry_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. 申万行业板块日度行情表
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
                change_pct REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(industry_code, trade_date)
            )
        """)
        
        # 4. 股票行业分类表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_industry (
                stock_code TEXT PRIMARY KEY,
                industry_code TEXT,
                industry_name TEXT,
                first_industry_code TEXT,
                first_industry_name TEXT,
                second_industry_code TEXT,
                second_industry_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_quote_code ON daily_quote(stock_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_quote_date ON daily_quote(trade_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_industry_quote_code ON industry_quote(industry_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_industry_quote_date ON industry_quote(trade_date)")
        
        self.conn.commit()
        self.logger.info("数据库表结构创建完成")
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取所有A股股票列表"""
        self.logger.info("正在获取A股股票列表...")
        
        try:
            # 获取沪深A股实时行情数据
            df = ak.stock_zh_a_spot_em()
            
            # 筛选需要的列（注意：AKShare返回的数据没有'上市时间'字段）
            df = df[['代码', '名称']]
            df.columns = ['stock_code', 'stock_name']
            
            # 过滤掉ST、退市股票
            df = df[~df['stock_name'].str.contains('ST|退')]
            
            self.logger.info(f"成功获取 {len(df)} 只股票")
            self.stats['total_stocks'] = len(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            raise
    
    def get_latest_dates(self) -> dict:
        """获取所有股票的最新交易日期"""
        self.logger.info("正在获取现有数据的最新日期...")
        try:
            cursor = self.conn.cursor()
            # 查询每只股票的最大日期
            cursor.execute("SELECT stock_code, MAX(trade_date) FROM daily_quote GROUP BY stock_code")
            result = {row[0]: row[1] for row in cursor.fetchall()}
            self.logger.info(f"获取到 {len(result)} 只股票的最新日期记录")
            return result
        except Exception as e:
            self.logger.warning(f"获取最新日期失败(可能是首次运行): {e}")
            return {}

    def download_stock_data(self, stock_code: str, stock_name: str, start_date: str = None) -> Optional[pd.DataFrame]:
        """
        下载单只股票的历史数据
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            start_date: 开始日期 (可选，默认使用self.start_date)
        
        Returns:
            DataFrame或None
        """
        # 使用指定的start_date，否则使用全局配置
        query_start_date = start_date if start_date else self.start_date
        
        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=query_start_date,
                end_date=self.end_date,
                adjust="qfq"  # 前复权
            )
            
            if df.empty:
                return None
            
            # 添加股票代码和名称
            df['stock_code'] = stock_code
            df['stock_name'] = stock_name
            
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
            
            return df
            
        except Exception as e:
            self.logger.warning(f"下载 {stock_code} {stock_name} 数据失败: {e}")
            return None
    
    def save_stock_data(self, df: pd.DataFrame):
        """保存股票数据到数据库"""
        try:
            df.to_sql('daily_quote', self.conn, if_exists='append', index=False)
            self.stats['total_records'] += len(df)
        except Exception as e:
            self.logger.error(f"保存数据失败: {e}")
            raise
    
    def init_stock_data(self, batch_size: int = 50, delay: float = 0.5, auto_update: bool = False):
        """
        初始化股票数据
        
        Args:
            batch_size: 每批次处理的股票数量
            delay: 每次请求的延迟时间（秒），避免被限流
            auto_update: 是否自动增量更新
        """
        self.logger.info("=" * 80)
        self.logger.info("开始初始化股票历史数据")
        if auto_update:
            self.logger.info(f"模式: 自动增量更新 (截至 {self.end_date})")
        else:
            self.logger.info(f"模式: 全量/范围下载 ({self.start_date} ~ {self.end_date})")
        self.logger.info("=" * 80)
        
        self.stats['start_time'] = datetime.now()
        
        # 获取股票列表
        stock_list = self.get_stock_list()
        
        # 获取最新日期缓存（如果开启自动更新）
        latest_dates = {}
        if auto_update:
            latest_dates = self.get_latest_dates()
        
        # 使用进度条
        with tqdm(total=len(stock_list), desc="下载进度") as pbar:
            for idx, row in stock_list.iterrows():
                stock_code = row['stock_code']
                stock_name = row['stock_name']
                
                # 计算开始日期
                current_start_date = self.start_date
                if auto_update and stock_code in latest_dates:
                    last_date_str = latest_dates[stock_code]
                    try:
                        # 简单的日期加1天逻辑
                        last_date = datetime.strptime(str(last_date_str), "%Y-%m-%d")
                        next_date = last_date + timedelta(days=1)
                        current_start_date = next_date.strftime("%Y%m%d")
                        
                        # 如果最新日期已经 >= 今天，则跳过
                        if int(current_start_date) > int(self.end_date):
                            pbar.update(1)
                            continue
                            
                    except ValueError:
                        # 日期格式解析失败，使用默认
                        pass

                # 下载数据
                df = self.download_stock_data(stock_code, stock_name, start_date=current_start_date)
                
                if df is not None and not df.empty:
                    # 保存到数据库
                    self.save_stock_data(df)
                    self.stats['success_stocks'] += 1
                    pbar.set_postfix({
                        '成功': self.stats['success_stocks'],
                        '失败': self.stats['failed_stocks'],
                        '记录数': self.stats['total_records']
                    })
                else:
                    # 如果是增量更新且没有新数据，不算失败
                    if not auto_update:
                        self.stats['failed_stocks'] += 1
                
                pbar.update(1)
                
                # 控制请求频率
                time.sleep(delay)
                
                # 每批次提交一次
                if (idx + 1) % batch_size == 0:
                    self.conn.commit()
                    self.logger.info(f"已处理 {idx + 1}/{len(stock_list)} 只股票")
        
        # 最后提交
        self.conn.commit()
        
        self.stats['end_time'] = datetime.now()
        self._print_stats()
    
    def init_stock_info(self):
        """初始化股票基本信息"""
        self.logger.info("开始初始化股票基本信息...")
        
        try:
            stock_list = self.get_stock_list()
            
            for idx, row in stock_list.iterrows():
                stock_code = row['stock_code']
                stock_name = row['stock_name']
                
                # 判断市场
                if stock_code.startswith('6'):
                    market = 'SH'  # 上海
                elif stock_code.startswith('0') or stock_code.startswith('3'):
                    market = 'SZ'  # 深圳
                elif stock_code.startswith('8') or stock_code.startswith('4'):
                    market = 'BJ'  # 北京
                else:
                    market = 'UNKNOWN'
                
                # 插入数据（不再使用list_date字段）
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO stock_info (stock_code, stock_name, market)
                    VALUES (?, ?, ?)
                """, (stock_code, stock_name, market))
            
            self.conn.commit()
            self.logger.info(f"成功初始化 {len(stock_list)} 只股票基本信息")
            
        except Exception as e:
            self.logger.error(f"初始化股票基本信息失败: {e}")
            raise
    
    def init_industry_data(self):
        """初始化申万行业板块数据"""
        self.logger.info("开始初始化申万行业板块数据...")
        
        try:
            # 获取申万行业指数列表
            df_industry_list = ak.index_stock_info()
            
            # 筛选申万二级行业
            df_sw = df_industry_list[df_industry_list['index_code'].str.startswith('801')]
            
            self.logger.info(f"共 {len(df_sw)} 个申万行业")
            
            for idx, row in tqdm(df_sw.iterrows(), total=len(df_sw), desc="下载行业数据"):
                industry_code = row['index_code']
                industry_name = row['display_name']
                
                try:
                    # 下载行业指数历史数据
                    df = ak.index_zh_a_hist(
                        symbol=industry_code,
                        period="daily",
                        start_date=self.start_date,
                        end_date=self.end_date
                    )
                    
                    if df.empty:
                        continue
                    
                    df['industry_code'] = industry_code
                    df['industry_name'] = industry_name
                    
                    # 重命名列
                    df = df.rename(columns={
                        '日期': 'trade_date',
                        '开盘': 'open_price',
                        '收盘': 'close_price',
                        '最高': 'high_price',
                        '最低': 'low_price',
                        '成交量': 'volume',
                        '成交额': 'turnover',
                        '涨跌幅': 'change_pct'
                    })
                    
                    # 保存到数据库
                    df.to_sql('industry_quote', self.conn, if_exists='append', index=False)
                    
                    time.sleep(0.5)  # 控制频率
                    
                except Exception as e:
                    self.logger.warning(f"下载行业 {industry_code} {industry_name} 数据失败: {e}")
            
            self.conn.commit()
            self.logger.info("申万行业板块数据初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化行业数据失败: {e}")
            raise
    
    def init_stock_industry_mapping(self):
        """初始化股票行业分类映射"""
        self.logger.info("开始初始化股票行业分类...")
        
        try:
            # 获取申万行业成分股
            df_industry_list = ak.index_stock_info()
            df_sw = df_industry_list[df_industry_list['index_code'].str.startswith('801')]
            
            for idx, row in tqdm(df_sw.iterrows(), total=len(df_sw), desc="下载行业成分股"):
                industry_code = row['index_code']
                industry_name = row['display_name']
                
                try:
                    # 获取该行业的成分股
                    df_cons = ak.index_stock_cons(symbol=industry_code)
                    
                    if df_cons.empty:
                        continue
                    
                    for _, stock_row in df_cons.iterrows():
                        stock_code = stock_row['品种代码']
                        
                        cursor = self.conn.cursor()
                        cursor.execute("""
                            INSERT OR REPLACE INTO stock_industry 
                            (stock_code, second_industry_code, second_industry_name)
                            VALUES (?, ?, ?)
                        """, (stock_code, industry_code, industry_name))
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.warning(f"下载行业 {industry_code} 成分股失败: {e}")
            
            self.conn.commit()
            self.logger.info("股票行业分类初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化股票行业分类失败: {e}")
            raise
    
    def init_hs300_data(self, auto_update: bool = False):
        """初始化沪深300指数数据"""
        self.logger.info("开始初始化沪深300指数数据...")
        try:
            stock_code = "399300"
            stock_name = "沪深300"
            
            # 计算开始日期
            current_start_date = "20200101" # 默认从2020年开始，与download_hs300保持一致
            if auto_update:
                latest_dates = self.get_latest_dates()
                if stock_code in latest_dates:
                    last_date_str = latest_dates[stock_code]
                    try:
                        last_date = datetime.strptime(str(last_date_str), "%Y-%m-%d")
                        next_date = last_date + timedelta(days=1)
                        current_start_date = next_date.strftime("%Y%m%d")
                        if int(current_start_date) > int(self.end_date):
                            self.logger.info("沪深300数据已是最新")
                            return
                    except ValueError:
                        pass

            # 下载数据
            self.logger.info(f"下载沪深300数据 ({current_start_date} ~ {self.end_date})...")
            # 使用 akshare.stock_zh_index_daily 接口
            df = ak.stock_zh_index_daily(symbol="sz399300")
            
            if df is None or df.empty:
                self.logger.warning("沪深300数据下载为空")
                return

            # 处理列名和日期
            if 'date' in df.columns:
                df['trade_date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            else:
                 # 尝试其他列名
                 pass
            
            # 过滤日期
            df = df[(df['trade_date'].str.replace('-', '').astype(int) >= int(current_start_date)) & 
                    (df['trade_date'].str.replace('-', '').astype(int) <= int(self.end_date))]
            
            if df.empty:
                 self.logger.info("沪深300无新数据")
                 return
            
            # 重命名列以匹配 daily_quote
            df['stock_code'] = stock_code
            df['stock_name'] = stock_name
            # stock_zh_index_daily 返回: date, open, high, low, close, volume
            df = df.rename(columns={
                'open': 'open_price',
                'high': 'high_price',
                'low': 'low_price',
                'close': 'close_price',
                'volume': 'volume'
            })
            
            if 'turnover' not in df.columns:
                df['turnover'] = 0.0
                
            # 选择需要的列
            required_cols = ['stock_code', 'stock_name', 'trade_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume', 'turnover']
            df = df[required_cols]
            
            # 保存到 daily_quote 表
            df.to_sql('daily_quote', self.conn, if_exists='append', index=False)
            self.conn.commit()
            self.logger.info(f"沪深300数据更新完成，新增 {len(df)} 条记录")

        except Exception as e:
            self.logger.error(f"初始化沪深300数据失败: {e}")

    def _print_stats(self):
        """打印统计信息"""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        self.logger.info("=" * 80)
        self.logger.info("数据初始化完成！")
        self.logger.info("=" * 80)
        self.logger.info(f"总股票数: {self.stats['total_stocks']}")
        self.logger.info(f"成功下载: {self.stats['success_stocks']}")
        self.logger.info(f"失败数量: {self.stats['failed_stocks']}")
        self.logger.info(f"总记录数: {self.stats['total_records']}")
        self.logger.info(f"耗时: {duration}")
        self.logger.info(f"数据库文件: {self.db_path}")
        self.logger.info(f"数据库大小: {os.path.getsize(self.db_path) / 1024 / 1024:.2f} MB")
        self.logger.info("=" * 80)
    
    def run(self, include_industry: bool = True, auto_update: bool = False, proxy: str = None):
        """
        运行完整的初始化流程
        
        Args:
            include_industry: 是否包含行业数据
            auto_update: 是否自动增量更新
            proxy: 代理地址 (http://host:port)
        """
        if proxy:
            self.logger.info(f"设置代理: {proxy}")
            os.environ['HTTP_PROXY'] = proxy
            os.environ['HTTPS_PROXY'] = proxy
            
        try:
            # 连接数据库
            self.connect_db()
            
            # 创建表结构
            self.create_tables()
            
            # 初始化股票基本信息
            self.init_stock_info()
            
            # 初始化股票历史数据
            self.init_stock_data(auto_update=auto_update)
            
            # 初始化行业数据（可选）
            if include_industry:
                self.init_industry_data()
                self.init_stock_industry_mapping()
                
            # 初始化HS300数据 (Step 0补充)
            self.init_hs300_data(auto_update=auto_update)
            
        except Exception as e:
            self.logger.error(f"初始化过程出错: {e}")
            raise
        finally:
            # 关闭数据库连接
            self.close_db()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='股票数据初始化/更新工具')
    default_db = str(get_db_path())
    parser.add_argument('--db', type=str, default=default_db, help='数据库文件路径')
    parser.add_argument('--start', type=str, default="20150101", help='起始日期 (YYYYMMDD)')
    parser.add_argument('--update', action='store_true', help='开启自动增量更新模式')
    parser.add_argument('--skip-industry', action='store_true', help='跳过行业数据下载')
    parser.add_argument('--yes', '-y', action='store_true', help='跳过确认提示')
    parser.add_argument('--proxy', type=str, help='设置代理 (e.g. http://127.0.0.1:7890)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("股票数据初始化工具")
    print("=" * 80)
    print()
    
    print(f"数据库文件: {args.db}")
    if args.update:
        print(f"模式: 自动增量更新 (忽略 --start 参数)")
    else:
        print(f"起始日期: {args.start}")
    
    if args.proxy:
        print(f"使用代理: {args.proxy}")
    
    print()
    
    # 确认
    if not args.yes:
        confirm = input("是否开始执行？(y/n): ")
        if confirm.lower() != 'y':
            print("已取消")
            return
    
    # 创建初始化器
    initializer = DataInitializer(db_path=args.db, start_date=args.start)
    
    # 运行初始化
    initializer.run(include_industry=not args.skip_industry, auto_update=args.update, proxy=args.proxy)
    
    print()
    print("执行完成！")


if __name__ == "__main__":
    main()
