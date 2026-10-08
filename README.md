# Stock Market Risk & Return Analyzer

An end-to-end analytics project that downloads 5 years of daily prices for 8 NSE-listed stocks
(across 8 sectors) and the Nifty 50 index, stores them in a **SQL database**, analyses risk and
return with **SQL window functions and Pandas**, and presents the results in an interactive
**Streamlit** dashboard.

**Question it answers:** *Which sectors and stocks gave the best return for the risk taken, and
how can an investor diversify across them?*

## Tech stack
Python, SQL (SQLite by default, MySQL 8 supported), Pandas, NumPy, SQLAlchemy, yfinance,
Streamlit, Plotly, pytest.

## Pipeline
```
Yahoo Finance --> data/raw/prices.csv --> SQL database (stocks, prices, daily_returns view)
                                              |
                      SQL queries (joins, CTEs, window functions)  +  Pandas metrics
                                              |
                                  Streamlit dashboard + reports/findings.md
```

## Run it
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_all.py            # downloads data, loads SQL, computes metrics, writes reports/
streamlit run app.py         # opens the dashboard
pytest                       # unit tests for the metric calculations
```
No internet? `python run_all.py --sample` uses clearly-labelled **synthetic** data for testing only.

**Use MySQL instead of SQLite (optional):**
```bash
pip install pymysql
export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/market"   # create the DB first
python run_all.py
```

## SQL concepts used (`sql/queries.sql`)
| Query | Concepts |
|---|---|
| `sector_avg_return` | JOIN across tables, GROUP BY, aggregates, CASE WHEN |
| `best_worst_month` | CTEs, ROW_NUMBER, LAG (window functions) |
| `moving_average` | Window frame `ROWS BETWEEN 49 PRECEDING AND CURRENT ROW` |
| `top_total_return` | CTEs, self-JOIN, ranking |
| `volume_by_sector` | JOIN + GROUP BY |

## Metrics (`src/analysis.py`)
- **CAGR** - compound annual growth rate of price.
- **Volatility** - std. dev. of daily returns x sqrt(252).
- **Sharpe ratio** - (CAGR - risk-free rate) / volatility. Risk-free rate is an *assumption* (6.5%, set in `src/config.py`).
- **Beta** - covariance with Nifty 50 returns / variance of Nifty 50 returns.
- **Max drawdown** - largest peak-to-trough fall.
- **Correlation matrix** of daily returns, used to discuss diversification.

## Results
Live Yahoo Finance data downloaded on 8 Oct 2026 covered 8 Oct 2021 to 7 Oct 2026
(1,240 trading days): 11,154 price rows across eight NSE stocks and the Nifty 50 benchmark.
The risk-free rate is assumed to be 6.5%; findings below are generated from the data.

- Sun Pharmaceutical had the strongest risk-adjusted return (Sharpe 0.57; CAGR 17.9%; annualized volatility 19.9%). Tata Consultancy Services had the weakest Sharpe (-0.71).
- Four of eight stocks beat the Nifty 50's 4.8% CAGR: ITC, Larsen & Toubro, Maruti Suzuki, and Sun Pharmaceutical.
- Larsen & Toubro had the highest beta (1.20); Sun Pharmaceutical had the lowest (0.56).
- Infosys and Tata Consultancy Services were most correlated (0.73); Infosys and Maruti Suzuki were least correlated (0.14).
- Tata Consultancy Services had the largest maximum drawdown (-53.4%).

## Limitations
- Past performance does not predict future returns; this is an educational analysis, not investment advice.
- Uses adjusted close prices from Yahoo Finance (free data, may contain gaps).
- Only 8 stocks, one stock per sector, so sector conclusions are indicative, not statistically strong.
- Sharpe uses CAGR and a single assumed risk-free rate for the whole period.

## Project structure
```
app.py                    Streamlit dashboard
run_all.py                one-command pipeline
sql/schema.sql            tables + daily_returns view
sql/queries.sql           analysis queries
src/                      config, fetch_data, db, analysis, generate_sample_data
tests/test_analysis.py    unit tests
```
