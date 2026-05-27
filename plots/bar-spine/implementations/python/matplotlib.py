""" anyplot.ai
bar-spine: Spine Plot for Two-Variable Proportions
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 93/100 | Created: 2026-05-08
"""

import importlib
import os
import sys


# This file is named matplotlib.py, which shadows the actual matplotlib package.
# Strip this directory from sys.path before importing matplotlib so Python finds
# the installed package instead of this script.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here and p != ""]

mpatches = importlib.import_module("matplotlib.patches")
plt = importlib.import_module("matplotlib.pyplot")
np = importlib.import_module("numpy")


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
_OUT = os.path.dirname(os.path.abspath(__file__))
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Titanic survival data by passenger class (classic contingency table)
classes = ["1st Class", "2nd Class", "3rd Class", "Crew"]
survived_counts = np.array([203, 118, 178, 212])
died_counts = np.array([122, 167, 528, 673])
class_totals = survived_counts + died_counts

# Marginal proportions → bar widths (width encodes class size)
grand_total = class_totals.sum()
bar_widths = class_totals / grand_total

# Conditional proportions within each bar (height encodes survival rate)
prop_survived = survived_counts / class_totals
prop_died = died_counts / class_totals

# Left-edge positions for adjacent bars
x_left = np.concatenate([[0], np.cumsum(bar_widths)[:-1]])

# Colors: Okabe-Ito positions 1 and 2
COLOR_SURVIVED = "#009E73"
COLOR_DIED = "#C475FD"

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, (x, w) in enumerate(zip(x_left, bar_widths, strict=True)):
    # Survived segment (bottom)
    ax.bar(x, prop_survived[i], width=w, bottom=0, color=COLOR_SURVIVED, align="edge", linewidth=0)
    # Did-not-survive segment (top)
    ax.bar(x, prop_died[i], width=w, bottom=prop_survived[i], color=COLOR_DIED, align="edge", linewidth=0)

    # Thin page-color separator between bars
    if i > 0:
        ax.axvline(x, color=PAGE_BG, linewidth=2.5, zorder=5)

    # Percentage labels inside each segment (only when segment is tall enough)
    cx = x + w / 2
    if prop_survived[i] > 0.08:
        ax.text(
            cx,
            prop_survived[i] / 2,
            f"{prop_survived[i]:.0%}",
            ha="center",
            va="center",
            fontsize=15,
            color="white",
            fontweight="bold",
            zorder=6,
        )
    if prop_died[i] > 0.08:
        ax.text(
            cx,
            prop_survived[i] + prop_died[i] / 2,
            f"{prop_died[i]:.0%}",
            ha="center",
            va="center",
            fontsize=15,
            color="white",
            fontweight="bold",
            zorder=6,
        )

# X-axis: centered tick labels under variable-width bars
center_positions = x_left + bar_widths / 2
ax.set_xticks(center_positions)
ax.set_xticklabels(classes, fontsize=16, color=INK_SOFT)
ax.tick_params(axis="x", length=0, labelcolor=INK_SOFT)

# Y-axis: percentage scale
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=16, color=INK_SOFT)
ax.tick_params(axis="y", length=0, labelcolor=INK_SOFT)

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

# Annotation: highlight 1st-class survival advantage over crew
cx_1st = x_left[0] + bar_widths[0] / 2
ax.annotate(
    f"1st class: {prop_survived[0]:.0%} survival\nvs. {prop_survived[-1]:.0%} for crew",
    xy=(cx_1st, prop_survived[0]),
    xytext=(0.28, 0.88),
    fontsize=14,
    color=INK_SOFT,
    ha="center",
    va="bottom",
    arrowprops={"arrowstyle": "-|>", "color": INK_SOFT, "lw": 1.5},
    bbox={"facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9, "boxstyle": "round,pad=0.35"},
    zorder=7,
)

# Style
ax.set_xlabel("Passenger Class", fontsize=20, color=INK)
ax.set_ylabel("Proportion of Passengers", fontsize=20, color=INK)
ax.set_title("bar-spine · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Legend
survived_patch = mpatches.Patch(color=COLOR_SURVIVED, label="Survived")
died_patch = mpatches.Patch(color=COLOR_DIED, label="Did Not Survive")
leg = ax.legend(handles=[survived_patch, died_patch], fontsize=16, loc="upper right", framealpha=1.0)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(os.path.join(_OUT, f"plot-{THEME}.png"), dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
