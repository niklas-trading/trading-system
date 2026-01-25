from __future__ import annotations

import os
import hashlib
import logging
import re
from dataclasses import dataclass
from threading import Lock
from typing import Optional, List
from datetime import date
import pandas as pd
import yfinance as yf


from .config import DataConfig
from .logging import log_kv

logger = logging.getLogger(__name__)


def _safe_mkdir(path: str) -> None:
    if path:
        os.makedirs(path, exist_ok=True)


def _key(*parts: str) -> str:
    raw = "|".join(parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def _load_any_cached_ohlcv(cache_dir: str) -> Optional[pd.DataFrame]:
    if not cache_dir or not os.path.exists(cache_dir):
        return None

    for fname in os.listdir(cache_dir):
        if not fname.endswith(".parquet"):
            continue
        try:
            df = pd.read_parquet(os.path.join(cache_dir, fname))
            if df is not None and len(df) > 0:
                return df
        except Exception:
            continue

    return None


def aggregate_1d_from_1h(df_1h: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Aggregate 1H OHLCV bars into synthetic Daily bars (close-only semantics).
    """
    if df_1h is None or df_1h.empty:
        return None

    df = df_1h.copy()
    df.index = pd.to_datetime(df.index)

    daily = (
        df
        .resample("1D", label="right", closed="right")
        .agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        })
        .dropna()
    )

    return daily


@dataclass
class YFDataLoader:
    cfg: DataConfig

    def __post_init__(self) -> None:
        _safe_mkdir(self.cfg.cache_dir)
        # Build a lightweight in-memory index of cached OHLCV files to avoid
        # repeated os.listdir()+regex scans on every request.
        self._cache_lock = Lock()
        self._cache_index: dict[tuple[str, str], list[str]] = {}
        if self.cfg.cache_dir and os.path.exists(self.cfg.cache_dir):
            try:
                for fn in os.listdir(self.cfg.cache_dir):
                    if not fn.endswith(".parquet"):
                        continue
                    parts = fn.split("__")
                    if len(parts) < 4:
                        continue
                    safe_ticker, interval_l = parts[0], parts[1]
                    self._cache_index.setdefault((safe_ticker, interval_l), []).append(fn)
                # Prefer newest files first
                for k, files in self._cache_index.items():
                    files.sort(key=lambda f: os.path.getmtime(os.path.join(self.cfg.cache_dir, f)), reverse=True)
            except Exception:
                self._cache_index = {}

    @staticmethod
    def _normalize_ohlcv(df: pd.DataFrame, ticker: str | None = None) -> pd.DataFrame:
        if isinstance(df.columns, pd.MultiIndex):
            levels = df.columns.names
            # robust: versuche in letzter Ebene den ticker zu finden
            if ticker in df.columns.get_level_values(-1):
                df = df.xs(ticker, axis=1, level=-1, drop_level=True)
            else:
                # fallback: nimm Level 0 nur wenn du sicher bist, dass es nur einen Ticker ist
                df.columns = [c[0] for c in df.columns]

        df = df.rename(columns={c: str(c).lower() for c in df.columns})
        keep = [c for c in ["open","high","low","close","volume"] if c in df.columns]
        df = df[keep].copy()
        df = df.loc[:, ~df.columns.duplicated()].copy()
        df.index = pd.to_datetime(df.index)
        return df

    def get_ohlcv(self, ticker: str, start: str | None, end: str | None, interval: str = "1d",lookback_days: int | None = None,) -> pd.DataFrame | None:
        """
        Fetch OHLCV data via yfinance with disk caching.
        """
        interval_l = str(interval).lower()

        start_eff = pd.Timestamp(start).normalize()
        end_eff = pd.Timestamp(end).normalize()

        if start_eff is not None and end_eff is not None and start_eff >= end_eff:
            log_kv(logger,logging.WARNING,"DATA_WINDOW_INVALID",ticker=ticker,interval=interval_l,start=str(start_eff),end=str(end_eff),)
            return None

        cache_path = None
        if self.cfg.cache_dir:
            os.makedirs(self.cfg.cache_dir, exist_ok=True)
            start_key = start_eff.date().isoformat() if start_eff is not None else "NA"
            end_key = end_eff.date().isoformat() if end_eff is not None else "NA"
            safe_ticker = re.sub(r"[^A-Za-z0-9\-_\.]+", "_", ticker)
            cache_name = f"{safe_ticker}__{interval_l}__{start_key}__{end_key}.parquet"
            cache_path = os.path.join(self.cfg.cache_dir, cache_name)

            pattern = rf"^{re.escape(safe_ticker)}__{re.escape(interval_l)}__.*__.*\.parquet$"

            log_kv(logger,logging.INFO,"SEARCHING_CACHE",ticker=ticker)

            # Fast path: consult in-memory cache index to avoid scanning the directory each call
            with self._cache_lock:
                candidates = list(self._cache_index.get((safe_ticker, interval_l), ()))

            for filename in candidates:
                try:
                    df = self._normalize_ohlcv(pd.read_parquet(os.path.join(self.cfg.cache_dir, filename)))
                    log_kv(logger, logging.DEBUG, "DATA_CACHE_HIT",
                           ticker=ticker, interval=interval_l,
                           path=os.path.join(self.cfg.cache_dir, filename),
                           rows=len(df))
                    return df
                except Exception as e:
                    log_kv(logger, logging.WARNING, "DATA_CACHE_READ_FAIL",
                           ticker=ticker, interval=interval_l,
                           path=os.path.join(self.cfg.cache_dir, filename),
                           err=str(e))


        try:
            log_kv(logger,logging.DEBUG,"DATA_DOWNLOAD",ticker=ticker,interval=interval_l,start=str(start_eff),end=str(end_eff),)
            df = yf.download(tickers=ticker,start=start_eff,end=end_eff,interval=interval_l,group_by="column",auto_adjust=False,progress=False,threads=False,)
        except Exception as e:
            log_kv(logger,logging.WARNING,"DATA_DOWNLOAD_FAIL",ticker=ticker,interval=interval_l,err=str(e),)
            df = None

        if df is None or len(df) == 0:
            log_kv(logger, logging.WARNING, "DATA_EMPTY_PRIMARY", ticker=ticker, interval=interval_l)
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]

        df = df.rename(columns={c: c.lower() for c in df.columns})
        keep = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
        df = df[keep]

        if cache_path is not None:
            try:
                df = self._normalize_ohlcv(df)
                df.to_parquet(cache_path, index=True)
                fn = os.path.basename(cache_path)
                with self._cache_lock:
                    key = (safe_ticker, interval_l)
                    lst = self._cache_index.setdefault(key, [])
                    if fn in lst:
                        lst.remove(fn)
                    lst.insert(0, fn)
            except Exception:
                pass

        return df

    def get_calendar(self, ticker: str, start: date, end: date) -> List[pd.Timestamp]:
        """
        Return yfinance earnings dates for a ticker as a DatetimeIndex.
        """
        ticker = yf.Ticker(ticker)
        df = ticker.get_earnings_dates(limit = 24)
        if df is None or df.empty:
            return []
        index = pd.to_datetime(df.index).tz_convert(None).normalize()
        log_kv(logger,logging.DEBUG,"CALENDAR_FOUND",ticker=ticker,start=start, end= end)
        return [pd.Timestamp(date.date()) for date in index[(index >= pd.Timestamp(start)) & (index <= pd.Timestamp(end))].unique()]