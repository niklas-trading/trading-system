from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class UniverseConfig:
    """Configuration for the UniverseBuilder.

    In the original implementation the universe pre‑screener applied
    additional liquidity filters on top of basic data hygiene (minimum
    price, minimum average dollar volume and a long lookback for
    intraday data).  These filters are not part of the user's trading
    rules described in `swing_trading_strategie_v_1_5.md` and would
    incorrectly bias the backtest by excluding otherwise valid
    instruments.  To honour the user's request to test the strategy
    exactly as specified, the defaults below disable those filters by
    setting them to zero.  Callers may override these values if they
    wish to apply stricter hygiene.
    """

    # Do not exclude tickers based on price by default.  Any positive
    # value here will enforce a minimum last close.  Set to zero to
    # accept all prices.
    min_price: float = 0.0

    # Do not exclude tickers based on average daily dollar volume by
    # default.  Any positive value here will enforce a minimum
    # liquidity filter on the daily data.  Set to zero to accept all
    # volumes.
    min_avg_dollar_vol_20d: float = 0.0  # USD

    # Minimum number of calendar days of 1H history required.  This
    # controls how far back the UniverseBuilder will look for intraday
    # data to ensure there is enough history to compute 4H features.
    # Setting this to zero will cause the hygiene checker to only
    # attempt a 30 day lookback (used for ATR and range) and will not
    # exclude symbols solely because they lack a full year of intraday
    # history.  This is useful when the user wants to test all NASDAQ
    # symbols without imposing artificial history constraints.
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

@dataclass(frozen=True)
class RegimeConfig:
    ref_ticker: str = "SPY"  # per v1.5 doc
    sma_fast: int = 50
    sma_slow: int = 200
    atr_len: int = 14
    atr_ma_len: int = 20
