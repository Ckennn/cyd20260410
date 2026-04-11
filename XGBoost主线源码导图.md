# XGBoost 主线源码导图

本文档只整理 **当前已经接入主流程的 XGBoost 主线**，不讨论旧版静态阈值方案。

---

## 1. 一句话结论

当前仓库中，**XGBoost 已正式接入 Step 3 的行业板块分析**，作用是：

**根据行业热度与价格特征，动态调整板块买入阈值，进而改变 Step 3 生成的交易指令。**

它对 Step 4 / Step 5 的影响是：

- **间接影响**
- 因为回测读取的是 Step 3 生成的交易指令文件

---

## 2. 主线总图

```text
main.py
 ├─ Step 2: quantitativestrategy.start_executing_strategy()
 │    └─ 生成 trigger.csv
 │
 ├─ Step 2.5.1: analyze_industry_heat.main()
 │    └─ 生成 industry_heat_history.csv
 │
 ├─ Step 2.5.2: train_xgboost_threshold_model.main()
 │    └─ 生成 industry_parameters_xgboost.csv
 │
 ├─ Step 3: industryanalysis.start_industry_sector_analysis()
 │    └─ 读取 industry_parameters_xgboost.csv
 │       └─ 按 prob_up 动态调整 buy_param / sell_param
 │          └─ 生成 stocks_tobe_traded_YYYYMMDD.csv
 │
 ├─ Step 4: quantitativetrading.run_strategy()
 │    └─ 读取 Step 3 交易指令，做个股回测
 │
 └─ Step 5: quantitativedcindustrytrading.run_strategy()
      └─ 读取 Step 3 交易指令，做行业回测
```

---

## 3. 文件级职责图

## 3.1 `main.py`

职责：

- 串联 Step 2.5 和 Step 3
- 在 `target_step == 0` 或 `target_step == 3` 时执行：
  - `analyze_industry_heat.main()`
  - `train_xgboost_threshold_model.main()`
  - `industryanalysis.start_industry_sector_analysis()`

作用：

- 是 XGBoost 主线真正的调度入口

---

## 3.2 `analyze_industry_heat.py`

职责：

- 读取所有 `results_zh_*_trigger.csv`
- 统计每天、每个行业的：
  - `sig_count`
  - `sig_ratio`
- 读取行业指数行情
- 合并 `close`、`pct_change`
- 输出：
  - `cache_files/industry_heat_history.csv`

### 关键函数

- `load_trigger_data()`
- `load_industry_params()`
- `load_all_industry_quotes()`
- `main()`

### 输入

- `cache_files/debug/quantitativeResultsOfStocks/results_zh_*_trigger.csv`
- `cache_files/debug/industry_parameters_model2.csv`
- `cache_files/debug/market_quotation_1d/zh_BK*_1d_ind.csv`

### 输出

- `cache_files/industry_heat_history.csv`

---

## 3.3 `train_xgboost_threshold_model.py`

职责：

- 读取 `industry_heat_history.csv`
- 做特征工程
- 用滚动窗口训练 XGBoost 分类器
- 预测每个行业、每个日期的上涨概率 `prob_up`
- 生成动态阈值表

### 关键函数

- `load_data()`
- `feature_engineering(df)`
- `train_and_predict(df, feature_cols)`
- `main()`

### 当前特征

- `sig_ratio`
- `sig_trend`
- `sig_ma5`
- `price_trend`
- `roc_5`
- `volatility`

### 当前标签

- 未来 3 天累计涨幅是否 > 2%

### 当前输出文件

- `cache_files/debug/industry_parameters_xgboost.csv`

### 输出字段

- `date`
- `board_name`
- `prob_up`
- `buy_threshold_ratio`
- `sell_threshold_ratio`

---

## 3.4 `qloption.py`

职责：

- 提供动态阈值文件读取门面

### 关键函数

- `get_industry_params_df2()`：读取基础静态参数
- `get_industry_dynamic_params_df()`：读取动态阈值参数

### 真实优先级

`get_industry_dynamic_params_df()` 当前优先级是：

1. `industry_parameters_xgboost.csv`
2. `industry_parameters_dynamic.csv`

这说明：

- **XGBoost 文件是当前主线优先级最高的动态阈值来源**

---

## 3.5 `industryanalysis.py`

