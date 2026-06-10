
import databaseutil
import qldef
import logutil
import logging
import sys

# Configure logging
# logutil.log might be a custom wrapper, so we just set level if possible or rely on default
# logutil.log.setLevel(logging.INFO)

if __name__ == "__main__":
    with open("export_debug.log", "w") as f:
        f.write("Starting export...\n")
    
    print("Starting export of EastMoney industry quotes (mapped to SW2 type)...")
    
    # Run export for ~10 years of data
    try:
        databaseutil.query_database(
            total_day_count=3650, # 10 years 
            per_query_day_count=3650, 
            skip_days=0, 
            daily_quote_type=qldef.daily_quote_type.sw2_industry_type
        )
        print("Export completed successfully.")
    except Exception as e:
        print(f"Export failed: {e}")
        import traceback
        traceback.print_exc()
