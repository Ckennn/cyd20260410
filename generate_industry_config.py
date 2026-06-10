
"""
工具脚本：从 Excel 策略文件生成 industry_parameters_model2.csv
功能：
1. 从 "C模型策略-1016.xlsx" 的 "板块交易参数" Sheet 读取基础配置
2. 提取 board_name, stock_count_2024, buy_param, sell_param
3. 如果目标 CSV 已存在，保留其动态生成的年份统计列 (stock_count_XXXX)
4. 将合并后的数据写入 cache_files/debug/industry_parameters_model2.csv
"""
import pandas as pd
import os
import sys

# 添加项目根目录到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置路径
# EXCEL_PATH = r'd:\Codepython\newpy\new\C模型策略-1016.xlsx'
# CSV_PATH = r'd:\Codepython\newpy\new\cache_files\debug\industry_parameters_model2.csv'
# Use relative paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, 'C模型策略-1016.xlsx')
CSV_PATH = os.path.join(BASE_DIR, 'cache_files', 'debug', 'industry_parameters_model2.csv')
SHEET_NAME = '板块交易参数'

def generate_config():
    print(f"🚀 开始处理...")
    print(f"📄 Excel 源文件: {EXCEL_PATH}")
    print(f"💾 CSV 目标文件: {CSV_PATH}")

    # 1. 读取 Excel
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ 错误: Excel 文件不存在!")
        return

    try:
        # 读取指定 Sheet，跳过第一行表头说明（根据之前的检查，第一行是中文说明，第二行才是列名）
        # 修正：之前的 raw dump 显示第一行是 "序号", "板块" 等列名
        # 让我们再确认一下之前的 dump:
        # 0: 序号, 1: 板块, 2: 板块个股数量, 3: 买入参数(数), 4: 买入参数(%), 5: 卖出参数, 6: 卖出参数(备注?)
        df_excel = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
        print(f"✅ 成功读取 Excel, 行数: {len(df_excel)}")
    except Exception as e:
        print(f"❌ 读取 Excel 失败: {e}")
        return

    # 2. 提取和重命名列
    # Excel 列名可能包含空格或换行，我们需要根据位置或模糊匹配来提取
    # 假设列顺序：序号(0), 板块(1), 板块个股数量(2), 买入参数-数(3), 买入参数-%(4), 卖出参数(5)
    
    try:
        # 创建新的 DataFrame
        df_new = pd.DataFrame()
        
        # 提取列 (使用 iloc 按位置提取更稳健，因为列名可能有变动)
        # 注意：pandas 读取时会自动处理表头，我们假设第一行是表头
        
        # 查找列索引
        cols = df_excel.columns
        col_board = [c for c in cols if '板块' in str(c) and '数量' not in str(c)][0] # 板块
        col_count = [c for c in cols if '数量' in str(c)][0] # 板块个股数量
        
        # 买入参数有两列，我们需要百分比那一列（通常是第二列买入参数）
        # 通过检查该列数据是否包含 '%' 来确定
        buy_cols = [c for c in cols if '买入参数' in str(c)]
        col_buy = None
        for c in buy_cols:
            sample = df_excel[c].iloc[0]
            if isinstance(sample, str) and '%' in sample:
                col_buy = c
                break
        # 如果没找到带%的，尝试取第二列
        if col_buy is None and len(buy_cols) >= 2:
            col_buy = buy_cols[1]
            
        # 卖出参数
        sell_cols = [c for c in cols if '卖出参数' in str(c)]
        col_sell = sell_cols[0] if sell_cols else None

        print(f"🔍 映射列名:")
        print(f"   - board_name       <- {col_board}")
        print(f"   - stock_count_2024 <- {col_count}")
        print(f"   - buy_param        <- {col_buy}")
        print(f"   - sell_param       <- {col_sell}")

        if not all([col_board, col_count, col_buy, col_sell]):
            print("❌ 错误: 无法找到所有必要的列")
            return

        df_new['board_name'] = df_excel[col_board]
        df_new['stock_count_2024'] = df_excel[col_count]
        df_new['buy_param'] = df_excel[col_buy]
        df_new['sell_param'] = df_excel[col_sell]
        
        # 清理数据：删除空行
        df_new = df_new.dropna(subset=['board_name'])
        
        # 填充 NaN
        # df_new = df_new.fillna('') 

        print(f"✅ 提取数据完成, 有效行数: {len(df_new)}")
        
    except Exception as e:
        print(f"❌ 数据提取失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. 合并旧数据的动态列
    if os.path.exists(CSV_PATH):
        try:
            print("🔄 检测到现有 CSV，尝试保留动态年份列...")
            df_old = pd.read_csv(CSV_PATH)
            
            # 找出所有 stock_count_XXXX 列 (除了 2024)
            dynamic_cols = [c for c in df_old.columns if c.startswith('stock_count_') and c != 'stock_count_2024']
            
            if dynamic_cols:
                print(f"   发现动态列: {dynamic_cols}")
                # 将动态列合并到新数据中 (基于 board_name)
                # 这是一个左连接：以新配置的 board_name 为准
                df_merged = pd.merge(df_new, df_old[['board_name'] + dynamic_cols], on='board_name', how='left')
                df_new = df_merged
            else:
                print("   未发现额外的动态年份列")
                
        except Exception as e:
            print(f"⚠️ 读取旧 CSV 失败 (将覆盖): {e}")

    # 4. 写入 CSV
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        
        df_new.to_csv(CSV_PATH, index=False, encoding='utf-8-sig') # 使用 utf-8-sig 兼容 Excel 打开
        print(f"✅ 成功写入文件: {CSV_PATH}")
        print("🎉 完成!")
        
    except Exception as e:
        print(f"❌ 写入 CSV 失败: {e}")

if __name__ == '__main__':
    generate_config()
