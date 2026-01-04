from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List
import logging
import pandas as pd

from .config import UniverseConfig
from .data import YFDataLoader, aggregate_1d_from_1h
from .logging import log_kv

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UniverseItem:
    ticker: str


class UniverseBuilder:
    """Pre-screener: hygiene + random sampling. Strategy-conform."""

    def __init__(self, cfg: UniverseConfig, loader: YFDataLoader):
        self.cfg = cfg
        self.loader = loader

    @staticmethod
    def read_tickers_file(path: str) -> List[str]:
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

            tu = t.upper()
            if tu.endswith(("W", "WS", "U", "R")):
                rejected += 1
                continue

            if self._passes_hygiene(t, start, end):
                accepted.append(t)
                log_kv(logger, logging.DEBUG, "UNIVERSE_ACCEPT", ticker=t, accepted=len(accepted))
            else:
                rejected += 1

            if len(accepted) >= sample_size:
                break

        log_kv(
            logger,
            logging.INFO,
            "UNIVERSE_SUMMARY",
            requested=sample_size,
            accepted=len(accepted),
            tested=tested,
            rejected=rejected,
        )

        if len(accepted) < sample_size:
            raise RuntimeError(
                f"Universe too small after hygiene filters: {len(accepted)} < {sample_size}"
            )

        return [UniverseItem(t) for t in accepted]

    def _passes_hygiene(self, ticker: str, start: str, end: str) -> bool:
        """
        Strategy-conform hygiene:
        - load 1H data
        - derive synthetic Daily from 1H
        """

        oneh = self.loader.get_ohlcv(
            ticker=ticker,
            start=start,
            end=end,
            interval="1h",
        )

        if oneh is None or len(oneh) < 50:
            log_kv(logger, logging.DEBUG, "UNIVERSE_REJECT", ticker=ticker, reason="NO_1H_DATA")
            return False

        daily = aggregate_1d_from_1h(oneh)
        if daily is None or len(daily) < 20:
            log_kv(logger, logging.DEBUG, "UNIVERSE_REJECT", ticker=ticker, reason="NO_DERIVED_DAILY")
            return False

        return True
