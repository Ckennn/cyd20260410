import pandas as pd
import os
from project_paths import get_market_quote_dir, get_project_root

# 配置
src_file = str(get_project_root() / "zh_000300_1d_ind.csv")
target_dir = str(get_market_quote_dir())
target_file = "zh_399300_hs300.csv"

# 检查源文件
if not os.path.exists(src_file):
    print(f"错误: 未找到源文件 {src_file}")
    # 尝试在当前目录找
    src_file = "zh_000300_1d_ind.csv"
    if not os.path.exists(src_file):
         print(f"错误: 当前目录也未找到 {src_file}")
         exit(1)

# 确保目标目录存在
os.makedirs(target_dir, exist_ok=True)
target_path = os.path.join(target_dir, target_file)

print(f"正在读取: {src_file}")
try:
    df = pd.read_csv(src_file)
    
    # 修正 inner_code 为系统使用的 399300
    df['inner_code'] = 399300
    
    # 保存到目标位置
    df.to_csv(target_path, index=False)
    print(f"成功保存至: {target_path}")
    print(f"数据行数: {len(df)}")
    
except Exception as e:
    print(f"处理失败: {e}")
