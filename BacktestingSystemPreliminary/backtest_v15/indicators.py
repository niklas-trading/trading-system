from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from .logging import log_kv
logger = logging.getLogger(__name__)

def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()

def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr

def atr(df: pd.DataFrame, n: int) -> pd.Series:
    log_kv(logger, logging.DEBUG, "IND_ATR", n=n, rows=(0 if df is None else len(df)))
    tr = true_range(df["High"], df["Low"], df["Close"])
    out = tr.rolling(n).mean()
    if out.isna().all():
        log_kv(logger, logging.DEBUG, "IND_ATR_ALL_NA", n=n)
    return out

def rolling_range(df: pd.DataFrame, n: int) -> pd.Series:
    log_kv(logger, logging.DEBUG, "IND_RANGE", n=n, rows=(0 if df is None else len(df)))
    hh = df["High"].rolling(n).max()
    ll = df["Low"].rolling(n).min()
    out = hh - ll
    if out.isna().all():
        log_kv(logger, logging.DEBUG, "IND_RANGE_ALL_NA", n=n)
    return out

def pct_change(s: pd.Series, n: int = 1) -> pd.Series:
    return s.pct_change(n)
