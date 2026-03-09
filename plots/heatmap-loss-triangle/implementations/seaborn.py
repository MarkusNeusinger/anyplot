""" pyplots.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-09
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Data
np.random.seed(42)

accident_years = list(range(2015, 2025))
development_periods = list(range(1, 11))
n_years = len(accident_years)
n_periods = len(development_periods)

# Base initial claims by accident year (in thousands)
base_claims = [4200, 4500, 4800, 5100, 5400, 5700, 6000, 6300, 6600, 7000]

# Age-to-age development factors (decreasing as claims mature)
dev_factors = [2.50, 1.45, 1.22, 1.12, 1.07, 1.04, 1.025, 1.015, 1.008]

# Build cumulative triangle
cumulative = np.full((n_years, n_periods), np.nan)
is_projected = np.full((n_years, n_periods), False)

for i in range(n_years):
    # Period 1 value
    cumulative[i, 0] = base_claims[i] + np.random.normal(0, 200)

    for j in range(1, n_periods):
        factor = dev_factors[j - 1] + np.random.normal(0, 0.02)
        cumulative[i, j] = cumulative[i, j - 1] * factor

    # Mark projected cells: for year i, periods after (n_years - i) are projected
    actual_periods = n_years - i
    for j in range(actual_periods, n_periods):
        is_projected[i, j] = True

# Create DataFrame for heatmap
heatmap_data = pd.DataFrame(
    cumulative, index=[str(y) for y in accident_years], columns=[str(p) for p in development_periods]
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Custom colormap
cmap = LinearSegmentedColormap.from_list("loss_triangle", ["#e8f0fe", "#306998", "#1a3a5c"], N=256)

# Draw heatmap without annotations (we'll add custom ones)
sns.heatmap(
    heatmap_data,
    ax=ax,
    cmap=cmap,
    annot=False,
    linewidths=1.5,
    linecolor="white",
    cbar_kws={"label": "Cumulative Claims ($K)", "shrink": 0.8},
)

# Customize colorbar label size
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=13)
cbar.set_label("Cumulative Claims ($K)", fontsize=15)

# Add annotations and visual distinction for actual vs projected
for i in range(n_years):
    for j in range(n_periods):
        val = cumulative[i, j]
        projected = is_projected[i, j]

        # Format value with thousands separator
        if val >= 10000:
            label = f"{val / 1000:.0f}K"
        else:
            label = f"{val:,.0f}"

        # Text color based on background brightness
        norm_val = (val - np.nanmin(cumulative)) / (np.nanmax(cumulative) - np.nanmin(cumulative))
        text_color = "white" if norm_val > 0.55 else "#1a1a1a"

        # Add hatching overlay for projected cells
        if projected:
            rect = mpatches.Rectangle((j, i), 1, 1, facecolor="white", edgecolor="none", alpha=0.25)
            ax.add_patch(rect)
            hatch_rect = mpatches.Rectangle(
                (j, i), 1, 1, facecolor="none", edgecolor="#666666", hatch="////", linewidth=0
            )
            ax.add_patch(hatch_rect)

        ax.text(
            j + 0.5,
            i + 0.5,
            label,
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold" if not projected else "normal",
            fontstyle="normal" if not projected else "italic",
            color=text_color,
        )

# Development factors row below the heatmap
factor_text = "  Dev Factors:  " + "  ".join([f"{f:.3f}" for f in dev_factors])
ax.text(
    0.5,
    1.06,
    factor_text,
    transform=ax.transAxes,
    ha="center",
    va="bottom",
    fontsize=13,
    fontfamily="monospace",
    color="#555555",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "#f5f5f5", "edgecolor": "#cccccc"},
)

# Style
ax.set_title("heatmap-loss-triangle \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=50)
ax.set_xlabel("Development Period (Years)", fontsize=20)
ax.set_ylabel("Accident Year", fontsize=20)
ax.tick_params(axis="both", labelsize=16)
ax.tick_params(axis="x", rotation=0)
ax.tick_params(axis="y", rotation=0)

# Legend for actual vs projected
actual_patch = mpatches.Patch(facecolor="#7ba3c9", edgecolor="black", label="Actual")
projected_patch = mpatches.Patch(facecolor="#7ba3c9", edgecolor="black", hatch="///", label="Projected (IBNR)")
ax.legend(handles=[actual_patch, projected_patch], loc="lower right", fontsize=14, framealpha=0.9, edgecolor="#cccccc")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
