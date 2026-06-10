import sqlite3
import os
import pandas as pd
from project_paths import get_db_path

DB_PATH = str(get_db_path())

print(f"Checking DB at: {DB_PATH}")

if not os.path.exists(DB_PATH):
    print("❌ Database file not found!")
else:
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Check for HS300 (399300 or 000300)
        print("\nChecking for HS300 (399300)...")
        try:
            df1 = pd.read_sql_query("SELECT count(*) as count FROM daily_quote WHERE stock_code='399300'", conn)
            print(f"Rows for 399300: {df1.iloc[0]['count']}")
        except Exception as e:
            print(f"Query for 399300 failed: {e}")
        
        print("\nChecking for HS300 (000300)...")
        try:
            df2 = pd.read_sql_query("SELECT count(*) as count FROM daily_quote WHERE stock_code='000300'", conn)
            print(f"Rows for 000300: {df2.iloc[0]['count']}")
        except Exception as e:
            print(f"Query for 000300 failed: {e}")

    except Exception as e:
        print(f"❌ Error querying DB: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
