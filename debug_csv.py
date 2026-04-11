
import pandas as pd
from project_paths import get_debug_cache_file

try:
    csv_path = get_debug_cache_file('industry_parameters_model2.csv')
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='gbk')

    print("Columns:", df.columns)
    
    for index, row in df.iterrows():
        sell_param = str(row['sell_param'])
        if pd.isna(sell_param) or sell_param == 'nan':
            continue
            
        if '/' in sell_param:
            parts = sell_param.split('/')
            if len(parts) > 1:
                try:
                    float(parts[0])
                except ValueError:
                    print(f"Index {index}: sell_param='{sell_param}', part0='{parts[0]}'")
                    
except Exception as e:
    print(e)
