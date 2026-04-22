""" pyplots.ai
ks-test-comparison: Kolmogorov-Smirnov Plot for Distribution Comparison
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 96/100 | Created: 2026-02-17
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


# Data
np.random.seed(42)
good_customers = np.random.beta(5, 2, 500) * 100
bad_customers = np.random.beta(2, 4, 500) * 100

# K-S test
ks_stat, p_value = stats.ks_2samp(good_customers, bad_customers)

# Compute ECDFs
good_sorted = np.sort(good_customers)
bad_sorted = np.sort(bad_customers)
good_ecdf = np.arange(1, len(good_sorted) + 1) / len(good_sorted)
bad_ecdf = np.arange(1, len(bad_sorted) + 1) / len(bad_sorted)

# Find maximum distance point
all_values = np.sort(np.concatenate([good_sorted, bad_sorted]))
good_cdf_at_all = np.searchsorted(good_sorted, all_values, side="right") / len(good_sorted)
bad_cdf_at_all = np.searchsorted(bad_sorted, all_values, side="right") / len(bad_sorted)
differences = np.abs(good_cdf_at_all - bad_cdf_at_all)
max_idx = np.argmax(differences)
max_x = all_values[max_idx]
max_y_good = good_cdf_at_all[max_idx]
max_y_bad = bad_cdf_at_all[max_idx]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# "Bad Customers" drawn with heavier weight and white outline — focal distribution
# White outline behind for separation from gridlines
ax.step(bad_sorted, bad_ecdf, where="post", linewidth=5.0, color="white", zorder=3)
ax.step(
    bad_sorted, bad_ecdf, where="post", linewidth=3.2, color="#E5921A", label="Bad Customers", linestyle="--", zorder=4
)

# "Good Customers" — reference distribution, slightly thinner
ax.step(
    good_sorted,
    good_ecdf,
    where="post",
    linewidth=2.6,
    color="#306998",
    label="Good Customers",
    linestyle="-",
    zorder=3,
)

# Gradient-style shaded region at maximum distance
y_span = np.linspace(max_y_bad, max_y_good, 40)
for i in range(len(y_span) - 1):
    frac = i / (len(y_span) - 1)
    alpha = 0.18 - 0.10 * abs(frac - 0.5) * 2
    ax.fill_betweenx([y_span[i], y_span[i + 1]], max_x - 2.0, max_x + 2.0, color="#306998", alpha=alpha, zorder=1)

# K-S distance line with double-ended annotation arrows
mid_y = (max_y_good + max_y_bad) / 2
ax.annotate(
    "",
    xy=(max_x, max_y_good),
    xytext=(max_x, max_y_bad),
    arrowprops={
        "arrowstyle": "<->",
        "color": "#2D2D2D",
        "linewidth": 2.2,
        "linestyle": ":",
        "shrinkA": 0,
        "shrinkB": 0,
    },
    zorder=5,
)

# Endpoint markers
ax.scatter([max_x, max_x], [max_y_bad, max_y_good], color="#2D2D2D", s=140, zorder=6, edgecolors="white", linewidth=1.5)

# K-S statistic annotation
ax.annotate(
    f"D = {ks_stat:.3f}",
    xy=(max_x, mid_y),
    xytext=(max_x + 8, mid_y + 0.06),
    fontsize=18,
    fontweight="bold",
    color="#2D2D2D",
    arrowprops={"arrowstyle": "->", "color": "#555555", "linewidth": 1.5, "connectionstyle": "arc3,rad=-0.15"},
    va="center",
    bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#AAAAAA", "alpha": 0.95},
)

# Interpretation text — guides the viewer to the key insight
ax.text(
    0.97,
    0.16,
    "Strong separation: distributions\nare significantly different",
    transform=ax.transAxes,
    fontsize=14,
    ha="right",
    va="bottom",
    color="#444444",
    linespacing=1.4,
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "#F0F4F8", "edgecolor": "#CCCCCC", "alpha": 0.85},
)

# P-value text
p_text = "p-value < 0.001" if p_value < 0.001 else f"p-value = {p_value:.4f}"
ax.text(
    0.97,
    0.05,
    p_text,
    transform=ax.transAxes,
    fontsize=16,
    ha="right",
    va="bottom",
    color="#555555",
    fontstyle="italic",
)

# Style
ax.set_xlabel("Credit Score (0–100)", fontsize=20)
ax.set_ylabel("Cumulative Proportion (0–1)", fontsize=20)
ax.set_title("ks-test-comparison · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=28)

# Subtitle for data storytelling — positioned below the title
ax.text(
    0.5,
    1.02,
    "K-S test reveals bad customers cluster at low scores while good customers spread higher",
    transform=ax.transAxes,
    fontsize=14,
    ha="center",
    va="bottom",
    color="#777777",
    fontstyle="italic",
)

ax.tick_params(axis="both", labelsize=16)
ax.set_ylim(-0.02, 1.04)
ax.set_xlim(-2, 102)
ax.legend(fontsize=16, loc="upper left", framealpha=0.9, edgecolor="#CCCCCC")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.6)
ax.spines["bottom"].set_linewidth(0.6)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color="#AAAAAA")
ax.set_facecolor("#FAFAFA")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
