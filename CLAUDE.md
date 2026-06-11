# CLAUDE.md — Quantitative Trading System (whz20260304)

## Project Identity

A **Python-based quantitative trading / backtesting system for the Chinese A-share market**. The current mainline is: individual stock rule-based signals → industry heat features → XGBoost dynamic thresholds → industry trading orders → backtest.

- **Author**: huanghx / Ckennn
- **Created**: 2024-07
- **Primary language**: Python 3.12 (originally 3.11)
- **Preferred platform**: Windows/PowerShell (runs in WSL/Ubuntu 24.04 with caveats)
- **Repository**: https://github.com/Ckennn/cyd20260410
- **Size**: 26,161 lines of Python across 55 source files (all at root level)

## Quick Reference — Run Commands

```bash
python3 main.py 0 20240101 20241130      # Full pipeline (all steps)
python3 main.py 1 20240101 20241130      # Step 1 only (export quotes from DB)
python3 main.py 2 20240101 20241130      # Step 2 only (generate stock signals)
python3 main.py 3 20240101 20241130      # Step 2.5 + Step 3 (XGBoost + trading orders)
python3 main.py 4 20240101 20241130      # Step 4 only (individual stock backtest)
python3 main.py 5 20240101 20241130      # Step 5 only (industry ETF backtest)
python3 main.py 0 20240101 20241130 --skip-query   # Skip DB query, use cached CSVs
python3 data_initializer.py              # Download A-share data from AKShare into SQLite
```

## Architecture — 6-Step Pipeline

```
┌─────────────────────────────────────────────────────────┐
│ Step 0: generate_industry_config.py (143 lines)         │
│   Excel → industry_parameters_model2.csv (static params)│
├─────────────────────────────────────────────────────────┤
│ Step 1: databaseutil.py (1,191 lines)                   │
│   SQLite → CSV (OHLCV + MA/EMA/MACD/BBI/MAVOL)         │
│   Output: cache_files/debug/market_quotation_1d/        │
├─────────────────────────────────────────────────────────┤
│ Step 2: quantitativestrategy.py (361 lines)             │
│   Computes 11 signal types from daily data              │
│   Uses qlsignal0.py / qlsignalcaochen.py                │
│   Output: results_zh_{start}_{end}_trigger.csv          │
├─────────────────────────────────────────────────────────┤
│ Step 2.5: analyze_industry_heat.py (177 lines)          │
│          + train_xgboost_threshold_model.py (221 lines) │
│   Rolling 90-day XGBoost binary classifier              │
│   Target: 3-day return > 2%                             │
│   Output: industry_parameters_xgboost.csv               │
├─────────────────────────────────────────────────────────┤
│ Step 3: industryanalysis.py (1,267 lines)               │
│   Merges stock signals per industry per day             │
│   Applies dynamic thresholds from XGBoost prob_up       │
│   Output: stocks_tobe_traded_YYYYMMDD.csv               │
├─────────────────────────────────────────────────────────┤
│ Step 4 / Step 5: quantitativetrading.py (932 lines)     │
│                + quantitativedcindustrytrading.py        │
│                  (733 lines)                            │
│   Backtrader-based backtest                             │
│   Support: drawingutil.py, trade_list_analyzer.py,      │
│            key_indicator_analyzer.py,                    │
│            attribution_report.py (197 lines)            │
│   Output: summary.csv, trades.csv, chart.png,           │
│           attribution reports                           │
└─────────────────────────────────────────────────────────┘
```

### Step dependencies (crucial)

| Step | Prerequisites |
|------|--------------|
| Step 0 | `C模型策略-1016.xlsx` |
| Step 1 | `data/stock_data.db` |
| Step 2 | Step 1 CSVs |
| Step 2.5 | Step 2 trigger.csv |
| Step 3 | Step 2 trigger + Step 0 model2 + Step 2.5 xgboost |
| Step 4 | Step 3 daily trading orders + Step 1 stock quotes |
| Step 5 | Step 3 daily trading orders + Step 1 industry quotes |

**main.py WILL NOT auto-run prerequisites** when targeting a single step. E.g., `main.py 3` needs Step 2 done already.

## Complete File Inventory (55 files, 26,161 lines)

### Mainline Pipeline (14 files — called by main.py or pipeline steps)

