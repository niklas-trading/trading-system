from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Iterable, List, Optional
import pandas as pd
from .config import UniverseConfig
from .data import YFDataLoader

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
        for t in tickers:
            if self._passes_hygiene(t, start, end):
                accepted.append(t)
            if len(accepted) >= sample_size:
                break

        if len(accepted) < sample_size:
            raise RuntimeError(
                f"Universe too small after hygiene filters: {len(accepted)} < {sample_size}. " 
                f"Relax UniverseConfig or provide more tickers."
            )

        return [UniverseItem(t) for t in accepted]

    def _passes_hygiene(self, ticker: str, start: str, end: str) -> bool:
        # 1) Price + dollar volume from DAILY last ~60 trading days (fast)
        daily = self.loader.get_ohlcv(ticker, start=start, end=end, interval="1d")
        if daily is None or len(daily) < 30:
            return False

        last_close = float(daily["Close"].iloc[-1])
        if last_close <= self.cfg.min_price:
            return False

        dv = (daily["Close"] * daily["Volume"]).rolling(20).mean().iloc[-1]
        if pd.isna(dv) or float(dv) < self.cfg.min_avg_dollar_vol_20d:
            return False

        # 2) 1H history presence for at least cfg.min_1h_days
        # We check by attempting to download the last min_1h_days+30 calendar days in 1h bars.
        oneh = self.loader.get_ohlcv(ticker, start=None, end=None, interval="1h", lookback_days=self.cfg.min_1h_days + 30)
        if oneh is None or len(oneh) < 200:  # coarse sanity
            return False

        # Must span at least min_1h_days in time
        span_days = (oneh.index.max() - oneh.index.min()).days
        if span_days < self.cfg.min_1h_days:
            return False

        return True
