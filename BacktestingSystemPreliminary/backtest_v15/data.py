from __future__ import annotations

import os
import hashlib
import logging
from dataclasses import dataclass
from typing import Optional

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


@dataclass
class YFDataLoader:
    cfg: DataConfig

    def __post_init__(self) -> None:
        _safe_mkdir(self.cfg.cache_dir)

    def get_ohlcv(
        self,
        ticker: str,
        start: Optional[str],
        end: Optional[str],
        interval: str,
        lookback_days: Optional[int] = None,
    ) -> Optional[pd.DataFrame]:
        """Download OHLCV via yfinance with optional on-disk caching.

        Returns a single-ticker DataFrame with columns: open, high, low, close, volume (lowercase).
        Returns None when data is unavailable or download fails.
        """
        cache_name = None
        path = None

        # Cache read
        if self.cfg.cache_dir:
            if lookback_days is not None:
                period = f"{int(lookback_days)}d"
                cache_name = _key(ticker, interval, period, str(self.cfg.auto_adjust))
            else:
                cache_name = _key(ticker, interval, str(start), str(end), str(self.cfg.auto_adjust))
            path = os.path.join(self.cfg.cache_dir, f"{cache_name}.parquet")

            log_kv(logger, logging.DEBUG, "DATA_CACHE_CHECK", ticker=ticker, interval=interval, path=path)
            if os.path.exists(path):
                log_kv(logger, logging.DEBUG, "DATA_CACHE_HIT", ticker=ticker, interval=interval, path=path)
                try:
                    df = pd.read_parquet(path)
                    if df is not None and len(df) > 0:
                        return df
                except Exception as e:
                    log_kv(logger, logging.WARNING, "DATA_CACHE_READ_FAIL", ticker=ticker, interval=interval, path=path, err=repr(e))

        # Download
        log_kv(logger, logging.DEBUG, "DATA_DOWNLOAD", ticker=ticker, interval=interval, start=start, end=end, lookback_days=lookback_days)
        try:
            if lookback_days is not None:
                df = yf.download(
                    ticker,
                    period=f"{int(lookback_days)}d",
                    interval=interval,
                    auto_adjust=self.cfg.auto_adjust,
                    progress=False,
                    threads=False,
                )
            else:
                df = yf.download(
                    ticker,
                    start=start,
                    end=end,
                    interval=interval,
                    auto_adjust=self.cfg.auto_adjust,
                    progress=False,
                    threads=False,
                )
        except Exception as e:
            log_kv(logger, logging.WARNING, "DATA_DOWNLOAD_EXCEPTION", ticker=ticker, interval=interval, err=repr(e))
            return None

        if df is None or len(df) == 0:
            log_kv(
                logger,
                logging.WARNING,
                "DATA_EMPTY_PRIMARY",
                ticker=ticker,
                interval=interval,
            )

            # HARD RULE: never do period-based fallback
            # Instead: try ANY cached OHLCV as universe-padding
            if self.cfg.cache_dir:
                fallback_df = _load_any_cached_ohlcv(self.cfg.cache_dir)
                if fallback_df is not None:
                    log_kv(
                        logger,
                        logging.WARNING,
                        "DATA_FALLBACK_FROM_CACHE",
                        ticker=ticker,
                        interval=interval,
                        rows=len(fallback_df),
                    )
                    return fallback_df

            log_kv(
                logger,
                logging.ERROR,
                "DATA_NO_FALLBACK_AVAILABLE",
                ticker=ticker,
                interval=interval,
            )
            return None


    # Flatten multi-index if present. yfinance returns DataFrame with MultiIndex columns where
        # level 0 is the field and level 1 is the ticker. For a single ticker, flatten using field names.
        if isinstance(df.columns, pd.MultiIndex):
            # capture the field names (level 0)
            raw_fields = [c[0] for c in df.columns]
            # lower-case field names to become columns
            df.columns = [f.lower() for f in raw_fields]
            log_kv(
                logger,
                logging.DEBUG,
                "DATA_MULTIINDEX_FLATTENED",
                ticker=ticker,
                interval=interval,
                fields=",".join(sorted(set(df.columns))),
            )
        else:
            # single-level columns: just lower-case them
            df.columns = [c.lower() for c in df.columns]

        # unify adj close to close if present
        if "adj close" in df.columns and "close" not in df.columns:
            df = df.rename(columns={"adj close": "close"})

        # verify we have expected columns
        expected = {"open", "high", "low", "close", "volume"}
        missing = expected - set(df.columns)
        if missing:
            log_kv(
                logger,
                logging.WARNING,
                "DATA_COLUMNS_INVALID",
                ticker=ticker,
                interval=interval,
                missing=",".join(sorted(missing)),
                columns=",".join(df.columns),
            )
            return None

        # drop any extra columns like dividends
        df = df[[col for col in df.columns if col in expected]]

        # drop rows where close is NaN
        df = df.dropna(subset=["close"])
        if len(df) == 0:
            log_kv(logger, logging.WARNING, "DATA_EMPTY_AFTER_CLEAN", ticker=ticker, interval=interval)
            return None

        log_kv(logger, logging.DEBUG, "DATA_OK", ticker=ticker, interval=interval, rows=len(df))

        # Cache write
        if self.cfg.cache_dir and cache_name is not None and path is not None:
            try:
                _safe_mkdir(self.cfg.cache_dir)
                df.to_parquet(path)
                log_kv(logger, logging.DEBUG, "DATA_CACHE_WRITE", ticker=ticker, interval=interval, path=path)
            except Exception as e:
                log_kv(logger, logging.WARNING, "DATA_CACHE_WRITE_FAIL", ticker=ticker, interval=interval, path=path, err=repr(e))

        return df

    def get_calendar(self, ticker: str) -> Optional[pd.DataFrame]:
        """Return yfinance ticker.calendar (earnings proxy), cached as parquet."""
        log_kv(logger, logging.DEBUG, "CALENDAR_FETCH", ticker=ticker)

        cache_name = None
        path = None
        if self.cfg.cache_dir:
            cache_name = _key(ticker, "calendar")
            path = os.path.join(self.cfg.cache_dir, f"{cache_name}.parquet")
            if os.path.exists(path):
                try:
                    cal = pd.read_parquet(path)
                    if cal is not None and len(cal) > 0:
                        log_kv(logger, logging.DEBUG, "CALENDAR_CACHE_HIT", ticker=ticker, path=path)
                        return cal
                except Exception as e:
                    log_kv(logger, logging.WARNING, "CALENDAR_CACHE_READ_FAIL", ticker=ticker, path=path, err=repr(e))

        try:
            cal = yf.Ticker(ticker).calendar
        except Exception as e:
            log_kv(logger, logging.WARNING, "CALENDAR_EXCEPTION", ticker=ticker, err=repr(e))
            return None

        if cal is None or len(cal) == 0:
            log_kv(logger, logging.DEBUG, "CALENDAR_EMPTY", ticker=ticker)
            return None

        try:
            cal = cal.copy()
        except Exception:
            pass

        if self.cfg.cache_dir and cache_name is not None and path is not None:
            try:
                _safe_mkdir(self.cfg.cache_dir)
                cal.to_parquet(path)
                log_kv(logger, logging.DEBUG, "CALENDAR_CACHE_WRITE", ticker=ticker, path=path)
            except Exception as e:
                log_kv(logger, logging.WARNING, "CALENDAR_CACHE_WRITE_FAIL", ticker=ticker, path=path, err=repr(e))

        log_kv(logger, logging.DEBUG, "CALENDAR_OK", ticker=ticker)
        return cal
