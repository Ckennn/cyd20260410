"""
数据库结构验证脚本
用于检查SQLite数据库的表结构和数据格式是否符合预期
"""

import sqlite3
import pandas as pd
from datetime import datetime

class DatabaseChecker:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"✅ 成功连接数据库: {self.db_path}\n")
            return True
        except Exception as e:
            print(f"❌ 连接数据库失败: {e}")
            return False
    
    def get_all_tables(self):
        """获取所有表名"""
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        cursor = self.conn.cursor()
        cursor.execute(query)
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    
    def get_table_schema(self, table_name):
        """获取表结构"""
        query = f"PRAGMA table_info({table_name});"
        df = pd.read_sql(query, self.conn)
        return df
    
    def get_sample_data(self, table_name, limit=5):
        """获取样本数据"""
        query = f"SELECT * FROM {table_name} LIMIT {limit};"
        df = pd.read_sql(query, self.conn)
        return df
    
    def get_row_count(self, table_name):
        """获取记录数"""
        query = f"SELECT COUNT(*) as count FROM {table_name};"
        cursor = self.conn.cursor()
        cursor.execute(query)
        count = cursor.fetchone()[0]
        return count
    
    def check_akshare_format(self, table_name):
        """检查是否符合AKShare的index_zh_a_hist格式"""
        print(f"🔍 检查表 '{table_name}' 是否符合AKShare格式...\n")
        
        # AKShare的标准字段
        akshare_columns = {
            '日期': 'object',
            '开盘': 'float64',
            '收盘': 'float64',
            '最高': 'float64',
            '最低': 'float64',
            '成交量': 'int64',  # 单位：手
            '成交额': 'float64',  # 单位：元
            '振幅': 'float64',  # 单位：%
            '涨跌幅': 'float64',  # 单位：%
            '涨跌额': 'float64',  # 单位：元
            '换手率': 'float64'  # 单位：%
        }
        
        # 可能的英文字段名映射
        english_mapping = {
            'date': '日期',
            'open': '开盘',
            'close': '收盘',
            'high': '最高',
            'low': '最低',
            'volume': '成交量',
            'amount': '成交额',
            'amplitude': '振幅',
            'change_pct': '涨跌幅',
            'change_amount': '涨跌额',
            'turnover_rate': '换手率'
        }
        
        # 获取表结构
        schema = self.get_table_schema(table_name)
        actual_columns = schema['name'].tolist()
        
        print("📋 实际字段:")
        for i, col in enumerate(actual_columns, 1):
            col_type = schema[schema['name'] == col]['type'].values[0]
            print(f"  {i}. {col:20s} ({col_type})")
        
        print("\n📋 AKShare标准字段:")
        for i, (col, dtype) in enumerate(akshare_columns.items(), 1):
            print(f"  {i}. {col:20s} ({dtype})")
        
        # 检查字段匹配
        print("\n🔍 字段匹配检查:")
        
        # 检查是否使用中文字段名
        if '日期' in actual_columns:
            print("  ✅ 使用中文字段名")
            missing_columns = []
            for col in akshare_columns.keys():
                if col not in actual_columns:
                    missing_columns.append(col)
            
            if missing_columns:
                print(f"  ⚠️ 缺少字段: {', '.join(missing_columns)}")
            else:
                print("  ✅ 所有标准字段都存在")
        
        # 检查是否使用英文字段名
        elif 'date' in actual_columns:
            print("  ✅ 使用英文字段名")
            print("\n  字段映射:")
            for eng, chn in english_mapping.items():
                if eng in actual_columns:
                    print(f"    {eng:20s} → {chn}")
                else:
                    print(f"    {eng:20s} → ❌ 缺失")
        
        else:
            print("  ❌ 字段名格式不符合预期")
        
        # 获取样本数据
        print("\n📊 样本数据（前3条）:")
        sample_data = self.get_sample_data(table_name, 3)
        print(sample_data.to_string())
        
        # 检查数据范围
        print("\n📈 数据统计:")
        print(f"  总记录数: {self.get_row_count(table_name):,}")
        
        # 检查日期范围
        if '日期' in actual_columns:
            date_col = '日期'
        elif 'date' in actual_columns:
            date_col = 'date'
        else:
            date_col = None
        
        if date_col:
            query = f"SELECT MIN({date_col}) as min_date, MAX({date_col}) as max_date FROM {table_name};"
            df_date_range = pd.read_sql(query, self.conn)
            print(f"  日期范围: {df_date_range['min_date'].values[0]} ~ {df_date_range['max_date'].values[0]}")
        
        return actual_columns
    
    def run_full_check(self):
        """运行完整检查"""
        print("=" * 80)
        print("数据库结构验证")
        print("=" * 80)
        print()
        
        if not self.connect():
            return
        
        # 获取所有表
        tables = self.get_all_tables()
        print(f"📁 数据库中的表（共{len(tables)}个）:")
        for i, table in enumerate(tables, 1):
            row_count = self.get_row_count(table)
            print(f"  {i}. {table:30s} ({row_count:,} 条记录)")
        
        print("\n" + "=" * 80)
        
        # 检查每个表
        for table in tables:
            print()
            self.check_akshare_format(table)
            print("\n" + "=" * 80)
        
        self.conn.close()
        print("\n✅ 检查完成！")


def main():
    """主函数"""
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                      数据库结构验证工具                                ║
║                                                                       ║
║  用途: 检查SQLite数据库是否符合AKShare的index_zh_a_hist格式            ║
║                                                                       ║
║  AKShare标准字段:                                                      ║
║    - 日期, 开盘, 收盘, 最高, 最低                                      ║
║    - 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率                       ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)
    
    # 数据库路径（请修改为你的实际路径）
    db_path = input("请输入数据库文件路径（例如: D:/Codepython/newpy/new/stock_data.db）: ").strip()
    
    if not db_path:
        print("❌ 未输入数据库路径")
        return
    
    # 创建检查器
    checker = DatabaseChecker(db_path)
    
    # 运行检查
    checker.run_full_check()


if __name__ == "__main__":
    main()
