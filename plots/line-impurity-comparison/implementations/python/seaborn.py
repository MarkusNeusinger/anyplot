""" pyplots.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-02-17
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data
p = np.linspace(0, 1, 500)

gini = 2 * p * (1 - p)
gini_normalized = gini / gini.max()

# Entropy with edge case handling (0 at p=0 and p=1)
entropy = np.zeros_like(p)
mask = (p > 0) & (p < 1)
entropy[mask] = -p[mask] * np.log2(p[mask]) - (1 - p[mask]) * np.log2(1 - p[mask])
entropy_normalized = entropy / entropy.max()

# Plot setup
sns.set_theme(
    style="whitegrid",
    rc={
        "axes.grid.axis": "y",
        "grid.alpha": 0.15,
        "grid.linewidth": 0.8,
        "axes.edgecolor": "#888888",
        "axes.linewidth": 1.2,
        "font.family": "sans-serif",
    },
)

fig, ax = plt.subplots(figsize=(16, 9))

palette = sns.color_palette(["#306998", "#E8833A"])

# Shaded divergence region between curves
ax.fill_between(p, gini_normalized, entropy_normalized, alpha=0.10, color=palette[0], zorder=1)

# Plot lines using seaborn
sns.lineplot(x=p, y=gini_normalized, color=palette[0], linewidth=3, linestyle="-", label="Gini: 2p(1\u2212p)", ax=ax)
sns.lineplot(
    x=p,
    y=entropy_normalized,
    color=palette[1],
    linewidth=2.8,
    linestyle="--",
    label="Entropy: \u2212p log\u2082p \u2212 (1\u2212p) log\u2082(1\u2212p)",
    ax=ax,
)

# Max divergence annotation — positioned close to the divergence region
divergence = np.abs(entropy_normalized - gini_normalized)
max_div_idx = np.argmax(divergence)
mid_y = (gini_normalized[max_div_idx] + entropy_normalized[max_div_idx]) / 2

ax.annotate(
    "Max divergence",
    xy=(p[max_div_idx], mid_y),
    xytext=(p[max_div_idx] + 0.06, mid_y + 0.08),
    fontsize=14,
    fontstyle="italic",
    color=palette[0],
    arrowprops={"arrowstyle": "->", "color": palette[0], "lw": 1.4},
)

# Max impurity annotation at p=0.5
ax.plot(0.5, 1.0, "o", color="#2c2c2c", markersize=9, zorder=5)
ax.annotate(
    "Max impurity\np = 0.5",
    xy=(0.5, 1.0),
    xytext=(0.35, 0.78),
    fontsize=15,
    fontweight="medium",
    color="#2c2c2c",
    arrowprops={"arrowstyle": "->", "color": "#666666", "lw": 1.6, "connectionstyle": "arc3,rad=0.15"},
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "#f0f4f8", "edgecolor": palette[0], "alpha": 0.92, "lw": 0.8},
)

# Style
ax.set_xlabel("Probability (p)", fontsize=20, labelpad=12)
ax.set_ylabel("Impurity (normalized)", fontsize=20, labelpad=12)
ax.set_title("line-impurity-comparison \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(0, 1)
ax.set_ylim(-0.02, 1.08)

sns.despine(ax=ax, top=True, right=True)

# Legend
legend = ax.legend(
    title="Splitting Criterion",
    title_fontsize=18,
    fontsize=16,
    loc="upper right",
    framealpha=0.95,
    edgecolor="#cccccc",
    fancybox=True,
    borderpad=1.0,
)
legend.get_frame().set_linewidth(0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