职责：

- 在 Step 3 中消费 XGBoost 输出
- 对每日行业参数进行动态覆盖
- 生成交易指令文件

### 关键接线点

- `start_industry_sector_analysis()`
- `qloption.database.get_industry_dynamic_params_df()`

### 实际消费方式

对于每个交易日：

1. 复制静态参数表 `industry_parameters_model2.csv`
2. 取出当日 `industry_parameters_xgboost.csv` 中对应 `date` 的记录
3. 建立映射：
   - `board_name -> prob_up`
   - `board_name -> buy_threshold_ratio`
   - `board_name -> sell_threshold_ratio`
4. 更新当天行业参数
5. 再跑行业板块分析，生成买卖指令

### 当前代码中的决策逻辑

| 条件 | 动作 |
|---|---|
| `prob_up < 0.45` | `buy_param = 999.0%`，禁止买入 |
| `prob_up > 0.70` | `buy_param = 5.0%`，激进买入 |
| `prob_up < 0.30` | `sell_param = 0.1/9999`，倾向强制清仓 |

### 当前输出

- `cache_files/debug/stocks_tobe_traded/stocks_tobe_traded_YYYYMMDD.csv`

---

## 3.6 `quantitativetrading.py`

职责：

- 读取 Step 3 的交易指令文件
- 做个股回测

与 XGBoost 的关系：

- **不直接读取 XGBoost 模型或概率文件**
- 但会读取被 XGBoost 改写后的 Step 3 交易指令

结论：

- Step 4 受 XGBoost **间接影响**

---

## 3.7 `quantitativedcindustrytrading.py`

职责：

- 读取 Step 3 的交易指令文件
- 做行业 / ETF 回测

与 XGBoost 的关系同 Step 4：

- **间接影响**

---

## 4. 输入输出文件图

```text
Step 2 输出
cache_files/debug/quantitativeResultsOfStocks/results_zh_{start}_{end}_trigger.csv
        ↓
analyze_industry_heat.py
        ↓
cache_files/industry_heat_history.csv
        ↓
train_xgboost_threshold_model.py
        ↓
cache_files/debug/industry_parameters_xgboost.csv
        ↓
industryanalysis.py
        ↓
cache_files/debug/stocks_tobe_traded/stocks_tobe_traded_YYYYMMDD.csv
        ↓
Step 4 / Step 5 回测
```

---

## 5. 阈值模型与卖出模型的区别

## 5.1 已接入主流程：阈值模型

文件：

- `train_xgboost_threshold_model.py`

状态：

- **已接入 `main.py`**
- **已被 `industryanalysis.py` 消费**

作用：

- 动态调整 Step 3 的买入阈值

---

## 5.2 尚未正式接入主流程：卖出模型

文件：

- `train_xgboost_sell_model.py`

状态：

- 可以独立运行
- 会输出：
  - `cache_files/debug/industry_parameters_xgboost_sell.csv`
- **但当前没有被 `main.py` 正式调用**
- **也没有被 Step 3 / Step 4 正式接入为主流程输入**

当前现状：

- `industryanalysis.py` 中的“紧急逃顶”主要还是用 `prob_up < 0.30` 近似代替
- 不是直接读取 `prob_down`

---

## 6. 当前 XGBoost 主线的成熟度判断

## 已落地部分

- 行业热度特征构造
- 滚动窗口训练
- 概率输出 `prob_up`
- Step 3 动态阈值接入
- 对回测输入的真实影响

## 尚不完善部分

- 模型本体未系统化保存为版本化工件
- `MODEL_DIR` 已创建，但当前阈值脚本没有稳定落地 `model.json` / `joblib` 工件
- 特征 schema / 元数据未单独持久化
- sell model 尚未接入主流程

因此当前更准确的定位是：

**已进入主流程的研究型工程主线，而非完全产品化的 ML 平台。**

---

## 7. 代码阅读顺序建议

如果要继续深入 XGBoost 主线，建议按下面顺序看：

1. `main.py`
2. `analyze_industry_heat.py`
3. `train_xgboost_threshold_model.py`
4. `qloption.py`
5. `industryanalysis.py`
6. `quantitativetrading.py`

---

## 8. 配套文档

- [项目真实运行手册](./项目真实运行手册.md)
- [README](./README.md)
