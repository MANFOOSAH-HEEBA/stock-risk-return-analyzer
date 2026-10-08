"""Download daily prices from Yahoo Finance and save one tidy CSV."""
import time
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from src.config import BENCHMARK, RAW_CSV, STOCKS, YEARS_OF_DATA


def fetch_one(ticker: str, start: date, end: date, retries: int = 3) -> pd.DataFrame:
    for attempt in range(1, retries + 1):
        try:
            hist = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=True)
            if not hist.empty:
                df = hist[["Close", "Volume"]].reset_index()
                df.columns = ["date", "close", "volume"]
                df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.strftime("%Y-%m-%d")
                df["ticker"] = ticker
                return df[["ticker", "date", "close", "volume"]]
        except Exception as exc:  # network hiccups, rate limits
            print(f"  attempt {attempt} failed for {ticker}: {exc}")
        time.sleep(2 * attempt)
    raise RuntimeError(f"Could not download data for {ticker}. Check your internet connection.")


def main() -> None:
    end = date.today()
    start = end - timedelta(days=int(365.25 * YEARS_OF_DATA))
    frames = []
    for ticker in [*STOCKS, BENCHMARK]:
        print(f"Downloading {ticker} ...")
        frames.append(fetch_one(ticker, start, end))
    out = pd.concat(frames, ignore_index=True).dropna(subset=["close"])
    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(RAW_CSV, index=False)
    print(f"Saved {len(out):,} rows for {out['ticker'].nunique()} tickers to {RAW_CSV}")


if __name__ == "__main__":
    main()
