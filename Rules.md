# 项目开发规范与策略文档 (Rules & Guidelines)

本文档旨在统一项目开发规范、明确核心策略逻辑，并作为后续开发的指导纲领。

## 1. 核心设计原则 (Core Principles)

1.  **数据驱动 (Data-Driven)**: 所有的策略优化必须基于回测数据，杜绝凭空臆想。
2.  **分层架构 (Layered Architecture)**: 严格遵守 `数据层 -> 策略层 -> 行业层 -> 回测层` 的单向依赖关系。
3.  **动态适应 (Dynamic Adaptation)**: 市场环境多变，参数不应是固定的，而应随市场热度、波动率等特征动态调整。
4.  **防御优先 (Defense First)**: 在收益与回撤之间，优先控制回撤。活着比赚钱更重要。
5.  **模块化 (Modularity)**: 每个功能模块（如信号生成、行业分析、回测执行）应独立可测试。

## 2. 交易对象与标的 (Trading Targets)

*   **核心标的**: **行业板块指数 (Industry Index / ETF)**。
    *   代码示例: `BK0420` (半导体), `BK0465` (医疗服务)。
    *   **交易逻辑**: 买入代表该行业的 ETF 或指数基金，而非个股。
    *   **优势**: 规避个股黑天鹅风险，纯粹赚取行业轮动 (Beta) 收益。

## 3. 策略体系 (Strategy Framework)

### 3.1 信号生成 (Step 2)
基于日线数据，计算 11 类核心信号：
*   **sig1**: 底部上破 (10日)
*   **sig2**: 上升趋势 (5日)
*   **sig3-5**: 上涨中继 (回调买入)
*   **sig6-8**: 年线稳涨 (长线趋势)
*   **sig9**: 低点中线上移
*   **sig10**: 单阳不破
*   **sig11**: 未成交旧信号

### 3.2 行业轮动逻辑 (Step 3) - "3天2热"
*   **买入信号**:
    *   **定义**: 一个板块在最近 3 天内，至少有 2 天被判定为“活跃”（活跃股数量占比 > 阈值）。
    *   **动态阈值 (XGBoost Buy Model)**:
        *   不再使用固定的“活跃股数量”阈值。
        *   使用 **XGBoost 模型** 预测板块未来 3 天上涨概率 (`Prob_Up`)。
        *   **进攻模式 (`Prob_Up > 0.7`)**: 降低买入且阈值至 5%。
        *   **防守模式 (`Prob_Up < 0.45`)**: 禁止买入 (阈值 999%)。

*   **卖出信号**:
    *   **被动止损**: 板块内活跃股数量连续下降，或低于最低阈值。
    *   **主动逃顶 (XGBoost Sell Model)**:
        *   使用独立 **XGBoost 卖出模型** 预测未来 3 天暴跌概率 (`Prob_Crash`)。
        *   **紧急逃顶 (`Prob_Crash > 0.65`)**: 无论当前排名多少，**强制卖出**。
        *   **预警减仓 (`0.5 < Prob_Crash <= 0.65`)**: 收紧止损线 (Rank > 10 即卖出)。

## 4. 开发与回测流程 (Workflow)

### 4.1 目录结构规范
*   `data/`: 原始数据库文件 (`stock_data.db`)。
*   `cache_files/`: 中间缓存文件 (CSV)。
    *   `debug/`: 调试输出与最终结果。
    *   `industry_heat_history.csv`: 训练模型的特征数据。
*   `stocks_tobe_traded/`: Step 3 生成的每日买卖指令 CSV。
*   `quantitativeResultsOfStocks/`: 回测结果 (资金曲线、交易明细)。

### 4.2 标准操作步骤 (SOP)
1.  **更新数据 (Step 0)**: 确保行情数据最新。
2.  **生成信号 (Step 1-2)**: 计算所有个股的 11 类信号。
3.  **训练模型与预测 (Step 2.5)**: 
    *   运行 `analyze_industry_heat.py` 生成行业热度特征。
    *   运行 `train_xgboost_threshold_model.py` 更新并预测买入/卖出概率。
    *   *(注: 运行 `main.py 3` 或 `main.py 0` 时会自动包含此步骤)*
4.  **生成指令 (Step 3)**: 运行 `main.py 3`，集成 XGBoost 概率，生成带防御/进攻机制的交易指令。
5.  **执行回测 (Step 4-5)**: 
    *   运行 `main.py 4`，验证个股(Dragon策略)交易效果。
    *   运行 `main.py 5`，验证行业 ETF 动态仓位交易效果。

## 5. 模型工程规范 (Machine Learning Ops)

### 5.1 数据集构建
*   **滚动窗口 (Rolling Window)**: 采用 90 天滚动窗口进行训练，每日重训，适应市场风格切换。
*   **特征工程 (Features)**:
    *   **热度特征**: `sig_ratio`, `sig_trend`, `sig_trend_acceleration`。
    *   **价格特征**: `price_trend` (乖离率), `roc_5` (动量)。
    *   **大盘特征**: `hs300_trend`, `hs300_volatility` (感知系统性风险)。
    *   **见顶特征**: `bias_60`, `heat_price_divergence` (量价背离)。

### 5.2 模型选择
*   **买入模型**: XGBoost Classifier (Target: Future 3D Return > 2%)。
*   **卖出模型**: XGBoost Classifier (Target: Future 3D Return < -3%)。
    *   *备选*: LightGBM (速度更快，但当前数据量下精度略低，暂作为备选)。

## 6. 代码提交与修改规范

1.  **不要随意修改核心逻辑**: 特别是 `industryanalysis.py` 和 `quantitativedcindustrytrading.py` 中的交易逻辑，修改前必须先理解其对回测的影响。
2.  **保持接口兼容**: 新增功能（如新模型）应通过配置文件或新的函数接口接入，尽量不破坏原有函数的签名。
3.  **注释**: 关键逻辑修改必须添加注释，说明修改原因和时间。
4.  **备份**: 在进行重大重构前，务必备份关键的 CSV 输出文件，以便对比结果。

---
**版本**: 1.0
**更新日期**: 2026-03-12
