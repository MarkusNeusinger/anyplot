""" pyplots.ai
line-growth-percentile: Pediatric Growth Chart with Percentile Curves
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-19
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


# Data - WHO-like weight-for-age reference for boys 0-36 months
age_months = np.arange(0, 37, 1)

median_weight = 3.3 + 0.7 * age_months - 0.009 * age_months**2 + 0.00007 * age_months**3
sd = 0.35 + 0.025 * age_months

z_scores = {"P3": -1.881, "P10": -1.282, "P25": -0.674, "P50": 0.0, "P75": 0.674, "P90": 1.282, "P97": 1.881}

percentiles = {}
for label, z in z_scores.items():
    percentiles[label] = median_weight + z * sd

# Patient with clinically interesting trajectory: starts near P75, falters toward P10, then recovers
patient_ages = np.array([0, 1, 2, 4, 6, 9, 12, 15, 18, 24, 30, 36])
patient_weights = np.array([3.7, 4.6, 5.7, 7.1, 7.6, 8.4, 9.2, 10.2, 11.0, 12.5, 14.5, 16.0])

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Refined blue gradient palette for bands
band_pairs = [("P3", "P10"), ("P10", "P25"), ("P25", "P75"), ("P75", "P90"), ("P90", "P97")]
band_colors = ["#1B4F72", "#2471A3", "#AED6F1", "#2471A3", "#1B4F72"]
band_alphas = [0.25, 0.20, 0.15, 0.20, 0.25]

for (lower, upper), bc, alpha in zip(band_pairs, band_colors, band_alphas, strict=True):
    ax.fill_between(age_months, percentiles[lower], percentiles[upper], color=bc, alpha=alpha, linewidth=0)

percentile_labels = ["P3", "P10", "P25", "P50", "P75", "P90", "P97"]
line_widths = [1.2, 1.2, 1.5, 3.5, 1.5, 1.2, 1.2]
line_styles = ["--", "--", "-", "-", "-", "--", "--"]
line_colors = ["#85C1E9", "#5DADE2", "#2E86C1", "#1A5276", "#2E86C1", "#5DADE2", "#85C1E9"]

for label, lw, ls, lc in zip(percentile_labels, line_widths, line_styles, line_colors, strict=True):
    ax.plot(age_months, percentiles[label], linewidth=lw, linestyle=ls, color=lc, alpha=0.85)

# Percentile labels on right margin
for label in percentile_labels:
    y_pos = percentiles[label][-1]
    fontweight = "bold" if label == "P50" else "normal"
    fontsize = 17 if label == "P50" else 16
    ax.annotate(
        label,
        xy=(36, y_pos),
        xytext=(37.2, y_pos),
        fontsize=fontsize,
        fontweight=fontweight,
        color="#1A5276",
        va="center",
        ha="left",
        annotation_clip=False,
    )

# Patient trajectory with emphasized markers
ax.plot(
    patient_ages,
    patient_weights,
    marker="o",
    markersize=10,
    linewidth=2.5,
    color="#E74C3C",
    markerfacecolor="#E74C3C",
    markeredgecolor="white",
    markeredgewidth=1.5,
    zorder=5,
    label="Patient (Boy)",
)

# Annotations at clinically meaningful points
ax.annotate(
    "Growth faltering",
    xy=(9, 8.4),
    xytext=(13, 6.0),
    fontsize=16,
    fontweight="medium",
    color="#C0392B",
    arrowprops={"arrowstyle": "-|>", "color": "#C0392B", "lw": 1.5, "connectionstyle": "arc3,rad=-0.2"},
    zorder=6,
)

ax.annotate(
    "Catch-up growth",
    xy=(30, 14.5),
    xytext=(23, 17.0),
    fontsize=16,
    fontweight="medium",
    color="#1E8449",
    arrowprops={"arrowstyle": "-|>", "color": "#1E8449", "lw": 1.5, "connectionstyle": "arc3,rad=-0.2"},
    zorder=6,
)

# Style
ax.set_xlabel("Age (months)", fontsize=20)
ax.set_ylabel("Weight (kg)", fontsize=20)
fig.suptitle("line-growth-percentile · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", y=0.98)
ax.set_title(
    "Weight-for-Age, Boys, 0\u201336 months  \u2022  WHO Growth Standards", fontsize=16, color="#5D6D7E", pad=12
)
ax.tick_params(axis="both", labelsize=16, length=5, width=0.8)
ax.set_xlim(0, 36)
ax.set_xticks(np.arange(0, 37, 3))
ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
ax.tick_params(axis="x", which="minor", length=3, width=0.5)
y_max = percentiles["P97"][-1] + 2.5
ax.set_ylim(0, y_max)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.8)
ax.spines["bottom"].set_linewidth(0.8)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color="#BDC3C7")
ax.legend(fontsize=16, loc="upper left", framealpha=0.9, edgecolor="#D5D8DC")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
