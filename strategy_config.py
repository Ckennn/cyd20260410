"""
Strategy Configuration
Defines Stop Loss and Take Profit rules for different signals.
"""
import os

class StrategyConfig:
    # Default rules
    DEFAULT_STOP_LOSS = -0.10  # 10% stop loss (跌破买入价10%)
    DEFAULT_TAKE_PROFIT = 0.30 # 30% take profit (涨幅超过30%)
    DEFAULT_MA_EXIT = 10       # Exit if close < MA10 (跌破10日均线) - 恢复为最优配置
    GLOBAL_MA_EXIT_OVERRIDE = int(os.getenv("QL_MA_EXIT_OVERRIDE", "0") or "0")

    # Signal specific rules
    # Format: "signal_name": { 
    #     "default": {"stop_loss": float, "take_profit": float, "ma_exit": int},
    #     "BULL": ..., "BEAR": ..., "RANGE": ..., "PANIC": ..., "CRAZY_BULL": ...
    # }
    RULES = {
        # ==========================================================
        # A. 趋势突破类 (Trend Breakout) - 目标: 抓主升浪
        # 逻辑: 股价站上MA5 + MACD金叉
        # ==========================================================
        "caochen_price_rise_predict_rise_x_20220914": {
            "default":    {"stop_loss": -0.10, "take_profit": 0.50, "ma_exit": 10},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 5},
            "BEAR":       {"stop_loss": -0.08, "take_profit": 0.10, "ma_exit": 5},
            "RANGE":      {"stop_loss": -0.10, "take_profit": 0.20, "ma_exit": 20},
            "BULL":       {"stop_loss": -0.12, "take_profit": 0.60, "ma_exit": 10},
            "CRAZY_BULL": {"stop_loss": -0.05, "take_profit": 0.80, "ma_exit": 5}
        },
        "caochen_price_rise_predict_rise_x_20220915": {
            "default":    {"stop_loss": -0.10, "take_profit": 0.50, "ma_exit": 10},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 5},
            "BEAR":       {"stop_loss": -0.08, "take_profit": 0.10, "ma_exit": 5},
            "RANGE":      {"stop_loss": -0.10, "take_profit": 0.20, "ma_exit": 20},
            "BULL":       {"stop_loss": -0.12, "take_profit": 0.60, "ma_exit": 10},
            "CRAZY_BULL": {"stop_loss": -0.05, "take_profit": 0.80, "ma_exit": 5}
        },

        # ==========================================================
        # B. 回调抄底类 (Dip Buying / Mean Reversion) - 目标: 博反弹
        # 逻辑: 股价回调缩量 + 回踩MA10/20
        # ==========================================================
        # 上涨中继1 (回调10日线)
        "caochen_price_down_predict_rise_1_x_20220915": {
            "default":    {"stop_loss": -0.08, "take_profit": 0.15, "ma_exit": 20},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 5},
            "BEAR":       {"stop_loss": -0.05, "take_profit": 0.10, "ma_exit": 10},
            "RANGE":      {"stop_loss": -0.08, "take_profit": 0.15, "ma_exit": 20},
            "BULL":       {"stop_loss": -0.10, "take_profit": 0.30, "ma_exit": 20},
            "CRAZY_BULL": {"stop_loss": -0.05, "take_profit": 0.40, "ma_exit": 10}
        },
        "caochen_price_down_predict_rise_1_x_20221020": {
            "default":    {"stop_loss": -0.08, "take_profit": 0.15, "ma_exit": 20},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 5},
            "BEAR":       {"stop_loss": -0.05, "take_profit": 0.10, "ma_exit": 10},
            "RANGE":      {"stop_loss": -0.08, "take_profit": 0.15, "ma_exit": 20},
            "BULL":       {"stop_loss": -0.10, "take_profit": 0.30, "ma_exit": 20},
            "CRAZY_BULL": {"stop_loss": -0.05, "take_profit": 0.40, "ma_exit": 10}
        },
        "caochen_price_down_predict_rise_1_x_20221129": {
            "default":    {"stop_loss": -0.08, "take_profit": 0.15, "ma_exit": 20},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 5},
            "BEAR":       {"stop_loss": -0.05, "take_profit": 0.10, "ma_exit": 10},
            "RANGE":      {"stop_loss": -0.08, "take_profit": 0.15, "ma_exit": 20},
            "BULL":       {"stop_loss": -0.10, "take_profit": 0.30, "ma_exit": 20},
            "CRAZY_BULL": {"stop_loss": -0.05, "take_profit": 0.40, "ma_exit": 10}
        },
        # 上涨中继2 (回调20日线) - 需要更宽的波动空间
        "caochen_price_down_predict_rise_2_1_x_20220915": {
            "default":    {"stop_loss": -0.10, "take_profit": 0.20, "ma_exit": 30},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 10},
            "BEAR":       {"stop_loss": -0.08, "take_profit": 0.10, "ma_exit": 20},
            "RANGE":      {"stop_loss": -0.10, "take_profit": 0.20, "ma_exit": 30},
            "BULL":       {"stop_loss": -0.12, "take_profit": 0.30, "ma_exit": 30},
            "CRAZY_BULL": {"stop_loss": -0.08, "take_profit": 0.40, "ma_exit": 10}
        },
        "caochen_price_down_predict_rise_2_2_x_20220915": {
            "default":    {"stop_loss": -0.10, "take_profit": 0.20, "ma_exit": 30},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 10},
            "BEAR":       {"stop_loss": -0.08, "take_profit": 0.10, "ma_exit": 20},
            "RANGE":      {"stop_loss": -0.10, "take_profit": 0.20, "ma_exit": 30},
            "BULL":       {"stop_loss": -0.12, "take_profit": 0.30, "ma_exit": 30},
            "CRAZY_BULL": {"stop_loss": -0.08, "take_profit": 0.40, "ma_exit": 10}
        },
        "caochen_price_down_predict_rise_2_x_20221011": {
            "default":    {"stop_loss": -0.10, "take_profit": 0.20, "ma_exit": 30},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 10},
            "BEAR":       {"stop_loss": -0.08, "take_profit": 0.10, "ma_exit": 20},
            "RANGE":      {"stop_loss": -0.10, "take_profit": 0.20, "ma_exit": 30},
            "BULL":       {"stop_loss": -0.12, "take_profit": 0.30, "ma_exit": 30},
            "CRAZY_BULL": {"stop_loss": -0.08, "take_profit": 0.40, "ma_exit": 10}
        },
        "caochen_price_down_predict_rise_2_x_20221020": {
            "default":    {"stop_loss": -0.10, "take_profit": 0.20, "ma_exit": 30},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 10},
            "BEAR":       {"stop_loss": -0.08, "take_profit": 0.10, "ma_exit": 20},
            "RANGE":      {"stop_loss": -0.10, "take_profit": 0.20, "ma_exit": 30},
            "BULL":       {"stop_loss": -0.12, "take_profit": 0.30, "ma_exit": 30},
            "CRAZY_BULL": {"stop_loss": -0.08, "take_profit": 0.40, "ma_exit": 10}
        },
        # 上涨中继3 (回调5日线) - 强势股，止损要紧
        "caochen_price_down_predict_rise_3_x_20221011": {
            "default":    {"stop_loss": -0.05, "take_profit": 0.20, "ma_exit": 10},
            "PANIC":      {"stop_loss": -0.03, "take_profit": 0.05, "ma_exit": 5},
            "BEAR":       {"stop_loss": -0.05, "take_profit": 0.10, "ma_exit": 5},
            "RANGE":      {"stop_loss": -0.05, "take_profit": 0.15, "ma_exit": 10},
            "BULL":       {"stop_loss": -0.08, "take_profit": 0.30, "ma_exit": 10},
            "CRAZY_BULL": {"stop_loss": -0.05, "take_profit": 0.40, "ma_exit": 5}
        },

        # ==========================================================
        # C. 底部反转类 (Bottom Reversal) - 目标: 抄大底
        # 逻辑: 长期横盘 + 放量突破
        # 优化: 宽幅硬止损(防洗盘) + 长期持有
        # ==========================================================
        "caochen_volume_bloom_above_bottom_x_20220915": {
            "default":    {"stop_loss": -0.12, "take_profit": 0.30, "ma_exit": 20},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 5},
            "BEAR":       {"stop_loss": -0.08, "take_profit": 0.15, "ma_exit": 10},
            "RANGE":      {"stop_loss": -0.12, "take_profit": 0.25, "ma_exit": 20},
            "BULL":       {"stop_loss": -0.15, "take_profit": 0.50, "ma_exit": 30},
            "CRAZY_BULL": {"stop_loss": -0.10, "take_profit": 0.60, "ma_exit": 10}
        },
        "caochen_volume_bloom_above_bottom_x_20221011": {
            "default":    {"stop_loss": -0.12, "take_profit": 0.30, "ma_exit": 20},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 5},
            "BEAR":       {"stop_loss": -0.08, "take_profit": 0.15, "ma_exit": 10},
            "RANGE":      {"stop_loss": -0.12, "take_profit": 0.25, "ma_exit": 20},
            "BULL":       {"stop_loss": -0.15, "take_profit": 0.50, "ma_exit": 30},
            "CRAZY_BULL": {"stop_loss": -0.10, "take_profit": 0.60, "ma_exit": 10}
        },
        "caochen_volume_bloom_above_bottom_x_20230110": {
            "default":    {"stop_loss": -0.12, "take_profit": 0.30, "ma_exit": 20},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 5},
            "BEAR":       {"stop_loss": -0.08, "take_profit": 0.15, "ma_exit": 10},
            "RANGE":      {"stop_loss": -0.12, "take_profit": 0.25, "ma_exit": 20},
            "BULL":       {"stop_loss": -0.15, "take_profit": 0.50, "ma_exit": 30},
            "CRAZY_BULL": {"stop_loss": -0.10, "take_profit": 0.60, "ma_exit": 10}
        },
        "caochen_volume_bloom_above_bottom_x_20230111": {
            "default":    {"stop_loss": -0.12, "take_profit": 0.30, "ma_exit": 20},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 5},
            "BEAR":       {"stop_loss": -0.08, "take_profit": 0.15, "ma_exit": 10},
            "RANGE":      {"stop_loss": -0.12, "take_profit": 0.25, "ma_exit": 20},
            "BULL":       {"stop_loss": -0.15, "take_profit": 0.50, "ma_exit": 30},
            "CRAZY_BULL": {"stop_loss": -0.10, "take_profit": 0.60, "ma_exit": 10}
        },
        "caochen_volume_bloom_above_bottom_x_20230112": {
            "default":    {"stop_loss": -0.12, "take_profit": 0.30, "ma_exit": 20},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 5},
            "BEAR":       {"stop_loss": -0.08, "take_profit": 0.15, "ma_exit": 10},
            "RANGE":      {"stop_loss": -0.12, "take_profit": 0.25, "ma_exit": 20},
            "BULL":       {"stop_loss": -0.15, "take_profit": 0.50, "ma_exit": 30},
            "CRAZY_BULL": {"stop_loss": -0.10, "take_profit": 0.60, "ma_exit": 10}
        },

        # ==========================================================
        # D. 其他策略 (Others)
        # ==========================================================
        # 年线策略
        "caochen_price_reach_year_rise_3_x_20230213": {
            "default":    {"stop_loss": -0.10, "take_profit": 0.40, "ma_exit": 60},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 10},
            "BEAR":       {"stop_loss": -0.08, "take_profit": 0.10, "ma_exit": 20},
            "RANGE":      {"stop_loss": -0.10, "take_profit": 0.30, "ma_exit": 60},
            "BULL":       {"stop_loss": -0.12, "take_profit": 0.50, "ma_exit": 60},
            "CRAZY_BULL": {"stop_loss": -0.08, "take_profit": 0.60, "ma_exit": 20}
        },
        # 低点上移
        "caochen_price_low_above_previous_x_20230203": {
            "default":    {"stop_loss": -0.08, "take_profit": 0.30, "ma_exit": 20},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 5},
            "BEAR":       {"stop_loss": -0.05, "take_profit": 0.10, "ma_exit": 10},
            "RANGE":      {"stop_loss": -0.08, "take_profit": 0.20, "ma_exit": 20},
            "BULL":       {"stop_loss": -0.10, "take_profit": 0.40, "ma_exit": 20},
            "CRAZY_BULL": {"stop_loss": -0.05, "take_profit": 0.50, "ma_exit": 10}
        },
        "caochen_price_low_above_previous_10_x_20230208": {
            "default":    {"stop_loss": -0.08, "take_profit": 0.30, "ma_exit": 20},
            "PANIC":      {"stop_loss": -0.05, "take_profit": 0.05, "ma_exit": 5},
            "BEAR":       {"stop_loss": -0.05, "take_profit": 0.10, "ma_exit": 10},
            "RANGE":      {"stop_loss": -0.08, "take_profit": 0.20, "ma_exit": 20},
            "BULL":       {"stop_loss": -0.10, "take_profit": 0.40, "ma_exit": 20},
            "CRAZY_BULL": {"stop_loss": -0.05, "take_profit": 0.50, "ma_exit": 10}
        },
        # 量增价涨
        "caochen_volume_enlarge_price_rise_4_x_20230310": {
            "default":    {"stop_loss": -0.05, "take_profit": 0.20, "ma_exit": 5},
            "PANIC":      {"stop_loss": -0.03, "take_profit": 0.05, "ma_exit": 3},
            "BEAR":       {"stop_loss": -0.05, "take_profit": 0.10, "ma_exit": 5},
            "RANGE":      {"stop_loss": -0.05, "take_profit": 0.15, "ma_exit": 5},
            "BULL":       {"stop_loss": -0.08, "take_profit": 0.30, "ma_exit": 5},
            "CRAZY_BULL": {"stop_loss": -0.05, "take_profit": 0.50, "ma_exit": 3}
        },
    }

    @staticmethod
    def get_rule(signal_name, regime_name=None):
        """
        Get strategy rule for a specific signal and market regime.
        Returns default rules if signal_name is not found.
        """
        # Default config
        default_cfg = {
            "stop_loss": StrategyConfig.DEFAULT_STOP_LOSS,
            "take_profit": StrategyConfig.DEFAULT_TAKE_PROFIT,
            "ma_exit": StrategyConfig.DEFAULT_MA_EXIT
        }

        if not signal_name or not isinstance(signal_name, str):
            cfg = default_cfg
            if StrategyConfig.GLOBAL_MA_EXIT_OVERRIDE > 0:
                cfg = cfg.copy()
                cfg["ma_exit"] = StrategyConfig.GLOBAL_MA_EXIT_OVERRIDE
            return cfg
            
        signal_rules = StrategyConfig.RULES.get(signal_name)
        if not signal_rules:
            cfg = default_cfg
            if StrategyConfig.GLOBAL_MA_EXIT_OVERRIDE > 0:
                cfg = cfg.copy()
                cfg["ma_exit"] = StrategyConfig.GLOBAL_MA_EXIT_OVERRIDE
            return cfg
            
        # If regime is provided, try to get regime-specific rules
        if regime_name:
            regime_cfg = signal_rules.get(regime_name)
            if regime_cfg:
                if StrategyConfig.GLOBAL_MA_EXIT_OVERRIDE > 0:
                    cfg = regime_cfg.copy()
                    cfg["ma_exit"] = StrategyConfig.GLOBAL_MA_EXIT_OVERRIDE
                    return cfg
                return regime_cfg
                
        # Fallback to signal's default rules
        cfg = signal_rules.get("default", default_cfg)
        if StrategyConfig.GLOBAL_MA_EXIT_OVERRIDE > 0:
            cfg = cfg.copy()
            cfg["ma_exit"] = StrategyConfig.GLOBAL_MA_EXIT_OVERRIDE
        return cfg
