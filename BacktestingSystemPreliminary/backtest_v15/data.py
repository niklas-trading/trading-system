from __future__ import annotations
import os
import hashlib
from dataclasses import dataclass
from typing import Optional
import pandas as pd
import yfinance as yf

from .config import DataConfig

def _safe_mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _key(*parts: str) -> str:
    raw = "|".join(parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]

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
        """Returns OHLCV with columns Open/High/Low/Close/Volume and a DatetimeIndex.


        If lookback_days is provided, yfinance uses 'period' instead of start/end.

        Cached to parquet to reduce repeated downloads.

        """
        if lookback_days is not None:
            period = f"{int(lookback_days)}d"
            cache_name = _key(ticker, interval, period, str(self.cfg.auto_adjust))
        else:
            cache_name = _key(ticker, interval, str(start), str(end), str(self.cfg.auto_adjust))

        path = os.path.join(self.cfg.cache_dir, f"{cache_name}.parquet")
        if os.path.exists(path):
            try:
                return pd.read_parquet(path)
            except Exception:
                pass

        try:
            if lookback_days is not None:
                df = yf.download(
                    ticker,
                    period=period,
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
        except Exception:
            return None

        if df is None or len(df) == 0:
            return None

        # Normalize columns (yfinance sometimes uses multiindex for multiple tickers)
        if isinstance(df.columns, pd.MultiIndex):
            if ticker not in df.columns.get_level_values(0):
                return None
            df = df.xs(ticker, axis=1, level=0, drop_level=True)

        # standardize names
        rename = {c: c.title() for c in df.columns}
        df = df.rename(columns=rename)

        needed = ["Open", "High", "Low", "Close", "Volume"]
        if not all(c in df.columns for c in needed):
            return None

        df = df[needed].dropna()
        if len(df) == 0:
            return None

        # Ensure datetime index is tz-aware UTC for intraday. yfinance usually returns tz-aware for 1h.
        if df.index.tz is None:
            # treat as UTC-naive; leave naive (daily) to be localized later where needed
            pass

        try:
            df.to_parquet(path)
        except Exception:
            pass

        return df

    def get_calendar(self, ticker: str) -> Optional[pd.DataFrame]:
        """Returns yfinance ticker.calendar (earnings/dividends/splits). Cached as parquet."""
        cache_name = _key(ticker, "calendar")
        path = os.path.join(self.cfg.cache_dir, f"{cache_name}.parquet")
        if os.path.exists(path):
            try:
                return pd.read_parquet(path)
            except Exception:
                pass

        try:
            cal = yf.Ticker(ticker).calendar
        except Exception:
            return None

        if cal is None or len(cal) == 0:
            return None

        # cal often is a DataFrame with columns like 'Earnings Date'
        if isinstance(cal, pd.Series):
            cal = cal.to_frame()

        try:
            cal.to_parquet(path)
        except Exception:
            pass
        return cal
