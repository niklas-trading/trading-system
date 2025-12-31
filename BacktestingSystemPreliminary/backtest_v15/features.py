from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional
import pandas as pd

from .config import StrategyConfig
from .logging import log_kv
logger = logging.getLogger(__name__)
from .indicators import atr, rolling_range
from .structure import is_hh_hl, last_higher_low_close, detect_swings_close_only

@dataclass
class FeatureSnapshot:
    # trend/structure
    hh_hl: bool
    last_hl_close: Optional[float]
    # volatility
    atr: Optional[float]
    atr_ma: Optional[float]
    range5: Optional[float]
    range20: Optional[float]
    # pullback / impulse
    pullback_bars: int
    pullback_retrace: Optional[float]
    # volume impulse vs pullback
    vol_pullback_avg: Optional[float]
    vol_impulse_avg: Optional[float]

class FeatureBuilder:
    def __init__(self, cfg: StrategyConfig):
        self.cfg = cfg

    def snapshot(self, bars_4h: pd.DataFrame, asof_idx: int) -> FeatureSnapshot:
        log_kv(logger, logging.DEBUG, "FEATURE_SNAPSHOT", asof_idx=asof_idx, bars_4h=(0 if bars_4h is None else len(bars_4h)))
        df = bars_4h.iloc[: asof_idx + 1].copy()
        if len(df) < max(self.cfg.atr_len + self.cfg.atr_ma_len, self.cfg.range_20d_bars) + 5:
            log_kv(logger, logging.DEBUG, "FEATURE_INSUFFICIENT", have=len(df))
            log_kv(logger, logging.DEBUG, "FEATURE_OK", hh_hl=hh_hl, atr=float(df['ATR'].iloc[-1]) if 'ATR' in df.columns and pd.notna(df['ATR'].iloc[-1]) else None)
        return FeatureSnapshot(False, None, None, None, None, None, 0, None, None, None)

        close = df["Close"]
        hh_hl = is_hh_hl(close, 2, 2)
        last_hl = last_higher_low_close(close, 2, 2)

        df["ATR"] = atr(df, self.cfg.atr_len)
        df["ATR_MA"] = df["ATR"].rolling(self.cfg.atr_ma_len).mean()
        df["R5"] = rolling_range(df, self.cfg.range_5d_bars)
        df["R20"] = rolling_range(df, self.cfg.range_20d_bars)

        atr_v = float(df["ATR"].iloc[-1]) if pd.notna(df["ATR"].iloc[-1]) else None
        atr_ma_v = float(df["ATR_MA"].iloc[-1]) if pd.notna(df["ATR_MA"].iloc[-1]) else None
        r5 = float(df["R5"].iloc[-1]) if pd.notna(df["R5"].iloc[-1]) else None
        r20 = float(df["R20"].iloc[-1]) if pd.notna(df["R20"].iloc[-1]) else None

        pb_bars, pb_retrace, vol_pb, vol_imp = self._pullback_metrics(df)

        return FeatureSnapshot(
            hh_hl=hh_hl,
            last_hl_close=last_hl,
            atr=atr_v,
            atr_ma=atr_ma_v,
            range5=r5,
            range20=r20,
            pullback_bars=pb_bars,
            pullback_retrace=pb_retrace,
            vol_pullback_avg=vol_pb,
            vol_impulse_avg=vol_imp,
        )

    def _pullback_metrics(self, df: pd.DataFrame):
        # pullback bars: count consecutive bars where Close <= prev Close (sideways/down) from the end
        closes = df["Close"].values
        vols = df["Volume"].values
        n = len(df)
        pb = 0
        i = n - 1
        while i > 0 and closes[i] <= closes[i-1]:
            pb += 1
            i -= 1
        # require at least 1 previous bar; pb counts bars against trend ending at last bar
        # impulse: from last swing low to last swing high before pullback start
        pb_start = n - pb - 1  # index of last bar before pullback sequence (impulse end candidate)
        if pb < 1 or pb_start < 5:
            return pb, None, None, None

        # swing points on close-only
        swings = detect_swings_close_only(df["Close"], 2, 2)
        swing_lows = df["Close"][swings.swing_low]
        swing_highs = df["Close"][swings.swing_high]
        if len(swing_lows) == 0 or len(swing_highs) == 0:
            return pb, None, None, None

        # last swing high before pb_start
        highs_before = swing_highs[swing_highs.index <= df.index[pb_start]]
        lows_before = swing_lows[swing_lows.index <= df.index[pb_start]]
        if len(highs_before) == 0 or len(lows_before) == 0:
            return pb, None, None, None

        last_high = float(highs_before.iloc[-1])
        # choose last low before that high
        low_before_high = lows_before[lows_before.index <= highs_before.index[-1]]
        if len(low_before_high) == 0:
            return pb, None, None, None
        last_low = float(low_before_high.iloc[-1])

        impulse = last_high - last_low
        if impulse <= 0:
            return pb, None, None, None

        pb_low = float(df["Close"].iloc[-pb:].min())
        retrace = (last_high - pb_low) / impulse  # fraction retraced
        # volume: compare avg volume in pullback vs impulse window (from low->high)
        # approximate impulse window: last 6 bars ending at pb_start
        imp_start = max(0, pb_start - 6)
        vol_imp = float(np.mean(vols[imp_start:pb_start+1])) if (pb_start+1-imp_start) >= 2 else None
        vol_pb = float(np.mean(vols[n-pb:n])) if pb >= 1 else None

        return pb, float(retrace), vol_pb, vol_imp
