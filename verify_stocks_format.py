
import sys
import os
import pandas as pd
import qldef
import dfutil

print(f"Directory: {qldef.stocks_tobe_traded_directory}")
if os.path.exists(qldef.stocks_tobe_traded_directory):
    files = os.listdir(qldef.stocks_tobe_traded_directory)
    print(f"Files found: {len(files)}")
    if files:
        file_path = os.path.join(qldef.stocks_tobe_traded_directory, files[0])
        print(f"Reading file: {file_path}")
        df = pd.read_csv(file_path)
        print("Columns:", df.columns.tolist())
        print("First 5 rows:")
        print(df.head())
        
        # Check for industry-only rows
        if 'mtn' in df.columns: # mtn seems to be stock code
             # Check if there are rows where mtn is empty but board_name is not
             if 'board_name' in df.columns:
                 industry_rows = df[df['mtn'].isna() & df['board_name'].notna()]
                 print(f"Industry-only rows: {len(industry_rows)}")
                 if not industry_rows.empty:
                     print(industry_rows.head())
else:
    print("Directory does not exist")
