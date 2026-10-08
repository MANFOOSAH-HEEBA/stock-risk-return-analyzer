import numpy as np
import pandas as pd

from src.analysis import compute_metrics, correlation_matrix, max_drawdown
from src.config import BENCHMARK


def _prices():
    idx = pd.bdate_range("2021-01-01", periods=600)
    rng = np.random.default_rng(0)
    mkt = rng.normal(0.0005, 0.01, 600)
    return pd.DataFrame({BENCHMARK: 100 * np.cumprod(1 + mkt),
                         "A.NS": 100 * np.cumprod(1 + 2 * mkt),     # beta should be ~2
                         "B.NS": 100 * np.cumprod(1 + rng.normal(0, 0.01, 600))}, index=idx)


def test_beta_of_scaled_market_is_two():
    assert abs(compute_metrics(_prices()).loc["A.NS", "beta"] - 2.0) < 1e-6


def test_benchmark_beta_is_one():
    assert abs(compute_metrics(_prices()).loc[BENCHMARK, "beta"] - 1.0) < 1e-9


def test_max_drawdown_simple():
    assert abs(max_drawdown(pd.Series([100, 120, 60, 90])) - (-0.5)) < 1e-9


def test_correlation_diagonal_is_one():
    assert np.allclose(np.diag(correlation_matrix(_prices())), 1.0)
