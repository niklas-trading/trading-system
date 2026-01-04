from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from .config import StrategyConfig
from .logging import log_kv
logger = logging.getLogger(__name__)
from .indicators import atr, rolling_range, sma
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
        """Compute the feature snapshot at a specific bar index.

        bars_4h is expected to have lowercase OHLCV columns: open/high/low/close/volume.
        """
        if bars_4h is None or len(bars_4h) == 0:
            log_kv(logger, logging.DEBUG, "FEATURE_EMPTY_INPUT")
            return FeatureSnapshot(False, None, None, None, None, None, None, None, None)

        # Use all data up to and including asof_idx
        asof_idx = int(asof_idx)
        if asof_idx < 0:
            return FeatureSnapshot(False, None, None, None, None, None, None, None, None)
        df = bars_4h.iloc[: asof_idx + 1].copy()

        required = max(
            int(getattr(self.cfg, "range_20d_bars", 120)),
            int(getattr(self.cfg, "atr_len", 14)) + int(getattr(self.cfg, "atr_ma_len", 20)) + 5,
            60,
        )
        if len(df) < required:
            log_kv(logger, logging.DEBUG, "FEATURE_INSUFFICIENT", have=len(df), need=required)
            return FeatureSnapshot(False, None, None, None, None, None, None, None, None, None)

        # Core indicators
        df["ATR"] = atr(df, int(self.cfg.atr_len))
        df["ATR_MA"] = sma(df["ATR"], int(self.cfg.atr_ma_len))
        df["R5"] = rolling_range(df, int(self.cfg.range_5d_bars))
        df["R20"] = rolling_range(df, int(self.cfg.range_20d_bars))

        hh_hl = is_hh_hl(df["close"], 2, 2)
        last_hl = last_higher_low_close(df["close"], 2, 2)

        atr_v = float(df["ATR"].iloc[-1]) if pd.notna(df["ATR"].iloc[-1]) else None
        atr_ma_v = float(df["ATR_MA"].iloc[-1]) if pd.notna(df["ATR_MA"].iloc[-1]) else None
        atr_ratio = (atr_v / atr_ma_v) if (atr_v is not None and atr_ma_v not in (None, 0.0) and pd.notna(atr_ma_v)) else None

        pb, retrace, vol_pb, vol_imp = self._pullback_metrics(df)

        r5 = float(df["R5"].iloc[-1]) if pd.notna(df["R5"].iloc[-1]) else None
        r20 = float(df["R20"].iloc[-1]) if pd.notna(df["R20"].iloc[-1]) else None

        log_kv(
            logger,
            logging.DEBUG,
            "FEATURE_OK",
            hh_hl=hh_hl,
            last_hl=last_hl,
            atr=atr_v,
            atr_ma=atr_ma_v,
            atr_ratio=atr_ratio,
            pb=pb,
            retrace=retrace,
            vol_pullback_avg=vol_pb,
            vol_impulse_avg=vol_imp,
            r5=r5,
            r20=r20
        )

        return FeatureSnapshot(
            hh_hl=hh_hl,
            last_hl_close=last_hl,
            atr=atr_v,
            atr_ma=atr_ma_v,
            range5=r5,
            range20=r20,
            pullback_bars=pb,
            pullback_retrace=retrace,
            vol_pullback_avg=vol_pb,
            vol_impulse_avg=vol_imp,
        )



    def _pullback_metrics(self, df: pd.DataFrame):
        if df is None or len(df) < 5:
            return 0, None, None, None

        swings = detect_swings_close_only(df["close"], 2, 2)

        low_idx = df.index[swings.swing_low].tolist()
        high_idx = df.index[swings.swing_high].tolist()

        if not low_idx or not high_idx:
            return 0, None, None, None

        last_low = low_idx[-1]
        last_high = high_idx[-1]

        if last_low >= last_high:
            return 0, None, None, None

        impulse = df.loc[last_low:last_high]

        pos_high = df.index.get_loc(last_high)
        pullback = df.iloc[pos_high + 1 :]

        pullback_bars = len(pullback)

        impulse_low = impulse["low"].min()
        impulse_high = impulse["high"].max()
        rng = impulse_high - impulse_low

        retrace = None
        if pullback_bars > 0 and rng > 0:
            retrace = (impulse_high - pullback["low"].min()) / rng

        vol_imp = impulse["volume"].mean() if "volume" in impulse else None
        vol_pb = pullback["volume"].mean() if pullback_bars > 0 else None

        return pullback_bars, retrace, vol_pb, vol_imp
