from __future__ import annotations
import argparse, os, time
import logging
import random
from datetime import date, timedelta

from .config import UniverseConfig, DataConfig, AggregationConfig, SlippageConfig, RiskConfig, StrategyConfig, RegimeConfig
from .data import YFDataLoader, aggregate_1d_from_1h
from .universe import UniverseBuilder
from .backtest import Backtester, BacktestParams
from .reporting import save_run
from .logging import setup_logging, log_kv
from concurrent.futures import ThreadPoolExecutor, as_completed
from .aggregation import BarAggregator

def _prepare_ticker(loader, aggregator, ticker, start, end, logger):
    try:
        d1h = loader.get_ohlcv(ticker, start=start, end=end, interval="1h")
        if d1h is None or len(d1h) == 0:
            return ticker, None, None, None
        b4 = aggregator.to_4h_session_aware(d1h)
        if b4 is None or len(b4) < 200:
            return ticker, None, None, None
        d1 = aggregate_1d_from_1h(d1h)
        return ticker, d1h, b4, d1
    except Exception as e:
        log_kv(logger, logging.WARN, "PREP_FAIL", ticker=ticker, exception=e)
        return ticker, None, None, None


def cmd_run(args):

    # Run-ID und Run-Ordner direkt zu Beginn festlegen
    run_id = time.strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join(args.out_dir, run_id)
    log_dir = os.path.join(run_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    setup_logging(log_dir=log_dir, overwrite=True, max_bytes = 250_000_000, backup_count=2)
    logger = logging.getLogger(__name__)

    # timeframe is dynamically set so it can get the oldest hourly data available with yfinance (730 days ago)
    start=date.today()-timedelta(days=365)
    end=date.today()

    log_kv(logger, logging.INFO, "RUN_START", start=start, end=end, sample=args.sample, tickers_file=args.tickers_file)
    # Setup

    ucfg = UniverseConfig(min_price=args.min_price,min_avg_dollar_vol_20d=args.min_dvol,min_1h_days=args.min_1h_days)
    dcfg = DataConfig(cache_dir=args.cache_dir, auto_adjust=True, max_workers=6)
    acfg = AggregationConfig()
    scfg = StrategyConfig()
    slip = SlippageConfig(seed=args.slip_seed, max_atr_frac=args.slip_atr_frac)
    rcfg = RiskConfig()
    regcfg = RegimeConfig(ref_ticker=args.regime_ref)

    loader = YFDataLoader(dcfg)
    ub = UniverseBuilder(ucfg, loader)
    aggregator = BarAggregator(acfg)

    # build universe
    all_tickers = ub.read_tickers_file(args.tickers_file)
    all_tickers = list(dict.fromkeys([t.strip() for t in all_tickers if t.strip()]))
    tickers = random.choices(all_tickers, k=args.sample)

    bars_4h ={}
    daily = {}
    accepted = []
    tested = 0

    max_workers = 6
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {}
        while len(accepted) < args.sample:
            for t in tickers:
                futures[ex.submit(_prepare_ticker, loader, aggregator, t, start, end, logger)] = t

                if len(futures) >= max_workers * 3 and len(accepted) >= args.sample:
                    break

                for fut in as_completed(futures):
                    t = futures[fut]
                    tested += 1
                    ticker, d1h, b4, d1 = fut.result()

                    if b4 is None or d1 is None:
                        continue

                    if ub._passes_hygiene(ticker=ticker, oneh=d1h, daily=d1):
                        accepted.append(t)
                        bars_4h[t] = b4
                        daily[t] = d1

                    if len(accepted) >= args.sample:
                        break
                if len(accepted) >= args.sample:
                    tickers.append(random.choice(all_tickers))

    # get earnings
    cal = loader.get_calendar(start=start, end=end)

    # run backtest
    bt = Backtester(loader, acfg, scfg, slip, rcfg, regcfg)
    pf = bt.run(bars_4h=bars_4h, daily=daily, cal = cal, params=BacktestParams(start=start, end=end, initial_equity=args.initial_equity))

    params = {
        "start": start,
        "end": end,
        "initial_equity": args.initial_equity,
        "tickers_file": args.tickers_file,
        "sample": args.sample,
        "sample_seed": args.sample_seed,
        "min_price": args.min_price,
        "min_dvol": args.min_dvol,
        "min_1h_days": args.min_1h_days,
        "slippage": {"seed": args.slip_seed, "max_atr_frac": args.slip_atr_frac},
        "regime_ref": args.regime_ref,
    }
    save_run(run_dir, pf, params)
    print(f"Run saved to: {run_dir}")
    print(f"Trades: {len(pf.trades)}  Final equity: {pf.equity:.2f}")

def build_parser():
    p = argparse.ArgumentParser(prog="backtest_v15")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run")
    r.add_argument("--tickers-file", required=True, help="One ticker per line.")
    r.add_argument("--sample", type=int, default=100)
    r.add_argument("--sample-seed", type=int, default=42)
    r.add_argument("--initial-equity", type=float, default=10000.0)
    r.add_argument("--cache-dir", default="cache")
    r.add_argument("--out-dir", default="runs")
    r.add_argument("--max-workers", type=int, default=6, help="Parallel downloads/prepare workers (ThreadPoolExecutor).")

    # hygiene
    #
    # By default the universe pre‑screener does not filter on price,
    # liquidity or long intraday history.  Users can still supply
    # positive values to enable stricter hygiene if desired.  See
    # UniverseConfig for details.
    r.add_argument("--min-price", type=float, default=0.0)
    r.add_argument("--min-dvol", type=float, default=0.0)
    r.add_argument("--min-1h-days", type=int, default=0)

    # slippage
    r.add_argument("--slip-seed", type=int, default=7)
    r.add_argument("--slip-atr-frac", type=float, default=0.10)

    # regime
    r.add_argument("--regime-ref", default="SPY")

    r.set_defaults(func=cmd_run)
    return p

def main():
    p = build_parser()
    args = p.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()


