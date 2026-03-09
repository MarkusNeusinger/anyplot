""" pyplots.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-09
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch


# Data
np.random.seed(42)

accident_years = list(range(2015, 2025))
development_periods = list(range(1, 11))
n_years = len(accident_years)
n_periods = len(development_periods)

# Age-to-age development factors (decreasing as claims mature)
dev_factors = [2.50, 1.60, 1.30, 1.15, 1.08, 1.05, 1.03, 1.02, 1.01]

# Generate cumulative paid claims triangle
initial_claims = np.array([4200, 4500, 4800, 5100, 5400, 5700, 6000, 6300, 6600, 7000], dtype=float)

triangle = np.full((n_years, n_periods), np.nan)
is_projected = np.full((n_years, n_periods), True)

# Fill the upper-left actual triangle
for i in range(n_years):
    triangle[i, 0] = initial_claims[i]
    n_actual = n_periods - i
    for j in range(1, n_actual):
        noise = 1 + np.random.uniform(-0.03, 0.03)
        triangle[i, j] = triangle[i, j - 1] * dev_factors[j - 1] * noise
    for j in range(n_actual):
        is_projected[i, j] = False

# Fill the lower-right projected triangle using chain-ladder
for i in range(1, n_years):
    n_actual = n_periods - i
    for j in range(n_actual, n_periods):
        triangle[i, j] = triangle[i, j - 1] * dev_factors[j - 1]

# Prepare masked arrays for actual and projected regions
actual_data = np.ma.masked_where(is_projected | np.isnan(triangle), triangle)
projected_data = np.ma.masked_where(~is_projected | np.isnan(triangle), triangle)

# Shared normalization across both regions
vmin, vmax = np.nanmin(triangle), np.nanmax(triangle)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Use imshow for each region with masked arrays
im_actual = ax.imshow(actual_data, cmap="Blues", vmin=vmin, vmax=vmax, aspect="auto")
im_projected = ax.imshow(projected_data, cmap="Oranges", vmin=vmin, vmax=vmax, aspect="auto")

# Add white cell borders
for i in range(n_years + 1):
    ax.axhline(i - 0.5, color="white", linewidth=1.5)
for j in range(n_periods + 1):
    ax.axvline(j - 0.5, color="white", linewidth=1.5)

# Annotate each cell with formatted value
for i in range(n_years):
    for j in range(n_periods):
        val = triangle[i, j]
        if np.isnan(val):
            continue
        projected = is_projected[i, j]
        cmap = plt.cm.Oranges if projected else plt.cm.Blues
        rgba = cmap((val - vmin) / (vmax - vmin))
        brightness = sum(rgba[:3]) / 3
        text_color = "white" if brightness < 0.55 else "#333333"
        fontstyle = "italic" if projected else "normal"
        ax.text(
            j,
            i,
            f"{val:,.0f}",
            ha="center",
            va="center",
            fontsize=12,
            color=text_color,
            fontstyle=fontstyle,
            fontweight="medium",
        )

# Axes setup
ax.set_xticks(range(n_periods))
ax.set_xticklabels(development_periods, fontsize=16)
ax.set_yticks(range(n_years))
ax.set_yticklabels(accident_years, fontsize=16)
ax.set_xlabel("Development Period (Years)", fontsize=20, labelpad=30)
ax.set_ylabel("Accident Year", fontsize=20)
ax.set_title("heatmap-loss-triangle · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="both", length=0)

# Development factors below the x-axis tick labels
ax.text(-0.5, n_years + 0.1, "Dev Factor:", ha="left", va="top", fontsize=11, color="#555555", fontweight="bold")
for j in range(len(dev_factors)):
    ax.text(
        j + 1,
        n_years + 0.1,
        f"{dev_factors[j]:.2f}",
        ha="center",
        va="top",
        fontsize=11,
        color="#555555",
        fontweight="medium",
    )

# Colorbars — one for each colormap, stacked vertically on the right
cbar_actual = fig.colorbar(im_actual, ax=ax, pad=0.015, shrink=0.42, anchor=(0.0, 1.0))
cbar_actual.set_label("Actual ($)", fontsize=14)
cbar_actual.ax.tick_params(labelsize=12)
cbar_actual.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))

cbar_projected = fig.colorbar(im_projected, ax=ax, pad=0.015, shrink=0.42, anchor=(0.0, 0.0))
cbar_projected.set_label("Projected ($)", fontsize=14)
cbar_projected.ax.tick_params(labelsize=12)
cbar_projected.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))

# Legend
legend_elements = [
    Patch(facecolor=plt.cm.Blues(0.5), edgecolor="white", label="Actual (Observed)"),
    Patch(facecolor=plt.cm.Oranges(0.5), edgecolor="white", label="Projected (Estimated)"),
]
ax.legend(
    handles=legend_elements,
    loc="upper left",
    fontsize=16,
    frameon=True,
    fancybox=True,
    shadow=False,
    edgecolor="#cccccc",
    facecolor="white",
    bbox_to_anchor=(0.0, -0.12),
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
