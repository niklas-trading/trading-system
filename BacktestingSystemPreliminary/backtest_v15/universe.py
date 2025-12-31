from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Iterable, List, Optional
import pandas as pd
from .config import UniverseConfig
from .data import YFDataLoader
from .logging import log_kv
import logging


logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class UniverseItem:
    ticker: str

class UniverseBuilder:
    """Pre-screener: hygiene + random sampling. No alpha, no trend/ATR filters."""

    def __init__(self, cfg: UniverseConfig, loader: YFDataLoader):
        self.cfg = cfg
        self.loader = loader

    @staticmethod
    def read_tickers_file(path: str) -> List[str]:
        # one ticker per line; comments with '#'
        out = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                out.append(s)
        return out

    def build_random_sample(
        self,
        tickers: Iterable[str],
        start: str,
        end: str,
        sample_size: int = 100,
        seed: int = 42,
        progress: bool = True,
    ) -> List[UniverseItem]:
        tickers = list(dict.fromkeys(list(tickers)))
        rnd = random.Random(seed)
        rnd.shuffle(tickers)

        accepted: List[str] = []
        tested = 0
        rejected = 0
        for t in tickers:
            tested += 1
            log_kv(logger, logging.DEBUG, "UNIVERSE_TEST", ticker=t)
            if self._passes_hygiene(t, start, end):
                accepted.append(t)
                log_kv(logger, logging.DEBUG, "UNIVERSE_ACCEPT", ticker=t, accepted=len(accepted))
            if len(accepted) >= sample_size:
                break

        log_kv(logger, logging.INFO, "UNIVERSE_SUMMARY", requested=sample_size, accepted=len(accepted), tested=tested, rejected=rejected)
        if len(accepted) < sample_size:
            raise RuntimeError(
                f"Universe too small after hygiene filters: {len(accepted)} < {sample_size}. " 
                f"Relax UniverseConfig or provide more tickers."
            )

        return [UniverseItem(t) for t in accepted]

    def _passes_hygiene(self, ticker: str, start: str, end: str) -> bool:
        """Return True if the given ticker has enough data to perform a backtest.

        The hygiene check here is intentionally conservative: it verifies
        that we can fetch some daily and intraday data for the symbol in
        the backtest window.  It no longer filters on price or
        liquidity; those constraints are controlled by the trading
        strategy itself.  Intraday data is required because 4H bars are
        synthesised from 1H bars; however, we only insist on a short
        lookback instead of a full year to avoid excluding newer
        listings or thinly traded stocks.  If no intraday data is
        available the symbol is skipped.
        """
        # 1) Ensure there is at least some daily data in the sample
        daily = self.loader.get_ohlcv(ticker, start=start, end=end, interval="1d")
        if daily is None or len(daily) < 30:
            # Not enough daily bars to compute swing structure, ATR etc.
            return False

        # 2) Optionally enforce minimum price and average dollar volume if configured
        # When cfg.min_price or cfg.min_avg_dollar_vol_20d are zero the
        # following checks always pass.
        last_close = float(daily["Close"].iloc[-1])
        if self.cfg.min_price > 0 and last_close <= self.cfg.min_price:
            return False

        if self.cfg.min_avg_dollar_vol_20d > 0:
            dv = (daily["Close"] * daily["Volume"]).rolling(20).mean().iloc[-1]
            if pd.isna(dv) or float(dv) < self.cfg.min_avg_dollar_vol_20d:
                return False

        # 3) Check for availability of some 1H data to build synthetic 4H bars.  We
        # look back min_1h_days + 30 calendar days to ensure we have at
        # least a couple of weeks worth of intraday bars.  If the user
        # sets min_1h_days=0 this becomes a 30‑day lookback.
        oneh = self.loader.get_ohlcv(
            ticker,
            start=None,
            end=None,
            interval="1h",
            lookback_days=self.cfg.min_1h_days + 30,
        )
        if oneh is None or len(oneh) == 0:
            return False

        # If a specific minimum number of 1H days is requested, verify the span
        if self.cfg.min_1h_days > 0:
            span_days = (oneh.index.max() - oneh.index.min()).days
            if span_days < self.cfg.min_1h_days:
                return False

        return True
