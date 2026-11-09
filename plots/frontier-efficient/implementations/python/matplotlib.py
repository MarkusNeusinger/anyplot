""" anyplot.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from scipy.optimize import minimize
from scipy.spatial import ConvexHull


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions; the Sharpe ratio uses the sequential Imprint colormap
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

# Constants
RISK_FREE_RATE = 3.0  # annual risk-free rate, in the unit of the return column (%)

# Columns: set these to your table's column names
RISK = "Risk: standard deviation (% per year)"  # role: risk
RETURN = "Expected return (% per year)"  # role: return

# Data: replace this block with your own table, for example df = pd.read_csv("portfolios.csv")
# Five-asset universe (bonds to small caps); 400 random long-only portfolios plus the
# long-only mean-variance optimum for 60 target returns
np.random.seed(42)
asset_returns = np.array([0.12, 0.10, 0.14, 0.08, 0.16])
asset_volatility = np.array([0.18, 0.12, 0.25, 0.10, 0.30])
asset_correlation = np.array(
    [
        [1.00, 0.30, 0.50, 0.20, 0.40],
        [0.30, 1.00, 0.25, 0.60, 0.35],
        [0.50, 0.25, 1.00, 0.15, 0.55],
        [0.20, 0.60, 0.15, 1.00, 0.25],
        [0.40, 0.35, 0.55, 0.25, 1.00],
    ]
)
asset_cov = np.outer(asset_volatility, asset_volatility) * asset_correlation
long_only = [(0.0, 1.0)] * len(asset_returns)
fully_invested = {"type": "eq", "fun": lambda w: w.sum() - 1.0}
min_variance_weights = minimize(
    lambda w: w @ asset_cov @ w, np.full(len(asset_returns), 0.2), bounds=long_only, constraints=[fully_invested]
).x
optimal_weights = [
    minimize(
        lambda w: w @ asset_cov @ w,
        min_variance_weights,
        bounds=long_only,
        constraints=[fully_invested, {"type": "eq", "fun": lambda w, t=target: w @ asset_returns - t}],
    ).x
    for target in np.linspace(min_variance_weights @ asset_returns, asset_returns.max(), 60)
]
weights = np.vstack([np.random.dirichlet(np.ones(len(asset_returns)), 400), optimal_weights])
df = pd.DataFrame(
    {RISK: 100 * np.sqrt(np.einsum("ij,jk,ik->i", weights, asset_cov, weights)), RETURN: 100 * weights @ asset_returns}
)

# Plot: reads only df and the constants above
points = df[[RISK, RETURN]].dropna().astype(float).to_numpy()
sharpe = (points[:, 1] - RISK_FREE_RATE) / points[:, 0]

# Efficient frontier: the upper-left edge of the convex hull, from the least risky to the highest-return portfolio
ring = ConvexHull(points).vertices  # counterclockwise
top = int(np.argmax(points[ring, 1]))
left = int(np.argmin(points[ring, 0]))
frontier = points[np.roll(ring, -top)[: (left - top) % len(ring) + 1][::-1]]
min_variance = frontier[0]
tangency = points[np.argmax(sharpe)]
cml_risk = np.array([0.0, 1.5 * tangency[0]])
cml_return = RISK_FREE_RATE + sharpe.max() * cml_risk

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG, layout="constrained")
ax.set_facecolor(PAGE_BG)
cloud = ax.scatter(points[:, 0], points[:, 1], c=sharpe, cmap=imprint_seq, s=16, alpha=0.75, linewidths=0, zorder=2)
ax.plot(
    frontier[:, 0],
    frontier[:, 1],
    color=IMPRINT_PALETTE[0],
    linewidth=3,
    solid_capstyle="round",
    path_effects=[pe.Stroke(linewidth=5.5, foreground=PAGE_BG), pe.Normal()],
    label="Efficient frontier",
    zorder=4,
)
ax.plot(
    cml_risk,
    cml_return,
    color=INK_SOFT,
    linewidth=1.2,
    linestyle=(0, (5, 3)),
    label=f"Capital market line (risk-free rate {RISK_FREE_RATE:g}%)",
    zorder=3,
)
ax.scatter(0, RISK_FREE_RATE, s=40, color=INK_SOFT, zorder=5, clip_on=False)
ax.scatter(
    *min_variance,
    s=110,
    marker="D",
    color=IMPRINT_PALETTE[1],
    edgecolors=INK,
    linewidths=0.9,
    label="Minimum variance portfolio",
    zorder=6,
)
ax.scatter(
    *tangency,
    s=260,
    marker="*",
    color=IMPRINT_PALETTE[3],
    edgecolors=INK,
    linewidths=0.9,
    label=f"Maximum Sharpe ratio portfolio ({sharpe.max():.2f})",
    zorder=6,
)

cbar = fig.colorbar(cloud, ax=ax, pad=0.02, fraction=0.035, aspect=24)
cbar.set_label("Sharpe ratio", fontsize=9, color=INK)
cbar.solids.set_alpha(1)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT, length=0)
cbar.outline.set_visible(False)

# Style
ax.set_title("frontier-efficient · python · matplotlib · anyplot.ai", fontsize=12, fontweight="bold", color=INK)
ax.set_xlabel(RISK, fontsize=10, color=INK)
ax.set_ylabel(RETURN, fontsize=10, color=INK)
ax.set_xlim(0, points[:, 0].max() * 1.04)
ax.set_ylim(0, max(points[:, 1].max(), cml_return.max()) * 1.06)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.grid(True, alpha=0.15, color=INK, linewidth=0.6)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
legend = ax.legend(fontsize=8, loc="upper left", frameon=True)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
legend.get_frame().set_linewidth(0.6)
plt.setp(legend.get_texts(), color=INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
