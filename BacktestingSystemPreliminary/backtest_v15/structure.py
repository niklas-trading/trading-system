from __future__ import annotations
import logging
from dataclasses import dataclass
import pandas as pd
from .logging import log_kv
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class SwingPoints:
    swing_high: pd.Series  # bool
    swing_low: pd.Series   # bool

def detect_swings_close_only(close: pd.Series, left: int = 2, right: int = 2) -> SwingPoints:
    log_kv(logger, logging.DEBUG, "STRUCT_SWINGS", rows=len(close), left=left, right=right)
    """Simple pivot detection on close-only.

    A swing high at t if close[t] is max in window [t-left, t+right].

    A swing low at t if close[t] is min in window.

    """
    c = close
    n = left + right + 1
    rolling_max = c.rolling(n, center=True).max()
    rolling_min = c.rolling(n, center=True).min()
    sh = (c == rolling_max)
    sl = (c == rolling_min)
    sh = sh.fillna(False)
    sl = sl.fillna(False)
    return SwingPoints(swing_high=sh, swing_low=sl)

def last_two_values(series: pd.Series, mask: pd.Series) -> tuple[float|None, float|None]:
    pts = series[mask]
    if len(pts) < 2:
        return None, None
    return float(pts.iloc[-2]), float(pts.iloc[-1])

def is_hh_hl(close: pd.Series, left: int = 2, right: int = 2) -> bool:
    log_kv(logger, logging.DEBUG, "STRUCT_HHHL_CHECK", rows=len(close))
    swings = detect_swings_close_only(close, left, right)
    hi2 = close[swings.swing_high]
    lo2 = close[swings.swing_low]
    if len(hi2) < 2 or len(lo2) < 2:
        return False
    # last two highs and lows must be higher
    return (hi2.iloc[-1] > hi2.iloc[-2]) and (lo2.iloc[-1] > lo2.iloc[-2])

def last_higher_low_close(close: pd.Series, left: int = 2, right: int = 2) -> float|None:
    swings = detect_swings_close_only(close, left, right)
    lows = close[swings.swing_low]
    if len(lows) == 0:
        return None
    return float(lows.iloc[-1])
