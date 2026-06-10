from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = PROJECT_ROOT / "cache_files"
DEBUG_CACHE_DIR = CACHE_DIR / "debug"
RELEASE_CACHE_DIR = CACHE_DIR / "release"
MODELS_DIR = CACHE_DIR / "models"


def get_project_root() -> Path:
    return PROJECT_ROOT


def get_db_path() -> Path:
    custom = os.environ.get("STOCK_DB_PATH")
    return Path(custom).expanduser() if custom else DATA_DIR / "stock_data.db"


def get_cache_root() -> Path:
    return CACHE_DIR


def get_debug_cache_dir() -> Path:
    return DEBUG_CACHE_DIR


def get_release_cache_dir() -> Path:
    return RELEASE_CACHE_DIR


def get_runtime_cache_dir(debug: bool = __debug__) -> Path:
    return DEBUG_CACHE_DIR if debug else RELEASE_CACHE_DIR


def get_models_dir() -> Path:
    return MODELS_DIR


def get_market_quote_dir(debug: bool = __debug__) -> Path:
    return get_runtime_cache_dir(debug) / "market_quotation_1d"


def get_quantitative_result_dir(debug: bool = __debug__) -> Path:
    return get_runtime_cache_dir(debug) / "quantitativeResultsOfStocks"


def get_stocks_tobe_traded_dir(debug: bool = __debug__) -> Path:
    return get_runtime_cache_dir(debug) / "stocks_tobe_traded"


def get_root_cache_file(filename: str) -> Path:
    return CACHE_DIR / filename


def get_debug_cache_file(filename: str) -> Path:
    return DEBUG_CACHE_DIR / filename


def get_market_quote_file(filename: str, debug: bool = __debug__) -> Path:
    return get_market_quote_dir(debug) / filename


def get_hs300_candidate_paths() -> list[Path]:
    return [
        get_market_quote_file("zh_000300_1d_ind.csv"),
        get_debug_cache_file("zh_000300.csv"),
        get_cache_root() / "zh_000300.csv",
        DATA_DIR / "zh_000300.csv",
    ]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_parent(path: Path) -> Path:
    ensure_dir(path.parent)
    return path
