
import sqlite3
import os
from project_paths import get_db_path

db_path = str(get_db_path())
print(f"Checking DB at: {db_path}")

if not os.path.exists(db_path):
    print("Error: Database file not found!")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables found:")
    for table in tables:
        print(f" - {table[0]}")
    conn.close()
    print("Database verification successful.")
except Exception as e:
    print(f"Error accessing database: {e}")
