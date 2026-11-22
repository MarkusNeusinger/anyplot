"""anyplot.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: pygal 3.1.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style
from scipy.optimize import minimize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
RISK_FREE_RATE = 0.02  # risk-free rate for the Sharpe ratio
RANDOM = "Random"  # kind of a randomly weighted portfolio
FRONTIER = "Frontier"  # kind of a portfolio on the efficient frontier

# Columns: set these to your table's column names
RISK = "Risk (standard deviation)"  # role: risk
RETURN = "Expected return"  # role: return
KIND = "Portfolio kind"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("portfolios.csv")
rng = np.random.default_rng(42)
asset_returns = np.array([0.08, 0.12, 0.15, 0.10, 0.18])
asset_vols = np.array([0.15, 0.20, 0.25, 0.18, 0.30])
asset_corr = np.array(
    [
        [1.0, 0.3, 0.4, 0.2, 0.3],
        [0.3, 1.0, 0.5, 0.3, 0.4],
        [0.4, 0.5, 1.0, 0.3, 0.5],
        [0.2, 0.3, 0.3, 1.0, 0.3],
        [0.3, 0.4, 0.5, 0.3, 1.0],
    ]
)
cov = np.outer(asset_vols, asset_vols) * asset_corr
n_assets = len(asset_returns)

weights = rng.dirichlet(np.ones(n_assets), size=400)
random_ret = weights @ asset_returns
random_risk = np.sqrt(np.einsum("ij,jk,ik->i", weights, cov, weights))

# Efficient frontier: minimum variance for each target return, long-only, fully invested
frontier_ret = np.linspace(asset_returns.min() + 0.002, asset_returns.max() - 0.002, 50)
frontier_risk = []
for target in frontier_ret:
    res = minimize(
        lambda w: w @ cov @ w,
        np.full(n_assets, 1 / n_assets),
        method="SLSQP",
        bounds=[(0, 1)] * n_assets,
        constraints=[
            {"type": "eq", "fun": lambda w: w.sum() - 1},
            {"type": "eq", "fun": lambda w, t=target: w @ asset_returns - t},
        ],
    )
    frontier_risk.append(np.sqrt(res.fun))

df = pd.DataFrame(
    {
        RISK: np.concatenate([random_risk, frontier_risk]),
        RETURN: np.concatenate([random_ret, frontier_ret]),
        KIND: [RANDOM] * len(random_risk) + [FRONTIER] * len(frontier_risk),
    }
)

# Plot: reads only df and the constants above
df["sharpe"] = (df[RETURN] - RISK_FREE_RATE) / df[RISK]
is_frontier = df[KIND] == FRONTIER
random_df = df[~is_frontier]
frontier_df = df[is_frontier].sort_values(RISK)
has_frontier = not frontier_df.empty
if has_frontier:
    frontier_df = frontier_df[frontier_df[RETURN] >= frontier_df.loc[frontier_df[RISK].idxmin(), RETURN]]
    min_var = frontier_df.loc[frontier_df[RISK].idxmin()]
    max_sharpe = frontier_df.loc[frontier_df["sharpe"].idxmax()]

# Sharpe bins for the cloud: terciles, coloured along the Imprint sequential ramp (#009E73 to #4467A3)
edge_lo, edge_hi = random_df["sharpe"].quantile([1 / 3, 2 / 3])
bins = [
    (f"Sharpe below {edge_lo:.2f}", random_df[random_df["sharpe"] < edge_lo]),
    (
        f"Sharpe {edge_lo:.2f} to {edge_hi:.2f}",
        random_df[(random_df["sharpe"] >= edge_lo) & (random_df["sharpe"] < edge_hi)],
    ),
    (f"Sharpe above {edge_hi:.2f}", random_df[random_df["sharpe"] >= edge_hi]),
]
seq_start, seq_end = IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]
seq_mid = "#" + "".join(f"{(int(seq_start[i : i + 2], 16) + int(seq_end[i : i + 2], 16)) // 2:02X}" for i in (1, 3, 5))
series_colors = [seq_start, seq_mid, seq_end, IMPRINT_PALETTE[4], IMPRINT_PALETTE[1], IMPRINT_PALETTE[3]]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(series_colors),
    opacity="0.65",
    opacity_hover="0.95",
    title_font_size=66,
    label_font_size=52,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=9,
)

x_pad = (df[RISK].max() - df[RISK].min()) * 0.04
y_pad = (df[RETURN].max() - df[RETURN].min()) * 0.04

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="frontier-efficient · python · pygal · anyplot.ai",
    x_title=RISK,
    y_title=RETURN,
    show_x_guides=True,
    show_y_guides=True,
    stroke=False,
    dots_size=9,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    truncate_legend=-1,
    x_value_formatter=lambda x: f"{x:.0%}",
    value_formatter=lambda y: f"{y:.0%}",
    xrange=(df[RISK].min() - x_pad, df[RISK].max() + x_pad),
    range=(df[RETURN].min() - y_pad, df[RETURN].max() + y_pad),
    margin=40,
)

for label, part in bins:
    chart.add(label, list(zip(part[RISK], part[RETURN], strict=True)))
if has_frontier:
    chart.add(
        "Efficient frontier",
        list(zip(frontier_df[RISK], frontier_df[RETURN], strict=True)),
        stroke=True,
        dots_size=0,
        stroke_style={"width": 9},
    )
    chart.add(
        f"Minimum variance ({min_var[RISK]:.1%} risk)",
        [(min_var[RISK], min_var[RETURN])],
        dots_size=24,
        stroke_style={"width": 0},
    )
    chart.add(
        f"Maximum Sharpe ({max_sharpe['sharpe']:.2f})",
        [(max_sharpe[RISK], max_sharpe[RETURN])],
        dots_size=24,
        stroke_style={"width": 0},
    )

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
