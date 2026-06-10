import pandas as pd
import numpy as np
from tqdm import tqdm
import xgboost as xgb
from sklearn.metrics import roc_auc_score, accuracy_score
import joblib
import warnings

import project_paths

# 忽略 pandas 的 SettingWithCopyWarning
warnings.filterwarnings('ignore')

# 配置
INPUT_FILE = project_paths.get_root_cache_file("industry_heat_history.csv")
OUTPUT_FILE = project_paths.get_debug_cache_file("industry_parameters_xgboost.csv")
MODEL_DIR = project_paths.ensure_dir(project_paths.get_models_dir())

# 训练参数
TRAIN_WINDOW = 90  # 训练窗口 (天)
PREDICT_HORIZON = 3  # 预测未来3天
TARGET_THRESHOLD = 0.02  # 涨幅 > 2% 视为正样本 (1)

def load_data():
    if not INPUT_FILE.exists():
        print(f"❌ 数据文件不存在: {INPUT_FILE}")
        return pd.DataFrame()
    
    df = pd.read_csv(INPUT_FILE)
    df['date'] = df['date'].astype(str)
    # 确保按日期排序
    df = df.sort_values(['board_name', 'date']).reset_index(drop=True)
    return df

def feature_engineering(df):
    """
    特征工程
    输入: 原始 DataFrame
    输出: 包含特征和标签的 DataFrame
    """
    print("🛠️ 开始特征工程...")
    
    # 1. 目标变量 (Y): 未来3天累计涨跌幅
    # 需要按 board_name 分组计算
    df['future_3d_return'] = df.groupby('board_name')['close'].shift(-PREDICT_HORIZON) / df['close'] - 1
    df['target'] = (df['future_3d_return'] > TARGET_THRESHOLD).astype(int)
    
    # 2. 特征构造 (X)
    
    # (1) 热度特征
    # sig_ratio 已经有了，不需要重新计算，但要确保它是数值型
    df['sig_ratio'] = pd.to_numeric(df['sig_ratio'], errors='coerce').fillna(0)
    
    # sig_trend: 环比变化 (今日 / 昨日 - 1)
    df['sig_ratio_prev'] = df.groupby('board_name')['sig_ratio'].shift(1)
    df['sig_trend'] = (df['sig_ratio'] - df['sig_ratio_prev']) / (df['sig_ratio_prev'] + 0.001) # 防止除零
    
    # sig_ma5: 5日热度均值 (平滑短期波动)
    df['sig_ma5'] = df.groupby('board_name')['sig_ratio'].transform(lambda x: x.rolling(5).mean())
    
    # (2) 价格趋势特征
    # price_trend: (收盘价 - MA20) / MA20
    df['ma20'] = df.groupby('board_name')['close'].transform(lambda x: x.rolling(20).mean())
    df['price_trend'] = (df['close'] - df['ma20']) / df['ma20']
    
    # roc_5: 5日涨跌幅
    df['close_prev5'] = df.groupby('board_name')['close'].shift(5)
    df['roc_5'] = (df['close'] - df['close_prev5']) / df['close_prev5']
    
    # (3) 波动率特征
    # volatility: 过去5日收益率的标准差
    df['daily_return'] = df.groupby('board_name')['close'].pct_change()
    df['volatility'] = df.groupby('board_name')['daily_return'].transform(lambda x: x.rolling(5).std())
    
    # 清洗数据：去除因 rolling 产生的 NaN
    # 注意：不要删除 future_3d_return 为 NaN 的行（那是我们要预测的最后几天），但在训练时要排除
    # 这里我们只删除特征为 NaN 的行
    feature_cols = ['sig_ratio', 'sig_trend', 'sig_ma5', 'price_trend', 'roc_5', 'volatility']
    df_clean = df.dropna(subset=feature_cols).copy()
    
    return df_clean, feature_cols

