# Quantitative Trading System

一个基于 Python 的 A 股量化交易/回测项目，当前主线已经演进为：

**个股规则信号 → 行业热度特征 → XGBoost 动态阈值 → 行业交易指令 → 个股 / 行业回测**

本 README 以当前仓库实际代码为准，目标是提供一个更接近开源项目首页的快速入口。

---

## 1. 当前主线概览

### 1.1 当前最新版主线

当前实际主线是：

1. 从 SQLite 读取个股与行业数据
2. 生成个股信号（Step 2）
3. 聚合行业热度特征（Step 2.5.1）
4. 用 XGBoost 预测行业未来 3 日上涨概率（Step 2.5.2）
5. 在 Step 3 中动态调整行业买入阈值
6. 生成每日交易指令
7. 在 Step 4 / Step 5 做回测验证

### 1.2 当前核心模块

- `main.py`：总入口
- `databaseutil.py`：数据库查询 + 技术指标计算
- `quantitativestrategy.py`：个股信号生成
- `analyze_industry_heat.py`：行业热度特征构造
- `train_xgboost_threshold_model.py`：XGBoost 动态阈值模型
- `industryanalysis.py`：行业板块分析 + 交易指令生成
- `quantitativetrading.py`：个股回测
- `quantitativedcindustrytrading.py`：行业/ETF 回测
- `strategy_config.py`：个股卖出规则
- `market_regime.py`：市场状态识别

---

## 2. 快速开始

### 2.1 推荐环境

- Python 3.11
- Windows / PowerShell 优先

### 2.2 安装依赖

```powershell
pip install -U pip setuptools wheel
pip install -r requirements.txt
pip install xgboost scikit-learn seaborn openpyxl ta-lib
```

### 2.3 准备数据库

默认数据库路径：

- `data/stock_data.db`

注意：

- **数据库文件不纳入 Git / GitHub 仓库**
- 当前项目使用的是本地 SQLite 数据库
- 若要完整运行 Step 1~5，需要先准备好本地 DB

如果数据库不存在，可先初始化：

```powershell
python data_initializer.py
```

如果你已经有一份本地数据库副本，也可以直接通过环境变量指定路径：

```powershell
$env:STOCK_DB_PATH="D:\your\path\stock_data.db"
python main.py 1 20240101 20241130
```

### 2.4 跑完整主流程

```powershell
python main.py 0 20240101 20241130
```

这会执行：

1. Step 0：生成行业参数
2. Step 1：导出行情与指标
3. Step 2：生成个股 trigger
4. Step 2.5：训练 XGBoost 动态阈值
5. Step 3：生成交易指令
6. Step 4：个股回测
7. Step 5：行业回测

---

## 3. 常用命令速查

| 场景 | 命令 |
|---|---|
| 全流程运行 | `python main.py 0 20240101 20241130` |
| 只跑 Step 1 | `python main.py 1 20240101 20241130` |
| 只跑 Step 2 | `python main.py 2 20240101 20241130` |
| 跑 Step 2.5 + Step 3 | `python main.py 3 20240101 20241130` |
| 只跑 Step 4 | `python main.py 4 20240101 20241130` |
| 只跑 Step 5 | `python main.py 5 20240101 20241130` |
| 复用已有行情缓存重跑 | `python main.py 0 20240101 20241130 --skip-query` |

### 重要说明

- `Step 0` 每次运行 `main.py` 都会执行
- `python main.py 3 ...` **不会自动执行 Step 2**
- `python main.py 4 ...` / `5 ...` **不会自动执行 Step 3**

也就是说：

- 跑 Step 3 前，要先有 trigger 文件
- 跑 Step 4 / 5 前，要先有交易指令文件

---

## 4. 项目结构（按当前代码）

```text
.
├── main.py
├── data_initializer.py
├── databaseutil.py
├── quantitativestrategy.py
├── industryanalysis.py
├── quantitativetrading.py
├── quantitativedcindustrytrading.py
├── analyze_industry_heat.py
├── train_xgboost_threshold_model.py
├── train_xgboost_sell_model.py
├── strategy_config.py
├── market_regime.py
├── attribution_report.py
├── trade_list_analyzer.py
├── qlsignal0.py
├── qlsignal1.py
├── qlsignalcaochen.py
├── generate_industry_config.py
├── qldef.py
├── qloption.py
├── data/
│   └── stock_data.db
├── cache_files/
│   └── debug/
│       ├── market_quotation_1d/
│       ├── quantitativeResultsOfStocks/
│       └── stocks_tobe_traded/
├── 项目真实运行手册.md
└── XGBoost主线源码导图.md
```

