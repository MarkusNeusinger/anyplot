"""anyplot.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-28
"""

import os

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: the ordered Likert levels below take steps of a ramp between its red and green members
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Diverging ramp for marks: matte red pole, grey midpoint, brand green pole (Imprint, ordered categories)
DIV_MARKS = [(0.0, "#AE3030"), (0.5, "#6B6A63" if THEME == "light" else "#686762"), (1.0, "#009E73")]
imprint_div = LinearSegmentedColormap.from_list("imprint_div", DIV_MARKS)

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

# Columns: set these to your table's column names
QUESTION = "Question"  # role: question
STRONGLY_DISAGREE = "Strongly Disagree"  # role: strongly_disagree
DISAGREE = "Disagree"  # role: disagree
NEUTRAL = "Neutral"  # role: neutral
AGREE = "Agree"  # role: agree
STRONGLY_AGREE = "Strongly Agree"  # role: strongly_agree

# Constants
LEVELS = [STRONGLY_DISAGREE, DISAGREE, NEUTRAL, AGREE, STRONGLY_AGREE]  # scale order, negative to positive
LABEL_MIN = 10  # segments narrower than this share (in %) stay unlabeled
STRONG_NET = 15  # a net agreement above this counts as strongly positive

# Data: replace this block with your own table, for example df = pd.read_csv("survey.csv")
df = pd.DataFrame(
    {
        QUESTION: [
            "Career growth opportunities",
            "Work-life balance",
            "Team collaboration",
            "Management communication",
            "Compensation & benefits",
            "Job security",
            "Training & development",
            "Workplace culture",
        ],
        STRONGLY_DISAGREE: [5, 8, 3, 14, 20, 4, 10, 6],
        DISAGREE: [10, 14, 7, 22, 28, 8, 18, 12],
        NEUTRAL: [15, 18, 12, 20, 17, 14, 16, 16],
        AGREE: [40, 35, 45, 28, 22, 42, 32, 38],
        STRONGLY_AGREE: [30, 25, 33, 16, 13, 32, 24, 28],
    }
)

# Plot: reads only df and the constants above
net = df[AGREE] + df[STRONGLY_AGREE] - df[DISAGREE] - df[STRONGLY_DISAGREE]
table = df.loc[net.sort_values(ascending=False).index].reset_index(drop=True)  # most agreed at the top
net = net.loc[net.sort_values(ascending=False).index].reset_index(drop=True)
questions = table[QUESTION].tolist()

# Every bar is centered on the middle of its neutral segment
mid = LEVELS.index(NEUTRAL)
widths = table[LEVELS]
start = -(widths.iloc[:, :mid].sum(axis=1) + widths[NEUTRAL] / 2)
rights = widths.cumsum(axis=1).add(start, axis=0)
lefts = rights - widths

colors = dict(zip(LEVELS, [imprint_div(v) for v in np.linspace(0, 1, len(LEVELS))], strict=True))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Subtle alternating row banding
for i in range(0, len(questions), 2):
    ax.axhspan(i - 0.5, i + 0.5, facecolor=INK, alpha=0.03, zorder=0)

bar_kw = {
    "y": questions,
    "order": questions,
    "orient": "h",
    "ax": ax,
    "width": 0.65,
    "edgecolor": PAGE_BG,
    "linewidth": 0.5,
    "saturation": 1,
    "zorder": 2,
}

# Overlay technique: outermost layer first, progressively narrower layers on top, per side
for level in LEVELS[mid:][::-1]:
    sns.barplot(x=rights[level].to_numpy(), color=colors[level], **bar_kw)
for level in LEVELS[: mid + 1]:
    sns.barplot(x=lefts[level].to_numpy(), color=colors[level], **bar_kw)

# Percentage labels inside the segments that have room for them
for level in LEVELS:
    for y_pos, (left, width) in enumerate(zip(lefts[level], widths[level], strict=True)):
        if width >= LABEL_MIN:
            ax.text(
                left + width / 2,
                y_pos,
                f"{width:g}%",
                ha="center",
                va="center",
                fontsize=8,
                fontweight="medium",
                color="white",
            )

# Net agreement callout at the right edge of each row
for y_pos, value in enumerate(net):
    badge_color = (
        colors[STRONGLY_AGREE] if value > STRONG_NET else colors[STRONGLY_DISAGREE] if value < 0 else INK_MUTED
    )
    ax.text(
        0.99,
        y_pos,
        f"net {value:+g}%",
        transform=ax.get_yaxis_transform(),
        ha="right",
        va="center",
        fontsize=8,
        color=badge_color,
        fontweight="bold",
    )

# Style
title = "Employee Engagement Survey · bar-diverging-likert · python · seaborn · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title)))

x_low = lefts.min().min() - 8
x_high = rights.max().max() + 0.2 * (rights.max().max() - x_low)
ax.set_xlim(x_low, x_high)
ax.set_xlabel("Share of responses (%)", fontsize=10, color=INK, labelpad=8)
ax.set_ylabel("")
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=10)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.axvline(0, color=INK, linewidth=0.8, zorder=1.5)  # behind the bars so it never strikes through the neutral labels
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{abs(x):g}%"))
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.yaxis.grid(False)
ax.set_axisbelow(True)

# Bold extreme question labels
for i in (0, len(questions) - 1):
    ax.get_yticklabels()[i].set_fontweight("bold")

sns.despine(ax=ax)

ax.legend(
    handles=[Patch(facecolor=colors[level], edgecolor=PAGE_BG, linewidth=0.5, label=level) for level in LEVELS],
    loc="upper center",
    bbox_to_anchor=(0.5, -0.15),
    ncol=len(LEVELS),
    fontsize=8,
    frameon=False,
    labelcolor=INK,
)

fig.subplots_adjust(left=0.27, right=0.97, top=0.91, bottom=0.21)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
