"""anyplot.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
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
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_gradient,
    scale_fill_manual,
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

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
RISK_FREE_RATE = 0.03  # annual risk-free rate for the Sharpe ratio and the capital market line

# Columns: set these to your table's column names
RISK = "Risk (standard deviation)"  # role: risk
RETURN = "Expected return"  # role: return
SHARPE = "Sharpe ratio"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("portfolios.csv")
np.random.seed(42)
n_assets = 6
n_portfolios = 300
asset_returns = np.array([0.08, 0.10, 0.12, 0.15, 0.07, 0.18])
asset_volatility = np.array([0.12, 0.15, 0.18, 0.25, 0.10, 0.30])
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

portfolio_returns = []
portfolio_risks = []
for _ in range(n_portfolios):
    weights = np.random.random(n_assets)
    weights /= np.sum(weights)
    portfolio_returns.append(np.sum(weights * asset_returns))
    portfolio_risks.append(np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))))

# Frontier: lowest-risk random portfolio near each target return
frontier_risks = []
frontier_returns = []
for target in np.linspace(0.07, 0.18, 50):
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

risks = np.array(portfolio_risks + frontier_risks)
returns = np.array(portfolio_returns + frontier_returns)
df = pd.DataFrame({RISK: risks, RETURN: returns, SHARPE: (returns - RISK_FREE_RATE) / risks})

# Plot: reads only df and the constants above
# Efficient frontier: portfolios that beat every lower-risk portfolio on return
by_risk = df.sort_values(RISK)
frontier = by_risk[by_risk[RETURN] >= by_risk[RETURN].cummax()]
cloud = df

min_var = frontier.loc[frontier[RISK].idxmin()]
max_sharpe = frontier.loc[frontier[SHARPE].idxmax()]
special = pd.DataFrame(
    {
        RISK: [min_var[RISK], max_sharpe[RISK]],
        RETURN: [min_var[RETURN], max_sharpe[RETURN]],
        "label": ["Minimum variance", "Maximum Sharpe"],
    }
)

# Capital market line: from the risk-free rate at zero risk through the tangency portfolio
cml_risks = np.array([0.0, max_sharpe[RISK] * 1.8])
cml = pd.DataFrame({RISK: cml_risks, RETURN: RISK_FREE_RATE + max_sharpe[SHARPE] * cml_risks})

title = "frontier-efficient · python · letsplot · anyplot.ai"

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=RULE, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=12, color=INK),
    axis_text=element_text(size=10, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=16, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=10, color=INK_SOFT),
    legend_title=element_text(size=11, color=INK),
    legend_position="right",
)

plot = (
    ggplot()
    + geom_point(data=cloud, mapping=aes(x=RISK, y=RETURN, color=SHARPE), size=2.2, alpha=0.65)
    + geom_line(data=cml, mapping=aes(x=RISK, y=RETURN), color=INK_SOFT, size=0.8, linetype="dashed")
    + geom_line(data=frontier, mapping=aes(x=RISK, y=RETURN), color=INK, size=1.6)
    + geom_point(
        data=special,
        mapping=aes(x=RISK, y=RETURN, fill="label"),
        color=INK,
        size=6,
        shape=23,
        stroke=1.2,
        show_legend=False,
    )
    + geom_text(
        data=special,
        mapping=aes(x=RISK, y=RETURN, label="label"),
        color=INK,
        size=4,
        hjust="left",
        nudge_x=0.004,
        nudge_y=-0.006,
        show_legend=False,
    )
    + scale_color_gradient(low=IMPRINT_PALETTE[0], high=IMPRINT_PALETTE[2])
    + scale_fill_manual(values=[IMPRINT_PALETTE[1], IMPRINT_PALETTE[3]])
    + labs(title=title)
    + ggsize(800, 450)
    + theme_minimal()
    + anyplot_theme
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