| Module | Lines | Role |
|--------|-------|------|
| `main.py` | 284 | Pipeline orchestrator, argparse, multi-process dispatch |
| `databaseutil.py` | 1,191 | SQLite queries, technical indicator calc (MA/EMA/MACD), CSV export |
| `quantitativestrategy.py` | 361 | Per-stock signal generation (multi-process), Step 2 |
| `qlsignalcaochen.py` | 2,437 | Primary signal system — 11 signal types |
| `qlsignal0.py` | 1,512 | Core signal definitions and signal listing |
| `qlsignal1.py` | 831 | Secondary signal definitions (imports qlsignal0) |
| `qlfunc.py` | 774 | Signal computation helper functions |
| `industryanalysis.py` | 1,267 | Industry sector analysis, "3-day-2-hot" logic, trading order generation |
| `analyze_industry_heat.py` | 177 | Builds industry heat features (sig_ratio, sig_trend, sig_ma5) |
| `train_xgboost_threshold_model.py` | 221 | Rolling 90-day XGBoost binary classifier → prob_up |
| `quantitativetrading.py` | 932 | Individual stock backtest using backtrader (Step 4) |
| `quantitativedcindustrytrading.py` | 733 | Industry/ETF backtest using backtrader (Step 5) |
| `strategy_config.py` | 242 | Per-signal stop-loss/take-profit/MA-exit rules × market regime |
| `market_regime.py` | 173 | Market state classifier (PANIC/BEAR/RANGE/BULL/CRAZY_BULL) using ta-lib |

### Backtest Support Modules (4 files — imported by Step 4/5)

| Module | Lines | Role |
|--------|-------|------|
| `drawingutil.py` | 207 | Matplotlib yield curve chart, CJK font handling |
| `trade_list_analyzer.py` | 141 | Trade list statistics and analysis |
| `key_indicator_analyzer.py` | 334 | Backtest key indicator computation (Sharpe, drawdown, etc.) |
| `attribution_report.py` | 197 | Sell-reason attribution: sector cooldown, dynamic stop, sig-specific, regime |

### Utility / Infrastructure (9 files)

| Module | Lines | Role |
|--------|-------|------|
| `dfutil.py` | 6,793 | **Monster utility** — date ranges, file I/O, data validation, multi-process, email, etc. |
| `qldef.py` | 1,359 | Global constants, signal/model configuration, directory paths (old-style string-based) |
| `qldebug.py` | 734 | Debug utilities and logging helpers |
| `qloption.py` | 386 | File I/O facade, CSV read/write, dynamic threshold reader (XGBoost priority) |
| `qlfocus.py` | ~15 | Excluded sector list (`trigger_score_adjust_zero_board_name_list`) — ST, finance, resources |
| `logutil.py` | 154 | Logging wrapper (RotatingFileHandler, colorlog support) |
| `tradedateutil.py` | 139 | Trading calendar (uses exchange_calendars) |
| `project_paths.py` | 85 | New path system (pathlib), DB/cache/result directory getters |
| `datarepairutil.py` | 207 | Data repair utilities (**imported by main.py but all calls commented out**) |

### Data & Config (2 files)

| Module | Lines | Role |
|--------|-------|------|
| `generate_industry_config.py` | 143 | Excel → model2.csv converter (Step 0) |
| `data_initializer.py` | 678 | AKShare downloader → SQLite (prerequisite step before pipeline) |

### Scripts NOT Wired into Mainline (13 files)

| Script | Lines | Status |
|--------|-------|--------|
| `train_xgboost_sell_model.py` | 242 | Exists, outputs `industry_parameters_xgboost_sell.csv`, **NOT called by main.py** |
| `train_lightgbm_sell_model.py` | 234 | Same — backup sell model using LightGBM, not wired |
| `quantitativesw2industrytrading.py` | 625 | Legacy SW2 variant of industry backtest, not used in main flow |
| `ML_pipeline_tf.py` | 125 | Experimental TensorFlow pipeline (keras Sequential), standalone |
| `ML_data_prep.py` | 142 | ML data preparation for TensorFlow pipeline (imported by ML_pipeline_tf.py) |
| `generate_dynamic_thresholds.py` | 128 | Pre-XGBoost statistical dynamic threshold approach, superseded |
| `stock_selector.py` | 179 | DragonStockSelector — filters/ranks candidate stocks. Completely isolated |
| `download_hs300.py` | 403 | Download HS300 index data from AKShare, standalone |
| `fix_industry_data_batch.py` | 396 | Batch industry data download/fix tool |
| `fix_hs300_data.py` | ~50 | HS300 data fix/repair tool |
| `fix_missing_file_only.py` | ~30 | Fix missing board target file |
| `clean_industry_tables.py` | ~100 | Clean old stock_industry and industry_quote tables from DB |
| `run_dc_quote_export.py` | ~40 | Export DC (East Money) quotes via databaseutil |

