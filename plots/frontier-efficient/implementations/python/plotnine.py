""" pyplots.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_gradient,
    theme,
    theme_minimal,
)
from scipy.optimize import minimize


# Data - Generate random portfolios and efficient frontier
np.random.seed(42)

# Asset parameters (5 assets)
n_assets = 5
n_portfolios = 300

# Expected returns and covariance matrix for assets
expected_returns = np.array([0.08, 0.12, 0.15, 0.10, 0.18])
cov_matrix = np.array(
    [
        [0.04, 0.01, 0.02, 0.01, 0.02],
        [0.01, 0.09, 0.03, 0.02, 0.04],
        [0.02, 0.03, 0.16, 0.04, 0.06],
        [0.01, 0.02, 0.04, 0.06, 0.03],
        [0.02, 0.04, 0.06, 0.03, 0.25],
    ]
)

# Generate random portfolio weights
weights = np.random.dirichlet(np.ones(n_assets), size=n_portfolios)

# Calculate portfolio returns and risks
portfolio_returns = weights @ expected_returns
portfolio_risks = np.sqrt(np.diag(weights @ cov_matrix @ weights.T))

# Calculate Sharpe ratio (assuming risk-free rate of 3%)
risk_free_rate = 0.03
sharpe_ratios = (portfolio_returns - risk_free_rate) / portfolio_risks

# Find efficient frontier using optimization
target_returns = np.linspace(min(expected_returns) + 0.01, max(expected_returns) - 0.01, 100)
frontier_risks = []
frontier_returns = []


def portfolio_variance(w):
    return w @ cov_matrix @ w


def portfolio_return(w):
    return w @ expected_returns


for target in target_returns:
    constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1},
        {"type": "eq", "fun": lambda w, t=target: portfolio_return(w) - t},
    ]
    bounds = tuple((0, 1) for _ in range(n_assets))
    result = minimize(
        portfolio_variance, np.ones(n_assets) / n_assets, method="SLSQP", bounds=bounds, constraints=constraints
    )
    if result.success:
        frontier_risks.append(np.sqrt(result.fun))
        frontier_returns.append(target)

# Find minimum variance portfolio
min_var_idx = np.argmin(frontier_risks)
min_var_risk = frontier_risks[min_var_idx]
min_var_return = frontier_returns[min_var_idx]

# Find maximum Sharpe ratio portfolio
frontier_sharpe = [(r - risk_free_rate) / s for r, s in zip(frontier_returns, frontier_risks, strict=True)]
max_sharpe_idx = np.argmax(frontier_sharpe)
max_sharpe_risk = frontier_risks[max_sharpe_idx]
max_sharpe_return = frontier_returns[max_sharpe_idx]

# Create DataFrames
df_portfolios = pd.DataFrame({"risk": portfolio_risks, "return": portfolio_returns, "sharpe": sharpe_ratios})

df_frontier = pd.DataFrame({"risk": frontier_risks, "return": frontier_returns})

# Plot
plot = (
    ggplot()
    + geom_point(df_portfolios, aes(x="risk", y="return", color="sharpe"), size=3, alpha=0.6)
    + geom_line(df_frontier, aes(x="risk", y="return"), color="#306998", size=2.5)
    + annotate("point", x=min_var_risk, y=min_var_return, color="#FFD43B", size=6, shape="s")
    + annotate("point", x=max_sharpe_risk, y=max_sharpe_return, color="#FFD43B", size=6, shape="D")
    + annotate("text", x=min_var_risk + 0.015, y=min_var_return, label="Min Variance", size=14, ha="left")
    + annotate("text", x=max_sharpe_risk + 0.015, y=max_sharpe_return, label="Max Sharpe", size=14, ha="left")
    + scale_color_gradient(low="#306998", high="#FFD43B", name="Sharpe Ratio")
    + labs(x="Risk (Standard Deviation)", y="Expected Return", title="frontier-efficient · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
    )
)

# Save
plot.save("plot.png", dpi=300)
