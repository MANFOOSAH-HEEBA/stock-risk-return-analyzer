"""One-command pipeline: fetch -> load SQL -> analyse -> write reports/findings.md

Usage:
    python run_all.py            # real data from Yahoo Finance
    python run_all.py --sample   # SYNTHETIC data, for offline testing only
"""
import argparse

from src import analysis, db
from src.config import REPORT_DIR


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="use synthetic test data (offline)")
    ap.add_argument("--skip-fetch", action="store_true", help="reuse existing data/raw/prices.csv")
    args = ap.parse_args()

    if args.sample:
        from src import generate_sample_data
        generate_sample_data.main()
    elif not args.skip_fetch:
        from src import fetch_data
        fetch_data.main()

    engine = db.get_engine()
    db.load_database(engine)

    prices = analysis.load_price_matrix(engine)
    names = analysis.company_names(engine)
    metrics = analysis.compute_metrics(prices)
    corr = analysis.correlation_matrix(prices)
    findings = analysis.generate_findings(metrics, corr, names)

    REPORT_DIR.mkdir(exist_ok=True)
    tag = "\n> WARNING: generated from SYNTHETIC test data. Do not use these numbers.\n" if args.sample else ""
    lines = ["# Findings", tag,
             f"Period: {prices.index.min():%d %b %Y} to {prices.index.max():%d %b %Y} "
             f"({len(prices):,} trading days)\n"]
    lines += [f"{i}. {f}" for i, f in enumerate(findings, 1)]
    (REPORT_DIR / "findings.md").write_text("\n".join(lines))
    metrics.round(4).to_csv(REPORT_DIR / "metrics.csv")

    print("\n=== METRICS ===")
    print(metrics.round(3).to_string())
    print("\n=== FINDINGS ===")
    for f in findings:
        print("-", f)
    print("\nNext: streamlit run app.py")


if __name__ == "__main__":
    main()
