from __future__ import annotations
import logging
from dataclasses import dataclass
import pandas as pd
import pytz
from .config import AggregationConfig
from .logging import log_kv
logger = logging.getLogger(__name__)

@dataclass
class BarAggregator:
    cfg: AggregationConfig

    def to_4h_session_aware(self, df_1h: pd.DataFrame) -> pd.DataFrame:
        """Builds synthetic 4H bars as 2 blocks/day for US regular session.


        Blocks:

        - Block 0: [09:30, 13:30)

        - Block 1: [13:30, 16:00]


        Input df_1h must be 1h OHLCV with tz-aware index or UTC. Output indexed by block-end timestamp (NY time).

        """
        log_kv(logger, logging.DEBUG, "AGG_START", bars_1h=(0 if df_1h is None else len(df_1h)))
        if df_1h is None or len(df_1h) == 0:
            return df_1h

        tz = pytz.timezone(self.cfg.tz)

        idx = df_1h.index
        # Convert to NY time for session logic
        if idx.tz is None:
            # assume UTC if missing tz
            idx_local = idx.tz_localize("UTC").tz_convert(tz)
        else:
            idx_local = idx.tz_convert(tz)

        df = df_1h.copy()
        df["_ts_local"] = idx_local
        df["_date"] = df["_ts_local"].dt.date
        df["_time"] = df["_ts_local"].dt.time

        open_t = pd.to_datetime(self.cfg.session_open).time()
        close_t = pd.to_datetime(self.cfg.session_close).time()
        split_t = pd.to_datetime(self.cfg.split_time).time()

        # Keep only regular session
        df = df[(df["_time"] >= open_t) & (df["_time"] <= close_t)]
        if len(df) == 0:
            return df_1h.iloc[0:0].copy()

        df["_block"] = (df["_time"] >= split_t).astype(int)

        # block end timestamp: set to split_time or close_time in local tz (vectorized)
        # df["_ts_local"] is already tz-aware in `tz`, so we can build "midnight + offset"
        # without per-row tz.localize().
        date_midnight = df["_ts_local"].dt.normalize()

        split_off = (
                pd.to_timedelta(split_t.hour, unit="h")
                + pd.to_timedelta(split_t.minute, unit="m")
        )
        close_off = (
                pd.to_timedelta(close_t.hour, unit="h")
                + pd.to_timedelta(close_t.minute, unit="m")
        )

        df["_block_end"] = date_midnight + split_off
        df.loc[df["_block"] == 1, "_block_end"] = date_midnight + close_off

        g = df.groupby("_block_end", sort=True)

        out = (
            g.agg(
                open=("open", "first"),
                high=("high", "max"),
                low=("low", "min"),
                close=("close", "last"),
                volume=("volume", "sum"),
            )
        )

        out.index.name = "Timestamp"
        log_kv(logger, logging.DEBUG, "AGG_DONE", bars_4h=len(out))
        return out
