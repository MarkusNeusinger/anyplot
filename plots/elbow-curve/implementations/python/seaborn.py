""" anyplot.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-10
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"
ACCENT = "#C475FD"

# Configure seaborn theme with theme-adaptive colors
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
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Simulate realistic elbow curve data
np.random.seed(42)
k_values = list(range(1, 11))

# Realistic inertia values showing typical elbow pattern
inertias = [
    2800,  # k=1
    1650,  # k=2
    950,  # k=3
    520,  # k=4 - elbow point
    450,  # k=5
    400,  # k=6
    365,  # k=7
    340,  # k=8
    320,  # k=9
    305,  # k=10
]

# Add small noise for realism
noise = np.random.uniform(-10, 10, len(inertias))
inertias = [max(0, i + n) for i, n in zip(inertias, noise, strict=True)]

# Create figure and plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot the elbow curve with seaborn
sns.lineplot(
    x=k_values,
    y=inertias,
    ax=ax,
    color=BRAND,
    linewidth=3.5,
    marker="o",
    markersize=16,
    markerfacecolor=ACCENT,
    markeredgecolor=BRAND,
    markeredgewidth=2.5,
)

# Annotate the elbow point (k=4)
elbow_k = 4
elbow_inertia = inertias[elbow_k - 1]
ax.annotate(
    f"Elbow Point (k={elbow_k})",
    xy=(elbow_k, elbow_inertia),
    xytext=(elbow_k + 2, elbow_inertia + 400),
    fontsize=18,
    arrowprops={"arrowstyle": "->", "color": INK, "lw": 2},
    color=INK,
    fontweight="bold",
)

# Labels and styling
ax.set_xlabel("Number of Clusters (k)", fontsize=20, color=INK)
ax.set_ylabel("Inertia (Within-Cluster Sum of Squares)", fontsize=20, color=INK)
ax.set_title("elbow-curve · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_xticks(k_values)

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Subtle y-axis grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
