from __future__ import annotations
import logging
from dataclasses import dataclass
import random
import pandas as pd

from .config import SlippageConfig, RiskConfig
from .logging import log_kv
logger = logging.getLogger(__name__)
from .types import Position
from .features import FeatureSnapshot

@dataclass
class SlippageModel:
    cfg: SlippageConfig

    def __post_init__(self):
        self.rng = random.Random(self.cfg.seed)

    def apply(self, price: float, atr: float|None, side: str) -> float:
        log_kv(logger, logging.DEBUG, "SLIPPAGE_APPLY", price=price, atr=atr, side=side)
        if atr is None or atr <= 0:
            log_kv(logger, logging.DEBUG, "SLIPPAGE_NONE")
            return price
        slip = self.rng.uniform(0.0, self.cfg.max_atr_frac * atr)
        fill = price + slip if side.lower() == "buy" else price - slip
        log_kv(logger, logging.DEBUG, "SLIPPAGE_DONE", slip=slip, fill=fill)
        return fill

@dataclass
class RiskEngine:
    cfg: RiskConfig

    def risk_pct(self, equity: float, equity_high: float, dd: float, regime: str, catalyst_class: str) -> float:
        log_kv(logger, logging.DEBUG, "RISK_PCT", equity=equity, equity_high=equity_high, dd=dd, regime=regime, catalyst_class=catalyst_class)
        # factors per v1.5
        regime_factor = {"Defensiv": 0.5, "Neutral": 1.0, "Expansion": 1.5}.get(regime, 1.0)
        qual_factor = {"K2": 1.0, "K1": 1.2}.get(catalyst_class, 1.0)

        # equity factor
        if equity_high <= 0:
            equity_factor = 1.0
        else:
            if equity < equity_high:
                equity_factor = 1.0
            else:
                # equity at new high: measure vs previous high
                # Here we use the gain above the last high; if >5% then 1.25 else 1.1
                # Caller maintains equity_high as all-time-high, so compare to (equity_high_previous) externally.
                # We approximate by comparing equity to equity_high (current) -> equity_factor set by external in portfolio.
                equity_factor = 1.1

        rp = self.cfg.base_risk * regime_factor * qual_factor * equity_factor
        rp = min(rp, self.cfg.hard_cap)

        # drawdown brake (overrides)
        if dd >= 0.10:
            rp = min(rp, self.cfg.dd_brake_10)
        elif dd >= 0.05:
            rp = min(rp, self.cfg.dd_brake_5)

        return float(rp)

    @staticmethod
    def position_size(equity: float, risk_pct: float, entry: float, stop: float) -> float:
        log_kv(logger, logging.DEBUG, "POSITION_SIZE", equity=equity, risk_pct=risk_pct, entry=entry, stop=stop)
        money_risk = equity * risk_pct
        dist = abs(entry - stop)
        if dist <= 0:
            return 0.0
        return money_risk / dist

def compute_drawdown(equity: float, equity_high: float) -> float:
    if equity_high <= 0:
        return 0.0
    return max(0.0, (equity_high - equity) / equity_high)
