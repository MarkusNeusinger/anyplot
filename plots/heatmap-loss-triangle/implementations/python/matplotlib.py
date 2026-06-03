"""anyplot.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-06-03
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch, Rectangle


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint sequential colormap — single-polarity cumulative claim amounts
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

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

# Fill upper-left actual triangle
for i in range(n_years):
    triangle[i, 0] = initial_claims[i]
    n_actual = n_periods - i
    for j in range(1, n_actual):
        noise = 1 + np.random.uniform(-0.03, 0.03)
        triangle[i, j] = triangle[i, j - 1] * dev_factors[j - 1] * noise
    for j in range(n_actual):
        is_projected[i, j] = False

# Fill lower-right projected triangle using chain-ladder
for i in range(1, n_years):
    n_actual = n_periods - i
    for j in range(n_actual, n_periods):
        triangle[i, j] = triangle[i, j - 1] * dev_factors[j - 1]

vmin, vmax = np.nanmin(triangle), np.nanmax(triangle)

# Plot — square canvas for symmetric heatmap grid (2400×2400 px)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Heatmap with Imprint sequential colormap
im = ax.imshow(triangle, cmap=imprint_seq, vmin=vmin, vmax=vmax, aspect="auto")

# Colorbar — create before twin axis so layout is established correctly
cbar = fig.colorbar(im, ax=ax, pad=0.02, shrink=0.80)
cbar.set_label("Cumulative Claims ($)", fontsize=8, color=INK)
cbar.ax.tick_params(labelsize=7, colors=INK_SOFT)
cbar.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
cbar.outline.set_edgecolor(INK_SOFT)
plt.setp(plt.getp(cbar.ax, "yticklabels"), color=INK_SOFT)

# Hatching overlay on projected cells
for i in range(n_years):
    for j in range(n_periods):
        if is_projected[i, j] and not np.isnan(triangle[i, j]):
            rect = Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, hatch="///", edgecolor=PAGE_BG, linewidth=0)
            ax.add_patch(rect)

# Cell borders
for i in range(n_years + 1):
    ax.axhline(i - 0.5, color=PAGE_BG, linewidth=1.0)
for j in range(n_periods + 1):
    ax.axvline(j - 0.5, color=PAGE_BG, linewidth=1.0)

# Cell annotations with brightness-adaptive text color
for i in range(n_years):
    for j in range(n_periods):
        val = triangle[i, j]
        if np.isnan(val):
            continue
        norm_val = (val - vmin) / (vmax - vmin)
        rgba = imprint_seq(norm_val)
        brightness = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
        text_color = PAGE_BG if brightness < 0.5 else INK
        fontstyle = "italic" if is_projected[i, j] else "normal"
        ax.text(
            j,
            i,
            f"{val:,.0f}",
            ha="center",
            va="center",
            fontsize=7,
            color=text_color,
            fontstyle=fontstyle,
            fontweight="medium",
        )

# Axes styling
title = "heatmap-loss-triangle · python · matplotlib · anyplot.ai"
n_chars = len(title)
ratio = 67 / n_chars if n_chars > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))

ax.set_xticks(range(n_periods))
ax.set_xticklabels(development_periods, fontsize=8, color=INK_SOFT)
ax.set_yticks(range(n_years))
ax.set_yticklabels(accident_years, fontsize=8, color=INK_SOFT)
ax.set_xlabel("Development Period (Years)", fontsize=10, color=INK, labelpad=8)
ax.set_ylabel("Accident Year", fontsize=10, color=INK, labelpad=6)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=30)
ax.tick_params(axis="both", length=0, colors=INK_SOFT)

for spine in ax.spines.values():
    spine.set_visible(False)

# Development factors on a twin x-axis at the top (after colorbar to avoid layout conflict)
ax_top = ax.twiny()
ax_top.set_xlim(ax.get_xlim())
ax_top.set_xticks([j + 1 for j in range(len(dev_factors))])
ax_top.set_xticklabels([f"{f:.2f}" for f in dev_factors], fontsize=7, color=INK_MUTED)
ax_top.set_xlabel("Age-to-Age Dev. Factors (LDF)", fontsize=8, color=INK_MUTED, labelpad=6)
ax_top.tick_params(length=0, colors=INK_MUTED, labelcolor=INK_MUTED)
for spine in ax_top.spines.values():
    spine.set_visible(False)

# Legend below the heatmap
legend_elements = [
    Patch(facecolor=imprint_seq(0.55), edgecolor=PAGE_BG, label="Actual (Observed)"),
    Patch(facecolor=imprint_seq(0.55), edgecolor=PAGE_BG, hatch="///", label="Projected (IBNR)"),
]
leg = ax.legend(
    handles=legend_elements,
    loc="upper left",
    fontsize=7,
    frameon=True,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    bbox_to_anchor=(0.0, -0.10),
    bbox_transform=ax.transAxes,
)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.10, bottom=0.14, top=0.90)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
