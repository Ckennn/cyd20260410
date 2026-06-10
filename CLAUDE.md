# CLAUDE.md — Quantitative Trading System (whz20260304)

## Project Identity

A **Python-based quantitative trading / backtesting system for the Chinese A-share market**. The current mainline is: individual stock rule-based signals → industry heat features → XGBoost dynamic thresholds → industry trading orders → backtest.

- **Author**: huanghx / Ckennn
- **Created**: 2024-07
- **Primary language**: Python 3.11
- **Preferred platform**: Windows/PowerShell (runs in WSL with caveats)
- **Repository**: https://github.com/Ckennn/cyd20260410
- **Size**: ~26K lines of Python across ~70 source files

## Quick Reference — Run Commands

```powershell
python main.py 0 20240101 20241130      # Full pipeline
python main.py 1 20240101 20241130      # Step 1 only (export quotes from DB)
python main.py 2 20240101 20241130      # Step 2 only (generate stock signals)
python main.py 3 20240101 20241130      # Step 2.5 + Step 3 (XGBoost + trading orders)
python main.py 4 20240101 20241130      # Step 4 only (individual stock backtest)
python main.py 5 20240101 20241130      # Step 5 only (industry ETF backtest)
python main.py 0 20240101 20241130 --skip-query   # Skip DB query, use cached CSVs
python data_initializer.py              # Download A-share data from AKShare into SQLite
```

## Architecture — 5-Layer Pipeline

```
┌─────────────────────────────────────────────────────────┐
│ Step 0: generate_industry_config.py                     │
│   Excel → industry_parameters_model2.csv (static params)│
├─────────────────────────────────────────────────────────┤
│ Step 1: databaseutil.py                                 │
│   SQLite → CSV (OHLCV + MA/EMA/MACD/BBI/MAVOL)         │
│   Output: cache_files/debug/market_quotation_1d/        │
├─────────────────────────────────────────────────────────┤
│ Step 2: quantitativestrategy.py                         │
│   Computes 11 signal types from daily data              │
│   Uses qlsignal0.py / qlsignalcaochen.py                │
│   Output: results_zh_{start}_{end}_trigger.csv          │
├─────────────────────────────────────────────────────────┤
│ Step 2.5: analyze_industry_heat.py                      │
│          + train_xgboost_threshold_model.py             │
│   Rolling 90-day XGBoost binary classifier              │
│   Target: 3-day return > 2%                             │
│   Output: industry_parameters_xgboost.csv               │
├─────────────────────────────────────────────────────────┤
│ Step 3: industryanalysis.py                             │
│   Merges stock signals per industry per day             │
│   Applies dynamic thresholds from XGBoost prob_up       │
│   Output: stocks_tobe_traded_YYYYMMDD.csv               │
├─────────────────────────────────────────────────────────┤
│ Step 4 / Step 5: quantitativetrading.py                 │
│                + quantitativedcindustrytrading.py        │
│   Backtrader-based backtest                             │
│   Output: summary.csv, trades.csv, chart.png,           │
│           attribution reports                           │
└─────────────────────────────────────────────────────────┘
```

### Step dependencies (crucial)

| Step | Prerequisites |
|------|--------------|
| Step 1 | `data/stock_data.db` |
| Step 2 | Step 1 CSVs |
| Step 2.5 | Step 2 trigger.csv |
| Step 3 | Step 2 trigger + Step 0 model2 + Step 2.5 xgboost |
| Step 4 | Step 3 daily trading orders + Step 1 stock quotes |
| Step 5 | Step 3 daily trading orders + Step 1 industry quotes |

**main.py WILL NOT auto-run prerequisites** when targeting a single step. E.g., `main.py 3` needs Step 2 done already.

## Core Modules (mainline — read first)

| Module | Lines | Role |
|--------|-------|------|
| `main.py` | 284 | Pipeline orchestrator, argument parsing |
| `databaseutil.py` | 1191 | SQLite queries, technical indicator calc (MA/EMA/MACD), CSV export |
| `quantitativestrategy.py` | 361 | Per-stock signal generation (multi-process) |
| `qlsignalcaochen.py` | 2437 | Primary signal system — 11 signal types |
| `qlsignal0.py` / `qlsignal1.py` | 1512 / 831 | Legacy/secondary signal systems |
| `industryanalysis.py` | 1267 | Industry sector analysis, "3-day-2-hot" logic, trading order generation |
| `analyze_industry_heat.py` | ~220 | Builds industry heat features (sig_ratio, sig_trend, sig_ma5) |
| `train_xgboost_threshold_model.py` | ~221 | Rolling-window XGBoost: outputs prob_up per industry per day |
| `quantitativetrading.py` | 932 | Individual stock backtest (Step 4) |
| `quantitativedcindustrytrading.py` | 733 | Industry/ETF backtest (Step 5) |
| `strategy_config.py` | 242 | Per-signal stop-loss/take-profit/MA-exit rules × market regime |
| `market_regime.py` | ~160 | Market state classifier (PANIC/BEAR/RANGE/BULL/CRAZY_BULL) using ta-lib |
| `attribution_report.py` | ~200 | Sell-reason attribution: sector cooldown, dynamic stop, sig-specific, regime |
| `qloption.py` | 361 | File I/O facade, dynamic threshold reader (XGBoost priority) |
| `project_paths.py` | 85 | New path system (pathlib), DB/cache/result directory getters |

