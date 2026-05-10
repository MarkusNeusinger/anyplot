""" anyplot.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-10
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1 — ALWAYS first series

# Generate realistic inertia decay pattern for K-means elbow curve
np.random.seed(42)
k_values = np.arange(1, 11)

base_inertia = 5000
inertias = []
for k in k_values:
    # Exponential decay with elbow effect at k=4
    if k <= 4:
        inertia = base_inertia * np.exp(-0.35 * (k - 1))
    else:
        inertia = base_inertia * np.exp(-0.35 * 3) * np.exp(-0.15 * (k - 4))
    inertia += np.random.uniform(-50, 50)
    inertias.append(max(inertia, 100))

inertias = np.array(inertias)

# Identify the elbow point
elbow_k = 4
elbow_inertia = inertias[elbow_k - 1]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.plot(
    k_values,
    inertias,
    color=BRAND,
    linewidth=3,
    marker="o",
    markersize=12,
    markerfacecolor=BRAND,
    markeredgecolor=PAGE_BG,
    markeredgewidth=0.5,
)

# Highlight the elbow point
ax.scatter([elbow_k], [elbow_inertia], s=400, color=BRAND, edgecolors=PAGE_BG, linewidths=0.5, zorder=5)

ax.annotate(
    f"Elbow Point\n(k={elbow_k})",
    xy=(elbow_k, elbow_inertia),
    xytext=(elbow_k + 1.8, elbow_inertia + 600),
    fontsize=18,
    fontweight="bold",
    color=INK,
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 2.5},
    bbox={"boxstyle": "round,pad=0.5", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9},
)

# Add diminishing returns region
ax.axvspan(elbow_k, max(k_values), alpha=0.1, color=INK_SOFT)

# Style
ax.set_xlabel("Number of Clusters (k)", fontsize=20, color=INK)
ax.set_ylabel("Inertia (Within-Cluster Sum of Squares)", fontsize=20, color=INK)
ax.set_title("elbow-curve · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.set_xticks(k_values)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
