""" anyplot.ai
bar-error: Bar Chart with Error Bars
Library: matplotlib 3.11.2 | Python 3.13.15
Quality: 93/100 | Updated: 2026-09-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint palette position 1

# Data: A/B test results comparing feature variants with confidence intervals
np.random.seed(42)
categories = ["Control", "Variant A", "Variant B", "Variant C", "Variant D"]
values = [12.3, 15.8, 14.2, 18.5, 11.7]
errors = [1.2, 2.1, 1.5, 2.8, 1.0]

control_value = values[0]
winner = int(np.argmax(values))
lift_pct = round((values[winner] - control_value) / control_value * 100)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

x = np.arange(len(categories))
bar_width = 0.6

bars = ax.bar(x, values, bar_width, color=BRAND, edgecolor=INK_SOFT, linewidth=1.2, zorder=2)
# Focal point: the winning variant gets a bolder outline, everything else stays even-weighted
bars[winner].set_edgecolor(INK)
bars[winner].set_linewidth(2.2)

ax.errorbar(x, values, yerr=errors, fmt="none", ecolor=INK_SOFT, elinewidth=2.2, capsize=7, capthick=1.8, zorder=3)

# Control baseline reference — lets every variant be read as a lift over Control
ax.axhline(control_value, color=INK_MUTED, linestyle="--", linewidth=1, alpha=0.6, zorder=1)

# Value labels above each error cap
for xi, value, error in zip(x, values, errors, strict=True):
    ax.text(xi, value + error + 0.5, f"{value:.1f}%", ha="center", va="bottom", fontsize=9, color=INK_SOFT)

# Labels and styling
ax.set_xlabel("Test Group", fontsize=10, color=INK)
ax.set_ylabel("Conversion Rate (%)", fontsize=10, color=INK)
ax.set_title("bar-error · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=8, color=INK_SOFT)
ax.tick_params(axis="y", labelsize=8, colors=INK_SOFT)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK, zorder=0)

# Annotation: ties the focal point to the story the error bars tell
ax.annotate(
    f"{categories[winner]}: +{lift_pct}% vs Control baseline\n(error bars: 95% CI)",
    xy=(winner, values[winner] + errors[winner]),
    xytext=(winner - 1.4, values[winner] + errors[winner] + 3.5),
    fontsize=9,
    ha="left",
    va="bottom",
    color=INK_SOFT,
    arrowprops={"arrowstyle": "-", "color": INK_SOFT, "linewidth": 1},
    bbox={"boxstyle": "round,pad=0.5", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9, "linewidth": 1},
)

ax.set_ylim(0, max(v + e for v, e in zip(values, errors, strict=True)) * 1.5)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
