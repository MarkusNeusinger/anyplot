""" pyplots.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-02-17
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Data
p = np.linspace(0, 1, 200)

gini = 2 * p * (1 - p)

entropy = np.zeros_like(p)
mask = (p > 0) & (p < 1)
entropy[mask] = -p[mask] * np.log2(p[mask]) - (1 - p[mask]) * np.log2(1 - p[mask])

gini_max = 2 * 0.5 * 0.5  # 0.5
entropy_max = 1.0

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Shaded region between curves to highlight the scaling difference
ax.fill_between(p, gini, entropy, alpha=0.10, color="#7B8FA1", label="Difference region")

ax.plot(
    p,
    gini,
    linewidth=3,
    color="#306998",
    label="Gini Impurity:  $2p(1-p)$",
    path_effects=[pe.Stroke(linewidth=5, foreground="white"), pe.Normal()],
)
ax.plot(
    p,
    entropy,
    linewidth=3,
    color="#C1694F",
    linestyle="--",
    label="Entropy (normalized):  $-p\\,\\log_2 p - (1{-}p)\\,\\log_2(1{-}p)$",
    path_effects=[pe.Stroke(linewidth=5, foreground="white"), pe.Normal()],
)

# Mark both maxima at p=0.5 with polished markers
ax.plot(0.5, gini_max, "o", color="#306998", markersize=11, zorder=5, markeredgecolor="white", markeredgewidth=2)
ax.plot(0.5, entropy_max, "o", color="#C1694F", markersize=11, zorder=5, markeredgecolor="white", markeredgewidth=2)

# Annotate Entropy maximum (arrow from left side for balance)
ax.annotate(
    "Entropy peak = 1.0\n$p = 0.5$",
    xy=(0.5, entropy_max),
    xytext=(0.18, 0.88),
    fontsize=15,
    color="#9E4A32",
    fontweight="medium",
    arrowprops={"arrowstyle": "->", "color": "#C1694F", "lw": 1.8, "connectionstyle": "arc3,rad=-0.15"},
    ha="center",
    va="top",
)

# Annotate Gini maximum (arrow from right side)
ax.annotate(
    "Gini peak = 0.5\n$p = 0.5$",
    xy=(0.5, gini_max),
    xytext=(0.72, 0.35),
    fontsize=15,
    color="#1E4A6E",
    fontweight="medium",
    arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 1.8, "connectionstyle": "arc3,rad=0.15"},
    ha="center",
    va="bottom",
)

# Bracket showing the difference at p=0.5
ax.annotate(
    "",
    xy=(0.505, entropy_max),
    xytext=(0.505, gini_max),
    arrowprops={"arrowstyle": "<->", "color": "#7B8FA1", "lw": 1.5},
)
ax.text(0.525, 0.75, "$\\Delta = 0.5$", fontsize=13, color="#5A6B7A", ha="left", va="center", fontstyle="italic")

# Vertical dashed line at p=0.5 for maximum impurity
ax.axvline(x=0.5, ymin=0, ymax=0.92, color="#AAAAAA", linestyle=":", linewidth=1.2, zorder=1)
ax.text(0.5, 0.04, "Maximum\nimpurity", fontsize=13, color="#777777", ha="center", va="bottom", fontstyle="italic")

# Style
ax.set_xlabel("Probability of Class 1 ($p$)", fontsize=20)
ax.set_ylabel("Impurity (normalized)", fontsize=20)
ax.set_title("line-impurity-comparison · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
legend = ax.legend(
    fontsize=15, loc="upper left", framealpha=0.92, edgecolor="#CCCCCC", fancybox=True, shadow=False, borderpad=1.0
)
legend.get_frame().set_linewidth(0.8)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.03, 1.08)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#BBBBBB")
ax.spines["bottom"].set_color("#BBBBBB")
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color="#999999")
ax.xaxis.grid(True, alpha=0.08, linewidth=0.5, color="#999999")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
