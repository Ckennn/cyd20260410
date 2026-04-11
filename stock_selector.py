
import pandas as pd
import numpy as np
import os
import dfutil
import qldef
import logutil

class DragonStockSelector:
    """
    Selects 'Dragon 3/4/5' stocks (strong followers) from a list of candidates.
    
    Logic:
    1. Exclude Dragon 1/2: High cumulative gain (>20% in last 20 days).
    2. Select Followers: Just triggered Sig1 or Sig2.
    3. Volume/Price: Volume Ratio > 1.5.
    4. Volatility (Elasticity): Prefer stocks with higher historical volatility (more active).
    5. Trend Safety: Prefer stocks above MA60 (Bullish foundation).
    6. Sort: By Composite Score (Volume + Volatility).
    """
    
    def __init__(self):
        self.cache_dir = qldef.market_quotation_directory
        
    def select_dragon_stocks(self, date_int, candidate_df, top_n=3):
        """
        Filter and rank candidate stocks.
        
        Args:
            date_int (int): Current date (YYYYMMDD).
            candidate_df (pd.DataFrame): DataFrame with columns [mtn, board_name, signal_name].
            top_n (int): Number of stocks to return per sector.
        
        Returns:
            pd.DataFrame: Filtered and ranked DataFrame.
        """
        if candidate_df is None or candidate_df.empty:
            return candidate_df
            
        # Ensure signal column exists
        if qldef.signal_key not in candidate_df.columns:
            return candidate_df
            
        selected_rows = []
        
        # Group by sector (board_name)
        grouped = candidate_df.groupby(qldef.board_name_key)
        
        for board, group in grouped:
            candidates = []
            
            for index, row in group.iterrows():
                stock_code = row[qldef.mtn_key]
                signal = row[qldef.signal_key]
                
                # Filter 1: Only Sig1 (Bottom Breakout) or Sig2 (Uptrend)
                # Match by Chinese keywords as signal names are verbose
                sig_str = str(signal)
                if not (('底部上破' in sig_str) or ('上升趋势' in sig_str)):
                    continue
                    
                # Load Stock History
                df_stock = self._load_stock_data(stock_code)
                if df_stock is None or df_stock.empty:
                    continue
                
                # Filter data up to date_int
                try:
                    # Find index of date_int
                    curr_idx_list = df_stock.index[df_stock['date'] == date_int].tolist()
                    if not curr_idx_list:
                        # Log date mismatch for debugging (only once per day to avoid spam)
                        # if index == 0:
                        #     logutil.log.warning(f"Stock {stock_code}: Date {date_int} not found in history. Available: {df_stock['date'].head().tolist()}")
                        continue
                    curr_idx = curr_idx_list[0]
                    
                    # Check history for 20 days lookback
                    if curr_idx + 20 >= len(df_stock):
                        continue
                        
                    # --- Logic 1: Exclude Dragon 1/2 (High Gain) ---
                    close_t = df_stock.loc[curr_idx, 'close']
                    close_t_20 = df_stock.loc[curr_idx + 20, 'close']
                    
                    if close_t_20 == 0: continue
                    cum_gain = (close_t - close_t_20) / close_t_20
                    
                    if cum_gain > 0.20: # Exclude if already rose > 20%
                        # if index == 0: logutil.log.info(f"Stock {stock_code} rejected: Gain {cum_gain:.2%} > 20%")
                        continue
                        
                    # --- Logic 2: Volume Ratio > 1.5 ---
                    vol_t = df_stock.loc[curr_idx, 'volume']
                    mavol5_t = df_stock.loc[curr_idx, 'mavol(5)']
                    
                    if mavol5_t == 0: continue
                    vol_ratio = vol_t / mavol5_t
                    
                    if vol_ratio <= 1.5:
                        # if index == 0: logutil.log.info(f"Stock {stock_code} rejected: VolRatio {vol_ratio:.2f} <= 1.5")
                        continue

                    # --- Logic 3: Trend Safety (Price > MA60) ---
                    # Check if MA60 exists and is valid
                    if 'ma(60)' in df_stock.columns:
                        ma60_t = df_stock.loc[curr_idx, 'ma(60)']
                        # Allow slight dip below MA60 (e.g. 2%), but not deep bear
                        if pd.notna(ma60_t) and ma60_t > 0:
                            if close_t < ma60_t * 0.98: 
                                # if index == 0: logutil.log.info(f"Stock {stock_code} rejected: Price {close_t} < MA60 {ma60_t}")
                                continue 

                    # --- Logic 4: Elasticity (Volatility) ---
                    # Calculate std dev of daily returns over last 20 days
                    # Data is descending, so we take slice [curr_idx : curr_idx+20]
                    # We need to reverse it to calculate pct_change correctly if we use pandas, 
                    # or just calculate manually.
                    # Simplest: use 'close' series.
                    closes_20 = df_stock.loc[curr_idx:curr_idx+19, 'close'][::-1] # Ascending order
                    daily_returns = closes_20.pct_change().dropna()
                    volatility = daily_returns.std()
                    
                    # If volatility is too low (dead stock), maybe skip?
                    # Let's just use it for ranking.
                    
                    # Composite Score
                    # Weighted score: 60% Volume Ratio + 40% Volatility (normalized roughly)
                    # Volatility is usually 0.01 - 0.05. Volume ratio 1.5 - 5.0.
                    # Scale volatility by 100 to make it comparable (1.0 - 5.0).
                    score = (vol_ratio * 0.6) + (volatility * 100 * 0.4)
                    
                    candidates.append({
                        'row': row,
                        'vol_ratio': vol_ratio,
                        'volatility': volatility,
                        'score': score
                    })
                    
                except Exception as e:
                    logutil.log.error(f"Error processing stock {stock_code}: {e}")
                    continue
            
            # Sort candidates by Composite Score (Explosiveness)
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
            # Pick Top N
            top_candidates = candidates[:top_n]
            
            for c in top_candidates:
                row_copy = c['row'].copy()
                row_copy[qldef.signal_key] = str(row_copy[qldef.signal_key]) + "_DRAGON"
                selected_rows.append(row_copy)
        
        # Log stats
        if not selected_rows:
            # logutil.log.info(f"Dragon Selector: No stocks selected for {date_int}. (Candidates checked: {len(candidate_df)})")
            pass
            
        if not selected_rows:
            return pd.DataFrame(columns=candidate_df.columns)
            
        return pd.DataFrame(selected_rows)

    def _load_stock_data(self, stock_code):
        filename = f"zh_{stock_code}_1d_ind.csv"
        filepath = os.path.join(self.cache_dir, filename)
        if not os.path.exists(filepath):
            return None
        try:
            # Read necessary columns
            cols = ['date', 'close', 'volume', 'mavol(5)', 'ma(60)']
            df = pd.read_csv(filepath, usecols=lambda c: c in cols)
            # Ensure date is int
            if 'date' in df.columns:
                df['date'] = pd.to_numeric(df['date'], errors='coerce').fillna(0).astype(int)
            return df
        except Exception:
            return None
