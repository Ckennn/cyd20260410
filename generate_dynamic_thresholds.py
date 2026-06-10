import pandas as pd
import numpy as np
from tqdm import tqdm

import project_paths

# 配置
INPUT_FILE = project_paths.get_root_cache_file("industry_heat_history.csv")
OUTPUT_FILE = project_paths.get_debug_cache_file("industry_parameters_dynamic.csv")
WINDOW_DAYS = 60  # 3个月约60个交易日
PREDICT_DAYS = 3  # 预测未来3天
MIN_SAMPLES = 10  # 最小样本数

def load_data():
    if not INPUT_FILE.exists():
        print(f"❌ 数据文件不存在: {INPUT_FILE}")
        return pd.DataFrame()
    
    df = pd.read_csv(INPUT_FILE)
    df['date'] = df['date'].astype(str)
    return df

def calculate_dynamic_thresholds(df):
    """
    计算动态阈值
    逻辑：
    1. 遍历每一天 T (从第 WINDOW_DAYS 天开始)
    2. 取 T-WINDOW_DAYS 到 T-1 的历史数据
    3. 找到历史上行业指数在未来 PREDICT_DAYS 天上涨概率较高的 sig_ratio 区间
    4. 简化版逻辑：取历史上涨前的 sig_ratio 的分位数作为买入阈值
    """
    
    # 确保按日期排序
    df = df.sort_values(['board_name', 'date']).reset_index(drop=True)
    
    # 计算未来3天的收益率 (shift -3)
    # 注意：这里需要按 board_name 分组 shift
    df['future_3d_return'] = df.groupby('board_name')['close'].shift(-PREDICT_DAYS) / df['close'] - 1
    
    dates = sorted(df['date'].unique())
    boards = df['board_name'].unique()
    
    results = []
    
    print(f"🔄 开始滚动预测，共 {len(dates)} 个交易日，{len(boards)} 个行业...")
    
    # 只需要生成最近一年的数据，或者全部生成
    # 为了效率，我们从 20240101 开始
    start_idx = 0
    for i, d in enumerate(dates):
        if d >= '20240101':
            start_idx = i
            break
            
    for i in tqdm(range(start_idx, len(dates))):
        current_date = dates[i]
        # 定义训练窗口：[start_date, end_date)
        # 实际取索引 i-WINDOW_DAYS 到 i
        if i < WINDOW_DAYS:
            continue
            
        window_start_date = dates[i - WINDOW_DAYS]
        
        # 获取窗口内的历史数据
        # 筛选条件：日期在窗口内，且未来收益率已知 (非空)
        mask = (df['date'] >= window_start_date) & (df['date'] < current_date) & (df['future_3d_return'].notna())
        history_df = df[mask]
        
        if history_df.empty:
            continue
            
        # 对每个行业计算阈值
        for board in boards:
            board_history = history_df[history_df['board_name'] == board]
            
            if len(board_history) < MIN_SAMPLES:
                # 样本不足，使用默认值或上一次的值
                # 这里暂时跳过或给一个保守值
                continue
                
            # 策略：寻找“有效买入点”的 sig_ratio
            # 定义有效买入：未来3天收益 > 2% (0.02)
            success_cases = board_history[board_history['future_3d_return'] > 0.02]
            
            if len(success_cases) < 3:
                # 成功案例太少，保守处理
                buy_threshold = 16.0 # 默认值
            else:
                # 取成功案例的 sig_ratio 的 20% 分位数作为启动点
                # 意味着：只要热度达到这个水平，历史上大概率后面有涨幅
                buy_threshold = success_cases['sig_ratio'].quantile(0.20)
                
                # 约束：阈值不能太低，比如至少 5%
                buy_threshold = max(buy_threshold, 5.0)
                
            # 策略：寻找“卖出顶点”
            # 定义顶点：热度很高，但未来收益转负
            # 简单起见，取历史 sig_ratio 的 90% 分位数作为顶点预警
            sell_threshold = board_history['sig_ratio'].quantile(0.90)
            
            # 记录结果
            results.append({
                'date': current_date,
                'board_name': board,
                'buy_threshold_ratio': round(buy_threshold, 2),
                'sell_threshold_ratio': round(sell_threshold, 2)
            })
            
    return pd.DataFrame(results)

def main():
    df = load_data()
    if df.empty:
        return
        
    print("📊 数据加载完成，开始计算...")
    df_thresholds = calculate_dynamic_thresholds(df)
    
    if not df_thresholds.empty:
        print(f"💾 保存动态阈值表到 {OUTPUT_FILE}...")
        df_thresholds.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print("✅ 完成！")
        print(df_thresholds.tail())
    else:
        print("⚠️ 未生成任何阈值数据")

if __name__ == "__main__":
    main()
