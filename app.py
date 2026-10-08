"""Streamlit dashboard: streamlit run app.py"""
import plotly.express as px
import streamlit as st

from src import analysis, db
from src.config import BENCHMARK, RISK_FREE_RATE

st.set_page_config(page_title="Stock Risk & Return Analyzer", layout="wide")
st.title("Stock Market Risk & Return Analyzer")
st.caption("NSE stocks vs Nifty 50 | Python + SQL (window functions, joins) + Pandas + Streamlit")


@st.cache_data(show_spinner=False)
def load_all():
    engine = db.get_engine()
    prices = analysis.load_price_matrix(engine)
    names = analysis.company_names(engine)
    return (prices, names, analysis.compute_metrics(prices), analysis.correlation_matrix(prices),
            {q: db.run_query(q, engine) for q in db.load_queries()})


try:
    prices, names, metrics, corr, q = load_all()
except Exception as exc:
    st.error(f"No data yet. Run `python run_all.py` first. ({exc})")
    st.stop()

label = names.set_index("ticker")["company"].to_dict()
sector = names.set_index("ticker")["sector"].to_dict()

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Price & 50-day MA", "Risk vs Return", "Correlation", "SQL insights", "Conclusions"])

with tab1:
    picks = st.multiselect("Stocks", [t for t in prices.columns], default=[prices.columns[0]],
                           format_func=lambda t: label[t])
    ma = q["moving_average"]
    ma["trade_date"] = ma["trade_date"].astype("datetime64[ns]")
    for t in picks:
        d = ma[ma["ticker"] == t].set_index("trade_date")[["close_price", "ma_50"]]
        st.plotly_chart(px.line(d, title=label[t], labels={"value": "Price", "trade_date": ""}))

with tab2:
    m = metrics.drop(index=BENCHMARK).reset_index()
    m["company"] = m["ticker"].map(label)
    m["sector"] = m["ticker"].map(sector)
    fig = px.scatter(m, x="volatility", y="cagr", size=m["sharpe"].clip(lower=0.05), color="sector",
                     text="company", hover_data=["sharpe", "beta", "max_drawdown"],
                     labels={"volatility": "Annualised volatility", "cagr": "CAGR"},
                     title="Risk vs Return (bubble size = Sharpe ratio)")
    fig.update_traces(textposition="top center")
    fig.update_xaxes(tickformat=".0%"); fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig)
    show = metrics.copy(); show.index = [label[t] for t in show.index]
    st.dataframe(show.style.format({"cagr": "{:.1%}", "volatility": "{:.1%}", "sharpe": "{:.2f}",
                                    "beta": "{:.2f}", "max_drawdown": "{:.1%}"}))
    st.caption(f"Sharpe = (CAGR - {RISK_FREE_RATE:.1%} risk-free) / volatility. Beta is vs Nifty 50.")

with tab3:
    c = corr.copy(); c.index = c.columns = [label[t] for t in c.columns]
    st.plotly_chart(px.imshow(c, color_continuous_scale="RdBu_r", zmin=-1, zmax=1, text_auto=".2f",
                              title="Daily return correlation"))

with tab4:
    st.subheader("Average daily return by sector"); st.dataframe(q["sector_avg_return"], hide_index=True)
    st.subheader("Total return ranking"); st.dataframe(q["top_total_return"], hide_index=True)
    st.subheader("Best and worst month per stock"); st.dataframe(q["best_worst_month"], hide_index=True)
    st.subheader("Average volume by sector"); st.dataframe(q["volume_by_sector"], hide_index=True)
    with st.expander("View the SQL"):
        for name, sql in db.load_queries().items():
            st.markdown(f"**{name}**"); st.code(sql, language="sql")

with tab5:
    st.subheader("Findings (computed from the data)")
    for f in analysis.generate_findings(metrics, corr, names):
        st.markdown(f"- {f}")
