import os
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

TICKERS = ["TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "RELIANCE.NS", "^NSEI"]
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RAW_FILE = os.path.join(DATA_DIR, "raw_prices.csv")
PERIOD_YEARS = 2

def is_stale(filepath, max_age_hours=20):
    """Return True if file doesn't exist or is older than max_age_hours."""
    if not os.path.exists(filepath):
        return True
    age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(filepath))
    return age > timedelta(hours=max_age_hours)


def download_data():
    """Download OHLCV data from Yahoo Finance."""
    end_date   = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - timedelta(days=365 * PERIOD_YEARS)).strftime("%Y-%m-%d")

    print(f"[fetch] Downloading {len(TICKERS)} tickers from {start_date} to {end_date}...")

    raw = yf.download(
        tickers    = TICKERS,
        start      = start_date,
        end        = end_date,
        group_by   = "ticker",
        auto_adjust= True,
        progress   = False,
    )

    # Flatten multi-level columns -> long format
    frames = []
    for ticker in TICKERS:
        try:
            df = raw[ticker].copy()
            df = df.dropna(subset=["Close"])
            df["Ticker"] = ticker
            df.reset_index(inplace=True)
            df.rename(columns={
                "Date":   "date",
                "Open":   "open",
                "High":   "high",
                "Low":    "low",
                "Close":  "close",
                "Volume": "volume",
                "Ticker": "ticker",
            }, inplace=True)
            df["date"] = pd.to_datetime(df["date"]).dt.date
            frames.append(df[["date", "ticker", "open", "high", "low", "close", "volume"]])
            print(f"  ✓ {ticker:15s}  {len(df)} rows")
        except Exception as e:
            print(f"  ✗ {ticker:15s}  ERROR: {e}")

    if not frames:
        raise RuntimeError("No data downloaded. Check your internet connection.")

    combined = pd.concat(frames, ignore_index=True)
    combined.sort_values(["ticker", "date"], inplace=True)
    return combined


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not is_stale(RAW_FILE):
        print(f"[fetch] Raw data is fresh (< 20 hrs old). Loading from cache: {RAW_FILE}")
        df = pd.read_csv(RAW_FILE, parse_dates=["date"])
        print(f"[fetch] Loaded {len(df)} rows from cache.")
        return df

    df = download_data()
    df.to_csv(RAW_FILE, index=False)
    print(f"\n[fetch] Saved {len(df)} rows to {RAW_FILE}")
    print(f"[fetch] Date range: {df['date'].min()}  →  {df['date'].max()}")
    print(f"[fetch] Done. ✓\n")
    return df


if __name__ == "__main__":
    main()
