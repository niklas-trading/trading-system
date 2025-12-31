from __future__ import annotations
import logging
import os, json
from dataclasses import asdict
import pandas as pd
from .logging import log_kv
logger = logging.getLogger(__name__)

from .portfolio import Portfolio

def portfolio_to_frames(p: Portfolio):
    trades = pd.DataFrame([t.__dict__ for t in p.trades])
    # equity curve approximation: cumulative pnl at exits
    if len(trades) == 0:
        equity = pd.DataFrame({"timestamp": [], "equity": []})
    else:
        trades = trades.sort_values("exit_ts")
        eq = [p.trades[0].__dict__.get("entry_price", 0)]
        # build equity from initial by cum pnl
        equity_vals = (trades["pnl"].cumsum() + (p.equity - trades["pnl"].sum()))
        equity = pd.DataFrame({"timestamp": trades["exit_ts"].values, "equity": equity_vals.values})
    return trades, equity

def save_run(run_dir: str, portfolio: Portfolio, params: dict):
    log_kv(logger, logging.INFO, "REPORT_SAVE_START", run_dir=run_dir, trades=len(portfolio.trades))
    os.makedirs(run_dir, exist_ok=True)
    log_kv(logger, logging.DEBUG, "REPORT_DIR_READY", run_dir=run_dir)
    trades, equity = portfolio_to_frames(portfolio)
    trades.to_csv(os.path.join(run_dir, "trades.csv"), index=False)
    equity.to_csv(os.path.join(run_dir, "equity.csv"), index=False)
    with open(os.path.join(run_dir, "params.json"), "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2, default=str)
