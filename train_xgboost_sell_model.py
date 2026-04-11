import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import warnings
from tqdm import tqdm

import project_paths

# 忽略 pandas 的 SettingWithCopyWarning
warnings.filterwarnings('ignore')

# 配置
INPUT_FILE = project_paths.get_root_cache_file("industry_heat_history.csv")
OUTPUT_FILE = project_paths.get_debug_cache_file("industry_parameters_xgboost_sell.csv")
MODEL_DIR = project_paths.ensure_dir(project_paths.get_models_dir())

# 训练参数
TRAIN_WINDOW = 90  # 训练窗口 (天)
PREDICT_HORIZON = 3  # 预测未来3天
TARGET_THRESHOLD = -0.03  # 跌幅 < -3% 视为正样本 (1) - 预测暴跌

def load_data():
    if not INPUT_FILE.exists():
        print(f"❌ 数据文件不存在: {INPUT_FILE}")
        return pd.DataFrame()
    
    df = pd.read_csv(INPUT_FILE)
    df['date'] = df['date'].astype(str)
    
    # 加载 HS300 数据 (如果存在)
    hs300_paths = project_paths.get_hs300_candidate_paths()
    
    df_hs300 = None
    for p in hs300_paths:
        if p.exists():
            print(f"✅ 加载 HS300 数据: {p}")
            df_hs300 = pd.read_csv(p)
            break
            
    if df_hs300 is not None:
        # 统一日期格式
        if 'trade_date' in df_hs300.columns:
             df_hs300 = df_hs300.rename(columns={'trade_date': 'date'})
        elif 'date' not in df_hs300.columns:
             for col in df_hs300.columns:
                 if 'date' in col.lower():
                     df_hs300 = df_hs300.rename(columns={col: 'date'})
                     break
        
        df_hs300['date'] = df_hs300['date'].astype(str)
        
        # 计算 HS300 特征
        df_hs300 = df_hs300.sort_values('date')
        df_hs300['hs300_close'] = df_hs300['close']
        df_hs300['hs300_ma20'] = df_hs300['hs300_close'].rolling(20).mean()
        df_hs300['hs300_trend'] = (df_hs300['hs300_close'] - df_hs300['hs300_ma20']) / df_hs300['hs300_ma20']
        df_hs300['hs300_daily_return'] = df_hs300['hs300_close'].pct_change()
        df_hs300['hs300_volatility'] = df_hs300['hs300_daily_return'].rolling(5).std()
        df_hs300['hs300_roc_5'] = df_hs300['hs300_close'].pct_change(5)
        
        hs300_features = df_hs300[['date', 'hs300_trend', 'hs300_volatility', 'hs300_roc_5']]
        df = pd.merge(df, hs300_features, on='date', how='left')
        
        df['hs300_trend'] = df['hs300_trend'].fillna(0)
        df['hs300_volatility'] = df['hs300_volatility'].fillna(0)
        df['hs300_roc_5'] = df['hs300_roc_5'].fillna(0)
    else:
        print("⚠️ 未找到 HS300 数据，将跳过大盘特征")
        df['hs300_trend'] = 0
        df['hs300_volatility'] = 0
        df['hs300_roc_5'] = 0

    # 确保按日期排序
    df = df.sort_values(['board_name', 'date']).reset_index(drop=True)
    return df

def feature_engineering(df):
    """
    特征工程 - 针对卖出模型优化
    """
    # 1. 基础热度特征
    df['sig_trend'] = df.groupby('board_name')['sig_ratio'].diff()
    df['sig_ma5'] = df.groupby('board_name')['sig_ratio'].transform(lambda x: x.rolling(5).mean())
    
    # 2. 价格特征
    df['ma20'] = df.groupby('board_name')['close'].transform(lambda x: x.rolling(20).mean())
    df['price_trend'] = (df['close'] - df['ma20']) / df['ma20']
    df['roc_5'] = df.groupby('board_name')['close'].pct_change(5)
    
    # 3. 波动率特征
    df['daily_return'] = df.groupby('board_name')['close'].pct_change()
    df['volatility'] = df.groupby('board_name')['daily_return'].transform(lambda x: x.rolling(5).std())

    # 4. 卖出模型特有特征
    # (A) 加速度特征: 热度增长是否放缓？
    df['sig_trend_acceleration'] = df.groupby('board_name')['sig_trend'].diff()
    
    # (B) 乖离率极值: bias_60 (长期乖离率)
    df['ma60'] = df.groupby('board_name')['close'].transform(lambda x: x.rolling(60).mean())
    df['bias_60'] = (df['close'] - df['ma60']) / df['ma60']
    
    # (C) 高位滞涨: 热度高但价格不涨 (Heat High, Price Flat)
    # 简单构建: sig_ratio / (abs(roc_5) + 0.001) -> 如果 sig_ratio 很大但 roc_5 很小，值会很大
    # 或者: sig_ma5 * (1 - roc_5)
    # 这里我们用一个交互特征
    df['heat_price_divergence'] = df['sig_ma5'] - (df['roc_5'] * 100) # 热度高(e.g. 20) 但涨幅低(e.g. 0) -> 20; 热度高且涨幅高(e.g. 0.2) -> 0

    # 目标变量：未来3天累计收益率
    # shift(-3) 表示取未来第3天的收盘价 / 今天的收盘价 - 1
    # 注意：这里要按 board_name 分组 shift
    df['future_3d_return'] = df.groupby('board_name')['close'].transform(lambda x: x.shift(-PREDICT_HORIZON) / x - 1)
    
    # 标记正样本 (Crash): 未来3天跌幅超过 3%
    df['target'] = (df['future_3d_return'] < TARGET_THRESHOLD).astype(int)
    
    # 清洗数据
    feature_cols = [
        'sig_ratio', 'sig_trend', 'sig_ma5', 
        'price_trend', 'roc_5', 'volatility', 
        'hs300_trend', 'hs300_volatility', 'hs300_roc_5',
        'sig_trend_acceleration', 'bias_60', 'heat_price_divergence'
    ]
    df_clean = df.dropna(subset=feature_cols).copy()
    
    return df_clean, feature_cols

