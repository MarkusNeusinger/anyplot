""" anyplot.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: matplotlib 3.11.0 | Python 3.13.14
Quality: 92/100 | Updated: 2026-06-20
"""

import os

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette positions used in this chart
BRAND = "#009E73"  # position 1 — histogram bars (first categorical series)
BLUE = "#4467A3"  # position 3 — target line
OCHRE = "#BD8233"  # position 4 — mean line
RED = "#AE3030"  # position 5 — spec limits (semantic: reject / bad zone)

# Data — mean shifted from target to demonstrate Cp vs Cpk distinction
np.random.seed(42)
measurements = np.random.normal(loc=10.008, scale=0.014, size=200)
lsl = 9.95
usl = 10.05
target = 10.00

# Capability indices
mean = np.mean(measurements)
sigma = np.std(measurements, ddof=1)
cp = (usl - lsl) / (6 * sigma)
cpk = min((usl - mean) / (3 * sigma), (mean - lsl) / (3 * sigma))

# Plot
title = "histogram-capability · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Histogram — brand green bars with page-background edges
ax.hist(measurements, bins=25, density=True, alpha=0.85, color=BRAND, edgecolor=PAGE_BG, linewidth=0.8, zorder=3)

# Fitted normal curve — theme-adaptive ink color with path effect depth
x_range = np.linspace(lsl - 0.012, usl + 0.012, 400)
y_curve = stats.norm.pdf(x_range, mean, sigma)
ax.plot(
    x_range,
    y_curve,
    color=INK,
    linewidth=2.5,
    zorder=4,
    path_effects=[pe.withStroke(linewidth=4.5, foreground=PAGE_BG, alpha=0.75)],
)

# Rejection regions shaded under curve tails beyond spec limits
ax.fill_between(x_range, y_curve, where=(x_range < lsl), color=RED, alpha=0.20, zorder=2)
ax.fill_between(x_range, y_curve, where=(x_range > usl), color=RED, alpha=0.20, zorder=2)

# Specification limits and reference lines
ax.axvline(lsl, color=RED, linestyle="--", linewidth=2.0, zorder=5, label=f"LSL = {lsl}")
ax.axvline(usl, color=RED, linestyle="--", linewidth=2.0, zorder=5, label=f"USL = {usl}")
ax.axvline(target, color=BLUE, linestyle="-.", linewidth=2.0, zorder=5, label=f"Target = {target:.2f}")
ax.axvline(mean, color=OCHRE, linestyle="-", linewidth=2.0, alpha=0.9, zorder=5, label=f"Mean = {mean:.4f}")

# Capability stats box
verdict = "CAPABLE" if cpk >= 1.0 else "NOT CAPABLE"
verdict_color = BRAND if cpk >= 1.0 else RED
stats_text = f"Cp   = {cp:.2f}\nCpk  = {cpk:.2f}\nσ    = {sigma:.4f}\nn    = {len(measurements)}"
ax.text(
    0.98,
    0.96,
    stats_text,
    transform=ax.transAxes,
    fontsize=8,
    verticalalignment="top",
    horizontalalignment="right",
    fontfamily="monospace",
    color=INK,
    bbox={"boxstyle": "round,pad=0.5", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.93},
    zorder=6,
)
ax.text(
    0.98,
    0.70,
    verdict,
    transform=ax.transAxes,
    fontsize=9,
    fontweight="bold",
    verticalalignment="top",
    horizontalalignment="right",
    fontfamily="monospace",
    color=verdict_color,
    zorder=6,
)

# Style
ax.set_xlabel("Shaft Diameter (mm)", fontsize=10, color=INK, labelpad=6)
ax.set_ylabel("Density", fontsize=10, color=INK, labelpad=6)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=10)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.xaxis.set_major_formatter(ticker.FormatStrFormatter("%.3f"))
ax.yaxis.grid(True, alpha=0.12, linewidth=0.6, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Legend
leg = ax.legend(fontsize=8, loc="upper left", framealpha=0.93)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Trim x-axis to bracket spec limits with a small margin — eliminates empty canvas edges
x_lo = min(lsl - 0.010, mean - 4.5 * sigma)
x_hi = max(usl + 0.010, mean + 4.5 * sigma)
ax.set_xlim(x_lo, x_hi)

# Save — no bbox_inches='tight' (would shave canvas pixels)
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
