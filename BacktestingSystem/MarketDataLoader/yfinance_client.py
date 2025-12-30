import yfinance as yf

def fetch_prices(symbol, interval):
    return yf.download(symbol, interval=interval)