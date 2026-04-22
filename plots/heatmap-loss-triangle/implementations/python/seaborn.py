""" pyplots.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-09
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
    cumulative[i, 0] = base_claims[i] + np.random.normal(0, 200)
    for j in range(1, n_periods):
        factor = dev_factors[j - 1] + np.random.normal(0, 0.02)
        cumulative[i, j] = cumulative[i, j - 1] * factor
    actual_periods = n_years - i
    for j in range(actual_periods, n_periods):
        is_projected[i, j] = True

# Create DataFrames for heatmap
heatmap_data = pd.DataFrame(
    cumulative, index=[str(y) for y in accident_years], columns=[str(p) for p in development_periods]
)

# Build annotation string array for seaborn's annot parameter
annot_labels = np.empty_like(cumulative, dtype=object)
for i in range(n_years):
    for j in range(n_periods):
        val = cumulative[i, j]
        annot_labels[i, j] = f"{val / 1000:.0f}K" if val >= 10000 else f"{val:,.0f}"
annot_df = pd.DataFrame(annot_labels, index=heatmap_data.index, columns=heatmap_data.columns)

# Masks for seaborn's mask parameter — distinguishes actual vs projected regions
mask_projected = pd.DataFrame(is_projected, index=heatmap_data.index, columns=heatmap_data.columns)
mask_actual = ~mask_projected

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Custom colormap
cmap = LinearSegmentedColormap.from_list("loss_triangle", ["#e8f0fe", "#306998", "#1a3a5c"], N=256)
vmin, vmax = np.nanmin(cumulative), np.nanmax(cumulative)

# Draw actual cells using seaborn's annot and mask features
sns.heatmap(
    heatmap_data,
    ax=ax,
    cmap=cmap,
    vmin=vmin,
    vmax=vmax,
    mask=mask_projected,
    annot=annot_df,
    fmt="",
    annot_kws={"fontsize": 13, "fontweight": "bold"},
    linewidths=1.5,
    linecolor="white",
    cbar_kws={"label": "Cumulative Claims ($K)", "shrink": 0.8},
)

# Draw projected cells as overlay with distinct annotation style
sns.heatmap(
    heatmap_data,
    ax=ax,
    cmap=cmap,
    vmin=vmin,
    vmax=vmax,
    mask=mask_actual,
    annot=annot_df,
    fmt="",
    annot_kws={"fontsize": 13, "fontweight": "normal", "fontstyle": "italic"},
    linewidths=1.5,
    linecolor="white",
    cbar=False,
)

# Fix annotation text colors based on background brightness
for text in ax.texts:
    x, y = text.get_position()
    col, row = int(x), int(y)
    if 0 <= row < n_years and 0 <= col < n_periods:
        val = cumulative[row, col]
        norm_val = (val - vmin) / (vmax - vmin)
        text.set_color("white" if norm_val > 0.55 else "#1a1a1a")

# Add hatching overlay for projected cells
for i in range(n_years):
    for j in range(n_periods):
        if is_projected[i, j]:
            ax.add_patch(mpatches.Rectangle((j, i), 1, 1, facecolor="white", edgecolor="none", alpha=0.25))
            ax.add_patch(
                mpatches.Rectangle((j, i), 1, 1, facecolor="none", edgecolor="#666666", hatch="////", linewidth=0)
            )

# Customize colorbar
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=13)
cbar.set_label("Cumulative Claims ($K)", fontsize=15)

# Development factors display
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
ax.set_title("heatmap-loss-triangle · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=50)
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
