from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional, Tuple, List
import pandas as pd
from .data import YFDataLoader
from .indicators import atr, pct_change
from .structure import detect_swings_close_only
from .logging import log_kv
logger = logging.getLogger(__name__)

@dataclass
class CatalystInfo:
    has_catalyst: bool
    catalyst_class: str  # K1 or K2 or NONE
    catalyst_date: Optional[pd.Timestamp]

@dataclass
class CatalystEngine:
    loader: YFDataLoader

    def get_earnings_catalyst(self, ticker: str, current_ts: pd.Timestamp, cal: List[pd.Timestamp]) -> CatalystInfo:
        log_kv(logger, logging.DEBUG, "CATALYST_CHECK", ticker=ticker, asof=str(current_ts.date()) if hasattr(current_ts, 'date') else str(current_ts))
        """Uses yfinance calendar as a catalyst proxy (earnings date).

        Classification K1/K2 uses a simplified daily reaction check.

        """
        if cal is None or len(cal) == 0:
            log_kv(logger, logging.DEBUG, "CATALYST_NONE", ticker=ticker, reason="NO_CALENDAR")
            return CatalystInfo(False, "NONE", None)

        for earnings_date in cal:
            if earnings_date > current_ts:
                break
            if earnings_date <= current_ts <= earnings_date + pd.Timedelta(days=14):
                return CatalystInfo(True, "K1", earnings_date)
        return CatalystInfo(False, "NONE", None)


