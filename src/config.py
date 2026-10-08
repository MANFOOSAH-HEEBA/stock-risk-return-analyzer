"""Project configuration: stock universe, paths, and assumptions."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_CSV = DATA_DIR / "raw" / "prices.csv"
SQL_DIR = ROOT / "sql"
REPORT_DIR = ROOT / "reports"

# ticker -> (company, sector). ".NS" = NSE India on Yahoo Finance. "^NSEI" = Nifty 50 index.
STOCKS = {
    "TCS.NS": ("Tata Consultancy Services", "IT"),
    "INFY.NS": ("Infosys", "IT"),
    "HDFCBANK.NS": ("HDFC Bank", "Banking"),
    "RELIANCE.NS": ("Reliance Industries", "Energy"),
    "ITC.NS": ("ITC", "FMCG"),
    "SUNPHARMA.NS": ("Sun Pharmaceutical", "Pharma"),
    "MARUTI.NS": ("Maruti Suzuki", "Auto"),
    "LT.NS": ("Larsen & Toubro", "Infrastructure"),
}
BENCHMARK = "^NSEI"
BENCHMARK_INFO = ("Nifty 50 Index", "Benchmark")

YEARS_OF_DATA = 5
TRADING_DAYS = 252
# Assumed annual risk-free rate (approx. Indian 10-year government bond yield).
# Change this if you want; it is an ASSUMPTION and should be stated in your README.
RISK_FREE_RATE = 0.065

# SQLite by default (zero setup). For MySQL set e.g.
# DATABASE_URL=mysql+pymysql://user:password@localhost:3306/market
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'market.db'}")