def train_and_predict(df, feature_cols):
    """
    滚动窗口训练与预测
    """
    dates = sorted(df['date'].unique())
    results = []
    
    # 从 20240101 开始预测
    start_predict_date = '20240101'
    try:
        start_idx = dates.index(start_predict_date)
    except ValueError:
        # 如果没有这一天，就从中间开始
        start_idx = max(TRAIN_WINDOW, int(len(dates) * 0.5))
    
    print(f"🔄 开始滚动训练 (XGBoost)，预测起点: {dates[start_idx]}...")
    
    # 为了提高速度，我们不每天重训，而是每 5 天重训一次模型，或者每天重训但只预测当天
    # 鉴于数据量不大，每天重训是可以接受的
    
    for i in tqdm(range(start_idx, len(dates))):
        current_date = dates[i]
        
        # 1. 定义训练集窗口: [T-TRAIN_WINDOW, T-PREDICT_HORIZON]
        # 注意：我们要预测 T 日，但 T 日的 target 是未知的（需要未来数据）
        # 所以训练集的 y 必须是已知的，即截止到 T-PREDICT_HORIZON 的数据
        
        train_end_date_idx = i - PREDICT_HORIZON
        train_start_date_idx = train_end_date_idx - TRAIN_WINDOW
        
        if train_start_date_idx < 0:
            continue
            
        train_start_date = dates[train_start_date_idx]
        train_end_date = dates[train_end_date_idx] # 包含这一天
        
        # 筛选训练数据
        mask_train = (df['date'] >= train_start_date) & (df['date'] <= train_end_date)
        df_train = df[mask_train]
        
        X_train = df_train[feature_cols]
        y_train = df_train['target']
        
        # 筛选预测数据 (当天)
        mask_predict = (df['date'] == current_date)
        df_predict = df[mask_predict]
        
        if df_train.empty or df_predict.empty:
            continue
            
        # 2. 训练 XGBoost 模型
        # 参数微调：max_depth 小一点防止过拟合，scale_pos_weight 处理样本不平衡
        pos_ratio = y_train.mean()
        scale_pos_weight = (1 - pos_ratio) / pos_ratio if pos_ratio > 0 else 1
        
        model = xgb.XGBClassifier(
            n_estimators=50,      # 树的数量
            max_depth=3,          # 树深
            learning_rate=0.1,    # 学习率
            subsample=0.8,        # 样本采样
            colsample_bytree=0.8, # 特征采样
            scale_pos_weight=scale_pos_weight, # 样本平衡
            eval_metric='logloss',
            n_jobs=1,             # 并行数 (外层已有循环，内层单核)
            random_state=42,
            verbosity=0
        )
        
        model.fit(X_train, y_train)
        
        # 3. 预测
        X_test = df_predict[feature_cols]
        probs = model.predict_proba(X_test)[:, 1] # 获取正类 (上涨) 的概率
        
        # 4. 生成动态阈值
        # 遍历该日的所有行业
        for idx, (row_idx, row) in enumerate(df_predict.iterrows()):
            board_name = row['board_name']
            prob_up = probs[idx]
            sig_ratio = row['sig_ratio']
            
            # --- 决策逻辑 ---
            
            # 默认值
            buy_threshold = 16.0
            sell_threshold = 23.0
            
            if prob_up > 0.7:
                # 进攻模式：概率高，降低门槛
                # 取历史分位数的 10% 或更低，甚至直接用当前值（如果是上升趋势）
                # 这里简单设定为：如果当前热度 > 5% 且模型看好，就设为当前热度稍低一点，确保能买入
                # 或者：buy_threshold = 5.0 (激进)
                buy_threshold = 5.0 
            elif prob_up < 0.4:
                # 防守模式：概率低，大幅提高门槛 (变相冷却)
                buy_threshold = 999.0 # 禁止买入
            else:
                # 中性模式：维持基准 (如 15-20%)
                buy_threshold = 15.0
                
            results.append({
                'date': current_date,
                'board_name': board_name,
                'prob_up': round(prob_up, 4),
                'buy_threshold_ratio': buy_threshold,
                'sell_threshold_ratio': sell_threshold # 卖出阈值暂时固定或另行预测
            })
            
    return pd.DataFrame(results)

def main():
    # 1. 加载数据
    df = load_data()
    if df.empty:
        return
        
    # 2. 特征工程
    df_features, feature_cols = feature_engineering(df)
    
    # 3. 训练与预测
    df_results = train_and_predict(df_features, feature_cols)
    
    # 4. 保存结果
    if not df_results.empty:
        print(f"💾 保存 XGBoost 动态阈值表到 {OUTPUT_FILE}...")
        df_results.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        # 简单统计
        print("\n📈 预测结果分布:")
        print(df_results['prob_up'].describe())
        print("\n🔥 进攻模式 (Prob > 0.7) 占比: {:.2%}".format((df_results['prob_up'] > 0.7).mean()))
        print("❄️ 防守模式 (Prob < 0.4) 占比: {:.2%}".format((df_results['prob_up'] < 0.4).mean()))
        
        print("✅ 完成！")
    else:
        print("⚠️ 未生成任何预测结果")

if __name__ == "__main__":
    main()
