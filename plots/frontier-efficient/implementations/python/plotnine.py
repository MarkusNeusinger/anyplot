"""anyplot.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    ggsave,
    guide_colorbar,
    guides,
    labs,
    scale_color_gradient,
    scale_shape_manual,
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
RISK_FREE_RATE = 0.02  # annual risk-free rate used for the Sharpe ratio

# Columns: set these to your table's column names
RISK = "Risk (annualized standard deviation)"  # role: risk
RETURN = "Expected return (annualized)"  # role: return
SHARPE = "Sharpe ratio"  # role: extra
KIND = "Key portfolio"  # legend and label text of the two marked portfolios, not a column of df

# Data: replace this block with your own table, for example df = pd.read_csv("portfolios.csv")
rng = np.random.default_rng(2024)
sector_returns = np.array([0.055, 0.065, 0.085, 0.105, 0.135, 0.150])  # utilities ... energy
sector_vols = np.array([0.13, 0.14, 0.16, 0.20, 0.27, 0.33])
sector_corr = np.array(
    [
        [1.00, 0.55, 0.40, 0.35, 0.25, 0.20],
        [0.55, 1.00, 0.50, 0.40, 0.30, 0.25],
        [0.40, 0.50, 1.00, 0.50, 0.45, 0.30],
        [0.35, 0.40, 0.50, 1.00, 0.60, 0.50],
        [0.25, 0.30, 0.45, 0.60, 1.00, 0.35],
        [0.20, 0.25, 0.30, 0.50, 0.35, 1.00],
    ]
)
sector_cov = sector_corr * np.outer(sector_vols, sector_vols)
n_sectors = len(sector_returns)

random_weights = rng.dirichlet(np.ones(n_sectors), size=220)
random_returns = random_weights @ sector_returns
random_risks = np.sqrt(np.einsum("ij,jk,ik->i", random_weights, sector_cov, random_weights))

frontier_targets = np.linspace(sector_returns.min(), sector_returns.max(), 80)
frontier_risks, frontier_returns = [], []
for target in frontier_targets:
    fit = minimize(
        lambda w: w @ sector_cov @ w,
        np.full(n_sectors, 1 / n_sectors),
        method="SLSQP",
        bounds=[(0, 1)] * n_sectors,
        constraints=[
            {"type": "eq", "fun": lambda w: w.sum() - 1},
            {"type": "eq", "fun": lambda w, t=target: w @ sector_returns - t},
        ],
    )
    if fit.success:
        frontier_risks.append(np.sqrt(fit.fun))
        frontier_returns.append(target)

# Keep the efficient branch only: from the minimum-variance portfolio upward
frontier_risks = np.array(frontier_risks)
frontier_returns = np.array(frontier_returns)
efficient = frontier_returns >= frontier_returns[frontier_risks.argmin()]
frontier_risks, frontier_returns = frontier_risks[efficient], frontier_returns[efficient]

df = pd.DataFrame(
    {RISK: np.concatenate([random_risks, frontier_risks]), RETURN: np.concatenate([random_returns, frontier_returns])}
)
df[SHARPE] = (df[RETURN] - RISK_FREE_RATE) / df[RISK]

# Plot: reads only df and the constants above
# The frontier is the set of portfolios that no lower-risk portfolio beats on return
by_risk = df.sort_values(RISK)
best_below = by_risk[RETURN].cummax().shift(fill_value=-np.inf)
is_frontier = by_risk[RETURN] > best_below
frontier = by_risk[is_frontier]
cloud = by_risk[~is_frontier]

# Key portfolios chosen by rule: lowest risk on the frontier, highest Sharpe ratio on the frontier
min_var = frontier.loc[frontier[RISK].idxmin()]
max_sharpe = frontier.loc[frontier[SHARPE].idxmax()]
marks = pd.DataFrame(
    {
        RISK: [min_var[RISK], max_sharpe[RISK]],
        RETURN: [min_var[RETURN], max_sharpe[RETURN]],
        KIND: ["Minimum variance", "Maximum Sharpe"],
    }
)
label_offset = 0.012 * (df[RISK].max() - df[RISK].min())

title = "frontier-efficient · python · plotnine · anyplot.ai"
imprint_seq = (IMPRINT_PALETTE[0], IMPRINT_PALETTE[2])  # single-polarity Imprint ramp

plot = (
    ggplot()
    + geom_point(cloud, aes(x=RISK, y=RETURN, color=SHARPE), size=2.2, alpha=0.75, stroke=0)
    + geom_line(frontier, aes(x=RISK, y=RETURN), color=INK, size=1.6)
    + geom_point(marks, aes(x=RISK, y=RETURN, shape=KIND), color=IMPRINT_PALETTE[4], fill=IMPRINT_PALETTE[3], size=4.5)
    + geom_text(
        marks,
        aes(x=RISK, y=RETURN, label=KIND),
        nudge_x=label_offset,
        nudge_y=-label_offset * 0.6,
        ha="left",
        va="top",
        size=8,
        color=INK,
    )
    + scale_color_gradient(low=imprint_seq[0], high=imprint_seq[1])
    + scale_shape_manual(values={"Minimum variance": "s", "Maximum Sharpe": "D"})
    + guides(shape="none", color=guide_colorbar(nbin=64))
    + labs(title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.12),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.04),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
    )
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
