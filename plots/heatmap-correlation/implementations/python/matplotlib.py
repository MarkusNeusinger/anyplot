""" anyplot.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: matplotlib 3.11.1 | Python 3.13.12
Quality: pending | Updated: 2026-08-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
EMPHASIS_POS = "#009E73"  # Imprint palette position 1 — strong positive correlation
EMPHASIS_NEG = "#AE3030"  # Imprint palette position 5 — strong negative correlation

# Data - realistic weather-station correlation matrix
np.random.seed(42)

variables = [
    "Temperature",
    "Humidity",
    "Wind Speed",
    "Precipitation",
    "Air Pressure",
    "Solar Radiation",
    "UV Index",
    "Cloud Cover",
]
n_vars = len(variables)

correlation_matrix = np.eye(n_vars)
correlations = {
    (0, 1): -0.82,  # Temperature - Humidity (strong negative)
    (0, 2): 0.15,  # Temperature - Wind Speed (weak positive)
    (0, 3): -0.48,  # Temperature - Precipitation (negative)
    (0, 4): -0.71,  # Temperature - Air Pressure (strong negative)
    (0, 5): 0.88,  # Temperature - Solar Radiation (strong positive)
    (0, 6): 0.79,  # Temperature - UV Index (strong positive)
    (0, 7): -0.65,  # Temperature - Cloud Cover (negative)
    (1, 2): 0.35,  # Humidity - Wind Speed (weak positive)
    (1, 3): 0.72,  # Humidity - Precipitation (strong positive)
    (1, 4): 0.58,  # Humidity - Air Pressure (positive)
    (1, 5): -0.84,  # Humidity - Solar Radiation (strong negative)
    (1, 6): -0.76,  # Humidity - UV Index (strong negative)
    (1, 7): 0.81,  # Humidity - Cloud Cover (strong positive)
    (2, 3): 0.42,  # Wind Speed - Precipitation (positive)
    (2, 4): -0.31,  # Wind Speed - Air Pressure (weak negative)
    (2, 5): 0.09,  # Wind Speed - Solar Radiation (very weak)
    (2, 6): -0.12,  # Wind Speed - UV Index (very weak negative)
    (2, 7): 0.38,  # Wind Speed - Cloud Cover (weak positive)
    (3, 4): -0.52,  # Precipitation - Air Pressure (negative)
    (3, 5): -0.68,  # Precipitation - Solar Radiation (strong negative)
    (3, 6): -0.61,  # Precipitation - UV Index (strong negative)
    (3, 7): 0.74,  # Precipitation - Cloud Cover (strong positive)
    (4, 5): 0.45,  # Air Pressure - Solar Radiation (positive)
    (4, 6): 0.39,  # Air Pressure - UV Index (positive)
    (4, 7): -0.43,  # Air Pressure - Cloud Cover (negative)
    (5, 6): 0.85,  # Solar Radiation - UV Index (strong positive)
    (5, 7): -0.79,  # Solar Radiation - Cloud Cover (strong negative)
    (6, 7): -0.71,  # UV Index - Cloud Cover (strong negative)
}
for (i, j), corr in correlations.items():
    correlation_matrix[i, j] = corr
    correlation_matrix[j, i] = corr

# Mask the upper triangle so each pair is shown once
mask = np.triu(np.ones_like(correlation_matrix, dtype=bool), k=1)
masked_corr = np.where(mask, np.nan, correlation_matrix)

# Imprint diverging colormap — matte-red (negative) through the theme midpoint to blue (positive)
midpoint = PAGE_BG
imprint_div = LinearSegmentedColormap.from_list("imprint_div", ["#AE3030", midpoint, "#4467A3"])

# Plot — square canvas for this symmetric matrix (see default-style-guide.md "Dimensions")
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG, layout="constrained")
ax.set_facecolor(PAGE_BG)

im = ax.imshow(masked_corr, cmap=imprint_div, vmin=-1, vmax=1, aspect="equal")

# Subtle cell-boundary grid
ax.set_xticks(np.arange(n_vars) - 0.5, minor=True)
ax.set_yticks(np.arange(n_vars) - 0.5, minor=True)
ax.grid(which="minor", color=INK_MUTED, linestyle="-", linewidth=0.6, alpha=0.25)
ax.tick_params(which="minor", bottom=False, left=False)

# Colorbar, fixed to the full correlation range
cbar = ax.figure.colorbar(im, ax=ax, shrink=0.74, pad=0.03)
cbar.ax.set_ylabel("Correlation Coefficient", fontsize=10, labelpad=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
cbar.outline.set_visible(False)

# Ticks and axis labels
ax.set_xticks(np.arange(n_vars))
ax.set_yticks(np.arange(n_vars))
ax.set_xticklabels(variables, fontsize=9, rotation=45, ha="right", rotation_mode="anchor", color=INK_SOFT)
ax.set_yticklabels(variables, fontsize=9, color=INK_SOFT)
ax.tick_params(which="major", bottom=False, left=False)

ax.set_xlabel("Weather Variables", fontsize=10, labelpad=12, color=INK)
ax.set_ylabel("Weather Variables", fontsize=10, labelpad=12, color=INK)

# Emphasis borders on strong correlations — solid for positive, dashed for negative,
# so the sign reads even without checking the colorbar
for i in range(n_vars):
    for j in range(n_vars):
        if not mask[i, j] and i != j and abs(correlation_matrix[i, j]) > 0.75:
            positive = correlation_matrix[i, j] > 0
            rect = Rectangle(
                (j - 0.45, i - 0.45),
                0.9,
                0.9,
                linewidth=1.8,
                edgecolor=EMPHASIS_POS if positive else EMPHASIS_NEG,
                facecolor="none",
                linestyle="-" if positive else "--",
                alpha=0.85,
            )
            ax.add_patch(rect)

# Cell annotations — text color follows the actual cell luminance so it stays
# legible against both saturated correlation colors and the near-neutral midpoint
for i in range(n_vars):
    for j in range(n_vars):
        if not mask[i, j]:
            value = correlation_matrix[i, j]
            r, g, b, _ = imprint_div((value + 1) / 2)
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            text_color = "white" if luminance < 0.55 else INK_SOFT
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", color=text_color, fontsize=9, fontweight="bold")

# Title on the full figure (not just the heatmap axes) so it stays centered over
# the colorbar too — the square canvas is narrower than the landscape default,
# so the mandated title needs a smaller fontsize than the 12pt landscape baseline
# to stay clear of the colorbar's top tick label.
fig.suptitle(
    "heatmap-correlation · python · matplotlib · anyplot.ai", fontsize=11, y=0.97, fontweight="medium", color=INK
)

for spine in ax.spines.values():
    spine.set_visible(False)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