## Utility / Infrastructure

| Module | Lines | Role |
|--------|-------|------|
| `dfutil.py` | 6793 | **Monster utility** — 604 functions: date ranges, file I/O, data validation, multi-process helpers |
| `qldef.py` | 1359 | Global constants, signal/model configuration, directory paths (old-style) |
| `qlfunc.py` | 774 | Signal computation functions |
| `logutil.py` | ~170 | Logging wrapper |
| `tradedateutil.py` | ~140 | Trading calendar (uses exchange_calendars) |
| `generate_industry_config.py` | ~150 | Excel → model2.csv converter (Step 0) |
| `data_initializer.py` | 678 | AKShare downloader → SQLite |

## Key Design Patterns

### Two path systems (coexisting, being unified)
- **Old**: `qldef.xxx_directory` — string-based, set in `qldef.py`
- **New**: `project_paths.py` — `pathlib.Path`, env-var `STOCK_DB_PATH`
- Not all modules use `project_paths` yet; older modules still rely on `qldef` constants. When adding new code, use `project_paths`.

### Multi-process concurrency
- `main.py` `multi_process()` wraps `concurrent.futures.ProcessPoolExecutor`
- CPU count − 1 workers; falls back to main process if ≤1 arg
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

## What's NOT wired into mainline

| Script | Status |
|--------|--------|
| `train_xgboost_sell_model.py` | Exists, outputs `industry_parameters_xgboost_sell.csv`, **NOT called by main.py** |
| `train_lightgbm_sell_model.py` | Same — backup sell model, not wired |
| `quantitativesw2industrytrading.py` | Legacy SW2 variant, not used in main flow |
| `ML_pipeline_tf.py` | Experimental TensorFlow pipeline, standalone |
| `key_indicator_analyzer.py` | Standalone analysis tool |

## Key Files & Paths

```
data/stock_data.db                          ← Default DB (env: STOCK_DB_PATH)
C模型策略-1016.xlsx                         ← Static industry params (Step 0 input)
cache_files/industry_heat_history.csv       ← Feature table for XGBoost
cache_files/debug/industry_parameters_model2.csv     ← Step 0 output
cache_files/debug/industry_parameters_xgboost.csv   ← Step 2.5 output (prob_up)
cache_files/debug/market_quotation_1d/     ← Step 1: zh_XXXXXX_1d_ind.csv
cache_files/debug/quantitativeResultsOfStocks/ ← Step 2 triggers + Step 4 results
cache_files/debug/stocks_tobe_traded/      ← Step 3: daily order CSVs
```

## Known Limitations

1. `requirements.txt` incomplete — needs `xgboost`, `scikit-learn`, `seaborn`, `openpyxl`, `ta-lib` added manually
2. Some scripts use hardcoded Windows-style paths (backslashes); WSL/Linux compatibility varies
3. Sell XGBoost model exists but not integrated into main pipeline
4. Step 5 output is less complete than Step 4 (chart only, no CSV attribution reports)
5. Old-style `qldef` constants and new `project_paths` coexist; path migration is partial
6. Root `stock_data.db` conflicts with `data/stock_data.db` — mainline uses the latter

## Code Conventions

- **Naming**: Chinese column names in DataFrames (e.g., `'代码'`, `'名称'`, `'利润'`); English for function/variable names
- **Comments**: Chinese and English mixed; key logic blocks have Chinese inline notes
- **Logging**: Uses `logutil.log` (custom wrapper); debug logging configured at module level
- **Error handling**: `dfutil` provides `not_empty()`, `len_safe()`, `fatal_exit()`, `unsupported_exit()` — use these rather than raw Python checks
- **File I/O**: Prefer `qloption.database.read_file_csv()` or `dfutil` helpers for CSV; use `project_paths` getters for new code

## Testing

There is no formal test suite. The closest:
- `test_data_loading.py` — ad-hoc script to verify DB/cache/backtrader integration
- `check_*.py` / `verify_*.py` — diagnostic scripts for DB schema and data integrity
- `debug_*.py` — debug helpers for board target and CSV inspection
- Real testing == running `main.py` with sample date ranges and inspecting outputs

## When Editing

- **`industryanalysis.py`**: Understand the "3-day-2-hot" buy rule and XGBoost threshold overlay before touching. Changes here directly impact backtest results.
- **`strategy_config.py`**: Per-signal rules are tuned from backtest. Document the reason when changing threshold values.
- **`qldef.py`**: Global constants — changes propagate to many modules. Check all consumers.
- **`databaseutil.py`**: SQLite schema assumptions (column names, date formats) — changes break Step 1 output format.
- **Keep function signatures compatible** when extending; prefer kwargs or new config files for new parameters.
