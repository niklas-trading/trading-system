from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import pandas as pd
from .logging import log_kv
logger = logging.getLogger(__name__)

from .types import Position

@dataclass
class TradeRecord:
    ticker: str
    entry_ts: pd.Timestamp
    exit_ts: pd.Timestamp
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    r_multiple: float
    risk_pct: float
    stop_close: float
    regime: str
    catalyst_class: str
    exit_reason: str

@dataclass
class Portfolio:
    equity: float = 10000.0
    positions: Dict[str, Position] = field(default_factory=dict)
    equity_high: float = 10000.0
    trades: List[TradeRecord] = field(default_factory=list)

    def mark_equity(self) -> None:
        log_kv(logger, logging.DEBUG, "EQUITY_MARK", equity=self.equity, equity_high=self.equity_high)
        self.equity_high = max(self.equity_high, self.equity)

    def open_position(self, pos: Position) -> None:
        log_kv(logger, logging.INFO, "PORTFOLIO_OPEN", ticker=pos.ticker, entry_price=pos.entry_price, size=pos.size, stop=pos.stop_close)
        self.positions[pos.ticker] = pos

    def close_position(self, ticker: str, ts, exit_price: float, reason: str) -> None:
        log_kv(logger, logging.INFO, "PORTFOLIO_CLOSE", ticker=ticker, exit_price=exit_price, reason=reason)
        pos = self.positions.pop(ticker, None)
        if pos is None:
            log_kv(logger, logging.WARNING, "PORTFOLIO_CLOSE_NO_POSITION", ticker=ticker)
            return
        pnl = (exit_price - pos.entry_price) * pos.size
        log_kv(logger, logging.DEBUG, "PORTFOLIO_PNL", ticker=ticker, pnl=pnl)
        # R-multiple computed vs initial risk per trade
        init_risk_money = abs(pos.entry_price - pos.stop_close) * pos.size
        r_mult = pnl / init_risk_money if init_risk_money > 0 else 0.0
        self.equity += pnl
        self.mark_equity()
        self.trades.append(TradeRecord(
            ticker=ticker,
            entry_ts=pd.Timestamp(pos.entry_ts),
            exit_ts=pd.Timestamp(ts),
            entry_price=float(pos.entry_price),
            exit_price=float(exit_price),
            size=float(pos.size),
            pnl=float(pnl),
            r_multiple=float(r_mult),
            risk_pct=float(pos.risk_pct),
            stop_close=float(pos.stop_close),
            regime=str(pos.regime),
            catalyst_class=str(pos.catalyst_class),
            exit_reason=str(reason),
        ))
