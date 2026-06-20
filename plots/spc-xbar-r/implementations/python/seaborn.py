""" anyplot.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 86/100 | Updated: 2026-06-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens — Imprint palette + adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Imprint pos 1 — primary data series
BLUE = "#4467A3"  # Imprint pos 3 — center line
OOC_COLOR = "#AE3030"  # Imprint semantic red — out-of-control / error
WARN_COLOR = "#DDCC77"  # Imprint semantic amber — warning / caution limits

# Seaborn theme with Imprint chrome tokens
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
        "grid.alpha": 0.12,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data — injection molding thickness measurements (target: 3.200 mm)
np.random.seed(7)

n_samples = 30
subgroup_size = 5
target = 3.200
process_std = 0.008

# SPC constants for subgroup size 5
A2, D3, D4 = 0.577, 0.0, 2.114

measurements = np.random.normal(target, process_std, (n_samples, subgroup_size))

# OOC signals at samples 9/17/26 — down/up/down pattern (different from sibling impls)
measurements[8] -= 0.030  # sample 9: below LCL
measurements[16] += 0.027  # sample 17: above UCL
measurements[25] -= 0.028  # sample 26: below LCL

sample_means = measurements.mean(axis=1)
sample_ranges = measurements.max(axis=1) - measurements.min(axis=1)

# Control limits — X-bar chart
xbar_bar = sample_means.mean()
r_bar = sample_ranges.mean()
xbar_ucl = xbar_bar + A2 * r_bar
xbar_lcl = xbar_bar - A2 * r_bar
xbar_upper_warn = xbar_bar + (2 / 3) * A2 * r_bar
xbar_lower_warn = xbar_bar - (2 / 3) * A2 * r_bar

# Control limits — R chart
r_ucl = D4 * r_bar
r_lcl = D3 * r_bar
r_upper_warn = r_bar + (2 / 3) * (r_ucl - r_bar)
r_lower_warn = max(0.0, r_bar - (2 / 3) * (r_bar - r_lcl))

sample_ids = np.arange(1, n_samples + 1)

xbar_ooc = (sample_means > xbar_ucl) | (sample_means < xbar_lcl)
r_ooc = (sample_ranges > r_ucl) | (sample_ranges < r_lcl)

# Plot — 3200×1800 px canvas (figsize=(8,4.5), dpi=400 — no bbox_inches="tight")
fig, (ax1, ax2) = plt.subplots(
    2,
    1,
    figsize=(8, 4.5),
    dpi=400,
    sharex=True,
    gridspec_kw={"height_ratios": [1, 1], "hspace": 0.1},
    facecolor=PAGE_BG,
)
ax1.set_facecolor(PAGE_BG)
ax2.set_facecolor(PAGE_BG)

# X-bar chart
sns.lineplot(x=sample_ids, y=sample_means, ax=ax1, color=BRAND, linewidth=2.5, marker="o", markersize=5, zorder=3)
ax1.scatter(
    sample_ids[xbar_ooc],
    sample_means[xbar_ooc],
    color=OOC_COLOR,
    s=120,
    zorder=5,
    edgecolors=PAGE_BG,
    linewidth=1.5,
    marker="D",
)
ax1.fill_between(sample_ids, xbar_lower_warn, xbar_upper_warn, alpha=0.07, color=BRAND, zorder=1)
ax1.axhline(xbar_bar, color=BLUE, linewidth=2, label=f"CL = {xbar_bar:.4f}")
ax1.axhline(xbar_ucl, color=OOC_COLOR, linewidth=1.5, linestyle="--", label=f"UCL = {xbar_ucl:.4f}")
ax1.axhline(xbar_lcl, color=OOC_COLOR, linewidth=1.5, linestyle="--", label=f"LCL = {xbar_lcl:.4f}")
ax1.axhline(xbar_upper_warn, color=WARN_COLOR, linewidth=1, linestyle=":", label=f"+2σ = {xbar_upper_warn:.4f}")
ax1.axhline(xbar_lower_warn, color=WARN_COLOR, linewidth=1, linestyle=":", label=f"−2σ = {xbar_lower_warn:.4f}")
ax1.set_ylabel("Sample Mean (mm)", fontsize=10, color=INK)
ax1.legend(fontsize=8, loc="upper right", framealpha=0.9)
ax1.tick_params(axis="both", labelsize=8)
ax1.text(0.01, 0.95, "X̄ Chart", transform=ax1.transAxes, fontsize=10, fontweight="bold", va="top", color=INK)
ax1.yaxis.grid(True, alpha=0.12, linewidth=0.8)

# R chart
sns.lineplot(x=sample_ids, y=sample_ranges, ax=ax2, color=BRAND, linewidth=2.5, marker="s", markersize=5, zorder=3)
ax2.scatter(
    sample_ids[r_ooc],
    sample_ranges[r_ooc],
    color=OOC_COLOR,
    s=120,
    zorder=5,
    edgecolors=PAGE_BG,
    linewidth=1.5,
    marker="D",
)
ax2.fill_between(sample_ids, r_lower_warn, r_upper_warn, alpha=0.07, color=BRAND, zorder=1)
ax2.axhline(r_bar, color=BLUE, linewidth=2, label=f"CL = {r_bar:.4f}")
ax2.axhline(r_ucl, color=OOC_COLOR, linewidth=1.5, linestyle="--", label=f"UCL = {r_ucl:.4f}")
ax2.axhline(r_lcl, color=OOC_COLOR, linewidth=1.5, linestyle="--", label=f"LCL = {r_lcl:.4f}")
ax2.axhline(r_upper_warn, color=WARN_COLOR, linewidth=1, linestyle=":", label=f"+2σ = {r_upper_warn:.4f}")
ax2.axhline(r_lower_warn, color=WARN_COLOR, linewidth=1, linestyle=":", label=f"−2σ = {r_lower_warn:.4f}")
ax2.set_xlabel("Sample Number", fontsize=10, color=INK)
ax2.set_ylabel("Sample Range (mm)", fontsize=10, color=INK)
ax2.legend(fontsize=8, loc="upper right", framealpha=0.9)
ax2.tick_params(axis="both", labelsize=8)
ax2.text(0.01, 0.95, "R Chart", transform=ax2.transAxes, fontsize=10, fontweight="bold", va="top", color=INK)
ax2.yaxis.grid(True, alpha=0.12, linewidth=0.8)

# Title and spine cleanup via seaborn
title = "spc-xbar-r · python · seaborn · anyplot.ai"
ax1.set_title(title, fontsize=12, fontweight="medium", pad=10, color=INK)
sns.despine(fig=fig, top=True, right=True)
plt.tight_layout()

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
