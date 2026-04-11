
import sys
import os
import pandas as pd
import qldef
import qloption
import dfutil

# Add project root to sys.path
sys.path.append(os.getcwd())

def debug_columns():
    try:
        target_path = qldef.market_quotation_directory
        filename = qldef.dc_board_target_file_name
        print(f"Reading {filename} from {target_path}")
        
        file_path = os.path.join(target_path, filename)
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return

        df = qloption.database.read_file_csv(target_path, filename, None, None, None)
        
        if df is None:
            print("DataFrame is None")
            return
            
        print("Columns found:")
        print(df.columns.tolist())
        
        if 'board_type' in df.columns:
            print("'board_type' exists.")
        else:
            print("'board_type' NOT found.")
            # Print columns with repr to see hidden chars
            for col in df.columns:
                print(f"Column: '{col}' (len={len(col)})")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_columns()
