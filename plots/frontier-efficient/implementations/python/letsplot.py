""" anyplot.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_viridis,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Generate simulated asset data
np.random.seed(42)
n_assets = 6
n_portfolios = 300
risk_free_rate = 0.03

# Asset expected returns and volatilities
asset_returns = np.array([0.08, 0.10, 0.12, 0.15, 0.07, 0.18])
asset_volatility = np.array([0.12, 0.15, 0.18, 0.25, 0.10, 0.30])

# Correlation matrix
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

# Generate efficient frontier
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

# Find special portfolios
min_var_idx = np.argmin(frontier_risks)
min_var_risk = frontier_risks[min_var_idx]
min_var_return = frontier_returns[min_var_idx]

sharpe_frontier = [(r - risk_free_rate) / s for r, s in zip(frontier_returns, frontier_risks, strict=False)]
max_sharpe_idx = np.argmax(sharpe_frontier)
tangency_risk = frontier_risks[max_sharpe_idx]
tangency_return = frontier_returns[max_sharpe_idx]

# DataFrames
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

# Custom theme
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_x=element_line(color=RULE, size=0.3),
    panel_grid_major_y=element_line(color=RULE, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=24, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=16, color=INK_SOFT),
    legend_title=element_text(size=18, color=INK),
)

# Plot
plot = (
    ggplot()
    + geom_point(data=df_portfolios, mapping=aes(x="risk", y="return", color="sharpe"), size=4, alpha=0.6)
    + geom_line(data=df_frontier, mapping=aes(x="risk", y="return"), color=IMPRINT[2], size=3)
    + geom_line(data=df_cml, mapping=aes(x="risk", y="return"), color=INK_SOFT, size=1.5, linetype="dashed")
    + geom_point(data=df_special, mapping=aes(x="risk", y="return"), color=IMPRINT[1], size=10, shape=18)
    + labs(
        x="Risk (Standard Deviation)",
        y="Expected Return",
        title="frontier-efficient · letsplot · anyplot.ai",
        color="Sharpe Ratio",
    )
    + scale_color_viridis()
    + ggsize(1600, 900)
    + theme_minimal()
    + anyplot_theme
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
