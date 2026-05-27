""" anyplot.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    ggsave,
    labs,
    scale_color_cmap,
    theme,
    theme_minimal,
)
from scipy.optimize import minimize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data
np.random.seed(42)

n_assets = 5
n_portfolios = 300

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

weights = np.random.dirichlet(np.ones(n_assets), size=n_portfolios)

portfolio_returns = weights @ expected_returns
portfolio_risks = np.sqrt(np.diag(weights @ cov_matrix @ weights.T))

risk_free_rate = 0.03
sharpe_ratios = (portfolio_returns - risk_free_rate) / portfolio_risks

target_returns = np.linspace(min(expected_returns) + 0.01, max(expected_returns) - 0.01, 100)
frontier_risks = []
frontier_returns = []

for target in target_returns:
    constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1},
        {"type": "eq", "fun": lambda w, t=target: w @ expected_returns - t},
    ]
    bounds = tuple((0, 1) for _ in range(n_assets))
    result = minimize(
        lambda w: w @ cov_matrix @ w,
        np.ones(n_assets) / n_assets,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )
    if result.success:
        frontier_risks.append(np.sqrt(result.fun))
        frontier_returns.append(target)

min_var_idx = np.argmin(frontier_risks)
min_var_risk = frontier_risks[min_var_idx]
min_var_return = frontier_returns[min_var_idx]

frontier_sharpe = [(r - risk_free_rate) / s for r, s in zip(frontier_returns, frontier_risks, strict=True)]
max_sharpe_idx = np.argmax(frontier_sharpe)
max_sharpe_risk = frontier_risks[max_sharpe_idx]
max_sharpe_return = frontier_returns[max_sharpe_idx]

df_portfolios = pd.DataFrame({"risk": portfolio_risks, "return": portfolio_returns, "sharpe": sharpe_ratios})

df_frontier = pd.DataFrame({"risk": frontier_risks, "return": frontier_returns})

# Plot
plot = (
    ggplot()
    + geom_point(df_portfolios, aes(x="risk", y="return", color="sharpe"), size=3, alpha=0.6)
    + geom_line(df_frontier, aes(x="risk", y="return"), color=IMPRINT[0], size=2.5)
    + annotate("point", x=min_var_risk, y=min_var_return, color=IMPRINT[4], size=6, shape="s")
    + annotate("point", x=max_sharpe_risk, y=max_sharpe_return, color=IMPRINT[4], size=6, shape="D")
    + annotate("text", x=min_var_risk + 0.012, y=min_var_return, label="Min Var", size=14, ha="left", color=INK)
    + annotate(
        "text", x=max_sharpe_risk + 0.012, y=max_sharpe_return, label="Max Sharpe", size=14, ha="left", color=INK
    )
    + scale_color_cmap(cmap_name="viridis", name="Sharpe Ratio")
    + labs(x="Risk (Standard Deviation)", y="Expected Return", title="frontier-efficient · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        figure_size=(16, 9),
    )
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", dpi=300, width=16, height=9)
