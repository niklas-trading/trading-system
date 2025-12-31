from __future__ import annotations
import numpy as np
import pandas as pd

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
    tr = true_range(df["High"], df["Low"], df["Close"])
    return tr.rolling(n).mean()

def rolling_range(df: pd.DataFrame, n: int) -> pd.Series:
    hh = df["High"].rolling(n).max()
    ll = df["Low"].rolling(n).min()
    return hh - ll

def pct_change(s: pd.Series, n: int = 1) -> pd.Series:
    return s.pct_change(n)
