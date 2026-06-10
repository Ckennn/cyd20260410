import os
import shutil
import qldef

def fix_board_target_file():
    # Use the directory where we found the file: cache_files/debug/market_quotation_1d
    # qldef.market_quotation_directory should point to it
    cache_dir = qldef.market_quotation_directory
    
    dc_file = os.path.join(cache_dir, "dc_board_target.csv")
    target_file = os.path.join(cache_dir, "zh_0_board_target.csv")
    
    if os.path.exists(dc_file):
        print(f"Found source file: {dc_file}")
        shutil.copy2(dc_file, target_file)
        print(f"✅ Successfully created {target_file}")
    else:
        print(f"❌ Source file not found: {dc_file}")

if __name__ == '__main__':
    fix_board_target_file()
