"""anyplot.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-28
"""

import os

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# imprint_div (marks): Imprint red -> theme grey midpoint -> Imprint blue; ordered Likert levels take its steps
DIV_MARKS = [(0.0, "#AE3030"), (0.5, "#6B6A63" if THEME == "light" else "#686762"), (1.0, "#4467A3")]
imprint_div = LinearSegmentedColormap.from_list("imprint_div", DIV_MARKS)

# Columns: set these to your table's column names
QUESTION = "Question"  # role: question
STRONGLY_DISAGREE = "Strongly disagree"  # role: strongly_disagree
DISAGREE = "Disagree"  # role: disagree
NEUTRAL = "Neutral"  # role: neutral
AGREE = "Agree"  # role: agree
STRONGLY_AGREE = "Strongly agree"  # role: strongly_agree

# Constants
LEVELS = [STRONGLY_DISAGREE, DISAGREE, NEUTRAL, AGREE, STRONGLY_AGREE]  # the Likert scale, in order
MIN_LABEL_SHARE = 7  # a segment gets a percentage label from this many percent

# Data: replace this block with your own table, for example df = pd.read_csv("survey.csv")
df = pd.DataFrame(
    {
        QUESTION: [
            "I feel valued at work",
            "Communication is transparent",
            "Leadership inspires confidence",
            "Work-life balance is respected",
            "Career growth opportunities exist",
            "Team collaboration is effective",
            "Resources are adequate",
            "Feedback is constructive",
            "Company culture is positive",
            "Compensation is fair",
        ],
        STRONGLY_DISAGREE: [4, 8, 18, 6, 12, 3, 2, 7, 5, 15],
        DISAGREE: [10, 15, 25, 12, 20, 8, 6, 14, 11, 22],
        NEUTRAL: [16, 20, 18, 18, 22, 14, 12, 20, 15, 20],
        AGREE: [42, 35, 24, 38, 28, 45, 48, 36, 40, 28],
        STRONGLY_AGREE: [28, 22, 15, 26, 18, 30, 32, 23, 29, 15],
    }
)

# Plot: reads only df and the constants above
n_levels = len(LEVELS)
mid = n_levels // 2
level_colors = [imprint_div(v) for v in np.linspace(0, 1, n_levels)]
pole_neg, pole_pos = level_colors[0], level_colors[-1]

# Net agreement, rows sorted ascending so the most agreed question sits at the top
net = df[LEVELS[mid + 1 :]].sum(axis=1) - df[LEVELS[:mid]].sum(axis=1)
df = df.assign(net=net).sort_values("net", kind="stable").reset_index(drop=True)

# Diverging layout: the middle level is split evenly across zero
half_mid = df[LEVELS[mid]] / 2
starts = {}
for k, level in enumerate(LEVELS):
    if k < mid:
        starts[level] = -(df[LEVELS[k : mid + 1]].sum(axis=1) - half_mid)
    elif k == mid:
        starts[level] = -half_mid
    else:
        starts[level] = half_mid + df[LEVELS[mid + 1 : k]].sum(axis=1)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
y_pos = np.arange(len(df))

for color, level in zip(level_colors, LEVELS, strict=True):
    ax.barh(
        y_pos,
        df[level],
        left=starts[level],
        height=0.7,
        color=color,
        edgecolor=PAGE_BG,
        linewidth=0.8,
        label=level,
        zorder=2,
    )
    for i, (width, start) in enumerate(zip(df[level], starts[level], strict=True)):
        if width >= MIN_LABEL_SHARE:
            ax.text(
                start + width / 2,
                i,
                f"{width:.0f}%",
                ha="center",
                va="center",
                fontsize=7,
                fontweight="bold",
                color="white",
                zorder=4,
            )

# Center line
ax.axvline(x=0, color=INK_SOFT, linewidth=1.2, zorder=3)

# X-axis grid
ax.xaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK, zorder=0)
ax.set_axisbelow(True)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:+.0f}%" if x != 0 else "0%"))
ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins=8, steps=[1, 2, 5, 10]))

# Style
title = "bar-diverging-likert · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_yticks(y_pos)
ax.set_yticklabels(df[QUESTION], fontsize=9, color=INK_SOFT)
ax.set_xlabel("Percentage of responses", fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=12)
ax.tick_params(axis="x", labelsize=8, colors=INK_SOFT)
ax.tick_params(axis="y", length=0)
for spine in ax.spines.values():
    spine.set_visible(False)

# Net agreement column on the right, in axes fraction (x) and data (y) coordinates
for i, value in enumerate(df["net"]):
    ax.annotate(
        f"{value:+.0f}",
        xy=(1.02, i),
        xycoords=("axes fraction", "data"),
        fontsize=7,
        fontweight="bold",
        color=pole_pos if value > 0 else pole_neg,
        va="center",
        ha="left",
        annotation_clip=False,
    )
ax.annotate(
    "Net",
    xy=(1.02, len(df) - 0.5),
    xycoords=("axes fraction", "data"),
    fontsize=7,
    fontweight="bold",
    color=INK_MUTED,
    va="center",
    ha="left",
    annotation_clip=False,
)

# Legend below chart
leg = ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.14),
    ncol=n_levels,
    fontsize=8,
    frameon=False,
    handlelength=1.5,
    columnspacing=1.5,
)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.30, right=0.90, top=0.92, bottom=0.20)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
