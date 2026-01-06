from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Dict, List
import pandas as pd
from tqdm import tqdm

from .config import StrategyConfig, SlippageConfig, RiskConfig, AggregationConfig, RegimeConfig
from .logging import log_kv
logger = logging.getLogger(__name__)
from .data import YFDataLoader, aggregate_1d_from_1h
from .aggregation import BarAggregator
from .features import FeatureBuilder
from .catalyst import CatalystEngine
from .strategy_v15 import StrategyV15
from .execution import SlippageModel, RiskEngine, compute_drawdown
from .portfolio import Portfolio
from .types import Position, SignalType
from .regime import RegimeEngine

@dataclass
class BacktestParams:
    start: str
    end: str
    initial_equity: float = 10_000.0

class Backtester:
    def __init__(
        self,
        loader: YFDataLoader,
        agg_cfg: AggregationConfig,
        strat_cfg: StrategyConfig,
        slip_cfg: SlippageConfig,
        risk_cfg: RiskConfig,
        regime_cfg: RegimeConfig,
    ):
        self.loader = loader
        self.aggregator = BarAggregator(agg_cfg)
        self.feats = FeatureBuilder(strat_cfg)
        self.catalyst = CatalystEngine(loader)
        self.strategy = StrategyV15(strat_cfg)
        self.slip = SlippageModel(slip_cfg)
        self.risk = RiskEngine(risk_cfg)
        self.regime_engine = RegimeEngine(regime_cfg, loader)

    def run(self, tickers: List[str], params: BacktestParams, show_progress: bool = True) -> Portfolio:
        log_kv(logger, logging.INFO, "BACKTEST_START", tickers=len(tickers), start=params.start, end=params.end)
        # regime feed (daily), later mapped to intraday timestamps
        regime_daily = self.regime_engine.compute_weekly_regime(params.start, params.end)

        # load & aggregate all tickers
        bars_4h: Dict[str, pd.DataFrame] = {}
        daily: Dict[str, pd.DataFrame] = {}
        for t in tqdm(tickers, disable=not show_progress, desc="Downloading"):
            log_kv(logger, logging.DEBUG, "BT_TICKER_DOWNLOAD", ticker=t)
            d1h = self.loader.get_ohlcv(t, start=params.start, end=params.end, interval="1h")
            if d1h is None or len(d1h) == 0:
                log_kv(logger, logging.DEBUG, "BT_TICKER_SKIP", ticker=t, reason="NO_1H_DATA")
                continue
            b4 = self.aggregator.to_4h_session_aware(d1h)
            if b4 is None or len(b4) < 200:
                log_kv(logger, logging.DEBUG, "BT_TICKER_SKIP", ticker=t, reason="INSUFFICIENT_4H_BARS", bars_4h=(0 if b4 is None else len(b4)))
                continue

            d1 = aggregate_1d_from_1h(d1h)
            if d1 is not None and len(d1) > 0:
                daily[t] = d1
            bars_4h[t] = b4

        if len(bars_4h) == 0:
            raise RuntimeError("No instruments with sufficient 4H data.")

        # build global event timeline
        all_ts = sorted(set().union(*[set(df.index) for df in bars_4h.values()]))
        portfolio = Portfolio(equity=params.initial_equity, equity_high=params.initial_equity)

        # helper to map intraday ts to daily regime (use date in local tz if tz-aware)
        def get_regime(ts: pd.Timestamp) -> str:
            d = ts.tz_localize(None).normalize()
            if d in regime_daily.index:
                v = regime_daily.loc[d]
                return str(v) if pd.notna(v) else "Neutral"
            # if missing, forward fill
            prior = regime_daily.loc[:d].dropna()
            return str(prior.iloc[-1]) if len(prior) else "Neutral"

        # main loop
        it = tqdm(all_ts, disable=not show_progress, desc="Backtest")
        for ts in it:
            # 1) exits first
            for t, pos in list(portfolio.positions.items()):
                df = bars_4h.get(t)
                if df is None or ts not in df.index:
                    continue
                i = df.index.get_loc(ts)
                close = float(df["close"].iloc[i])
                feat = self.feats.snapshot(df, i)

                # stop on close below stop_close
                if close < float(pos.stop_close):
                    exit_px = self.slip.apply(close, feat.atr, side="sell")
                    portfolio.close_position(t, ts, exit_px, reason="STOP_CLOSE")
                    continue
                # strategy-based exit on trend break
                sig = self.strategy.evaluate(df, i, feat, cat=self.catalyst.get_earnings_catalyst(
                    t, daily.get(t, pd.DataFrame()), asof=ts, max_age_days=self.strategy.cfg.catalyst_max_age_days
                ), in_position=True)
                if sig.type == SignalType.EXIT:
                    exit_px = self.slip.apply(close, feat.atr, side="sell")
                    portfolio.close_position(t, ts, exit_px, reason="TREND_BREAK")
                    continue

            # 2) entries
            for t, df in bars_4h.items():
                if t in portfolio.positions:
                    continue
                if ts not in df.index:
                    continue
                i = df.index.get_loc(ts)
                feat = self.feats.snapshot(df, i)

                dd = daily.get(t)
                cat = self.catalyst.get_earnings_catalyst(
                    t, dd, asof=ts, max_age_days=self.strategy.cfg.catalyst_max_age_days
                )

                sig = self.strategy.evaluate(df, i, feat, cat, in_position=False)
                if sig.type != SignalType.ENTRY:
                    if getattr(sig, "reasons", None):
                        log_kv(
                            logger,
                            logging.DEBUG,
                            "ENTRY_REJECT",
                            ticker=t,
                            ts=str(ts),
                            reasons="|".join(sig.reasons),
                        )
                    continue
                # Long-only rule: no new trades in Defensiv regime
                regime = get_regime(ts)
                if regime == "Defensiv":
                    log_kv(logger, logging.DEBUG, "ENTRY_BLOCKED_REGIME", ticker=t, ts=str(ts), regime=regime)
                    continue

                # risk pct and size
                portfolio.mark_equity()
                ddn = compute_drawdown(portfolio.equity, portfolio.equity_high)
                risk_pct = self.risk.risk_pct(
                    equity=portfolio.equity,
                    equity_high=portfolio.equity_high,
                    dd=ddn,
                    regime=regime,
                    catalyst_class=cat.catalyst_class,
                )

                entry_close = float(df["close"].iloc[i])
                entry_px = self.slip.apply(entry_close, feat.atr, side="buy")

                stop = float(feat.last_hl_close) if feat.last_hl_close is not None else entry_close
                size = self.risk.position_size(portfolio.equity, risk_pct, entry_px, stop)
                if size <= 0:
                    continue

                portfolio.open_position(Position(
                    ticker=t,
                    entry_ts=ts,
                    entry_price=entry_px,
                    size=size,
                    stop_close=stop,
                    risk_pct=risk_pct,
                    catalyst_class=cat.catalyst_class,
                    regime=regime,
                ))

        # close remaining at last available close
        last_ts = all_ts[-1]
        for t, pos in list(portfolio.positions.items()):
            df = bars_4h.get(t)
            if df is None:
                continue
            ts = df.index[-1]
            i = len(df) - 1
            feat = self.feats.snapshot(df, i)
            close = float(df["close"].iloc[i])
            exit_px = self.slip.apply(close, feat.atr, side="sell")
            portfolio.close_position(t, ts, exit_px, reason="EOD_FORCE")

        log_kv(logger, logging.INFO, "BACKTEST_DONE", trades=len(portfolio.trades), equity=portfolio.equity)
        return portfolio
