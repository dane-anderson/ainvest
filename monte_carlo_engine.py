import numpy as np
import pandas as pd
import yfinance as yf


def run_monte_carlo(
    tickers,
    weights,
    initial_value=10000,
    years=1,
    simulations=1000,
    trading_days=252,
):
    prices = yf.download(tickers, period="2y", auto_adjust=True, progress=False)["Close"]

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    prices = prices.dropna(axis=1, how="all").ffill().dropna()

    returns = prices.pct_change().dropna()

    mean_returns = returns.mean()
    cov_matrix = returns.cov()

    weights = np.array(weights, dtype=float)
    weights = weights / weights.sum()

    days = years * trading_days

    all_paths = np.zeros((days, simulations))

    for sim in range(simulations):
        daily_returns = np.random.multivariate_normal(
            mean_returns,
            cov_matrix,
            days,
        )

        portfolio_returns = daily_returns @ weights
        path = initial_value * np.cumprod(1 + portfolio_returns)
        all_paths[:, sim] = path

    ending_values = all_paths[-1, :]

    return {
        "expected_final_value": float(np.mean(ending_values)),
        "median_final_value": float(np.median(ending_values)),
        "worst_5_percent": float(np.percentile(ending_values, 5)),
        "best_95_percent": float(np.percentile(ending_values, 95)),
        "probability_loss": float(np.mean(ending_values < initial_value)),
        "paths": all_paths,
    }