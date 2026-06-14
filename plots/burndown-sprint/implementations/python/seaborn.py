"""anyplot.ai
burndown-sprint: Agile Sprint Burndown Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Created: 2026-06-14
"""

import sys


sys.path = sys.path[1:]  # prevent this file from shadowing the seaborn library

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens — see prompts/default-style-guide.md "Theme-adaptive Chrome"
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # actual burndown line — always first series
DANGER = IMPRINT_PALETTE[4]  # scope-change marker — semantic: risk / alert

# Data — 10-working-day sprint, 14 calendar days (Mon–Fri × 2 weeks)
np.random.seed(42)
calendar_days = np.arange(15)  # days 0 through 14

# Actual remaining story points (step series, recorded at end-of-day)
remaining = np.array(
    [
        40,  # Day 0  Mon W1 — sprint start, 40 SP committed
        37,  # Day 1  Tue W1
        34,  # Day 2  Wed W1
        32,  # Day 3  Thu W1
        36,  # Day 4  Fri W1 — scope change: burned 4, added 8 (net +4)
        36,  # Day 5  Sat     — weekend, no progress
        36,  # Day 6  Sun     — weekend, no progress
        31,  # Day 7  Mon W2
        25,  # Day 8  Tue W2
        18,  # Day 9  Wed W2
        10,  # Day 10 Thu W2
        3,  # Day 11 Fri W2 — sprint winds down
        3,  # Day 12 Sat     — weekend
        3,  # Day 13 Sun     — weekend
        0,  # Day 14 Mon     — retro day, all SP delivered
    ]
)

# Ideal burndown: straight line from original scope (40 SP) on day 0 to 0 on day 14
ideal = 40.0 * (1.0 - calendar_days / 14.0)

# X-axis labels: abbreviated day names across both sprint weeks
day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "Mon"]

# DataFrames for seaborn plotting API
df_actual = pd.DataFrame({"day": calendar_days, "remaining": remaining})
df_ideal = pd.DataFrame({"day": calendar_days, "ideal": ideal})

# Seaborn theme — Imprint chrome tokens applied globally
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

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Weekend shading bands (Sat–Sun, weeks 1 and 2)
for sat_day in [5, 12]:
    ax.axvspan(sat_day - 0.5, sat_day + 1.5, color=INK_SOFT, alpha=0.07, zorder=0, linewidth=0)

# Ideal burndown — dashed muted reference line via seaborn lineplot
sns.lineplot(
    data=df_ideal,
    x="day",
    y="ideal",
    ax=ax,
    color=INK_MUTED,
    linewidth=2.0,
    linestyle="--",
    label="Ideal burndown",
    alpha=0.9,
    zorder=2,
)

# Actual remaining — step series via seaborn lineplot with drawstyle (brand green, always first series)
sns.lineplot(
    data=df_actual,
    x="day",
    y="remaining",
    ax=ax,
    color=BRAND,
    linewidth=2.8,
    drawstyle="steps-post",
    label="Actual remaining",
    zorder=4,
)
ax.fill_between(calendar_days, remaining, 0, step="post", color=BRAND, alpha=0.07, zorder=1)

# Scope-change marker at day 4 — vertical dotted line (semantic danger red)
ax.axvline(x=4, color=DANGER, linewidth=1.5, linestyle=":", alpha=0.9, zorder=3)
ax.text(
    4.22,
    41.5,
    "+8 SP\nscope change",
    fontsize=9,
    color=DANGER,
    va="top",
    ha="left",
    fontweight="medium",
    linespacing=1.4,
)

# Style
title = "burndown-sprint · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=12)
ax.set_xlabel("Sprint Day", fontsize=10, color=INK, labelpad=6)
ax.set_ylabel("Remaining Story Points", fontsize=10, color=INK, labelpad=6)
ax.tick_params(axis="both", colors=INK_SOFT)

# X-axis ticks — one per calendar day with abbreviated day name
ax.set_xticks(calendar_days)
ax.set_xticklabels(day_labels, fontsize=8, color=INK_SOFT)
ax.set_xlim(-0.5, 14.5)
ax.set_ylim(-2, 48)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Subtle y-axis grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK, zorder=0)
ax.set_axisbelow(True)

# Legend
legend = ax.legend(fontsize=8, loc="upper right", framealpha=0.9, edgecolor=INK_SOFT, borderpad=0.8)
legend.get_frame().set_facecolor(ELEVATED_BG)
for text in legend.get_texts():
    text.set_color(INK_SOFT)

fig.subplots_adjust(left=0.09, right=0.97, top=0.91, bottom=0.12)

# Save — no bbox_inches='tight' (seaborn canvas rule: figsize × dpi must be exact)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
