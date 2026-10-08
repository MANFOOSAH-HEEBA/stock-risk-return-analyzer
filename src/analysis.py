"""Risk / return analytics computed from prices stored in SQL."""
import numpy as np
import pandas as pd
from sqlalchemy import text

from src.config import BENCHMARK, RISK_FREE_RATE, TRADING_DAYS


def load_price_matrix(engine) -> pd.DataFrame:
    """Wide DataFrame: index = date, columns = ticker, values = close price."""
    df = pd.read_sql(text("SELECT ticker, trade_date, close_price FROM prices"), engine)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    return df.pivot(index="trade_date", columns="ticker", values="close_price").sort_index()


def company_names(engine) -> pd.DataFrame:
    return pd.read_sql(text("SELECT ticker, company, sector FROM stocks"), engine)


def max_drawdown(prices: pd.Series) -> float:
    return float((prices / prices.cummax() - 1).min())


def compute_metrics(prices: pd.DataFrame, rf: float = RISK_FREE_RATE) -> pd.DataFrame:
    """Per-instrument CAGR, volatility, Sharpe, beta vs benchmark, max drawdown."""
    returns = prices.pct_change().dropna(how="all")
    bench = returns[BENCHMARK]
    rows = []
    for t in prices.columns:
        p = prices[t].dropna()
        r = returns[t].dropna()
        years = (p.index[-1] - p.index[0]).days / 365.25
        cagr = (p.iloc[-1] / p.iloc[0]) ** (1 / years) - 1
        vol = r.std() * np.sqrt(TRADING_DAYS)
        joint = pd.concat([r, bench], axis=1, join="inner").dropna()
        beta = joint.iloc[:, 0].cov(joint.iloc[:, 1]) / joint.iloc[:, 1].var()
        rows.append({"ticker": t, "cagr": cagr, "volatility": vol,
                     "sharpe": (cagr - rf) / vol if vol else np.nan,
                     "beta": beta, "max_drawdown": max_drawdown(p)})
    return pd.DataFrame(rows).set_index("ticker")


def correlation_matrix(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna().corr()


def generate_findings(metrics: pd.DataFrame, corr: pd.DataFrame, names: pd.DataFrame,
                      rf: float = RISK_FREE_RATE) -> list:
    """Plain-English findings derived ONLY from the computed numbers."""
    nm = names.set_index("ticker")["company"].to_dict()
    sec = names.set_index("ticker")["sector"].to_dict()
    m = metrics.drop(index=BENCHMARK)
    bench = metrics.loc[BENCHMARK]
    out = []

    best = m["sharpe"].idxmax()
    worst = m["sharpe"].idxmin()
    out.append(f"Best risk-adjusted return: {nm[best]} ({sec[best]}) with a Sharpe ratio of "
               f"{m.loc[best, 'sharpe']:.2f} (CAGR {m.loc[best, 'cagr']:.1%}, volatility "
               f"{m.loc[best, 'volatility']:.1%}). Weakest: {nm[worst]} at {m.loc[worst, 'sharpe']:.2f}.")

    beat = m[m["cagr"] > bench["cagr"]]
    out.append(f"{len(beat)} of {len(m)} stocks beat the Nifty 50 on CAGR ({bench['cagr']:.1%})"
               + (f": {', '.join(nm[t] for t in beat.index)}." if len(beat) else "."))

    hb, lb = m["beta"].idxmax(), m["beta"].idxmin()
    out.append(f"Most market-sensitive: {nm[hb]} (beta {m.loc[hb, 'beta']:.2f}). "
               f"Most defensive: {nm[lb]} (beta {m.loc[lb, 'beta']:.2f}).")

    c = corr.drop(index=BENCHMARK, columns=BENCHMARK)
    pairs = c.where(np.triu(np.ones(c.shape), k=1).astype(bool)).stack()
    hi, lo = pairs.idxmax(), pairs.idxmin()
    out.append(f"Most correlated pair: {nm[hi[0]]} & {nm[hi[1]]} ({pairs[hi]:.2f}); least correlated: "
               f"{nm[lo[0]]} & {nm[lo[1]]} ({pairs[lo]:.2f}). Pairing low-correlation stocks "
               f"gives better diversification.")

    dd = m["max_drawdown"].idxmin()
    out.append(f"Largest peak-to-trough fall: {nm[dd]} ({m.loc[dd, 'max_drawdown']:.1%}).")
    out.append(f"Assumptions: risk-free rate {rf:.1%}, {TRADING_DAYS} trading days/year, "
               f"adjusted close prices, benchmark = Nifty 50.")
    return out