### Diagnostic / Test Scripts (13 files — all standalone)

| Files | Role |
|-------|------|
| `check_database_structure.py` (212), `verify_database_schema.py` (254) | DB schema verification |
| `check_db_more.py`, `check_db_path_and_tables.py`, `check_db_schema.py` | Additional DB checks |
| `check_dc_quotes.py`, `check_hs300_in_db_v2.py`, `check_sample_values.py` | Data integrity checks |
| `check_syntax.py` | Syntax validation (import test) |
| `debug_board_target.py`, `debug_csv.py` | Debug helpers |
| `verify_stocks_format.py` | Stock data format verification |
| `test_data_loading.py` (84) | Ad-hoc DB/cache/backtrader integration test |

## Import Dependency Graph

```
project_paths.py          (no project imports — pure pathlib + os)
    ↓
qldef.py                  (imports project_paths, dfutil)
    ↓
dfutil.py                 (no project imports — pure stdlib + pandas/numpy)
logutil.py                (imports dfutil)
qldebug.py                (imports dfutil, logutil)
qloption.py               (imports dfutil, logutil, qldef)
tradedateutil.py          (imports dfutil, logutil, qldef)
    ↓
databaseutil.py           (imports dfutil, logutil, qldef, qloption, tradedateutil, project_paths)
datarepairutil.py         (imports dfutil, logutil, qldef, qloption, databaseutil)
    ↓
qlfunc.py                 (imports dfutil, qldebug, qldef)
qlfocus.py                (no project imports)
qlsignal0.py              (imports dfutil, qldebug, qldef, qloption)
qlsignal1.py              (imports dfutil, qldebug, qlfunc, qlsignal0)
qlsignalcaochen.py        (imports dfutil, qldef, qlfocus, qloption, qlsignal0, qlsignal1)
    ↓
quantitativestrategy.py   (imports dfutil, logutil, qldef, qloption, qlsignal0, qlsignalcaochen, tradedateutil)
    ↓
market_regime.py          (imports dfutil, qldef, qloption)
industryanalysis.py       (imports dfutil, logutil, qldef, qloption, tradedateutil)
analyze_industry_heat.py  (imports project_paths)
train_xgboost_threshold_model.py (imports project_paths)
    ↓
quantitativetrading.py    (imports dfutil, logutil, qldef, qloption, drawingutil,
                           key_indicator_analyzer, trade_list_analyzer, attribution_report)
quantitativedcindustrytrading.py (imports same set as above)
    ↓
main.py                   (imports databaseutil, datarepairutil, dfutil, industryanalysis,
                           qldef, qloption, quantitativedcindustrytrading,
                           quantitativetrading, quantitativestrategy, generate_industry_config)
```

**Key observations:**
- `dfutil.py` (6,793 lines) is the true foundation — imported by almost everything
- `qldef.py` is imported by all mainline modules except `project_paths` and ML modules
- `project_paths.py` is used by only 10 of 55 files — path migration is partial
- `stock_selector.py` (DragonStockSelector) is completely isolated — no module imports it

## Key Design Patterns

### Two path systems (coexisting, being unified)
- **Old**: `qldef.xxx_directory` — string-based, set in `qldef.py`
- **New**: `project_paths.py` — `pathlib.Path`, env-var `STOCK_DB_PATH`
- Not all modules use `project_paths` yet; older modules still rely on `qldef` constants. When adding new code, use `project_paths`.

### Multi-process concurrency
- `main.py` `multi_process()` wraps `concurrent.futures.ProcessPoolExecutor`
- CPU count − 1 workers; falls back to main process if ≤1 arg
- Uses `multiprocessing.Manager().Lock()` for shared file access
- Used by Steps 2, 3, 4 for per-stock/per-date parallelism

### XGBoost dynamic threshold logic (current mainline)
In `industryanalysis.py`, per day per industry:

| `prob_up` | Action | Effect |
|-----------|--------|--------|
| `< 0.45` | Defensive | `buy_param = 999%` — block all buys |
| `> 0.70` | Aggressive | `buy_param = 5%` — buy on weak signal |
| `< 0.30` | Forced exit | `sell_param = 0.1/9999` — liquidate holdings |
| otherwise | Neutral | Use static parameters from model2 |

### Market regime → strategy config chain
1. `market_regime.py` classifies each day as PANIC/BEAR/RANGE/BULL/CRAZY_BULL
2. `strategy_config.py` maps `signal_name × regime → {stop_loss, take_profit, ma_exit}`
3. Step 4 backtest consumes these per-trade

