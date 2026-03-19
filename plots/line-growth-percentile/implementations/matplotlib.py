"""pyplots.ai
line-growth-percentile: Pediatric Growth Chart with Percentile Curves
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-19
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - WHO-like weight-for-age reference for boys 0-36 months
age_months = np.arange(0, 37, 1)

median_weight = 3.3 + 0.7 * age_months - 0.009 * age_months**2 + 0.00007 * age_months**3
sd = 0.35 + 0.025 * age_months

z_scores = {"P3": -1.881, "P10": -1.282, "P25": -0.674, "P50": 0.0, "P75": 0.674, "P90": 1.282, "P97": 1.881}

percentiles = {}
for label, z in z_scores.items():
    percentiles[label] = median_weight + z * sd

patient_ages = np.array([0, 1, 2, 4, 6, 9, 12, 15, 18, 24, 30, 36])
patient_weights = np.array([3.4, 4.5, 5.6, 7.0, 7.8, 9.0, 10.0, 10.8, 11.5, 12.6, 13.8, 14.8])

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

band_pairs = [("P3", "P10"), ("P10", "P25"), ("P25", "P75"), ("P75", "P90"), ("P90", "P97")]
band_alphas = [0.35, 0.25, 0.15, 0.25, 0.35]
band_color = "#4A90D9"

for (lower, upper), alpha in zip(band_pairs, band_alphas, strict=True):
    ax.fill_between(age_months, percentiles[lower], percentiles[upper], color=band_color, alpha=alpha, linewidth=0)

percentile_labels = ["P3", "P10", "P25", "P50", "P75", "P90", "P97"]
line_widths = [1.5, 1.5, 1.5, 3.0, 1.5, 1.5, 1.5]
line_styles = ["--", "--", "-", "-", "-", "--", "--"]
line_colors = ["#7BAFD4", "#6BA3CC", "#5B97C4", "#2A6496", "#5B97C4", "#6BA3CC", "#7BAFD4"]

for label, lw, ls, lc in zip(percentile_labels, line_widths, line_styles, line_colors, strict=True):
    ax.plot(age_months, percentiles[label], linewidth=lw, linestyle=ls, color=lc, alpha=0.8)

for label in percentile_labels:
    y_pos = percentiles[label][-1]
    fontweight = "bold" if label == "P50" else "normal"
    ax.annotate(
        label,
        xy=(36, y_pos),
        xytext=(37.2, y_pos),
        fontsize=14,
        fontweight=fontweight,
        color="#2A6496",
        va="center",
        ha="left",
        annotation_clip=False,
    )

ax.plot(
    patient_ages,
    patient_weights,
    marker="o",
    markersize=10,
    linewidth=2.5,
    color="#E8563A",
    markeredgecolor="white",
    markeredgewidth=1.5,
    zorder=5,
    label="Patient (Boy)",
)

# Style
ax.set_xlabel("Age (months)", fontsize=20)
ax.set_ylabel("Weight (kg)", fontsize=20)
ax.set_title("line-growth-percentile · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(0, 36)
ax.set_xticks(np.arange(0, 37, 3))
y_max = percentiles["P97"][-1] + 1.5
ax.set_ylim(0, y_max)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.legend(fontsize=16, loc="upper left")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
