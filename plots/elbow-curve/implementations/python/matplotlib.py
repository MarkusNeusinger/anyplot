""" anyplot.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, first series is always brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
K = "Number of Clusters (k)"  # role: k_values
INERTIA = "Inertia (Within-Cluster Sum of Squares)"  # role: inertia

# Data: replace this block with your own table, for example df = pd.read_csv("kmeans_inertia.csv")
np.random.seed(42)
k_values = np.arange(1, 11)
inertias = []
for k in k_values:
    # Exponential decay with a bend at k=4, plus a little noise
    if k <= 4:
        inertia = 5000 * np.exp(-0.35 * (k - 1))
    else:
        inertia = 5000 * np.exp(-0.35 * 3) * np.exp(-0.15 * (k - 4))
    inertia += np.random.uniform(-50, 50)
    inertias.append(max(inertia, 100))
df = pd.DataFrame({K: k_values, INERTIA: inertias})

# Plot: reads only df and the constants above
ks = df[K].to_numpy()
inertia_values = df[INERTIA].to_numpy()

# Elbow = point farthest from the straight line joining the first and last point (in normalized units)
nx = (ks - ks.min()) / (ks.max() - ks.min())
ny = (inertia_values - inertia_values.min()) / (inertia_values.max() - inertia_values.min())
elbow_idx = int(np.argmax(np.abs(ny - (ny[0] + (ny[-1] - ny[0]) * (nx - nx[0]) / (nx[-1] - nx[0])))))
elbow_k = ks[elbow_idx]
elbow_inertia = inertia_values[elbow_idx]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.plot(
    ks,
    inertia_values,
    color=IMPRINT_PALETTE[0],
    linewidth=2.5,
    marker="o",
    markersize=7,
    markeredgecolor=PAGE_BG,
    markeredgewidth=0.5,
)

# Highlight the elbow point
ax.scatter([elbow_k], [elbow_inertia], s=170, color=IMPRINT_PALETTE[0], edgecolors=INK, linewidths=1.2, zorder=5)

ax.annotate(
    f"Elbow point (k={elbow_k})",
    xy=(elbow_k, elbow_inertia),
    xytext=(60, 45),
    textcoords="offset points",
    fontsize=11,
    fontweight="bold",
    color=INK,
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.5},
    bbox={"boxstyle": "round,pad=0.4", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9},
)

# Diminishing-returns region after the elbow
ax.axvspan(elbow_k, ks.max(), alpha=0.1, color=INK_SOFT, linewidth=0)

# Style
ax.set_xlabel(K, fontsize=10, color=INK)
ax.set_ylabel(INERTIA, fontsize=10, color=INK)
ax.set_title("elbow-curve · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xticks(ks)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8, color=INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
