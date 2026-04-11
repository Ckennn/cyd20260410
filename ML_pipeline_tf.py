import pandas as pd
import numpy as np
import os
import glob
from sklearn.metrics import accuracy_score, classification_report
from project_paths import get_market_quote_dir, get_quantitative_result_dir, get_market_quote_file

# 导入 TensorFlow 及其 Keras 核心组件
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam

# 导入我们之前写的特征提取模块 
from ML_data_prep import generate_ml_dataset 

def load_all_board_data(market_dir):
    """辅助函数：读取所有 BK 板块行情数据拼接成完整 DataFrame"""
    print("📥 正在加载所有板块行情数据...")
    all_files = glob.glob(os.path.join(market_dir, "*BK*.csv"))
    df_list = []
    for file in all_files:
        df = pd.read_csv(file)
        board_code = os.path.basename(file).split('_')[1] 
        df['board_name'] = board_code  
        df_list.append(df)
    
    if not df_list:
        raise ValueError(f"在 {market_dir} 下没有找到任何 BK 板块数据！")
    return pd.concat(df_list, ignore_index=True)


if __name__ == "__main__":
    # ==========================================
    # 步骤 1: 准备原材料 (请根据您的实际路径修改)
    # ==========================================
    print("--- 第一步：加载原材料 ---")
    path_result = get_quantitative_result_dir() / "results_zh_20240101_20240401_trigger.csv"
    df_result = pd.read_csv(path_result)
    
    path_market_dir = str(get_market_quote_dir())
    df_board_market = load_all_board_data(path_market_dir)
    
    path_benchmark = get_market_quote_file("zh_000300_1d_ind.csv")
    df_benchmark = pd.read_csv(path_benchmark)

    # ==========================================
    # 步骤 2: 调用模块，生成 X 和 y
    # ==========================================
    print("\n--- 第二步：特征工程与打标签 ---")
    
    # 🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟
    # 👇👇👇 [高亮标注]: 这里是调用函数获取机器学习特征和标签的核心行 👇👇👇
    
    X, y, dataset = generate_ml_dataset(df_result, df_board_market, df_benchmark)
    
    # 👆👆👆 [高亮标注结束] 👆👆👆
    # 🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟

    # ==========================================
    # 步骤 3: 划分训练集与测试集 (严格按时间切分，禁止随机打乱)
    # ==========================================
    print("\n--- 第三步：划分数据集 ---")
    split_index = int(len(X) * 0.8)
    
    X_train, X_test = X[:split_index], X[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]
    
    print(f"训练集大小: {len(X_train)} | 测试集大小: {len(X_test)}")
    print(f"输入特征维度: {X_train.shape[1]}")

    # ==========================================
    # 步骤 4: 构筑 TensorFlow MLP 神经网络框架
    # ==========================================
    print("\n--- 第四步：构建并训练 TensorFlow MLP 模型 ---")
    
    # 初始化 Sequential 序贯模型
    model = Sequential([
        # 第一层隐藏层: 32个神经元，使用 relu 激活函数，input_shape 自动匹配特征维度
        Dense(32, activation='relu', input_shape=(X_train.shape[1],)),
        
        # ⚠️ 量化必备: Dropout 层，每次训练随机丢弃 30% 的神经元，防止模型死记硬背(过拟合)
        Dropout(0.3),
        
        # 第二层隐藏层: 16个神经元
        Dense(16, activation='relu'),
        Dropout(0.2),
        
        # 输出层: 1个神经元。因为是二分类(胜/负)，必须使用 sigmoid 激活函数输出 0~1 的概率
        Dense(1, activation='sigmoid')
    ])
    
    # 编译模型: 设定优化器、损失函数和评估指标
    # 学习率设为 0.001 是一个比较稳妥的起点
    optimizer = Adam(learning_rate=0.001)
    model.compile(
        optimizer=optimizer,
        loss='binary_crossentropy', # 二分类标准损失函数
        metrics=['accuracy']
    )
    
    # 查看网络结构摘要
    model.summary()
    
    # 开始训练网络
    # epochs=50 表示看 50 遍数据；validation_data 可以在训练时实时监控测试集表现
    history = model.fit(
        X_train, y_train, 
        epochs=50, 
        batch_size=32, 
        validation_data=(X_test, y_test),
        verbose=1 # 显示训练进度条
    )
    
    # ==========================================
    # 步骤 5: 成绩单展示与预测
    # ==========================================
    print("\n--- 第五步：模型预测与评估 ---")
    # TensorFlow 输出的是 0~1 的概率值，我们需要根据 0.5 阈值将其转换为 0 或 1 的硬标签
    y_pred_prob = model.predict(X_test)
    y_pred_class = (y_pred_prob > 0.5).astype(int).flatten()
    
    print(f"🎯 测试集整体准确率 (Accuracy): {accuracy_score(y_test, y_pred_class) * 100:.2f}%")
    print("\n📊 详细分类报告:")
    print(classification_report(y_test, y_pred_class, target_names=['跑输大盘(0)', '跑赢大盘(1)']))