### Signal system architecture
- `qlsignal0.py` — core signal definitions (base classes, signal listing)
- `qlsignal1.py` — additional signal definitions (imports qlsignal0 as `qls0`)
- `qlsignalcaochen.py` — primary signal system with 11 signal types (imports both)
- `qlfunc.py` — shared signal computation helper functions
- `qlfocus.py` — sector exclusion list (ST stocks, finance, resource sectors excluded from scoring)

## Key Files & Paths

```
data/stock_data.db                          ← Default DB (2.09 GB), env: STOCK_DB_PATH
C模型策略-1016.xlsx                         ← Static industry params (Step 0 input)
dc_board_target.csv                         ← East Money board target mapping
cache_files/
  debug/
    industry_parameters_model2.csv          ← Step 0 output (static params)
    industry_parameters_xgboost.csv         ← Step 2.5 output (prob_up predictions)
    market_quotation_1d/                    ← Step 1: zh_XXXXXX_1d_ind.csv (5,264 files)
    quantitativeResultsOfStocks/            ← Step 2 triggers + Step 4/5 results
    stocks_tobe_traded/                     ← Step 3: daily order CSVs
  models/                                   ← Saved XGBoost model files
  industry_heat_history.csv                 ← Feature table for XGBoost
  heat_vs_return_scatter.png               ← Diagnostic chart
stocks_tobe_traded/                         ← Legacy directory (gitignored)
logs/                                       ← Runtime logs
```

## Known Limitations

1. `requirements.txt` is **complete for core pipeline** — all mainline deps listed. Missing only `exchange_calendars` (used by `tradedateutil.py`)
2. Some scripts use hardcoded Windows-style paths (backslashes); WSL/Linux compatibility varies
3. Sell XGBoost model (`train_xgboost_sell_model.py`) and LightGBM variant exist but not integrated into main pipeline
4. Step 5 output is less complete than Step 4 (chart only, no CSV attribution reports)
5. Old-style `qldef` constants and new `project_paths` coexist; `project_paths` used by only 10 of 55 files
6. Root `stock_data.db` conflicts with `data/stock_data.db` — mainline uses the latter
7. `datarepairutil.py` is imported by `main.py` but all its calls are commented out (dead import)
8. Font handling: `drawingutil.py` defaults to `SimHei` which doesn't exist on Linux/WSL. Mitigated by mapping to WenQuanYi Micro Hei in WSL environment

## Code Conventions

- **Naming**: Chinese column names in DataFrames (e.g., `'代码'`, `'名称'`, `'利润'`); English for function/variable names
- **Comments**: Chinese and English mixed; key logic blocks have Chinese inline notes
- **Logging**: Uses `logutil.log` (custom wrapper); debug logging configured at module level; RotatingFileHandler
- **Error handling**: `dfutil` provides `not_empty()`, `len_safe()`, `fatal_exit()`, `unsupported_exit()` — use these rather than raw Python checks
- **File I/O**: Prefer `qloption.database.read_file_csv()` or `dfutil` helpers for CSV; use `project_paths` getters for new code
- **Python version**: Now running on Python 3.12 in WSL/Ubuntu 24.04 (originally 3.11 on Windows)

## Testing

There is no formal test suite. The closest:
- `test_data_loading.py` — ad-hoc script to verify DB/cache/backtrader integration
- `check_*.py` / `verify_*.py` (13 scripts) — diagnostic scripts for DB schema and data integrity
- `debug_*.py` — debug helpers for board target and CSV inspection
- Real testing == running `main.py` with sample date ranges and inspecting outputs

## When Editing

- **`industryanalysis.py`**: Understand the "3-day-2-hot" buy rule and XGBoost threshold overlay before touching. Changes here directly impact backtest results.
- **`strategy_config.py`**: Per-signal rules are tuned from backtest. Document the reason when changing threshold values.
- **`qldef.py`**: Global constants — changes propagate to many modules. Check all consumers.
- **`databaseutil.py`**: SQLite schema assumptions (column names, date formats) — changes break Step 1 output format.
- **`qloption.py`**: Contains the `load_indicator_by_target()` method (added for WSL compatibility) and the `get_industry_dynamic_params_df()` XGBoost priority reader.
- **`dfutil.py`**: 6,793 line utility — before adding a helper, check if it already exists here.
- **Keep function signatures compatible** when extending; prefer kwargs or new config files for new parameters.
