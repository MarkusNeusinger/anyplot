""" anyplot.ai
curve-power-duration: Mean-Maximal Power Duration Curve
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Created: 2026-06-13
"""

import os
import sys


# Remove the script's directory from sys.path so 'import seaborn' resolves
# to the installed package rather than this file.
if sys.path and sys.path[0] in ("", os.path.dirname(os.path.abspath(__file__))):
    sys.path.pop(0)

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — canonical order, first series always #009E73
BRAND = "#009E73"  # empirical MMP curve — first series
MODEL_COLOR = "#4467A3"  # CP model fit — third Imprint position

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

# Data — well-trained cyclist: CP ≈ 280 W, W′ ≈ 21 kJ
np.random.seed(42)
CP = 280  # critical power (W) — aerobic asymptote
W_PRIME = 21000  # anaerobic work capacity (J)
NM_CAP = 1100  # neuromuscular peak power cap (W) at very short efforts

# Empirical MMP: CP model with neuromuscular cap + realistic scatter
emp_durations = np.logspace(0, np.log10(18000), 50)
emp_base = np.minimum(CP + W_PRIME / emp_durations, NM_CAP)
emp_power = emp_base + np.random.normal(0, 9, size=len(emp_durations))
for i in range(1, len(emp_power)):
    if emp_power[i] > emp_power[i - 1]:
        emp_power[i] = emp_power[i - 1]

# CP model line: smooth curve from 30 s to 5 h (valid fitting range)
mod_durations = np.logspace(np.log10(30), np.log10(18000), 250)
mod_power = CP + W_PRIME / mod_durations

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Empirical MMP curve (primary series — Imprint brand green)
sns.lineplot(
    x=emp_durations, y=emp_power, ax=ax, errorbar=None, color=BRAND, linewidth=2.5, label="Mean-maximal power (MMP)"
)

# CP model overlay — dashed, Imprint blue
ax.plot(
    mod_durations,
    mod_power,
    color=MODEL_COLOR,
    linewidth=1.8,
    linestyle="--",
    label=f"CP model  (CP = {CP} W, W′ = {W_PRIME // 1000} kJ)",
    zorder=3,
)

# CP asymptote reference line
ax.axhline(CP, color=INK_MUTED, linewidth=1.0, linestyle=":", alpha=0.75, zorder=2)
ax.text(16500, CP + 8, f"CP = {CP} W", color=INK_MUTED, fontsize=7.5, ha="right", va="bottom")

# Reference duration markers (spec: 5 s, 1 min, 5 min, 20 min)
ref_markers = {5: "5 s sprint", 60: "1 min", 300: "5 min", 1200: "20 min"}
for t, label in ref_markers.items():
    ax.axvline(t, color=INK_SOFT, linewidth=0.9, linestyle="--", alpha=0.5, zorder=1)
    ax.text(t, 1210, label, color=INK_SOFT, fontsize=7, ha="center", va="bottom")

# X-axis — log scale with human-readable duration labels
ax.set_xscale("log")
xtick_pos = [1, 5, 30, 60, 300, 1200, 3600, 18000]
xtick_lbl = ["1 s", "5 s", "30 s", "1 min", "5 min", "20 min", "1 h", "5 h"]
ax.set_xticks(xtick_pos)
ax.set_xticklabels(xtick_lbl)
ax.xaxis.set_minor_locator(ticker.NullLocator())
ax.set_xlim(0.8, 22000)
ax.set_ylim(220, 1300)

# Style
title = "curve-power-duration · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=12)
ax.set_xlabel("Duration", fontsize=10, color=INK)
ax.set_ylabel("Power (W)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Legend — lower left keeps it clear of the reference-duration labels at the top
legend = ax.legend(fontsize=8, loc="lower left", facecolor=ELEVATED_BG, edgecolor=INK_SOFT, framealpha=0.9)
for text in legend.get_texts():
    text.set_color(INK)

fig.subplots_adjust(left=0.10, right=0.97, top=0.92, bottom=0.14)

# Save — bbox_inches must stay default (None) per seaborn canvas rule
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
