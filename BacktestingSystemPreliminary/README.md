# Backtest v1.5 (Close-only, 1H→4H, yfinance)

This project implements the architecture defined in the canvas:

Universe → Data → Aggregation → Features/Context → Strategy (v1.5) → Execution/Risk → Portfolio/Reporting

The core design principles are:
- strict separation of **Universe** and **Strategy**
- close-only logic (no intrabar assumptions)
- reproducibility over optimisation
- realistic execution (random slippage, regime-based risk)

---

## Quickstart

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 2. Generate the universe (NASDAQ-like, Yahoo-only)

The universe is generated **without** using NASDAQ FTP or external registries.
Instead, it uses Yahoo Finance ETF holdings as a robust NASDAQ proxy.

Run:

```bash
python generate_universe.py
```

This creates:

- `tickers.txt`  → raw universe (NASDAQ-like, unfiltered)

Important:
- `tickers.txt` is **not a screener**
- no trend / ATR / volatility logic is applied here
- random sampling and hygiene filters happen later in the pipeline

---

### 3. Run the backtest

```bash
python -m backtest_v15.cli run --tickers-file tickers.txt --sample 1
```

What happens internally:
1. UniverseBuilder draws a **random sample** from `tickers.txt`
2. Hygiene filters are applied (price, liquidity, data availability)
3. 1H data is downloaded via yfinance
4. 4H bars are built (US regular session, session-aware)
5. Strategy v1.5 evaluates trades
6. Execution & risk are simulated

---

## Data sources

All market data comes from **Yahoo Finance via yfinance**:

- Price data:
  - `1h` → aggregated to synthetic 4H
  - `1d` → market regime & catalyst evaluation
- Corporate events:
  - Earnings dates via `Ticker.calendar`

There are **no other data sources**.

---

## Outputs

Each run creates a timestamped folder in `runs/` containing:

- `trades.csv`   → executed trades with R-multiples
- `equity.csv`   → equity curve
- `params.json`  → full run configuration (reproducibility)

---

## Notes on the 4H timeframe

- 4H bars are **synthetic**, built from 1H data
- US regular session only (no overnight bars)
- Two blocks per day:
  - 09:30–13:30
  - 13:30–16:00

This matches the strategy’s 2–5 day holding period without intrabar assumptions.

---

## Important clarifications

- This project does **not** test the NASDAQ as an index
- It tests whether **Strategy v1.5 can extract edge from a realistic NASDAQ-like universe**
- Market selection ≠ strategy optimisation
- All edge must come from the strategy rules themselves

---

## Typical workflow

```text
generate_universe.py
        ↓
    tickers.txt        (raw universe)
        ↓
UniverseBuilder        (random + hygiene)
        ↓
Strategy v1.5
        ↓
Trades / Equity
```

---

## Extensibility

The architecture allows later extensions without changing the strategy:

- different universe generators (NYSE, mixed US, EU)
- additional regime references
- alternative data providers

Strategy v1.5 remains untouched.

