import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

import project_paths

# 配置路径
CACHE_DIR = project_paths.get_debug_cache_dir()
TRIGGER_FILE_PATTERN = "quantitativeResultsOfStocks/results_zh_*_trigger.csv"
INDUSTRY_PARAMS_FILE = "industry_parameters_model2.csv"
INDUSTRY_QUOTE_DIR = "market_quotation_1d"
OUTPUT_FILE = project_paths.get_root_cache_file("industry_heat_history.csv")
SCATTER_OUTPUT_FILE = project_paths.get_root_cache_file("heat_vs_return_scatter.png")

# 设置字体以支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def load_trigger_data():
    """加载所有 trigger.csv 文件"""
    all_files = list(CACHE_DIR.glob(TRIGGER_FILE_PATTERN))
    if not all_files:
        print("❌ 未找到 trigger.csv 文件")
        return pd.DataFrame()
    
    print(f"🔍 找到 {len(all_files)} 个 trigger 文件，开始加载...")
    df_list = []
    for f in tqdm(all_files):
        try:
            # 读取 CSV，只取需要的列
            # 假设列名是 date, mtn, board_name, sm, signal_name
            # 注意：有些 trigger 文件可能没有 board_name 列，需要处理
            df = pd.read_csv(f)
            
            # 统一列名
            if 'board_name' not in df.columns:
                # 尝试从 mtn 解析 board_name (如果需要，目前暂不处理复杂解析，假设都有或后续补充)
                # 这里假设 board_name 是必须的，如果没有则可能是旧格式或数据缺失
                # 观察样例数据，board_name 有时为空字符串
                pass
            
            # 确保 date 列是 int 或 str 统一格式
            df['date'] = df['date'].astype(str)
            
            # 过滤掉 board_name 为空的行
            if 'board_name' in df.columns:
                df = df[df['board_name'].notna() & (df['board_name'] != '')]
            
            df_list.append(df)
        except Exception as e:
            print(f"⚠️ 读取文件 {f} 失败: {e}")
            
    if not df_list:
        return pd.DataFrame()
        
    df_all = pd.concat(df_list, ignore_index=True)
    print(f"✅ 加载完成，共 {len(df_all)} 条记录")
    return df_all

def load_industry_params():
    """加载行业参数表，获取 stock_count"""
    path = CACHE_DIR / INDUSTRY_PARAMS_FILE
    if not path.exists():
        print(f"❌ 未找到行业参数文件: {path}")
        return pd.DataFrame()
    
    df = pd.read_csv(path)
    # 只需要 board_name 和 stock_count_2024 (或类似的列)
    # 动态查找 stock_count 列
    count_col = next((c for c in df.columns if 'stock_count' in c), None)
    if not count_col:
        print("❌ 行业参数表中未找到 stock_count 列")
        return pd.DataFrame()
    
    return df[['board_name', count_col]].rename(columns={count_col: 'total_count'})

def get_industry_quote_change(date_str, board_name):
    """获取行业指数当日涨跌幅 (预留函数，批量处理更高效)"""
    pass

def load_all_industry_quotes():
    """加载所有行业指数日线数据，提取涨跌幅"""
    # 行业指数文件通常是 zh_BKxxxx_1d_ind.csv
    # 需要建立 board_name -> BK_code 的映射
    # 这里我们先尝试从 industry_parameters_model2.csv 或其他地方获取映射，
    # 或者直接遍历目录下所有 zh_BK*_1d_ind.csv，读取其中的 stock_name 作为 board_name
    
    quote_dir = CACHE_DIR / INDUSTRY_QUOTE_DIR
    all_files = list(quote_dir.glob("zh_BK*_1d_ind.csv"))
    
    print(f"🔍 开始加载行业指数数据，共 {len(all_files)} 个文件...")
    quote_list = []
    
    for f in tqdm(all_files):
        try:
            # 只读前几行获取 name，然后读 date, close, prev_close
            # 或者直接读所有
            df = pd.read_csv(f, usecols=['stock_name', 'date', 'close', 'prev_close'])
            if df.empty:
                continue
                
            # 统一 board_name
            board_name = df['stock_name'].iloc[0]
            
            # 计算涨跌幅
            df['pct_change'] = (df['close'] - df['prev_close']) / df['prev_close'] * 100
            df['board_name'] = board_name
            df['date'] = df['date'].astype(str)
            
            quote_list.append(df[['date', 'board_name', 'pct_change', 'close']])
        except Exception as e:
            # print(f"⚠️ 读取行业指数 {f} 失败: {e}")
            pass
            
    if not quote_list:
        return pd.DataFrame()
        
    df_quotes = pd.concat(quote_list, ignore_index=True)
    return df_quotes

def main():
    # 1. 加载触发信号数据
    df_triggers = load_trigger_data()
    if df_triggers.empty:
        return

    # 2. 统计每日每行业的触发数量
    # 按照 date, board_name 分组计数
    print("📊 正在统计行业热度...")
    df_heat = df_triggers.groupby(['date', 'board_name']).size().reset_index(name='sig_count')
    
    # 3. 加载行业总数，计算触发比例
    df_params = load_industry_params()
    if not df_params.empty:
        df_heat = pd.merge(df_heat, df_params, on='board_name', how='left')
        # 计算比例，处理 total_count 为空或0的情况
        df_heat['sig_ratio'] = df_heat.apply(
            lambda x: (x['sig_count'] / x['total_count'] * 100) if (pd.notnull(x['total_count']) and x['total_count'] > 0) else 0, 
            axis=1
        )
    else:
        print("⚠️ 缺少行业总数数据，无法计算 sig_ratio")
        df_heat['sig_ratio'] = 0

    # 4. 加载行业指数涨跌幅，合并数据
    df_quotes = load_all_industry_quotes()
    if not df_quotes.empty:
        print("🔗 合并行业行情数据...")
        df_heat = pd.merge(df_heat, df_quotes, on=['date', 'board_name'], how='left')
    else:
        print("⚠️ 缺少行业行情数据")
        df_heat['pct_change'] = 0
        df_heat['close'] = 0

    # 5. 保存结果
    print(f"💾 保存热度数据到 {OUTPUT_FILE}...")
    df_heat.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    
    # 6. 简单分析与可视化 (Top 5 热门行业的相关性)
    print("\n📈 简单分析 (Top 10 样本):")
    print(df_heat.sort_values('sig_ratio', ascending=False).head(10))
    
    # 绘制散点图：Sig Ratio vs Next Day Return (需计算次日涨跌)
    # 这里先简单画 Sig Ratio vs 当日涨跌
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df_heat, x='sig_ratio', y='pct_change', alpha=0.5)
    plt.title('行业热度 (Sig Ratio) vs 当日涨跌幅')
    plt.xlabel('触发比例 (%)')
    plt.ylabel('当日涨跌幅 (%)')
    plt.axhline(0, color='red', linestyle='--')
    plt.tight_layout()
    plt.savefig(SCATTER_OUTPUT_FILE)
    print(f"🖼️ 已保存散点图到 {SCATTER_OUTPUT_FILE}")

if __name__ == "__main__":
    main()