---

## 5. 数据流与执行链路

```text
SQLite / AKShare
    ↓
Step 1: databaseutil.py
    ↓
指标化行情 CSV
    ↓
Step 2: quantitativestrategy.py
    ↓
trigger.csv
    ↓
Step 2.5.1: analyze_industry_heat.py
    ↓
industry_heat_history.csv
    ↓
Step 2.5.2: train_xgboost_threshold_model.py
    ↓
industry_parameters_xgboost.csv
    ↓
Step 3: industryanalysis.py
    ↓
stocks_tobe_traded_YYYYMMDD.csv
    ↓
Step 4 / Step 5 回测
```

---

## 6. 数据准备

默认数据库路径：

- `data/stock_data.db`

### 6.1 为什么数据库不放进 GitHub

当前项目使用的是本地 SQLite 数据库。对于这类量化项目，数据库通常：

- 文件较大
- 更新频繁
- 属于二进制文件
- 不适合普通 Git 版本管理

因此本仓库只管理：

- 源码
- 文档
- 配置与参数文件

不直接管理：

- `*.db`
- SQLite 运行时 sidecar 文件（如 `*.db-wal`, `*.db-shm`）

### 6.2 如何获得可运行数据库

你有两种方式：

#### 方式 A：自己初始化生成

```powershell
python data_initializer.py
```

适合：

- 首次搭环境
- 想从代码侧完整生成/更新本地数据库

#### 方式 B：使用已有数据库副本

如果团队内部已经有现成数据库，可以直接放在本机任意位置，然后通过环境变量指定：

```powershell
$env:STOCK_DB_PATH="D:\your\path\stock_data.db"
python main.py 1 20240101 20241130
```

在 WSL / Linux 下：

```bash
export STOCK_DB_PATH="/path/to/stock_data.db"
python main.py 1 20240101 20241130
```

如果数据库不存在，可先运行：

```powershell
python data_initializer.py
```

说明：

- `databaseutil.py` 默认从 `data/stock_data.db` 读取数据
- 根目录下若存在另一个 `stock_data.db`，它不是当前主流程默认路径
- 如果设置了 `STOCK_DB_PATH`，则优先使用该路径

Step 0 还依赖：

- `C模型策略-1016.xlsx`

它会被 `generate_industry_config.py` 读取，并生成：

- `cache_files/debug/industry_parameters_model2.csv`

---

## 7. 如何运行

## 7.1 全流程（推荐）

```powershell
python main.py 0 20240101 20241130
```

这会执行：

1. Step 0：生成行业静态参数
2. Step 1：从数据库导出行情 + 计算指标
3. Step 2：生成个股 trigger
4. Step 2.5：训练 XGBoost 动态阈值
5. Step 3：生成每日交易指令
6. Step 4：个股回测
7. Step 5：行业回测

## 7.2 分步运行

### Step 1：导出行情与指标

```powershell
python main.py 1 20240101 20241130
```

输出到：

- `cache_files/debug/market_quotation_1d/`

### Step 2：生成个股 trigger

```powershell
python main.py 2 20240101 20241130
```

输出到：

- `cache_files/debug/quantitativeResultsOfStocks/results_zh_20240101_20241130_trigger.csv`

### Step 3：XGBoost 动态阈值 + 行业分析

```powershell
python main.py 3 20240101 20241130
```

注意：

- 该命令会执行 Step 2.5 与 Step 3
- **不会自动执行 Step 2**
- 因此要求 Step 2 的 trigger 文件已存在

输出到：

- `cache_files/industry_heat_history.csv`
- `cache_files/debug/industry_parameters_xgboost.csv`
- `cache_files/debug/stocks_tobe_traded/stocks_tobe_traded_YYYYMMDD.csv`

### Step 4：个股回测

```powershell
python main.py 4 20240101 20241130
```

注意：

- **不会自动执行 Step 3**
- 需要已有 Step 3 的交易指令文件

输出到：

