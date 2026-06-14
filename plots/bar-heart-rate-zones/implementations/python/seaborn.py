"""anyplot.ai
bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-06-14
"""

import os

import matplotlib.pyplot as plt
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Zone colors — semantic mapping per spec (conventional fitness zone colors)
# Z1 grey   → Imprint muted anchor (theme-adaptive)
# Z2 blue   → Imprint #4467A3
# Z3 green  → Imprint #009E73 (brand green; aerobic / moderate effort)
# Z4 orange → Imprint #BD8233 (ochre, nearest to orange in Imprint palette)
# Z5 red    → Imprint #AE3030 (matte red, semantic anchor for max / critical)
ZONE_COLORS = [INK_MUTED, "#4467A3", "#009E73", "#BD8233", "#AE3030"]

# Data — 60-minute tempo run: most time near threshold (Z4)
zones = ["Z1", "Z2", "Z3", "Z4", "Z5"]
zone_names = ["Recovery", "Endurance", "Aerobic", "Threshold", "Maximum"]
minutes = [5, 10, 18, 20, 7]
hr_ranges = ["< 111 bpm", "111–130 bpm", "130–148 bpm", "148–166 bpm", "> 166 bpm"]

# Multi-line x-tick labels: zone ID / zone name / HR boundary
x_tick_labels = [f"{z}\n{n}\n{h}" for z, n, h in zip(zones, zone_names, hr_ranges, strict=False)]

# Seaborn theme
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

# Plot — landscape 3200 × 1800 px
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

bars = ax.bar(range(len(zones)), minutes, color=ZONE_COLORS, width=0.55, edgecolor=PAGE_BG, linewidth=1.2)

# X-tick labels (zone ID / name / HR boundary)
ax.set_xticks(range(len(zones)))
ax.set_xticklabels(x_tick_labels, fontsize=8)
ax.tick_params(axis="x", which="both", length=0)

# Y-tick labels
ax.tick_params(axis="y", labelsize=8, colors=INK_SOFT)

# Bar duration labels
for bar, mins in zip(bars, minutes, strict=False):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.4,
        f"{mins} min",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color=INK,
    )

# Title and axis labels
title = "bar-heart-rate-zones · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=12)
ax.set_xlabel("Heart Rate Zone", fontsize=10, color=INK, labelpad=10)
ax.set_ylabel("Time (minutes)", fontsize=10, color=INK, labelpad=8)

# Y-axis grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Spines
sns.despine(ax=ax, top=True, right=True)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Y-axis range — headroom for bar labels
ax.set_ylim(0, max(minutes) * 1.3)

# Layout
fig.subplots_adjust(left=0.09, right=0.97, top=0.93, bottom=0.22)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
