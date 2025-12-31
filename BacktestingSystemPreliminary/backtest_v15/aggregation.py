from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
import pytz
from .config import AggregationConfig

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

        # block end timestamp: set to split_time or close_time in local tz
        def _block_end(row):
            t = split_t if row["_block"] == 0 else close_t
            # combine date + time and localize
            return tz.localize(pd.Timestamp.combine(row["_date"], t))

        df["_block_end"] = df.apply(_block_end, axis=1)

        g = df.groupby("_block_end", sort=True)

        out = pd.DataFrame({
            "Open": g["Open"].first(),
            "High": g["High"].max(),
            "Low":  g["Low"].min(),
            "Close": g["Close"].last(),
            "Volume": g["Volume"].sum(),
        })

        out.index.name = "Timestamp"
        return out
