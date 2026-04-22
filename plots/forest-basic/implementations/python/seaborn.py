""" pyplots.ai
forest-basic: Meta-Analysis Forest Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-27
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Meta-analysis of treatment effect (mean difference) from 10 studies
np.random.seed(42)

studies = [
    "Smith et al. 2018",
    "Johnson et al. 2019",
    "Williams et al. 2019",
    "Brown et al. 2020",
    "Davis et al. 2020",
    "Miller et al. 2021",
    "Wilson et al. 2021",
    "Moore et al. 2022",
    "Taylor et al. 2022",
    "Anderson et al. 2023",
]

# Effect sizes (mean differences) - some favor treatment, some favor control
effect_sizes = [-0.45, 0.12, -0.28, -0.52, 0.05, -0.38, -0.15, -0.42, -0.22, -0.35]
ci_widths = [0.35, 0.28, 0.42, 0.25, 0.55, 0.32, 0.38, 0.30, 0.45, 0.28]
ci_lower = [e - w for e, w in zip(effect_sizes, ci_widths, strict=True)]
ci_upper = [e + w for e, w in zip(effect_sizes, ci_widths, strict=True)]
weights = [12.5, 8.2, 6.8, 14.1, 5.5, 10.3, 7.9, 11.8, 6.2, 9.7]

# Calculate pooled estimate (weighted mean)
pooled_effect = np.average(effect_sizes, weights=weights)
pooled_se = np.sqrt(1 / np.sum([w / (ci_w**2) for w, ci_w in zip(weights, ci_widths, strict=True)]))
pooled_ci_lower = pooled_effect - 1.96 * pooled_se
pooled_ci_upper = pooled_effect + 1.96 * pooled_se

df = pd.DataFrame(
    {"study": studies, "effect": effect_sizes, "ci_lower": ci_lower, "ci_upper": ci_upper, "weight": weights}
)

# Sort by effect size
df = df.sort_values("effect", ascending=True).reset_index(drop=True)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Y positions for studies (leave space at bottom for pooled estimate)
y_positions = np.arange(len(df)) + 1.5

# Scale marker sizes based on weight (larger for more precise studies)
marker_sizes = (df["weight"] / df["weight"].max()) * 400 + 100

# Plot confidence intervals as horizontal lines
for i, (_, row) in enumerate(df.iterrows()):
    ax.hlines(y=y_positions[i], xmin=row["ci_lower"], xmax=row["ci_upper"], color="#306998", linewidth=2.5, zorder=1)

# Plot point estimates using seaborn
sns.scatterplot(
    data=df,
    x="effect",
    y=y_positions,
    size="weight",
    sizes=(100, 500),
    color="#306998",
    edgecolor="white",
    linewidth=1.5,
    legend=False,
    ax=ax,
    zorder=2,
)

# Add study labels on the left
for i, (_, row) in enumerate(df.iterrows()):
    ax.text(-1.4, y_positions[i], row["study"], fontsize=14, va="center", ha="left", fontweight="medium")

# Add effect size values on the right
for i, (_, row) in enumerate(df.iterrows()):
    ax.text(
        1.1,
        y_positions[i],
        f"{row['effect']:.2f} [{row['ci_lower']:.2f}, {row['ci_upper']:.2f}]",
        fontsize=12,
        va="center",
        ha="left",
        family="monospace",
    )

# Draw pooled estimate diamond
diamond_y = 0.3
diamond_height = 0.4
diamond = mpatches.Polygon(
    [
        [pooled_effect, diamond_y],
        [pooled_ci_lower, diamond_y + diamond_height / 2],
        [pooled_effect, diamond_y + diamond_height],
        [pooled_ci_upper, diamond_y + diamond_height / 2],
    ],
    closed=True,
    facecolor="#FFD43B",
    edgecolor="#306998",
    linewidth=2,
    zorder=3,
)
ax.add_patch(diamond)

# Add pooled estimate label
ax.text(-1.4, diamond_y + diamond_height / 2, "Pooled Estimate", fontsize=14, va="center", ha="left", fontweight="bold")
ax.text(
    1.1,
    diamond_y + diamond_height / 2,
    f"{pooled_effect:.2f} [{pooled_ci_lower:.2f}, {pooled_ci_upper:.2f}]",
    fontsize=12,
    va="center",
    ha="left",
    family="monospace",
    fontweight="bold",
)

# Vertical reference line at null effect (0)
ax.axvline(x=0, color="#666666", linestyle="--", linewidth=2, zorder=0, alpha=0.7)

# Separator line above pooled estimate
ax.axhline(y=1.0, color="#CCCCCC", linewidth=1.5, zorder=0)

# Styling
ax.set_xlim(-1.5, 1.8)
ax.set_ylim(-0.3, len(df) + 2)
ax.set_xlabel("Mean Difference (Treatment - Control)", fontsize=20)
ax.set_ylabel("")
ax.set_title("forest-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Remove y-axis ticks (study names are shown as text)
ax.set_yticks([])

# Style x-axis ticks
ax.tick_params(axis="x", labelsize=16)

# Add annotation for interpretation
ax.text(
    -0.75,
    len(df) + 1.5,
    "← Favors Treatment",
    fontsize=14,
    ha="center",
    va="center",
    color="#306998",
    fontweight="medium",
)
ax.text(
    0.75, len(df) + 1.5, "Favors Control →", fontsize=14, ha="center", va="center", color="#666666", fontweight="medium"
)

# Adjust grid
ax.grid(axis="x", alpha=0.3, linestyle="--")
ax.grid(axis="y", visible=False)

# Remove top and right spines
sns.despine(left=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
