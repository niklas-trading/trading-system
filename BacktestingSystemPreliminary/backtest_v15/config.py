from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class UniverseConfig:

    min_price: float = 0.0
    min_avg_dollar_vol_20d: float = 0.0
    min_1h_days: int = 0

@dataclass(frozen=True)
class DataConfig:
    cache_dir: str = "cache"
    auto_adjust: bool = True
    max_workers: int = 6

@dataclass(frozen=True)
class AggregationConfig:
    tz: str = "America/New_York"
    session_open: str = "09:30"
    session_close: str = "16:00"
    split_time: str = "13:30"  # session-aware 2 blocks/day => “synthetic 4H”

@dataclass(frozen=True)
class SlippageConfig:
    seed: int = 7
    max_atr_frac: float = 0.10  # max slippage = 10% of ATR

@dataclass(frozen=True)
class RiskConfig:
    base_risk: float = 0.01
    hard_cap: float = 0.02
    dd_brake_5: float = 0.01
    dd_brake_10: float = 0.005

@dataclass(frozen=True)
class StrategyConfig:
    pullback_min_bars: int = 2
    pullback_max_retrace: float = 0.50  # 50%
    atr_len: int = 14
    atr_ma_len: int = 20
    range_5d_bars: int = 10     # 5 trading days * 2 blocks/day
    range_20d_bars: int = 40    # 20 trading days * 2 blocks/day
    catalyst_max_age_days: int = 10  # trading days
    require_catalyst: bool = True

@dataclass(frozen=True)
class RegimeConfig:
    ref_ticker: str = "SPY"  # per v1.5 doc
    sma_fast: int = 50
    sma_slow: int = 200
    atr_len: int = 14
    atr_ma_len: int = 20
