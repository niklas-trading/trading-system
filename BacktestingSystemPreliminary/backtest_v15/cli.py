from __future__ import annotations
import argparse, os, time
from dataclasses import asdict

from .config import UniverseConfig, DataConfig, AggregationConfig, SlippageConfig, RiskConfig, StrategyConfig, RegimeConfig
from .data import YFDataLoader
from .universe import UniverseBuilder
from .backtest import Backtester, BacktestParams
from .reporting import save_run

def cmd_run(args):
    ucfg = UniverseConfig(
        min_price=args.min_price,
        min_avg_dollar_vol_20d=args.min_dvol,
        min_1h_days=args.min_1h_days,
    )
    dcfg = DataConfig(cache_dir=args.cache_dir, auto_adjust=True, max_workers=6)
    acfg = AggregationConfig()
    scfg = StrategyConfig()
    slip = SlippageConfig(seed=args.slip_seed, max_atr_frac=args.slip_atr_frac)
    rcfg = RiskConfig()
    regcfg = RegimeConfig(ref_ticker=args.regime_ref)

    loader = YFDataLoader(dcfg)
    ub = UniverseBuilder(ucfg, loader)

    tickers = ub.read_tickers_file(args.tickers_file)
    universe = ub.build_random_sample(
        tickers=tickers,
        start=args.start,
        end=args.end,
        sample_size=args.sample,
        seed=args.sample_seed,
    )
    universe_tickers = [u.ticker for u in universe]

    bt = Backtester(loader, acfg, scfg, slip, rcfg, regcfg)
    pf = bt.run(universe_tickers, BacktestParams(start=args.start, end=args.end, initial_equity=args.initial_equity))

    run_id = time.strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join(args.out_dir, run_id)
    params = {
        "start": args.start,
        "end": args.end,
        "initial_equity": args.initial_equity,
        "tickers_file": args.tickers_file,
        "sample": args.sample,
        "sample_seed": args.sample_seed,
        "min_price": args.min_price,
        "min_dvol": args.min_dvol,
        "min_1h_days": args.min_1h_days,
        "slippage": {"seed": args.slip_seed, "max_atr_frac": args.slip_atr_frac},
        "regime_ref": args.regime_ref,
        "universe_tickers": universe_tickers,
    }
    save_run(run_dir, pf, params)
    print(f"Run saved to: {run_dir}")
    print(f"Trades: {len(pf.trades)}  Final equity: {pf.equity:.2f}")

def build_parser():
    p = argparse.ArgumentParser(prog="backtest_v15")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run")
    r.add_argument("--tickers-file", required=True, help="One ticker per line.")
    r.add_argument("--start", required=True, help="YYYY-MM-DD")
    r.add_argument("--end", required=True, help="YYYY-MM-DD")
    r.add_argument("--sample", type=int, default=100)
    r.add_argument("--sample-seed", type=int, default=42)
    r.add_argument("--initial-equity", type=float, default=10000.0)
    r.add_argument("--cache-dir", default="cache")
    r.add_argument("--out-dir", default="runs")

    # hygiene
    r.add_argument("--min-price", type=float, default=5.0)
    r.add_argument("--min-dvol", type=float, default=10_000_000.0)
    r.add_argument("--min-1h-days", type=int, default=365)

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
