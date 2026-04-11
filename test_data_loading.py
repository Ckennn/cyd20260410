import sys
import os
import pandas as pd
import datetime
import logging

# Add current directory to path
sys.path.append(os.getcwd())

import qldef
import qloption
import dfutil
import logutil

# Set log level to DEBUG for console
logutil.log.logger.setLevel(logging.DEBUG)
for handler in logutil.log.logger.handlers:
    handler.setLevel(logging.DEBUG)

stock_code = "000001"
start_date = 20240101
end_date = 20240131

print(f"Testing data loading for {stock_code} from {start_date} to {end_date}")

# 1. Test qloption.database.get_code_daily_quote_data
target_path = qldef.market_quotation_directory
print(f"Target path: {target_path}")

try:
    stock_df = qloption.database.get_code_daily_quote_data(stock_code, start_date, end_date, target_path)
except Exception as e:
    print(f"get_code_daily_quote_data failed: {e}")
    stock_df = None

if stock_df is None:
    print("stock_df is None")
elif stock_df.empty:
    print("stock_df is empty")
else:
    print(f"stock_df loaded, shape: {stock_df.shape}")
    print(f"Index type: {type(stock_df.index)}")
    print(f"Index values: {stock_df.index}")
    print(f"Columns: {stock_df.columns}")

    # 2. Test quantitativetrading logic
    start_date_time = dfutil.datetime_by_date(start_date)
    end_date_time = dfutil.datetime_by_date(end_date)
    
    print(f"Backtest range: {start_date_time} to {end_date_time}")

    if not isinstance(stock_df.index, pd.DatetimeIndex):
        print("Index is not DatetimeIndex, converting...")
        try:
            stock_df.index = pd.to_datetime(stock_df.index)
            print("Converted index.")
        except Exception as e:
            print(f"Conversion failed: {e}")

    # Check range
    print(f"Data start: {stock_df.index[0]}")
    print(f"Data end: {stock_df.index[-1]}")
    
    if stock_df.index[-1] < pd.Timestamp(start_date_time) or stock_df.index[0] > pd.Timestamp(end_date_time):
        print(f"Time range mismatch: Data ({stock_df.index[0]} - {stock_df.index[-1]}) vs Backtest ({start_date_time} - {end_date_time})")
    else:
        print("Time range OK")

    # 3. Test Backtrader PandasData
    import backtrader as bt
    print("Testing Backtrader PandasData creation...")
    try:
        data = bt.feeds.PandasData(dataname=stock_df, fromdate=start_date_time, todate=end_date_time)
        print("PandasData created successfully.")
        
        # Test iterating data
        print("Testing data iteration...")
        cerebro = bt.Cerebro()
        cerebro.adddata(data)
        cerebro.run()
        print("Cerebro run finished.")
        
    except Exception as e:
        print(f"Backtrader failed: {e}")
