from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional, Tuple
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

    def get_earnings_catalyst(self, ticker: str, daily: pd.DataFrame, asof: pd.Timestamp, cal: pd.DataFrame, max_age_days: int = 10, ) -> CatalystInfo:
        log_kv(logger, logging.DEBUG, "CATALYST_CHECK", ticker=ticker, asof=str(asof.date()) if hasattr(asof,'date') else str(asof), max_age_days=max_age_days)
        """Uses yfinance calendar as a catalyst proxy (earnings date).

        Classification K1/K2 uses a simplified daily reaction check.

        """
        if daily is None or daily.empty:
            log_kv(logger, logging.DEBUG, "CATALYST_NONE", ticker=ticker, reason="NO_DAILY_BARS")
            return CatalystInfo(False, "NONE", None)
        if cal is None:
            log_kv(logger, logging.DEBUG, "CATALYST_NONE", ticker=ticker, reason="NO_CALENDAR")
            return CatalystInfo(False, "NONE", None)

        # attempt to find an earnings date
        earn_dt = None
        for col in cal.columns:
            if "earn" in str(col).lower():
                # many calendars store as list-like or Timestamp
                v = cal[col].iloc[0]
                if isinstance(v, (list, tuple)) and len(v) > 0:
                    earn_dt = pd.to_datetime(v[0])
                else:
                    earn_dt = pd.to_datetime(v)
                break
        if earn_dt is None or pd.isna(earn_dt):
            return CatalystInfo(False, "NONE", None)

        earn_dt = pd.Timestamp(earn_dt).normalize()

        # catalyst valid if within last max_age_days trading days relative to asof date
        asof_d = pd.Timestamp(asof).tz_localize(None).normalize()
        # map to trading days using daily index
        idx = pd.to_datetime(daily.index).normalize()
        if earn_dt not in set(idx):
            # allow nearest next trading day
            later = idx[idx >= earn_dt]
            if len(later) == 0:
                return CatalystInfo(False, "NONE", None)
            earn_dt = later[0]

        # compute age in trading days
        pos_earn = idx.get_loc(earn_dt)
        pos_asof = idx.get_loc(asof_d) if asof_d in set(idx) else None
        if pos_asof is None:
            # if asof is intraday, map to last daily bar <= asof
            prior = idx[idx <= asof_d]
            if len(prior) == 0:
                return CatalystInfo(False, "NONE", None)
            pos_asof = idx.get_loc(prior[-1])

        age = pos_asof - pos_earn
        if age < 0 or age > max_age_days:
            return CatalystInfo(False, "NONE", earn_dt)

        # classify reaction (simplified): check earnings-day bar only
        d = daily.copy()
        d.index = pd.to_datetime(d.index).normalize()
        d = d.loc[:asof_d]
        if len(d) < 60:
            return CatalystInfo(True, "K2", earn_dt)

        d["ATR"] = atr(d, 14)
        d["VOL_MA"] = d["volume"].rolling(20).mean()
        day = d.loc[earn_dt:earn_dt].iloc[0]

        # Criteria (count)
        c = 0
        # range >= 1.5*ATR and close in upper third
        rng = float(day["high"] - day["low"])
        if pd.notna(day["ATR"]) and day["ATR"] > 0:
            if rng >= 1.5 * float(day["ATR"]):
                if float(day["close"]) >= float(day["low"]) + (rng * (2/3)):
                    c += 1
        # close above last swing high (close-only)
        swings = detect_swings_close_only(d["close"], 2, 2)
        highs = d["close"][swings.swing_high]
        if len(highs) > 0:
            prev_high = float(highs.iloc[-1])
            if float(day["close"]) > prev_high:
                c += 1
        # volume >= 1.5*MA OR close pct >= 1.2%
        if pd.notna(day["VOL_MA"]) and float(day["VOL_MA"]) > 0:
            if float(day["volume"]) >= 1.5 * float(day["VOL_MA"]):
                c += 1
            else:
                # pct change vs prev close
                prev = d.loc[:earn_dt].iloc[-2]["close"] if len(d.loc[:earn_dt]) >= 2 else None
                if prev is not None and prev > 0:
                    if (float(day["close"]) / float(prev) - 1.0) >= 0.012:
                        c += 1

        cls = "K1" if c >= 2 else "K2"
        return CatalystInfo(True, cls, earn_dt)