- `results_zh_{start}_{end}_summary.csv`
- `results_zh_{start}_{end}_trades.csv`
- `results_zh_{start}_{end}_chart.png`
- 多个卖出原因归因 CSV

位置：

- `cache_files/debug/quantitativeResultsOfStocks/`

### Step 5：行业 / ETF 回测

```powershell
python main.py 5 20240101 20241130
```

注意：

- **不会自动执行 Step 3**
- 需要已有 Step 3 的交易指令文件

当前稳定输出：

- `cache_files/debug/quantitativeResultsOfStocks/results_industry_{start}_{end}_chart.png`

---

## 8. 输出产物示例

当前仓库里已存在的真实输出样例包括：

### Step 2 输出样例

- `cache_files/debug/quantitativeResultsOfStocks/results_zh_20240101_20241130_trigger.csv`

### Step 3 输出样例

- `cache_files/debug/industry_parameters_xgboost.csv`
- `cache_files/debug/stocks_tobe_traded/stocks_tobe_traded_20241129.csv`

### Step 4 输出样例

- `cache_files/debug/quantitativeResultsOfStocks/results_zh_20240101_20241130_summary.csv`
- `cache_files/debug/quantitativeResultsOfStocks/results_zh_20240101_20241130_trades.csv`
- `cache_files/debug/quantitativeResultsOfStocks/results_zh_20240101_20241130_chart.png`

### Step 5 输出样例

- `cache_files/debug/quantitativeResultsOfStocks/results_industry_20240101_20241130_chart.png`

---

## 9. 当前 XGBoost 主线怎么接入

当前 XGBoost 主线的真实接法：

1. `quantitativestrategy.py` 生成 trigger.csv
2. `analyze_industry_heat.py` 生成 `industry_heat_history.csv`
3. `train_xgboost_threshold_model.py` 生成 `industry_parameters_xgboost.csv`
4. `qloption.py` 优先读取该 XGBoost 文件
5. `industryanalysis.py` 根据 `prob_up` 调整 `buy_param`
6. Step 3 输出新的交易指令
7. Step 4 / 5 间接受到影响

当前阈值逻辑：

- `prob_up < 0.45`：禁止买入
- `prob_up > 0.70`：激进买入
- `prob_up < 0.30`：倾向强制卖出/清仓

---

## 10. 当前已落地的风险控制

Step 4 个股回测已结合：

- `SectorCooldown`
- `DynamicStop`
- `SigSpecific`
- `Market Regime`
- 卖出原因归因报表

对应模块：

- `strategy_config.py`
- `market_regime.py`
- `trade_list_analyzer.py`
- `attribution_report.py`

---

## 11. FAQ

### Q1：XGBoost 是不是当前正式主线？

是。

当前 `main.py` 在 Step 2.5 中会直接调用：

- `analyze_industry_heat.py`
- `train_xgboost_threshold_model.py`

而 `industryanalysis.py` 会优先消费：

- `industry_parameters_xgboost.csv`

### Q2：`train_xgboost_sell_model.py` 也算主线吗？

不算。

它已存在，但目前还没有正式接入 `main.py` 主流程。

### Q3：为什么我跑 Step 4 没结果？

通常先检查：

1. 是否已经先跑过 Step 3
2. `cache_files/debug/stocks_tobe_traded/` 是否已有对应日期的交易指令文件

### Q4：为什么我跑 Step 3 没结果？

通常先检查：

1. 是否已经先跑过 Step 2
2. `results_zh_*_trigger.csv` 是否存在

### Q5：为什么安装完 `requirements.txt` 还会缺包？

因为当前主线实际依赖比 `requirements.txt` 更完整，建议额外安装：

```powershell
pip install xgboost scikit-learn seaborn openpyxl ta-lib
```

---

## 12. 相关文档

- [项目真实运行手册](./项目真实运行手册.md)
- [XGBoost主线源码导图](./XGBoost主线源码导图.md)
- [下一轮改造清单](./下一轮改造清单.md)

---

## 13. 当前已知事实 / 限制

1. 当前最新版优化主线是 **XGBoost 动态阈值**
2. `train_xgboost_sell_model.py` 已存在，但 **尚未正式接入 `main.py` 主流程**
3. `requirements.txt` 对当前完整主线依赖覆盖不全
4. Step 5 当前输出能力不如 Step 4 完整
5. 旧版 README 中存在多版本内容混合，当前 README 已按现状重写
