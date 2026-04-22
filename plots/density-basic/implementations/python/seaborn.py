""" pyplots.ai
density-basic: Basic Density Plot
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 91/100 | Updated: 2026-02-23
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - bimodal distribution of test scores
np.random.seed(42)
test_scores = np.concatenate(
    [
        np.random.normal(68, 8, 280),  # Main group centered at 68
        np.random.normal(90, 4, 120),  # High achievers group
    ]
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# KDE line first (for peak detection), then fill
sns.kdeplot(data=test_scores, ax=ax, fill=False, color="#306998", linewidth=3, bw_adjust=0.9)
line = ax.get_lines()[0]
x_kde, y_kde = line.get_xdata(), line.get_ydata()
ax.fill_between(x_kde, y_kde, alpha=0.5, color="#306998")

sns.rugplot(data=test_scores, ax=ax, color="#1a3a5c", alpha=0.5, height=0.05)

# Annotate the two peaks to tell the bimodal story
peak1_idx = np.argmax(y_kde[x_kde < 80])
peak2_idx = len(y_kde[x_kde < 80]) + np.argmax(y_kde[x_kde >= 80])

px1, py1 = x_kde[peak1_idx], y_kde[peak1_idx]
ax.annotate(
    "Main group",
    xy=(px1, py1),
    xytext=(px1 - 14, py1 - 0.008),
    fontsize=16,
    fontweight="medium",
    color="#1a3a5c",
    arrowprops={"arrowstyle": "->", "color": "#1a3a5c", "lw": 1.5},
    ha="center",
    va="top",
)
ax.axvline(px1, color="#306998", alpha=0.15, linestyle="--", linewidth=1.5)

px2, py2 = x_kde[peak2_idx], y_kde[peak2_idx]
ax.annotate(
    "High achievers",
    xy=(px2, py2),
    xytext=(px2 + 12, py2 - 0.004),
    fontsize=16,
    fontweight="medium",
    color="#1a3a5c",
    arrowprops={"arrowstyle": "->", "color": "#1a3a5c", "lw": 1.5},
    ha="center",
    va="top",
)
ax.axvline(px2, color="#306998", alpha=0.15, linestyle="--", linewidth=1.5)

# Style
ax.set_xlabel("Test Score (points)", fontsize=20)
ax.set_ylabel("Density", fontsize=20)
ax.set_title("density-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
