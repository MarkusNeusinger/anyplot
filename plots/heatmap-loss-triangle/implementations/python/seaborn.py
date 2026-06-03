"""anyplot.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Updated: 2026-06-03
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Imprint sequential colormap for continuous heatmap data (single-polarity)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

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

heatmap_data = pd.DataFrame(
    cumulative, index=[str(y) for y in accident_years], columns=[str(p) for p in development_periods]
)

# Annotation strings
annot_labels = np.empty_like(cumulative, dtype=object)
for i in range(n_years):
    for j in range(n_periods):
        val = cumulative[i, j]
        annot_labels[i, j] = f"{val:,.0f}"
annot_df = pd.DataFrame(annot_labels, index=heatmap_data.index, columns=heatmap_data.columns)

# Masks for actual vs projected regions
mask_projected = pd.DataFrame(is_projected, index=heatmap_data.index, columns=heatmap_data.columns)
mask_actual = ~mask_projected

# Plot — square canvas for symmetric heatmap (2400 × 2400 px)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400)

vmin, vmax = np.nanmin(cumulative), np.nanmax(cumulative)

# Draw actual cells (bold annotations)
sns.heatmap(
    heatmap_data,
    ax=ax,
    cmap=imprint_seq,
    vmin=vmin,
    vmax=vmax,
    mask=mask_projected,
    annot=annot_df,
    fmt="",
    annot_kws={"fontsize": 8, "fontweight": "bold"},
    linewidths=1.0,
    linecolor=PAGE_BG,
    cbar_kws={"label": "Cumulative Claims ($K)", "shrink": 0.8},
)

# Draw projected cells (italic annotations, no extra colorbar)
sns.heatmap(
    heatmap_data,
    ax=ax,
    cmap=imprint_seq,
    vmin=vmin,
    vmax=vmax,
    mask=mask_actual,
    annot=annot_df,
    fmt="",
    annot_kws={"fontsize": 8, "fontweight": "normal", "fontstyle": "italic"},
    linewidths=1.0,
    linecolor=PAGE_BG,
    cbar=False,
)

# Adaptive annotation text colors based on cell brightness in the colormap
for text in ax.texts:
    x, y = text.get_position()
    col, row = int(x), int(y)
    if 0 <= row < n_years and 0 <= col < n_periods:
        val = cumulative[row, col]
        norm_val = (val - vmin) / (vmax - vmin)
        text.set_color("white" if norm_val > 0.55 else INK)

# Hatching overlay for projected cells
for i in range(n_years):
    for j in range(n_periods):
        if is_projected[i, j]:
            ax.add_patch(mpatches.Rectangle((j, i), 1, 1, facecolor=PAGE_BG, edgecolor="none", alpha=0.2))
            ax.add_patch(
                mpatches.Rectangle((j, i), 1, 1, facecolor="none", edgecolor=INK_SOFT, hatch="////", linewidth=0)
            )

# Diagonal step-line marking the latest evaluation boundary (actual vs projected)
diag_x = [n_periods, n_periods]
diag_y = [0, 1]
for i in range(1, n_years):
    actual_periods = n_years - i
    diag_x.extend([actual_periods, actual_periods])
    diag_y.extend([i, i + 1])
ax.plot(diag_x, diag_y, color=INK, linewidth=2.5, linestyle="-", zorder=5, solid_capstyle="butt")

# Colorbar styling
cbar = ax.collections[0].colorbar
if cbar is not None:
    cbar.ax.tick_params(labelsize=8, labelcolor=INK_SOFT)
    cbar.set_label("Cumulative Claims ($K)", fontsize=10, color=INK)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=INK_SOFT)

# Development factors text — placed above the heatmap
factor_text = "Dev Factors: " + "  ".join([f"{f:.3f}" for f in dev_factors])
ax.text(
    0.5,
    1.05,
    factor_text,
    transform=ax.transAxes,
    ha="center",
    va="bottom",
    fontsize=7,
    fontfamily="monospace",
    color=INK_MUTED,
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "linewidth": 0.5},
)

# Style
title = "heatmap-loss-triangle · python · seaborn · anyplot.ai"
n_chars = len(title)
ratio = 67 / n_chars if n_chars > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=40)
ax.set_xlabel("Development Period (Years)", fontsize=10, color=INK)
ax.set_ylabel("Accident Year", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8)
ax.tick_params(axis="x", rotation=0)
ax.tick_params(axis="y", rotation=0)

# Legend for actual vs projected regions
actual_patch = mpatches.Patch(facecolor="#009E73", edgecolor=INK_SOFT, label="Actual")
projected_patch = mpatches.Patch(facecolor="#4467A3", edgecolor=INK_SOFT, hatch="///", label="Projected (IBNR)")
ax.legend(
    handles=[actual_patch, projected_patch],
    loc="upper center",
    bbox_to_anchor=(0.5, -0.12),
    fontsize=8,
    framealpha=0.9,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    labelcolor=INK,
    ncol=2,
)

# Save — no bbox_inches='tight'; figsize×dpi fixes the canvas at 2400×2400
plt.tight_layout(rect=[0, 0.08, 1, 1])
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
