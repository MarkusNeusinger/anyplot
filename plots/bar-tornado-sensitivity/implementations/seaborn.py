"""pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-07
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
# Some parameters have inverted relationships:
# - Material Cost: lower cost → higher NPV (low input = positive effect)
# - Tax Rate: lower tax → higher NPV (low input = positive effect)
low_values = base_npv + np.array([-38, -30, 22, -18, 10, -14, -10, -8, -5, -3], dtype=float)
high_values = base_npv + np.array([32, 28, -18, 22, -8, 11, 13, 9, 6, 4], dtype=float)

# Calculate ranges and sort by total impact
total_range = np.abs(high_values - low_values)
sort_idx = np.argsort(total_range)
parameters = [parameters[i] for i in sort_idx]
low_values = low_values[sort_idx]
high_values = high_values[sort_idx]

# Build deltas relative to base case
low_delta = low_values - base_npv
high_delta = high_values - base_npv

# Custom palette anchored on Python Blue
color_low = "#D4652F"  # warm copper-orange for low scenario
color_high = "#306998"  # Python Blue for high scenario

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

# Base case reference line with annotation at top
ax.axvline(x=0, color="#333333", linewidth=1.8, linestyle="--", zorder=3)
ax.annotate(
    f"Base Case ${int(base_npv)}M",
    xy=(0, len(parameters) - 1),
    xytext=(8, -20),
    textcoords="offset points",
    fontsize=12,
    fontweight="bold",
    color="#333333",
    ha="left",
    va="top",
    fontstyle="italic",
)

# Bar-end value annotations
for i, _param in enumerate(parameters):
    lv = low_values[i]
    hv = high_values[i]
    ld = low_delta[i]
    hd = high_delta[i]
    # Position annotations at the outer end of each bar
    neg_x = min(ld, hd)
    pos_x = max(ld, hd)
    ax.text(neg_x - 1.2, i, f"${min(lv, hv):.0f}M", va="center", ha="right", fontsize=12, color="#555555")
    ax.text(pos_x + 1.2, i, f"${max(lv, hv):.0f}M", va="center", ha="left", fontsize=12, color="#555555")

# Emphasize top 3 most impactful parameters with bold labels
ytick_labels = ax.get_yticklabels()
for i, label in enumerate(ytick_labels):
    if i >= len(parameters) - 3:
        label.set_fontweight("bold")
        label.set_fontsize(17)

# Style refinements
ax.set_ylabel("Input Parameter", fontsize=20)
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
