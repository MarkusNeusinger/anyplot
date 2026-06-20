"""anyplot.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: seaborn | Python 3.14
Quality: pending | Updated: 2026-06-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.lines import Line2D
from scipy.stats import norm


# Theme tokens — Imprint palette
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Imprint position 1 — histogram bars
BLUE = "#4467A3"  # Imprint position 3 — fitted normal curve
RED = "#AE3030"  # Imprint position 5 — semantic: spec limits / out-of-spec
AMBER = "#DDCC77"  # Imprint semantic anchor — target / caution

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

# Data — pharmaceutical tablet weight QC (target 500 mg, n=200)
np.random.seed(42)
weights = np.random.normal(loc=500.2, scale=2.8, size=200)
lsl = 490.0
usl = 510.0
target = 500.0

mean = np.mean(weights)
sigma = np.std(weights, ddof=1)
cp = (usl - lsl) / (6 * sigma)
cpk = min((usl - mean) / (3 * sigma), (mean - lsl) / (3 * sigma))

# Fitted normal distribution curve (scipy — not KDE)
x_fit = np.linspace(lsl - 4, usl + 4, 400)
y_fit = norm.pdf(x_fit, mean, sigma)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
ax.set_facecolor(PAGE_BG)

# Histogram bars
sns.histplot(weights, bins=25, stat="density", color=BRAND, edgecolor=PAGE_BG, linewidth=0.6, alpha=0.70, ax=ax)

# Fitted normal distribution
ax.plot(x_fit, y_fit, color=BLUE, linewidth=2.5, zorder=5)

# Specification limit and target lines
ax.axvline(lsl, color=RED, linestyle="--", linewidth=2.0, zorder=4)
ax.axvline(usl, color=RED, linestyle="--", linewidth=2.0, zorder=4)
ax.axvline(target, color=AMBER, linestyle="-.", linewidth=2.0, zorder=4)

# Shaded capability zones
xlim = ax.get_xlim()
ax.axvspan(lsl, usl, alpha=0.05, color=BRAND, zorder=0)
ax.axvspan(xlim[0], lsl, alpha=0.07, color=RED, zorder=0)
ax.axvspan(usl, xlim[1], alpha=0.07, color=RED, zorder=0)

# Capability status color
cp_color = BRAND if cpk >= 1.33 else AMBER if cpk >= 1.0 else RED

# Metrics annotation box
annotation_text = f"Cp  = {cp:.2f}\nCpk = {cpk:.2f}\nμ   = {mean:.2f} mg\nσ   = {sigma:.2f} mg"
ax.text(
    0.975,
    0.96,
    annotation_text,
    transform=ax.transAxes,
    fontsize=8,
    verticalalignment="top",
    horizontalalignment="right",
    family="monospace",
    bbox={
        "boxstyle": "round,pad=0.4",
        "facecolor": ELEVATED_BG,
        "edgecolor": cp_color,
        "linewidth": 1.5,
        "alpha": 0.95,
    },
    color=INK,
)

# Capability status label
status = "Capable" if cpk >= 1.33 else "Adequate" if cpk >= 1.0 else "Not Capable"
ax.text(
    0.975,
    0.70,
    status,
    transform=ax.transAxes,
    fontsize=8,
    fontweight="bold",
    verticalalignment="top",
    horizontalalignment="right",
    color=cp_color,
)

# Style
title = "histogram-capability · python · seaborn · anyplot.ai"
ax.set_xlabel("Tablet Weight (mg)", fontsize=10, color=INK)
ax.set_ylabel("Density", fontsize=10, color=INK)
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK)

# Legend
legend_handles = [
    Line2D([0], [0], color=BLUE, linewidth=2.5, label="Normal Fit"),
    Line2D([0], [0], color=RED, linestyle="--", linewidth=2.0, label=f"LSL = {lsl:.0f} mg"),
    Line2D([0], [0], color=RED, linestyle="--", linewidth=2.0, label=f"USL = {usl:.0f} mg"),
    Line2D([0], [0], color=AMBER, linestyle="-.", linewidth=2.0, label=f"Target = {target:.0f} mg"),
]
ax.legend(handles=legend_handles, fontsize=8, loc="upper left", frameon=True, framealpha=0.95)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
