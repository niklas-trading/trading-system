from __future__ import annotations

import logging
from dataclasses import dataclass
import pandas as pd

from .config import RegimeConfig
from .logging import log_kv
from .data import YFDataLoader, aggregate_1d_from_1h
from .indicators import sma, atr

logger = logging.getLogger(__name__)


@dataclass
class RegimeEngine:
    cfg: RegimeConfig
    loader: YFDataLoader

    def compute_weekly_regime(self, start: str, end: str) -> pd.Series:
        """
        Returns a daily-indexed Series with regime values that are held constant
        for the next week.

        Strategy-conform:
        - 1H is the only external data source
        - Daily is derived from 1H
        - Regime computed on daily close (synthetic)
        """

        log_kv(
            logger,
            logging.INFO,
            "REGIME_START",
            ref=self.cfg.ref_ticker,
            start=start,
            end=end,
        )

        # 1) Load 1H data (ONLY source of truth)
        oneh = self.loader.get_ohlcv(
            self.cfg.ref_ticker,
            start=start,
            end=end,
            interval="1h",
        )

        if oneh is None or len(oneh) < 50:
            raise RuntimeError("Not enough 1H data for regime computation.")

        # 2) Aggregate synthetic Daily from 1H
        df = aggregate_1d_from_1h(oneh)
        if df is None or len(df) < max(
                self.cfg.sma_slow,
                self.cfg.atr_len + self.cfg.atr_ma_len,
        ) + 10:
            raise RuntimeError("Not enough derived daily data for regime computation.")

        d = df.copy()

        # 3) Indicators (close-only)
        d["SMA_F"] = sma(d["close"], self.cfg.sma_fast)
        d["SMA_S"] = sma(d["close"], self.cfg.sma_slow)
        d["ATR"] = atr(d, self.cfg.atr_len)
        d["ATR_MA"] = d["ATR"].rolling(self.cfg.atr_ma_len).mean()

        # 4) Daily regime classification (close-only)
        def _reg(row):
            if (
                    pd.isna(row["SMA_F"])
                    or pd.isna(row["SMA_S"])
                    or pd.isna(row["ATR"])
                    or pd.isna(row["ATR_MA"])
            ):
                return None

            close = row["close"]

            if close < row["SMA_S"]:
                return "Defensiv"

            if (close > row["SMA_F"]) and (row["ATR"] >= row["ATR_MA"]):
                return "Expansion"

            return "Neutral"

        d["Regime_Daily"] = d.apply(_reg, axis=1)

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

        out = out.ffill()
        return out
