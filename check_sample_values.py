import sqlite3
from project_paths import get_db_path

DB_PATH = str(get_db_path())
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
print("Checking stock_industry for 000513...")
cursor.execute("SELECT * FROM stock_industry WHERE stock_code = '000513'")
print(cursor.fetchall())
conn.close()
