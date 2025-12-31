from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from .config import RegimeConfig
from .data import YFDataLoader
from .indicators import sma, atr

@dataclass
class RegimeEngine:
    cfg: RegimeConfig
    loader: YFDataLoader

    def compute_weekly_regime(self, start: str, end: str) -> pd.Series:
        """Returns a daily-indexed Series with regime values that are held constant for the next week.

        Regime computed on weekly close (Friday) using daily data, applied to next week's dates.

        """
        df = self.loader.get_ohlcv(self.cfg.ref_ticker, start=start, end=end, interval="1d")
        if df is None or len(df) < max(self.cfg.sma_slow, self.cfg.atr_len + self.cfg.atr_ma_len) + 10:
            raise RuntimeError("Not enough data for regime computation.")

        d = df.copy()
        d["SMA_F"] = sma(d["Close"], self.cfg.sma_fast)
        d["SMA_S"] = sma(d["Close"], self.cfg.sma_slow)
        d["ATR"] = atr(d, self.cfg.atr_len)
        d["ATR_MA"] = d["ATR"].rolling(self.cfg.atr_ma_len).mean()

        # Determine regime on each day (close-only)
        def _reg(row):
            if pd.isna(row["SMA_F"]) or pd.isna(row["SMA_S"]) or pd.isna(row["ATR"]) or pd.isna(row["ATR_MA"]):
                return None
            close = row["Close"]
            if close < row["SMA_S"]:
                return "Defensiv"
            if (close > row["SMA_F"]) and (row["ATR"] >= row["ATR_MA"]):
                return "Expansion"
            return "Neutral"

        d["Regime_Daily"] = d.apply(_reg, axis=1)

        # Hold regime per next week based on last weekday (Fri) available
        d = d.dropna(subset=["Regime_Daily"])
        d["Week"] = pd.to_datetime(d.index).to_period("W-FRI")
        weekly = d.groupby("Week")["Regime_Daily"].last()

        # Expand weekly to daily for application: regime determined at week end applies to next week
        daily_idx = pd.to_datetime(df.index)
        out = pd.Series(index=daily_idx, dtype="object")
        weeks = daily_idx.to_period("W-FRI")
        for w in weeks.unique():
            # regime known at end of week w; apply to week w+1
            reg = weekly.get(w, None)
            next_w = (w + 1)
            mask = (weeks == next_w)
            if reg is not None:
                out.loc[mask] = reg
        out = out.ffill()
        return out
