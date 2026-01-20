from __future__ import annotations

import logging
from dataclasses import dataclass
import pandas as pd

from .config import RegimeConfig
from .logging import log_kv
from .data import YFDataLoader, aggregate_1d_from_1h
from .indicators import sma, atr

logger = logging.getLogger(__name__)

def classify_daily_regime(d: pd.DataFrame) -> pd.Series:
    """
    Erwartet Spalten: close, SMA_F, SMA_S, ATR, ATR_MA
    Gibt pd.Series[str|None] zurück (Index wie d.index).
    """
    # NaN-Guard (Indikatoren noch nicht “warmgelaufen”)
    ready = (
            d["SMA_F"].notna()
            & d["SMA_S"].notna()
            & d["ATR"].notna()
            & d["ATR_MA"].notna()
    )

    out = pd.Series(index=d.index, dtype="object")
    out.loc[~ready] = None

    close = d["close"]

    defensiv = ready & (close < d["SMA_S"])
    expansion = ready & (close > d["SMA_F"]) & (d["ATR"] >= d["ATR_MA"])
    neutral = ready & ~defensiv & ~expansion

    out.loc[defensiv] = "Defensiv"
    out.loc[expansion] = "Expansion"
    out.loc[neutral] = "Neutral"

    return out

@dataclass
class RegimeEngine:
    cfg: RegimeConfig
    loader: YFDataLoader

    def compute_weekly_regime(self, daily: dict[str, pd.DataFrame]) -> dict[str, pd.Series]:
        """
        Returns a daily-indexed Series with regime values that are held constant
        for the next week.

        Strategy-conform:
        - 1H is the only external data source
        - Daily is derived from 1H
        - Regime computed on daily close (synthetic)
        """
        regimes: dict[str, pd.Series] = {}
        for ticker, df in daily.items():
            if df is None: # or len(df) < max(self.cfg.sma_slow,self.cfg.atr_len + self.cfg.atr_ma_len,) + 10:
                raise RuntimeError("Not enough derived daily data for regime computation.")

            d = df.copy()

            # 3) Indicators (close-only)
            d["SMA_F"] = sma(d["close"], self.cfg.sma_fast)
            d["SMA_S"] = sma(d["close"], self.cfg.sma_slow)
            d["ATR"] = atr(d, self.cfg.atr_len)
            d["ATR_MA"] = d["ATR"].rolling(self.cfg.atr_ma_len).mean()

            d["Regime_Daily"] = classify_daily_regime(d)

            # 5) Weekly regime: use last close of each week (Fri)
            d = d.dropna(subset=["Regime_Daily"])
            d["Week"] = pd.to_datetime(d.index).to_period("W-FRI")
            weekly = d.groupby("Week")["Regime_Daily"].last()

            # 6) Expand weekly regime to daily index (applies to NEXT week)
            daily_idx = pd.to_datetime(df.index)
            out = pd.Series(index=daily_idx, dtype="object")

            weeks = daily_idx.to_period("W-FRI")
            for w in weeks.unique():
                reg = weekly.get(w, None)
                next_w = w + 1
                mask = weeks == next_w
                if reg is not None:
                    out.loc[mask] = reg

            regimes[ticker] = out.ffill()
        return regimes
