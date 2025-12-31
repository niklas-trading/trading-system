from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import pandas as pd
import logging
from .logging import log_kv

logger = logging.getLogger(__name__)


from .config import StrategyConfig
from .types import Signal, SignalType
from .features import FeatureSnapshot
from .catalyst import CatalystInfo

@dataclass
class StrategyV15:
    cfg: StrategyConfig

    def evaluate(self, bars_4h: pd.DataFrame, idx: int, feat: FeatureSnapshot, cat: CatalystInfo, in_position: bool) -> Signal:
        reasons = []
        # Map internal reason tags to stable debug reason codes
        REASON_MAP = {
            "NO_TREND_HHHL": "FAIL_TREND_STRUCTURE",
            "VOL_FILTER_FAIL": "FAIL_ATR_CONTRACTION",
            "NO_CATALYST": "FAIL_NO_CATALYST",
            "PULLBACK_TOO_SHORT": "FAIL_PULLBACK_TOO_SHORT",
            "PULLBACK_TOO_DEEP": "FAIL_PULLBACK_TOO_DEEP",
            "PULLBACK_VOL_NOT_LOWER": "FAIL_PULLBACK_VOLUME",
            "TRIGGER_NOT_MET": "FAIL_TRIGGER_CLOSE",
        }


        bar_ts = bars_4h.index[idx] if bars_4h is not None and len(bars_4h) > idx else None
        # Not enough data safety
        if idx < 5:
            return Signal(SignalType.NONE, ("DATA_TOO_SHORT",), {})

        # ENTRY logic
        if not in_position:
            # 1) Trend HH/HL (Close-only)
            if not feat.hh_hl:
                reasons.append("NO_TREND_HHHL")
            # 2) Volatility filter: at least one condition
            vol_ok = False
            if feat.atr is not None and feat.atr_ma is not None and feat.atr > feat.atr_ma:
                vol_ok = True
            if feat.range5 is not None and feat.range20 is not None and feat.range20 > 0 and feat.range5 >= 1.3 * feat.range20:
                vol_ok = True
            if cat.has_catalyst:
                vol_ok = True
            if not vol_ok:
                reasons.append("VOL_FILTER_FAIL")
            # 3) Catalyst required
            if not cat.has_catalyst:
                reasons.append("NO_CATALYST")
            # 4) Pullback rules
            if feat.pullback_bars < self.cfg.pullback_min_bars:
                reasons.append("PULLBACK_TOO_SHORT")
            if feat.pullback_retrace is None or feat.pullback_retrace > self.cfg.pullback_max_retrace:
                reasons.append("PULLBACK_TOO_DEEP")
            # 5) Structural stop: no close under last HL
            if feat.last_hl_close is None:
                reasons.append("NO_LAST_HL")
            else:
                if float(bars_4h["Close"].iloc[idx]) < float(feat.last_hl_close):
                    reasons.append("CLOSE_BELOW_LAST_HL")
            # 6) Volume filter v1.5: pullback avg volume must be <= impulse avg volume
            if (feat.vol_pullback_avg is None) or (feat.vol_impulse_avg is None):
                reasons.append("VOLUME_METRICS_MISSING")
            else:
                if feat.vol_pullback_avg > feat.vol_impulse_avg:
                    reasons.append("PULLBACK_VOL_NOT_LOWER")
            # 7) Trigger: Close > High(prev bar)
            if float(bars_4h["Close"].iloc[idx]) <= float(bars_4h["High"].iloc[idx-1]):
                reasons.append("TRIGGER_NOT_MET")

            if len(reasons) == 0:
                return Signal(SignalType.ENTRY, (), {"catalyst_class": cat.catalyst_class})
            return Signal(SignalType.NONE, tuple(reasons), {})

        # EXIT logic (close-only)
        else:
            # Stop / trend break handled by Execution/Risk layer using stop_close and trend state.
            # Strategy can propose EXIT on trend break (close-only).
            if not feat.hh_hl:
                return Signal(SignalType.EXIT, ("TREND_BREAK",), {})
            return Signal(SignalType.NONE, (), {})
