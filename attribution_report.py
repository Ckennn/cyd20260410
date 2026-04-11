import os
import pandas as pd
import qldef
from pandas.errors import EmptyDataError


def _to_datetime_safe(series):
    try:
        return pd.to_datetime(series, errors='coerce')
    except Exception:
        return pd.to_datetime(pd.Series([], dtype='object'))


def _normalize_regime(regime):
    if pd.isna(regime):
        return "UNKNOWN"
    regime_str = str(regime).upper()
    if regime_str in {"PANIC", "BEAR"}:
        return "BEAR"
    if regime_str in {"RANGE"}:
        return "RANGE"
    if regime_str in {"BULL", "CRAZY_BULL"}:
        return "BULL"
    return "UNKNOWN"


def _prepare_trade_df(df):
    trade_df = df.copy()
    if '利润' not in trade_df.columns:
        trade_df['利润'] = 0.0
    if '持仓期' not in trade_df.columns:
        trade_df['持仓期'] = 0
    trade_df['利润'] = pd.to_numeric(trade_df['利润'], errors='coerce').fillna(0.0)
    trade_df['持仓期'] = pd.to_numeric(trade_df['持仓期'], errors='coerce').fillna(0)
    if '卖出日期' in trade_df.columns:
        trade_df['卖出日期_dt'] = _to_datetime_safe(trade_df['卖出日期'])
    else:
        trade_df['卖出日期_dt'] = pd.NaT
    trade_df['loss_abs'] = trade_df['利润'].apply(lambda x: abs(x) if x < 0 else 0.0)
    trade_df['is_win'] = trade_df['利润'] > 0
    if qldef.regime_code_key not in trade_df.columns:
        trade_df[qldef.regime_code_key] = "UNKNOWN"
    trade_df['market_phase'] = trade_df[qldef.regime_code_key].apply(_normalize_regime)
    if qldef.sell_reason_key not in trade_df.columns:
        trade_df[qldef.sell_reason_key] = None
    return trade_df


def _build_reason_summary(trade_df):
    valid_df = trade_df[trade_df[qldef.sell_reason_key].notna()].copy()
    if valid_df.empty:
        return pd.DataFrame()
    total_loss = valid_df['loss_abs'].sum()
    grouped = valid_df.groupby(qldef.sell_reason_key).agg(
        trigger_count=('利润', 'count'),
        total_pnl=('利润', 'sum'),
        total_loss_abs=('loss_abs', 'sum'),
        avg_pnl=('利润', 'mean'),
        avg_loss=('利润', lambda s: s[s < 0].mean() if (s < 0).any() else 0.0),
        win_rate=('is_win', 'mean'),
        holding_mean=('持仓期', 'mean'),
        holding_p50=('持仓期', lambda s: s.quantile(0.5)),
        holding_p75=('持仓期', lambda s: s.quantile(0.75)),
    ).reset_index()
    grouped['loss_ratio'] = grouped['total_loss_abs'].apply(lambda x: x / total_loss if total_loss > 0 else 0.0)
    grouped['win_rate'] = grouped['win_rate'].fillna(0.0)
    return grouped.sort_values('total_loss_abs', ascending=False).reset_index(drop=True)


def _build_drawdown_contrib(trade_df):
    valid_df = trade_df[trade_df[qldef.sell_reason_key].notna()].copy()
    if valid_df.empty:
        return pd.DataFrame()
    valid_df = valid_df.sort_values(['卖出日期_dt']).reset_index(drop=True)
    valid_df['cum_pnl'] = valid_df['利润'].cumsum()
    valid_df['peak'] = valid_df['cum_pnl'].cummax()
    valid_df['drawdown'] = valid_df['peak'] - valid_df['cum_pnl']
    valid_df['in_drawdown'] = valid_df['drawdown'] > 0
    valid_df['dd_loss_abs'] = valid_df.apply(
        lambda r: abs(r['利润']) if (r['利润'] < 0 and r['in_drawdown']) else 0.0,
        axis=1
    )
    total_dd_loss = valid_df['dd_loss_abs'].sum()
    grouped = valid_df.groupby(qldef.sell_reason_key).agg(
        drawdown_loss_abs=('dd_loss_abs', 'sum')
    ).reset_index()
    grouped['drawdown_loss_ratio'] = grouped['drawdown_loss_abs'].apply(
        lambda x: x / total_dd_loss if total_dd_loss > 0 else 0.0
    )
    return grouped.sort_values('drawdown_loss_abs', ascending=False).reset_index(drop=True)


