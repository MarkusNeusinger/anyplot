""" pyplots.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Generate simulated asset data
np.random.seed(42)
n_assets = 6
n_portfolios = 300
risk_free_rate = 0.03

# Asset expected returns and volatilities
asset_returns = np.array([0.08, 0.10, 0.12, 0.15, 0.07, 0.18])
asset_volatility = np.array([0.12, 0.15, 0.18, 0.25, 0.10, 0.30])

# Correlation matrix (realistic correlations)
corr_matrix = np.array(
    [
        [1.00, 0.30, 0.25, 0.20, 0.50, 0.15],
        [0.30, 1.00, 0.40, 0.35, 0.25, 0.30],
        [0.25, 0.40, 1.00, 0.50, 0.20, 0.45],
        [0.20, 0.35, 0.50, 1.00, 0.15, 0.60],
        [0.50, 0.25, 0.20, 0.15, 1.00, 0.10],
        [0.15, 0.30, 0.45, 0.60, 0.10, 1.00],
    ]
)
cov_matrix = np.outer(asset_volatility, asset_volatility) * corr_matrix

# Generate random portfolios
portfolio_returns = []
portfolio_risks = []
sharpe_ratios = []

for _ in range(n_portfolios):
    weights = np.random.random(n_assets)
    weights /= np.sum(weights)
    port_return = np.sum(weights * asset_returns)
    port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    portfolio_returns.append(port_return)
    portfolio_risks.append(port_vol)
    sharpe_ratios.append((port_return - risk_free_rate) / port_vol)

# Generate efficient frontier via Monte Carlo sampling
target_returns = np.linspace(0.07, 0.18, 50)
frontier_risks = []
frontier_returns = []

for target in target_returns:
    best_risk = float("inf")
    for _ in range(2000):
        weights = np.random.random(n_assets)
        weights /= np.sum(weights)
        port_return = np.sum(weights * asset_returns)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        if abs(port_return - target) < 0.003 and port_vol < best_risk:
            best_risk = port_vol
    if best_risk < float("inf"):
        frontier_risks.append(best_risk)
        frontier_returns.append(target)

# Find minimum variance portfolio
min_var_idx = np.argmin(frontier_risks)
min_var_risk = frontier_risks[min_var_idx]
min_var_return = frontier_returns[min_var_idx]

# Find maximum Sharpe ratio (tangency portfolio)
sharpe_frontier = [(r - risk_free_rate) / s for r, s in zip(frontier_returns, frontier_risks, strict=False)]
max_sharpe_idx = np.argmax(sharpe_frontier)
tangency_risk = frontier_risks[max_sharpe_idx]
tangency_return = frontier_returns[max_sharpe_idx]

# Create DataFrames
df_portfolios = pd.DataFrame({"risk": portfolio_risks, "return": portfolio_returns, "sharpe": sharpe_ratios})

df_frontier = pd.DataFrame({"risk": frontier_risks, "return": frontier_returns})

df_special = pd.DataFrame(
    {
        "risk": [min_var_risk, tangency_risk],
        "return": [min_var_return, tangency_return],
        "label": ["Min Variance", "Max Sharpe"],
    }
)

# Capital Market Line
cml_risks = np.array([0, tangency_risk * 1.8])
cml_returns = risk_free_rate + (tangency_return - risk_free_rate) / tangency_risk * cml_risks
df_cml = pd.DataFrame({"risk": cml_risks, "return": cml_returns})

# Create plot
plot = (
    ggplot()  # noqa: F405
    # Random portfolios colored by Sharpe ratio
    + geom_point(  # noqa: F405
        data=df_portfolios,
        mapping=aes(x="risk", y="return", color="sharpe"),  # noqa: F405
        size=4,
        alpha=0.6,
    )
    # Efficient frontier curve
    + geom_line(  # noqa: F405
        data=df_frontier,
        mapping=aes(x="risk", y="return"),  # noqa: F405
        color="#306998",
        size=3,
    )
    # Capital Market Line
    + geom_line(  # noqa: F405
        data=df_cml,
        mapping=aes(x="risk", y="return"),  # noqa: F405
        color="#666666",
        size=1.5,
        linetype="dashed",
    )
    # Special portfolios (Min Variance and Max Sharpe)
    + geom_point(  # noqa: F405
        data=df_special,
        mapping=aes(x="risk", y="return"),  # noqa: F405
        color="#DC2626",
        size=10,
        shape=18,
    )
    # Labels
    + labs(  # noqa: F405
        x="Risk (Standard Deviation)",
        y="Expected Return",
        title="frontier-efficient · letsplot · pyplots.ai",
        color="Sharpe Ratio",
    )
    # Color scale
    + scale_color_gradient(low="#FFD43B", high="#306998")  # noqa: F405
    # Theme
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        legend_title=element_text(size=18),  # noqa: F405
        legend_text=element_text(size=14),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save plot to current directory
export_ggsave(plot, "plot.png", path=".", scale=3)
export_ggsave(plot, "plot.html", path=".")
