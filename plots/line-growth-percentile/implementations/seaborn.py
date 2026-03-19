"""pyplots.ai
line-growth-percentile: Pediatric Growth Chart with Percentile Curves
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-19
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


sns.set_style("whitegrid", {"grid.alpha": 0.2, "grid.linewidth": 0.8})

# Data — WHO-style weight-for-age reference for boys, 0-36 months
np.random.seed(42)

age_months = np.arange(0, 37, 1)

median_weight = 3.3 + 0.8 * age_months - 0.008 * age_months**2 + 0.00005 * age_months**3
sd = 0.4 + 0.04 * age_months

# Z-scores for standard normal percentiles
percentile_values = {
    "P3": -1.8808,
    "P10": -1.2816,
    "P25": -0.6745,
    "P50": 0.0,
    "P75": 0.6745,
    "P90": 1.2816,
    "P97": 1.8808,
}

percentiles = {}
for label, z in percentile_values.items():
    percentiles[label] = median_weight + z * sd

# Individual patient data — healthy boy tracked at well-child visits
patient_ages = np.array([0, 1, 2, 4, 6, 9, 12, 15, 18, 24, 30, 36])
patient_weights = np.array([3.5, 4.3, 5.4, 7.0, 8.1, 9.2, 10.1, 10.9, 11.5, 12.8, 14.0, 15.2])

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

blue_shades = [
    "#08306b",  # P3-P10 (darkest)
    "#2171b5",  # P10-P25
    "#6baed6",  # P25-P50
    "#6baed6",  # P50-P75
    "#2171b5",  # P75-P90
    "#08306b",  # P90-P97 (darkest)
]

band_labels = list(percentiles.keys())
band_alphas = [0.25, 0.30, 0.35, 0.35, 0.30, 0.25]

for i in range(len(band_labels) - 1):
    lower = percentiles[band_labels[i]]
    upper = percentiles[band_labels[i + 1]]
    ax.fill_between(age_months, lower, upper, color=blue_shades[i], alpha=band_alphas[i])

# Percentile lines
line_alphas = {"P3": 0.5, "P10": 0.5, "P25": 0.6, "P50": 1.0, "P75": 0.6, "P90": 0.5, "P97": 0.5}
line_widths = {"P3": 1.0, "P10": 1.0, "P25": 1.2, "P50": 2.5, "P75": 1.2, "P90": 1.0, "P97": 1.0}

for label, values in percentiles.items():
    ax.plot(age_months, values, color="#08306b", alpha=line_alphas[label], linewidth=line_widths[label])

# Percentile labels on the right margin
for label, values in percentiles.items():
    ax.text(
        age_months[-1] + 0.8,
        values[-1],
        label,
        fontsize=13,
        fontweight="bold" if label == "P50" else "normal",
        color="#08306b",
        va="center",
        alpha=0.8,
    )

# Patient data overlay
patient_df = pd.DataFrame({"age": patient_ages, "weight": patient_weights})
sns.lineplot(data=patient_df, x="age", y="weight", color="#d62728", linewidth=2.5, zorder=5, ax=ax)
sns.scatterplot(
    data=patient_df, x="age", y="weight", color="#d62728", s=120, zorder=6, edgecolor="white", linewidth=1.5, ax=ax
)

# Style
ax.set_xlabel("Age (months)", fontsize=20)
ax.set_ylabel("Weight (kg)", fontsize=20)
ax.set_title("line-growth-percentile · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_xlim(0, 36)
ax.set_xticks(np.arange(0, 37, 3))
ax.xaxis.grid(False)
ax.set_ylim(0, None)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