def _build_regime_summary(trade_df):
    valid_df = trade_df[trade_df[qldef.sell_reason_key].notna()].copy()
    if valid_df.empty:
        return pd.DataFrame()
    grouped = valid_df.groupby([qldef.sell_reason_key, qldef.regime_code_key, 'market_phase']).agg(
        trigger_count=('利润', 'count'),
        total_pnl=('利润', 'sum'),
        total_loss_abs=('loss_abs', 'sum'),
        avg_pnl=('利润', 'mean'),
        win_rate=('is_win', 'mean'),
        holding_mean=('持仓期', 'mean')
    ).reset_index()
    grouped['win_rate'] = grouped['win_rate'].fillna(0.0)
    return grouped.sort_values(['total_loss_abs', 'trigger_count'], ascending=[False, False]).reset_index(drop=True)


def _build_sector_sig_regime_summary(trade_df):
    valid_df = trade_df[trade_df[qldef.sell_reason_key].notna()].copy()
    if valid_df.empty:
        return pd.DataFrame()
    if qldef.sector_id_key not in valid_df.columns:
        valid_df[qldef.sector_id_key] = 'UNKNOWN'
    if qldef.signal_key not in valid_df.columns:
        valid_df[qldef.signal_key] = 'UNKNOWN'
    grouped = valid_df.groupby(
        [qldef.sector_id_key, qldef.signal_key, qldef.regime_code_key, qldef.sell_reason_key]
    ).agg(
        trigger_count=('利润', 'count'),
        total_pnl=('利润', 'sum'),
        total_loss_abs=('loss_abs', 'sum'),
        avg_pnl=('利润', 'mean'),
        win_rate=('is_win', 'mean')
    ).reset_index()
    grouped['win_rate'] = grouped['win_rate'].fillna(0.0)
    return grouped.sort_values(['total_loss_abs', 'trigger_count'], ascending=[False, False]).reset_index(drop=True)


def _build_sector_sig_heatmap(trade_df):
    valid_df = trade_df[trade_df[qldef.sell_reason_key].notna()].copy()
    if valid_df.empty:
        return pd.DataFrame()
    if qldef.sector_id_key not in valid_df.columns:
        valid_df[qldef.sector_id_key] = 'UNKNOWN'
    if qldef.signal_key not in valid_df.columns:
        valid_df[qldef.signal_key] = 'UNKNOWN'
    heatmap_df = valid_df.pivot_table(
        index=qldef.sector_id_key,
        columns=qldef.signal_key,
        values='loss_abs',
        aggfunc='sum',
        fill_value=0.0
    )
    return heatmap_df


def generate_attribution_reports(trades_file_path, output_dir, start_date, end_date):
    if not os.path.exists(trades_file_path):
        return
    try:
        trade_df = pd.read_csv(trades_file_path)
    except EmptyDataError:
        return
    if trade_df.empty:
        return
    trade_df = _prepare_trade_df(trade_df)

    reason_summary = _build_reason_summary(trade_df)
    drawdown_contrib = _build_drawdown_contrib(trade_df)
    regime_summary = _build_regime_summary(trade_df)
    sector_sig_regime = _build_sector_sig_regime_summary(trade_df)
    sector_sig_heatmap = _build_sector_sig_heatmap(trade_df)

    prefix = f"results_zh_{start_date}_{end_date}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not reason_summary.empty:
        reason_summary.to_csv(
            os.path.join(output_dir, f"{prefix}_sell_reason_summary.csv"),
            index=False,
            encoding='utf-8-sig'
        )
    if not drawdown_contrib.empty:
        drawdown_contrib.to_csv(
            os.path.join(output_dir, f"{prefix}_sell_reason_drawdown_contrib.csv"),
            index=False,
            encoding='utf-8-sig'
        )
    if not regime_summary.empty:
        regime_summary.to_csv(
            os.path.join(output_dir, f"{prefix}_sell_reason_regime_summary.csv"),
            index=False,
            encoding='utf-8-sig'
        )
    if not sector_sig_regime.empty:
        sector_sig_regime.to_csv(
            os.path.join(output_dir, f"{prefix}_sell_reason_sector_sig_regime.csv"),
            index=False,
            encoding='utf-8-sig'
        )
    if not sector_sig_heatmap.empty:
        sector_sig_heatmap.to_csv(
            os.path.join(output_dir, f"{prefix}_sell_reason_sector_sig_heatmap.csv"),
            encoding='utf-8-sig'
        )
