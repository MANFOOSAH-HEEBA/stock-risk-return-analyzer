"""Create SYNTHETIC price data in the same CSV format as fetch_data.py.

FOR TESTING ONLY (offline runs, CI). The numbers are random and mean nothing.
Never put results from this data in your README, resume or interviews.
"""
import numpy as np
import pandas as pd

from src.config import BENCHMARK, RAW_CSV, STOCKS


def main(n_days: int = 1260, seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n_days)
    market = rng.normal(0.0004, 0.009, n_days)  # common "market" factor
    rows = []

    def add(ticker, rets, base):
        price = base * np.cumprod(1 + rets)
        vol = rng.integers(500_000, 5_000_000, n_days)
        rows.append(pd.DataFrame({"ticker": ticker, "date": dates.strftime("%Y-%m-%d"),
                                  "close": price.round(2), "volume": vol}))

    add(BENCHMARK, market, 15000)
    for ticker in STOCKS:
        beta = rng.uniform(0.6, 1.3)
        idio = rng.normal(0.0002, rng.uniform(0.007, 0.013), n_days)
        add(ticker, beta * market + idio, rng.uniform(300, 3000))
    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(rows).to_csv(RAW_CSV, index=False)
    print(f"[SYNTHETIC TEST DATA] written to {RAW_CSV}")


if __name__ == "__main__":
    main()
