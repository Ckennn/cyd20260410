#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证数据库字段是否与项目代码完全匹配
"""

import os
import sqlite3
from project_paths import get_db_path as get_project_db_path

def get_db_path():
    """获取数据库路径"""
    return str(get_project_db_path())

def get_table_schema(conn, table_name):
    """获取表结构"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return {col[1]: col[2] for col in columns}  # {字段名: 类型}

def main():
    db_path = get_db_path()
    
    print("="*80)
    print("数据库字段匹配验证")
    print("="*80)
    print(f"\n数据库: {db_path}\n")
    
    with sqlite3.connect(db_path) as conn:
        
        # ====================================================================
        # 1. daily_quote 表
        # ====================================================================
        print("="*80)
        print("1. daily_quote 表")
        print("="*80)
        
        actual = get_table_schema(conn, "daily_quote")
        
        # 代码期望的字段（来自databaseutil.py query_sqlite函数）
        expected_query_fields = [
            'stock_code', 'stock_name', 'trade_date', 
            'open_price', 'high_price', 'low_price', 'close_price',
            'volume', 'turnover'
        ]
        
        # 代码期望的重命名后字段（来自databaseutil.py第780-789行）
        expected_renamed_fields = {
            'trade_date': 'date',
            'open_price': 'open',
            'close_price': 'close',
            'high_price': 'high',
            'low_price': 'low',
            'volume': 'volume',
            'turnover': 'turnover'
        }
        
        print(f"\n实际字段 ({len(actual)}个):")
        for field, dtype in actual.items():
            print(f"  {field:20s} {dtype}")
        
        print(f"\n代码查询的字段 ({len(expected_query_fields)}个):")
        all_match = True
        for field in expected_query_fields:
            exists = field in actual
            status = "✅" if exists else "❌"
            print(f"  {status} {field:20s} {'存在' if exists else '缺失'}")
            if not exists:
                all_match = False
        
        print(f"\n代码重命名后的字段:")
        for old, new in expected_renamed_fields.items():
            exists = old in actual
            status = "✅" if exists else "❌"
            print(f"  {status} {old:20s} → {new:10s} {'正常' if exists else '缺失'}")
            if not exists:
                all_match = False
        
        if all_match:
            print("\n✅ daily_quote 表字段完全匹配")
        else:
            print("\n❌ daily_quote 表字段不匹配")
        
        # ====================================================================
        # 2. stock_info 表
        # ====================================================================
        print("\n" + "="*80)
        print("2. stock_info 表")
        print("="*80)
        
        actual = get_table_schema(conn, "stock_info")
        expected = ['stock_code', 'stock_name']
        
        print(f"\n实际字段 ({len(actual)}个):")
        for field, dtype in actual.items():
            print(f"  {field:20s} {dtype}")
        
        print(f"\n代码期望的字段 ({len(expected)}个):")
        all_match = True
        for field in expected:
            exists = field in actual
            status = "✅" if exists else "❌"
            print(f"  {status} {field:20s} {'存在' if exists else '缺失'}")
            if not exists:
                all_match = False
        
        if all_match:
            print("\n✅ stock_info 表字段完全匹配")
        else:
            print("\n❌ stock_info 表字段不匹配")
        
        # ====================================================================
        # 3. stock_industry 表
        # ====================================================================
        print("\n" + "="*80)
        print("3. stock_industry 表")
        print("="*80)
        
        actual = get_table_schema(conn, "stock_industry")
        
        # 代码期望的字段（来自databaseutil.py第756-757行）
        expected = ['stock_code', 'stock_name', 'second_industry_code', 'second_industry_name']
        
        print(f"\n实际字段 ({len(actual)}个):")
        for field, dtype in actual.items():
            print(f"  {field:20s} {dtype}")
        
        print(f"\n代码期望的字段 ({len(expected)}个):")
        all_match = True
        for field in expected:
            exists = field in actual
            status = "✅" if exists else "❌"
            print(f"  {status} {field:20s} {'存在' if exists else '缺失'}")
            if not exists:
                all_match = False
        
        if all_match:
            print("\n✅ stock_industry 表字段完全匹配")
        else:
            print("\n❌ stock_industry 表字段不匹配")
        
        # ====================================================================
        # 4. industry_quote 表
        # ====================================================================
        print("\n" + "="*80)
        print("4. industry_quote 表")
        print("="*80)
        
        actual = get_table_schema(conn, "industry_quote")
        
        # 代码期望的字段（来自databaseutil.py第807-873行）
        expected = [
            'industry_code', 'industry_name', 'trade_date',
            'open_price', 'high_price', 'low_price', 'close_price',
            'volume', 'turnover'
        ]
        
        print(f"\n实际字段 ({len(actual)}个):")
        for field, dtype in actual.items():
            print(f"  {field:20s} {dtype}")
        
        print(f"\n代码期望的字段 ({len(expected)}个):")
        all_match = True
        for field in expected:
            exists = field in actual
            status = "✅" if exists else "❌"
            print(f"  {status} {field:20s} {'存在' if exists else '缺失'}")
            if not exists:
                all_match = False
        
        if all_match:
            print("\n✅ industry_quote 表字段完全匹配")
        else:
            print("\n❌ industry_quote 表字段不匹配")
        
        # ====================================================================
        # 5. 数据完整性检查
        # ====================================================================
        print("\n" + "="*80)
        print("5. 数据完整性检查")
        print("="*80)
        
        cursor = conn.cursor()
        
        # daily_quote
        cursor.execute("SELECT COUNT(*) FROM daily_quote")
        dq_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT stock_code) FROM daily_quote")
        dq_stocks = cursor.fetchone()[0]
        print(f"\ndaily_quote:")
        print(f"  总记录数: {dq_count:,}")
        print(f"  股票数量: {dq_stocks:,}")
        
        # stock_info
        cursor.execute("SELECT COUNT(*) FROM stock_info")
        si_count = cursor.fetchone()[0]
        print(f"\nstock_info:")
        print(f"  股票数量: {si_count:,}")
        
        # stock_industry
        cursor.execute("SELECT COUNT(*) FROM stock_industry")
        sind_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT second_industry_code) FROM stock_industry WHERE second_industry_code IS NOT NULL")
        sind_industries = cursor.fetchone()[0]
        print(f"\nstock_industry:")
        print(f"  股票数量: {sind_count:,}")
        print(f"  行业数量: {sind_industries}/86")
        
        # industry_quote
        cursor.execute("SELECT COUNT(*) FROM industry_quote")
        iq_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT industry_code) FROM industry_quote WHERE industry_code IS NOT NULL")
        iq_industries = cursor.fetchone()[0]
        print(f"\nindustry_quote:")
        print(f"  总记录数: {iq_count:,}")
        print(f"  行业数量: {iq_industries}/86")
        
        # ====================================================================
        # 6. 总结
        # ====================================================================
        print("\n" + "="*80)
        print("6. 总结")
        print("="*80)
        
        issues = []
        
        if sind_industries < 86:
            issues.append(f"⚠️ stock_industry 只有 {sind_industries}/86 个行业")
        
        if iq_industries < 86:
            issues.append(f"⚠️ industry_quote 只有 {iq_industries}/86 个行业（但有Fallback机制）")
        
        if issues:
            print("\n发现的问题:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("\n✅ 所有检查通过！")
        
        print("\n建议:")
        if sind_industries < 86:
            print("  1. 继续下载缺失的行业成分股")
            print("     python fix_industry_data_batch.py --start-index 0 --batch-size 86 --type cons")
        else:
            print("  1. ✅ 行业成分股已完整")
        
        if iq_industries < 86:
            print("  2. ⚠️ 行业行情不完整，但有Fallback机制，系统可以正常运行")
        else:
            print("  2. ✅ 行业行情已完整")

if __name__ == "__main__":
    main()
