
import sqlite3
import pandas as pd
import os
from project_paths import get_db_path

DB_PATH = str(get_db_path())

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)

    if ('daily_quote',) in tables:
        # Check daily_quote date range
        print("\n=== Data Range Check ===")
        cursor.execute("SELECT MIN(trade_date), MAX(trade_date) FROM daily_quote")
        min_date, max_date = cursor.fetchone()
        print(f"daily_quote range: {min_date} to {max_date}")

        cursor.execute("SELECT MIN(trade_date), MAX(trade_date) FROM industry_quote")
        min_idate, max_idate = cursor.fetchone()
        print(f"industry_quote range: {min_idate} to {max_idate}")
        
        # Check count
        cursor.execute("SELECT COUNT(*) FROM industry_quote")
        total_iq = cursor.fetchone()[0]
        print(f"Total industry_quote records: {total_iq}")
        
        # Check coverage percentage
        print("\n=== Coverage Check ===")
        cursor.execute("SELECT COUNT(DISTINCT trade_date) FROM daily_quote")
        dq_days = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT trade_date) FROM industry_quote")
        iq_days = cursor.fetchone()[0]
        print(f"Daily quote trade days: {dq_days}")
        print(f"Industry quote trade days: {iq_days}")
        cursor.execute("SELECT * FROM industry_quote LIMIT 5")
        columns = [description[0] for description in cursor.description]
        print(columns)
        for row in cursor.fetchall():
            print(row)

        print("\nChecking for BK codes in industry_quote:")
        cursor.execute("SELECT DISTINCT industry_code FROM industry_quote WHERE industry_code LIKE 'BK%' LIMIT 10")
        bk_ind_targets = cursor.fetchall()
        if bk_ind_targets:
            print("Found BK targets in industry_quote:", bk_ind_targets)
        else:
            print("No BK targets found in industry_quote.")
            
        # Check stock_industry table
        print("\nChecking stock_industry table:")
        cursor.execute("SELECT * FROM stock_industry LIMIT 5")
        columns = [description[0] for description in cursor.description]
        print(columns)
        for row in cursor.fetchall():
            print(row)
        
    else:
        print("Table 'daily_quote' not found.")

    conn.close()

if __name__ == "__main__":
    check_db()
