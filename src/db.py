"""Database helpers: create schema, load CSV into SQL, run named queries."""
import re

import pandas as pd
from sqlalchemy import create_engine, text

from src.config import BENCHMARK, BENCHMARK_INFO, DATABASE_URL, RAW_CSV, SQL_DIR, STOCKS


def get_engine():
    return create_engine(DATABASE_URL)


def _run_script(engine, path) -> None:
    script = re.sub(r"--.*", "", path.read_text())  # strip comments
    with engine.begin() as conn:
        for stmt in filter(None, (s.strip() for s in script.split(";"))):
            conn.execute(text(stmt))


def load_database(engine=None) -> None:
    """Rebuild the schema and load prices from data/raw/prices.csv."""
    engine = engine or get_engine()
    if not RAW_CSV.exists():
        raise FileNotFoundError(f"{RAW_CSV} not found. Run `python -m src.fetch_data` first.")
    _run_script(engine, SQL_DIR / "schema.sql")

    stocks = [(t, c, s) for t, (c, s) in STOCKS.items()]
    stocks.append((BENCHMARK, *BENCHMARK_INFO))
    pd.DataFrame(stocks, columns=["ticker", "company", "sector"]).to_sql(
        "stocks", engine, if_exists="append", index=False)

    prices = pd.read_csv(RAW_CSV).rename(columns={"date": "trade_date", "close": "close_price"})
    prices = prices.dropna(subset=["close_price"]).drop_duplicates(["ticker", "trade_date"])
    prices.to_sql("prices", engine, if_exists="append", index=False, chunksize=2000)
    print(f"Loaded {len(stocks)} instruments and {len(prices):,} price rows into {engine.url}")


def load_queries() -> dict:
    """Parse sql/queries.sql into {name: sql}."""
    text_ = (SQL_DIR / "queries.sql").read_text()
    parts = re.split(r"^-- name:\s*(\w+)\s*$", text_, flags=re.M)
    return {parts[i]: parts[i + 1].strip().rstrip(";") for i in range(1, len(parts), 2)}


def run_query(name: str, engine=None) -> pd.DataFrame:
    engine = engine or get_engine()
    return pd.read_sql(text(load_queries()[name]), engine)
