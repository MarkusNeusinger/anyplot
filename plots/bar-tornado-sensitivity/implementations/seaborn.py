"""pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 72/100 | Created: 2026-03-07
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Configure seaborn style and context
sns.set_style("whitegrid", {"grid.linestyle": "--", "grid.alpha": 0.3})
sns.set_context("talk", font_scale=1.1)

# Data - NPV sensitivity analysis for a capital investment project
parameters = [
    "Discount Rate",
    "Revenue Growth",
    "Material Cost",
    "Labor Cost",
    "Tax Rate",
    "Initial Investment",
    "Operating Margin",
    "Terminal Value",
    "Working Capital",
    "Inflation Rate",
]

base_npv = 120.0  # Base case NPV in $M

np.random.seed(42)
low_values = base_npv + np.array([-38, -30, -25, -18, -15, -14, -10, -8, -5, -3], dtype=float)
high_values = base_npv + np.array([32, 28, 20, 22, 12, 11, 13, 9, 6, 4], dtype=float)

# Calculate ranges and sort by total impact
total_range = high_values - low_values
sort_idx = np.argsort(total_range)
parameters = [parameters[i] for i in sort_idx]
low_values = low_values[sort_idx]
high_values = high_values[sort_idx]

# Build deltas relative to base case
low_delta = low_values - base_npv
high_delta = high_values - base_npv

# Use seaborn color palette
palette = sns.color_palette("colorblind")
color_low = palette[1]  # orange
color_high = palette[0]  # blue

# Create long-form DataFrame for seaborn barplot
df_low = pd.DataFrame({"Parameter": parameters, "NPV ($M)": low_delta, "Scenario": "Low Scenario"})
df_high = pd.DataFrame({"Parameter": parameters, "NPV ($M)": high_delta, "Scenario": "High Scenario"})
df = pd.concat([df_low, df_high], ignore_index=True)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

sns.barplot(
    data=df,
    y="Parameter",
    x="NPV ($M)",
    hue="Scenario",
    hue_order=["Low Scenario", "High Scenario"],
    palette=[color_low, color_high],
    dodge=False,
    ax=ax,
    zorder=2,
    edgecolor="none",
)

# Shift x-axis to show absolute NPV values
current_ticks = ax.get_xticks()
ax.set_xticks(current_ticks)
ax.set_xticklabels([f"${int(t + base_npv)}" for t in current_ticks])

# Base case reference line with annotation
ax.axvline(x=0, color="#333333", linewidth=1.8, linestyle="--", zorder=3)
ax.text(
    1.0,
    len(parameters) - 0.5,
    f"Base Case ${int(base_npv)}M",
    fontsize=13,
    fontweight="bold",
    color="#333333",
    ha="left",
    va="bottom",
    fontstyle="italic",
)

# Bar-end value annotations
for i, _param in enumerate(parameters):
    lv = low_values[i]
    hv = high_values[i]
    ld = low_delta[i]
    hd = high_delta[i]
    ax.text(ld - 1.2, i, f"${lv:.0f}M", va="center", ha="right", fontsize=12, color="#555555")
    ax.text(hd + 1.2, i, f"${hv:.0f}M", va="center", ha="left", fontsize=12, color="#555555")

# Emphasize top 3 most impactful parameters with bold labels
ytick_labels = ax.get_yticklabels()
for i, label in enumerate(ytick_labels):
    if i >= len(parameters) - 3:
        label.set_fontweight("bold")
        label.set_fontsize(17)

# Style refinements
ax.set_ylabel("")
ax.set_xlabel("Net Present Value ($M)", fontsize=20)
ax.set_title("bar-tornado-sensitivity \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.tick_params(axis="y", labelsize=16)
ax.tick_params(axis="x", labelsize=16)
sns.despine(left=True, bottom=False)
ax.yaxis.grid(False)
ax.xaxis.grid(True, alpha=0.2, linewidth=0.8)

# Legend
ax.legend(fontsize=15, frameon=False, loc="upper right")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
