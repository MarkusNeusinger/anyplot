"""anyplot.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-10
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
K = "Number of clusters (k)"  # role: k_values
INERTIA = "Inertia (within-cluster sum of squares)"  # role: inertia

# Data: replace this block with your own table, for example df = pd.read_csv("inertia.csv")
rng = np.random.default_rng(42)
base_inertia = [2800, 1650, 950, 520, 450, 400, 365, 340, 320, 305]
df = pd.DataFrame(
    {K: np.arange(1, len(base_inertia) + 1), INERTIA: np.array(base_inertia) + rng.uniform(-10, 10, len(base_inertia))}
)

# Plot: reads only df and the constants above
# Elbow = the point farthest from the chord joining the first and last points (normalised axes)
kx = (df[K] - df[K].min()) / (df[K].max() - df[K].min())
ky = (df[INERTIA] - df[INERTIA].min()) / (df[INERTIA].max() - df[INERTIA].min())
chord_gap = (kx + ky - 1).abs() if ky.iloc[0] > ky.iloc[-1] else (kx - ky).abs()
elbow = df.loc[chord_gap.idxmax()]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.lineplot(
    data=df,
    x=K,
    y=INERTIA,
    ax=ax,
    color=IMPRINT_PALETTE[0],
    linewidth=2.0,
    marker="o",
    markersize=8,
    markerfacecolor=IMPRINT_PALETTE[0],
    markeredgecolor=PAGE_BG,
    markeredgewidth=1.2,
)

# Highlight the elbow at its own data point
ax.plot(
    elbow[K],
    elbow[INERTIA],
    marker="o",
    markersize=13,
    markerfacecolor=IMPRINT_PALETTE[1],
    markeredgecolor=INK,
    markeredgewidth=1.5,
    zorder=5,
)
ax.annotate(
    f"Elbow at k = {int(elbow[K])}",
    xy=(elbow[K], elbow[INERTIA]),
    xytext=(40, 30),
    textcoords="offset points",
    fontsize=10,
    fontweight="bold",
    color=INK,
    arrowprops={"arrowstyle": "->", "color": INK, "lw": 1.2},
)

# Style
ax.set_title("elbow-curve · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(K, fontsize=10, color=INK)
ax.set_ylabel(INERTIA, fontsize=10, color=INK)
ax.set_xticks(df[K])
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_ylim(0, df[INERTIA].max() * 1.08)
sns.despine(ax=ax)
ax.yaxis.grid(True, linewidth=0.6)
ax.set_axisbelow(True)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
