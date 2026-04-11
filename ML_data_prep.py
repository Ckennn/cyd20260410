import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

def generate_ml_dataset(df_result, df_board_market, df_benchmark):
    """
    从量化结果和市场数据中生成机器学习特征 X 和标签 y
    
    参数:
    df_result: Step 2 产生的个股策略结果 DataFrame (包含 date, board_name, trigger 等)
    df_board_market: 板块的真实日线行情 DataFrame (包含 date, board_name, close 等)
    df_benchmark: 沪深300日线行情 DataFrame (包含 date, close)
    """
    print("🚀 开始构建机器学习特征与标签...")

    # ==========================================
    # 步骤 1: 构建输入特征 X (板块维度的共振指标)
    # ==========================================
    # 1.1 统计每天每个板块触发买入信号的股票数量
    # 假设 df_result 中 trigger == True 代表触发信号
    #trigger_df = df_result[df_result['trigger'] == True]
    # 1. 过滤掉早期数据中板块名称为空的行（因为我们要按板块统计）
    trigger_df = df_result.dropna(subset=['board_name'])
    
    # 按日期和板块分组，计算触发数量
    #feature_df = trigger_df.groupby(['date', 'board_name']).size().reset_index(name='trigger_count')
    # 2. 直接按日期和板块分组，计算触发数量 (即计算该板块当天有几行数据)
    feature_df = trigger_df.groupby(['date', 'board_name']).size().reset_index(name='trigger_count')
    
    # 1.2 计算触发数量的动量 (比昨天增加了多少)
    # 确保按日期排序
    feature_df = feature_df.sort_values(by=['board_name', 'date'])
    feature_df['trigger_count_yesterday'] = feature_df.groupby('board_name')['trigger_count'].shift(1)
    feature_df['trigger_momentum'] = feature_df['trigger_count'] - feature_df['trigger_count_yesterday']
    
    # 1.3 假设我们有一个包含了板块总股数的字典或列 (这里用常数代替演示，您可以替换为真实总数)
    # feature_df['board_total_stocks'] = 获取对应板块的总股数
    # feature_df['trigger_ratio'] = feature_df['trigger_count'] / feature_df['board_total_stocks']
    
    # 为了演示，我们暂时用 trigger_count 和 trigger_momentum 作为核心特征
    feature_df.dropna(inplace=True) 

    # ==========================================
    # 步骤 2: 构建目标标签 y (T+1 的超额真实胜负)
    # ==========================================
    # 2.1 计算板块的 T+1 收益率
    df_board_market = df_board_market.sort_values(by=['board_name', 'date'])
    # shift(-1) 是量化中最关键的一步：把明天的收盘价挪到今天这行，用于计算“明天”的收益
    df_board_market['next_day_close'] = df_board_market.groupby('board_name')['close'].shift(-1)
    df_board_market['board_return_t1'] = (df_board_market['next_day_close'] - df_board_market['close']) / df_board_market['close']
    
    # 2.2 计算沪深300的 T+1 收益率
    df_benchmark = df_benchmark.sort_values(by='date')
    df_benchmark['next_day_close'] = df_benchmark['close'].shift(-1)
    df_benchmark['benchmark_return_t1'] = (df_benchmark['next_day_close'] - df_benchmark['close']) / df_benchmark['close']
    
    # ==========================================
    # 步骤 3: 数据合并与打标签
    # ==========================================
    print("🔧 正在清洗并统一合并主键 (Date & Board Name)...")

    # 1. 统一日期格式：全部强制转换为标准的 pandas datetime 格式
    feature_df['date'] = pd.to_datetime(feature_df['date'].astype(str).str.replace('-', ''))
    df_board_market['date'] = pd.to_datetime(df_board_market['date'].astype(str).str.replace('-', ''))
    df_benchmark['date'] = pd.to_datetime(df_benchmark['date'].astype(str).str.replace('-', ''))

    # 2. 统一板块名称：这是一个临时的映射字典，把中文名翻译成 BK 代码
    # ⚠️ 您需要根据您实际下载了哪些 BK 文件，把对应的中文名加到这个字典里
    name_to_bk_map = {
        "生物制品": "BK0538",
        "半导体": "BK1036",  # 假设半导体是这个代码，请核实
        "航天航空": "BK0447"
        # ... 在这里继续补充您 trigger.csv 里出现的板块和对应的 BK 代码 ...
    }
    
    # 翻译 feature_df 里的中文板块名
    feature_df['board_name_mapped'] = feature_df['board_name'].map(name_to_bk_map)
    
    # 过滤掉没有翻译成功的板块 (比如有些板块您没下载 BK 数据)
    feature_df = feature_df.dropna(subset=['board_name_mapped'])

    # --- 开始合并 ---
    # 注意：现在 feature_df 用 'board_name_mapped' 去对接 df_board_market 的 'board_name'
    dataset = pd.merge(
        feature_df, 
        df_board_market[['date', 'board_name', 'board_return_t1']], 
        left_on=['date', 'board_name_mapped'], 
        right_on=['date', 'board_name'], 
        how='inner'
    )
    
    # 再合并大盘数据
    dataset = pd.merge(dataset, df_benchmark[['date', 'benchmark_return_t1']], on='date', how='inner')
    
    # 检查如果合并后还是空，赶紧抛出警告而不是报错
    if dataset.empty:
        print("❌ 严重警告：合并后数据量为 0！请检查日期范围是否有交集，或者板块映射字典是否正确！")
        # 您可以在这里打印一下特征表的日期和板块看看长什么样
        print("特征表可用日期:", feature_df['date'].unique()[:3])
        print("特征表可用板块:", feature_df['board_name_mapped'].unique()[:3])
        print("行情表可用板块:", df_board_market['board_name'].unique()[:3])
        return np.array([]), np.array([]), dataset
    
    # 核心逻辑：打标签 (Labeling)
    # 条件：1. 板块 T+1 收益 > 0 (绝对赚钱)  且  2. 板块 T+1 收益 > 大盘 T+1 收益 (相对跑赢)
    dataset['label'] = np.where(
        (dataset['board_return_t1'] > 0) & (dataset['board_return_t1'] > dataset['benchmark_return_t1']), 
        1,  # 胜
        0   # 败
    )
    
    # 清理缺失值 (最后一天没有 T+1 数据，必须丢弃)
    dataset.dropna(inplace=True)

    # ==========================================
    # 步骤 4: 提取 X 和 y，并进行标准化 (MLP 必备)
    # ==========================================
    # 定义我们的特征列名
    feature_cols = ['trigger_count', 'trigger_momentum'] # 如果有 trigger_ratio 也要加进来
    
    X_raw = dataset[feature_cols].values
    y = dataset['label'].values
    
    # MLP 必须的一步：特征标准化处理 (均值为0，方差为1)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)
    
    print(f"✅ 数据集构建完成！总样本数: {len(dataset)}，特征维度: {X_scaled.shape[1]}")
    print(f"📊 正样本(胜)比例: {(y.sum() / len(y)) * 100:.2f}%")
    
    # 返回 标准化后的特征 X，标签 y，以及用于查验的完整 DataFrame
    return X_scaled, y, dataset

# --- 使用示例 ---
# 假设您已经加载了数据：
# X, y, full_df = generate_ml_dataset(df_result, df_board_market, df_benchmark)
# 
# 接下来您就可以直接把 X, y 喂给 PyTorch, TensorFlow 或者 sklearn 的 MLPClassifier 了：
# from sklearn.neural_network import MLPClassifier
# clf = MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=500)
# clf.fit(X_train, y_train)

