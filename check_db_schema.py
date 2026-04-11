import sqlite3
from project_paths import get_db_path

DB_PATH = str(get_db_path())
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
print("industry_quote indices:")
cursor.execute("PRAGMA index_list(industry_quote)")
indices = cursor.fetchall()
for idx in indices:
    print(idx)
    idx_name = idx[1]
    cursor.execute(f"PRAGMA index_info({idx_name})")
    print(f"  Info for {idx_name}: {cursor.fetchall()}")

conn.close()