def train_and_predict(df, feature_cols):
    """
    滚动窗口训练与预测 (Sell Model)
    """
    dates = sorted(df['date'].unique())
    results = []
    
    # 从第 TRAIN_WINDOW 天开始预测
    start_idx = TRAIN_WINDOW
    
    print(f"🚀 开始滚动训练 Sell Model (窗口={TRAIN_WINDOW}天)...")
    
    for i in tqdm(range(start_idx, len(dates))):
        current_date = dates[i]
        
        # 定义训练集窗口: [current_date - PREDICT_HORIZON - TRAIN_WINDOW, current_date - PREDICT_HORIZON]
        # 必须确保训练集的 target 是已知的 (即回溯 3 天前的数据作为训练集终点)
        
        train_end_date_idx = i - PREDICT_HORIZON
        train_start_date_idx = train_end_date_idx - TRAIN_WINDOW
        
        if train_start_date_idx < 0:
            continue
            
        train_start_date = dates[train_start_date_idx]
        train_end_date = dates[train_end_date_idx]
        
        # 切分训练集
        mask_train = (df['date'] >= train_start_date) & (df['date'] <= train_end_date)
        df_train = df[mask_train]
        
        X_train = df_train[feature_cols]
        y_train = df_train['target']
        
        # 切分预测集 (当天)
        mask_predict = (df['date'] == current_date)
        df_predict = df[mask_predict]
        
        if df_train.empty or df_predict.empty:
            continue
            
        # 检查正样本比例
        pos_ratio = y_train.mean()
        if pos_ratio == 0 or pos_ratio == 1:
            # 样本极度不平衡，无法训练，默认给 0 (安全)
            probs = np.zeros(len(df_predict))
        else:
            scale_pos_weight = (1 - pos_ratio) / pos_ratio
            
            # 训练模型
            model = xgb.XGBClassifier(
                n_estimators=50,
                max_depth=3,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                scale_pos_weight=scale_pos_weight,
                eval_metric='logloss',
                n_jobs=1,
                random_state=42,
                verbosity=0
            )
            model.fit(X_train, y_train)
            
            # 预测
            X_test = df_predict[feature_cols]
            probs = model.predict_proba(X_test)[:, 1]  # 获取正类 (Crash) 的概率
        
        # 记录结果
        for idx, (row_idx, row) in enumerate(df_predict.iterrows()):
            board_name = row['board_name']
            prob_down = probs[idx]
            
            results.append({
                'date': current_date,
                'board_name': board_name,
                'prob_down': round(prob_down, 4)
            })
            
    return pd.DataFrame(results)

def main():
    # 1. 加载数据
    print("1️⃣ 加载数据...")
    df = load_data()
    if df.empty:
        return

    # 2. 特征工程
    print("2️⃣ 特征工程...")
    df_clean, feature_cols = feature_engineering(df)
    print(f"   特征列表: {feature_cols}")
    print(f"   样本数量: {len(df_clean)}")

    # 3. 滚动训练与预测
    print("3️⃣ 滚动训练与预测 (Sell Model)...")
    df_results = train_and_predict(df_clean, feature_cols)
    
    # 4. 保存结果
    if not df_results.empty:
        print(f"💾 保存 Sell Model 预测结果到 {OUTPUT_FILE}...")
        df_results.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        # 简单统计
        print("\n📉 预测风险分布:")
        print(df_results['prob_down'].describe())
        print("\n🚨 紧急逃顶 (Prob > 0.65) 占比: {:.2%}".format((df_results['prob_down'] > 0.65).mean()))
        print("⚠️ 预警减仓 (Prob > 0.5) 占比: {:.2%}".format((df_results['prob_down'] > 0.5).mean()))
        
        print("✅ 完成！")
    else:
        print("⚠️ 未生成任何预测结果")

if __name__ == "__main__":
    main()
