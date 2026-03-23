""" pyplots.ai
line-growth-percentile: Pediatric Growth Chart with Percentile Curves
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 95/100 | Created: 2026-03-19
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Seaborn theming and context — distinctive seaborn features
sns.set_theme(
    style="whitegrid",
    rc={"grid.alpha": 0.15, "grid.linewidth": 0.6, "axes.edgecolor": "#cccccc", "font.family": "sans-serif"},
)
sns.set_context("talk", font_scale=1.1, rc={"lines.linewidth": 2.0})

# Data — WHO weight-for-age reference for boys, 0-36 months (realistic values)
np.random.seed(42)

age_months = np.arange(0, 37, 1)

# Approximate WHO P50 weight-for-age boys via interpolation of reference points
who_ref_ages = np.array([0, 1, 2, 3, 4, 5, 6, 9, 12, 15, 18, 24, 30, 36])
who_ref_p50 = np.array([3.3, 4.5, 5.6, 6.4, 7.0, 7.5, 7.9, 9.2, 9.6, 10.3, 11.0, 12.2, 13.3, 14.3])
median_weight = np.interp(age_months, who_ref_ages, who_ref_p50)
sd = 0.4 + 0.028 * age_months

# Z-scores for standard normal percentiles
percentile_z = {"P3": -1.8808, "P10": -1.2816, "P25": -0.6745, "P50": 0.0, "P75": 0.6745, "P90": 1.2816, "P97": 1.8808}

percentiles = {label: median_weight + z * sd for label, z in percentile_z.items()}

# Build long-format DataFrame for percentile curves — seaborn-idiomatic approach
records = []
for label, values in percentiles.items():
    for i, age in enumerate(age_months):
        records.append({"Age (months)": age, "Weight (kg)": values[i], "Percentile": label})
percentile_df = pd.DataFrame(records)

# Individual patient data — boy with gradual drift below P25
patient_ages = np.array([0, 1, 2, 4, 6, 9, 12, 15, 18, 24, 30, 36])
patient_weights = np.array([3.5, 4.4, 5.4, 6.8, 7.6, 8.8, 9.1, 9.7, 10.2, 11.2, 12.0, 12.5])
patient_df = pd.DataFrame({"Age (months)": patient_ages, "Weight (kg)": patient_weights})

# Generate graduated blue palette using seaborn's color utilities
blue_palette = sns.light_palette("#08306b", n_colors=8, reverse=True)
band_colors = [blue_palette[1], blue_palette[2], blue_palette[3], blue_palette[3], blue_palette[2], blue_palette[1]]
band_alphas = [0.30, 0.25, 0.20, 0.20, 0.25, 0.30]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Percentile bands (fill_between is the only part requiring matplotlib directly)
band_labels = list(percentiles.keys())
for i in range(len(band_labels) - 1):
    ax.fill_between(
        age_months,
        percentiles[band_labels[i]],
        percentiles[band_labels[i + 1]],
        color=band_colors[i],
        alpha=band_alphas[i],
    )

# Percentile lines via seaborn lineplot with hue — core library usage
line_sizes = {"P3": 1.0, "P10": 1.0, "P25": 1.2, "P50": 2.8, "P75": 1.2, "P90": 1.0, "P97": 1.0}
line_palette = sns.dark_palette("#08306b", n_colors=7, reverse=False)
percentile_color_map = dict(zip(percentile_z.keys(), line_palette, strict=False))
percentile_color_map["P50"] = "#08306b"

sns.lineplot(
    data=percentile_df,
    x="Age (months)",
    y="Weight (kg)",
    hue="Percentile",
    hue_order=list(percentile_z.keys()),
    palette=percentile_color_map,
    size="Percentile",
    sizes=line_sizes,
    alpha=0.6,
    legend=False,
    ax=ax,
)
# Emphasize P50 with stronger alpha
p50_data = percentile_df[percentile_df["Percentile"] == "P50"]
sns.lineplot(
    data=p50_data, x="Age (months)", y="Weight (kg)", color="#08306b", linewidth=2.8, alpha=1.0, legend=False, ax=ax
)

# Patient trajectory — seaborn lineplot + scatterplot with larger markers
sns.lineplot(
    data=patient_df, x="Age (months)", y="Weight (kg)", color="#c0392b", linewidth=3.0, zorder=5, legend=False, ax=ax
)
sns.scatterplot(
    data=patient_df,
    x="Age (months)",
    y="Weight (kg)",
    color="#c0392b",
    s=200,
    zorder=6,
    edgecolor="white",
    linewidth=2.0,
    legend=False,
    ax=ax,
)

# Percentile labels on right margin
for label, values in percentiles.items():
    ax.text(
        age_months[-1] + 0.8,
        values[-1],
        label,
        fontsize=16,
        fontweight="bold" if label == "P50" else "normal",
        color="#08306b" if label == "P50" else "#2171b5",
        va="center",
        alpha=0.9 if label == "P50" else 0.7,
    )

# Axes and title
ax.set_xlabel("Age (months)", fontsize=20)
ax.set_ylabel("Weight (kg)", fontsize=20)
ax.set_title("line-growth-percentile · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(0, 36)
ax.set_xticks(np.arange(0, 37, 3))
ax.xaxis.grid(False)
ax.set_ylim(0, None)

# Seaborn despine — idiomatic spine removal
sns.despine(ax=ax, top=True, right=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
