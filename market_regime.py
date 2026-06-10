# coding=utf-8
"""
market_regime.py
Market Regime Classification Module
Implements logic to classify market states into 5 categories:
PANIC, BEAR, RANGE, BULL, CRAZY_BULL
"""

import pandas as pd
import numpy as np
from enum import Enum
import qloption
import qldef
import dfutil
import talib

class MarketRegime(Enum):
    PANIC = 0       # 恐慌/危机
    BEAR = 1        # 熊市/阴跌
    RANGE = 2       # 震荡/平衡
    BULL = 3        # 牛市/趋势
    CRAZY_BULL = 4  # 疯牛/情绪

class MarketRegimeDetector:
    def __init__(self, index_code="sh000300"): # 默认使用沪深300
        self.index_code = index_code
        self.df_index = None
        self._load_data()

    def _load_data(self):
        """
        Load index data and calculate technical indicators
        """
        # Load index data (assuming daily data is available in cache)
        # Note: In real implementation, this might need to fetch from database or AKShare if not cached
        # For now, we assume the data follows standard format in market_quotation_1d
        
        # Try to load from standard cache path first
        # Construct path: cache_files/debug/market_quotation_1d/zh_sh000300_1d_ind.csv
        # file_path = f"{qldef.market_quotation_directory}/zh_{self.index_code}_1d_ind.csv"
        
        # Using database util to load index data is safer
        # Assuming index data is stored with 'zh' prefix and index code
        # Adjust 'target' parameter based on actual data storage
        
        # For simulation, we will try to load from qloption.database
        # If index data is missing, we might need to fetch it first.
        # Let's assume it exists for now as per project description.
        
        try:
            self.df_index = qloption.database.load_indicator_by_target(
                "zh", self.index_code, division=qldef.history_division_1d
            )
        except Exception as e:
            print(f"Error loading index data: {e}")
            self.df_index = pd.DataFrame()
            return

        if dfutil.empty(self.df_index):
            print(f"Warning: Index data for {self.index_code} is empty.")
            return

        # Ensure sorted by date
        self.df_index.sort_values('date', inplace=True)
        self.df_index.reset_index(drop=True, inplace=True)
        
        # Calculate Indicators
        close = self.df_index['close'].values
        high = self.df_index['high'].values
        low = self.df_index['low'].values
        volume = self.df_index['volume'].values

        # 1. Moving Averages
        self.df_index['ma5'] = talib.SMA(close, timeperiod=5)
        self.df_index['ma20'] = talib.SMA(close, timeperiod=20)
        self.df_index['ma60'] = talib.SMA(close, timeperiod=60)
        
        # 2. RSI (Relative Strength Index) - 14 days
        self.df_index['rsi'] = talib.RSI(close, timeperiod=14)
        
        # 3. ADX (Average Directional Movement Index) - 14 days
        self.df_index['adx'] = talib.ADX(high, low, close, timeperiod=14)
        
        # 4. ATR (Average True Range) - 14 days (Volatility)
        self.df_index['atr'] = talib.ATR(high, low, close, timeperiod=14)
        # Normalized ATR (ATR / Close)
        self.df_index['natr'] = self.df_index['atr'] / close * 100
        
        # 5. Slope of MA20 (Trend Strength)
        # Calculate slope over last 5 days (simple linear regression or just pct change)
        # Using percent change of MA20 over 5 days as a proxy for slope
        self.df_index['ma20_slope'] = self.df_index['ma20'].pct_change(periods=5) * 100
        
        # 6. Bias (Deviation from MA20)
        self.df_index['bias_ma20'] = (close - self.df_index['ma20']) / self.df_index['ma20'] * 100
        
        # 7. Volume Ratio (Volume / MA20_Volume)
        self.df_index['vol_ma20'] = talib.SMA(volume, timeperiod=20)
        self.df_index['vol_ratio'] = volume / self.df_index['vol_ma20']

    def get_regime(self, date_int):
        """
        Determine market regime for a specific date
        @param date_int: Integer date (YYYYMMDD)
        @return: MarketRegime Enum
        """
        if dfutil.empty(self.df_index):
            return MarketRegime.RANGE # Default fallback

        # Find row for the date
        row = self.df_index[self.df_index['date'] == date_int]
        if row.empty:
            # Fallback: find closest previous date
            row = self.df_index[self.df_index['date'] < date_int].iloc[-1:]
            if row.empty:
                return MarketRegime.RANGE
        
        # Extract metrics
        rsi = row['rsi'].values[0]
        adx = row['adx'].values[0]
        ma20_slope = row['ma20_slope'].values[0]
        bias_ma20 = row['bias_ma20'].values[0]
        vol_ratio = row['vol_ratio'].values[0]
        close = row['close'].values[0]
        ma20 = row['ma20'].values[0]
        ma60 = row['ma60'].values[0]
        
        # Logic Tree for Regime Classification
        
        # 1. CRAZY_BULL (疯牛)
        # 条件：极度超买 (RSI>80) OR 乖离率过大 (>10%) OR 均线陡峭且放量
        if (rsi > 80) or (bias_ma20 > 10) or (ma20_slope > 3 and vol_ratio > 1.5):
            return MarketRegime.CRAZY_BULL
            
        # 2. PANIC (恐慌)
        # 条件：跌破MA60 且 加速下跌 (Slope < -1.5) 且 乖离率负值过大 (<-5%)
        # 或者 ADX很高(趋势强) 且 是下跌趋势
        if (close < ma60) and (ma20_slope < -1.5):
            return MarketRegime.PANIC
            
        # 3. BULL (慢牛)
        # 条件：站上MA20 且 斜率向上 且 RSI健康 (50-75)
        if (close > ma20) and (ma20_slope > 0.2) and (rsi > 50):
            return MarketRegime.BULL
            
        # 4. BEAR (阴跌)
        # 条件：MA20斜率向下 且 位于均线下方
        if (ma20_slope < -0.2) and (close < ma20):
            return MarketRegime.BEAR
            
        # 5. RANGE (震荡)
        # 条件：其余情况，通常 ADX < 20 或 斜率走平
        return MarketRegime.RANGE

# Global instance
_detector = None

def get_market_regime(date_int, index_code="sh000300"):
    global _detector
    if _detector is None or _detector.index_code != index_code:
        _detector = MarketRegimeDetector(index_code)
    
    return _detector.get_regime(date_int)

if __name__ == "__main__":
    # Test block
    detector = MarketRegimeDetector()
    if not dfutil.empty(detector.df_index):
        # Test a few dates
        test_dates = [20240205, 20240520, 20240910, 20240930, 20241008, 20241101]
        for d in test_dates:
            regime = detector.get_regime(d)
            print(f"Date: {d}, Regime: {regime}")
