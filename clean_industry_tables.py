#!/usr/bin/env python3
"""
清理旧的 stock_industry 和 industry_quote 表

这个脚本会：
1. 删除旧的 stock_industry 表
2. 删除旧的 industry_quote 表
3. 为重新运行 fix_industry_data_eastmoney_corrected.py 做准备
"""

import os
import sqlite3
from project_paths import get_db_path

# 数据库路径
DB_PATH = str(get_db_path())

def main():
    print("=" * 80)
    print("清理旧的行业表")
    print("=" * 80)
    print(f"\n数据库路径: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库不存在: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_industry'")
        if cursor.fetchone():
            print("\n检查 stock_industry 表结构...")
            cursor.execute("PRAGMA table_info(stock_industry)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"当前字段: {', '.join(columns)}")
            
            # 删除旧表
            print("\n删除 stock_industry 表...")
            cursor.execute("DROP TABLE IF EXISTS stock_industry")
            print("✅ stock_industry 表已删除")
        else:
            print("\n✅ stock_industry 表不存在，无需删除")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='industry_quote'")
        if cursor.fetchone():
            print("\n检查 industry_quote 表...")
            cursor.execute("SELECT COUNT(*) FROM industry_quote")
            count = cursor.fetchone()[0]
            print(f"当前记录数: {count}")
            
            # 删除旧表
            print("\n删除 industry_quote 表...")
            cursor.execute("DROP TABLE IF EXISTS industry_quote")
            print("✅ industry_quote 表已删除")
        else:
            print("\n✅ industry_quote 表不存在，无需删除")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ 清理完成！")
        print("=" * 80)
        print("\n下一步：")
        print("运行修正版脚本重新创建表：")
        print("  python fix_industry_data_eastmoney_corrected.py")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
