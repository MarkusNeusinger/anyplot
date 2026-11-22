"""anyplot.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize
from scipy.optimize import minimize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

sns.set_theme(
    style="whitegrid",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
RISK_FREE_RATE = 0.02  # annual return of the risk-free asset, as a fraction

# Columns: set these to your table's column names
RISK = "Risk (standard deviation, %)"  # role: risk
RETURN = "Expected return (%)"  # role: return
ON_FRONTIER = "On efficient frontier"  # role: extra
SHARPE = "Sharpe ratio"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("portfolios.csv")
# One row per portfolio: the random portfolios plus the points of the efficient frontier.
np.random.seed(42)
n_assets = 5
expected_returns = np.array([0.08, 0.12, 0.10, 0.15, 0.07])
volatilities = np.array([0.15, 0.22, 0.18, 0.28, 0.12])
correlation = np.array(
    [
        [1.0, 0.3, 0.2, 0.4, 0.1],
        [0.3, 1.0, 0.5, 0.3, 0.2],
        [0.2, 0.5, 1.0, 0.4, 0.3],
        [0.4, 0.3, 0.4, 1.0, 0.2],
        [0.1, 0.2, 0.3, 0.2, 1.0],
    ]
)
cov_matrix = np.outer(volatilities, volatilities) * correlation


def calc_vol(w):
    return np.sqrt(w @ cov_matrix @ w)


random_weights = np.random.random((300, n_assets))
random_weights /= random_weights.sum(axis=1, keepdims=True)
random_risks = np.array([calc_vol(w) for w in random_weights])
random_returns = random_weights @ expected_returns

bounds = [(0, 1)] * n_assets
init_weights = np.full(n_assets, 1 / n_assets)
min_var = minimize(
    calc_vol, init_weights, method="SLSQP", bounds=bounds, constraints={"type": "eq", "fun": lambda x: x.sum() - 1}
)
frontier_risks, frontier_returns = [], []
for target in np.linspace(min_var.x @ expected_returns, expected_returns.max() * 0.98, 100):
    result = minimize(
        calc_vol,
        init_weights,
        method="SLSQP",
        bounds=bounds,
        constraints=[
            {"type": "eq", "fun": lambda x: x.sum() - 1},
            {"type": "eq", "fun": lambda x, t=target: x @ expected_returns - t},
        ],
    )
    if result.success:
        frontier_risks.append(calc_vol(result.x))
        frontier_returns.append(target)

df = pd.DataFrame(
    {
        RISK: np.concatenate([random_risks, frontier_risks]) * 100,
        RETURN: np.concatenate([random_returns, frontier_returns]) * 100,
        ON_FRONTIER: [False] * len(random_risks) + [True] * len(frontier_risks),
    }
)

# Plot: reads only df and the constants above
df[SHARPE] = (df[RETURN] - RISK_FREE_RATE * 100) / df[RISK]
cloud = df[~df[ON_FRONTIER]]
frontier = df[df[ON_FRONTIER]].sort_values(RISK)
has_frontier = not frontier.empty

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.scatterplot(
    data=cloud,
    x=RISK,
    y=RETURN,
    hue=SHARPE,
    palette=imprint_seq,
    s=45,
    alpha=0.65,
    edgecolor=PAGE_BG,
    linewidth=0.3,
    legend=False,
    ax=ax,
)

cbar = fig.colorbar(
    ScalarMappable(norm=Normalize(cloud[SHARPE].min(), cloud[SHARPE].max()), cmap=imprint_seq), ax=ax, pad=0.02
)
cbar.set_label(SHARPE, fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

if has_frontier:
    min_var_point = frontier.loc[frontier[RISK].idxmin()]
    max_sharpe_point = frontier.loc[frontier[SHARPE].idxmax()]

    # Capital market line: from the risk-free rate through the tangency portfolio
    cml_x = np.array([0, max_sharpe_point[RISK] * 1.5])
    cml_y = RISK_FREE_RATE * 100 + max_sharpe_point[SHARPE] * cml_x

    sns.lineplot(
        data=frontier,
        x=RISK,
        y=RETURN,
        color=IMPRINT_PALETTE[0],
        linewidth=2.5,
        label="Efficient frontier",
        zorder=5,
        ax=ax,
    )
    ax.plot(
        cml_x, cml_y, color=IMPRINT_PALETTE[2], linewidth=1.5, linestyle="--", label="Capital market line", zorder=4
    )

    for point, color, label in [
        (min_var_point, IMPRINT_PALETTE[2], "Minimum variance portfolio"),
        (max_sharpe_point, IMPRINT_PALETTE[1], "Maximum Sharpe portfolio"),
    ]:
        ax.scatter(
            point[RISK],
            point[RETURN],
            color=color,
            s=220,
            marker="*",
            edgecolors=PAGE_BG,
            linewidths=1,
            zorder=10,
            label=label,
        )

ax.scatter(0, RISK_FREE_RATE * 100, color=IMPRINT_PALETTE[2], s=70, edgecolors=PAGE_BG, linewidths=1, zorder=10)
ax.annotate(
    f"Risk-free rate ({RISK_FREE_RATE:.0%})",
    xy=(0, RISK_FREE_RATE * 100),
    xytext=(8, 8),
    textcoords="offset points",
    fontsize=8,
    color=INK,
)

# Style
ax.set_title("frontier-efficient · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(RISK, fontsize=10)
ax.set_ylabel(RETURN, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.set_xlim(-0.03 * df[RISK].max(), df[RISK].max() * 1.05)
ax.set_ylim(0, df[RETURN].max() * 1.15)
ax.legend(loc="lower right", fontsize=8, framealpha=0.95)
fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
