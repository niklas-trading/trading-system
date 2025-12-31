import pandas as pd
import random

IN_FILE = "nasdaqlisted.txt"
OUT_FILE = "tickers.txt"
SEED = 42

def main():
    df = pd.read_csv(IN_FILE, sep="|")

    # offizielle NASDAQ-Filter
    df = df[df["ETF"] == "N"]
    df = df[df["Test Issue"] == "N"]

    tickers = (
        df["Symbol"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    tickers = sorted(set(tickers))
    random.Random(SEED).shuffle(tickers)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for t in tickers:
            f.write(t + "\n")

    print(f"Wrote {len(tickers)} NASDAQ tickers to {OUT_FILE}")

if __name__ == "__main__":
    main()
