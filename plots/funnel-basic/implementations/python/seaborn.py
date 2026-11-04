"""anyplot.ai
funnel-basic: Basic Funnel Chart
Library: seaborn 0.13.2 | Python 3.14.4
Quality: pending | Updated: 2026-04-26
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.patches import Polygon


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first series always #009E73, one color per stage in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "text.color": INK,
        "axes.labelcolor": INK,
        "ytick.color": INK,
        "xtick.color": INK_SOFT,
    },
)

# Columns: set these to your table's column names
STAGE = "Stage"  # role: stage
VALUE = "Visitors"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("funnel.csv")
df = pd.DataFrame(
    {STAGE: ["Awareness", "Interest", "Consideration", "Intent", "Purchase"], VALUE: [1000, 600, 400, 200, 100]}
)

# Plot: reads only df and the constants above
n_stages = len(df)
stage_colors = [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(n_stages)]
max_value = df[VALUE].max()
percentages = df[VALUE] / df[VALUE].iloc[0] * 100

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Seaborn draws the rectangular core of each stage; trapezoidal panels added
# below tie the cores into a continuous funnel silhouette in stage colors.
sns.barplot(
    data=df,
    x=VALUE,
    y=STAGE,
    hue=STAGE,
    order=df[STAGE],
    palette=stage_colors,
    ax=ax,
    legend=False,
    width=0.50,
    edgecolor="none",
)

# Center each bar on x=0 so the silhouette narrows symmetrically
bars = list(ax.patches)[:n_stages]
for patch in bars:
    patch.set_x(-patch.get_width() / 2)

# Trapezoidal panels between stages: each panel inherits the upper stage color
for i in range(n_stages - 1):
    p_top, p_bot = bars[i], bars[i + 1]
    top_y = p_top.get_y() + p_top.get_height()
    bot_y = p_bot.get_y()
    ax.add_patch(
        Polygon(
            [
                (p_top.get_x(), top_y),
                (p_top.get_x() + p_top.get_width(), top_y),
                (p_bot.get_x() + p_bot.get_width(), bot_y),
                (p_bot.get_x(), bot_y),
            ],
            facecolor=stage_colors[i],
            edgecolor="none",
            zorder=1,
        )
    )

# Closing tail below the last stage so the funnel ends with a proper taper
last_bar = bars[-1]
last_top_y = last_bar.get_y() + last_bar.get_height()
tail_height = 0.50
tail_bot_w = last_bar.get_width() * 0.5
ax.add_patch(
    Polygon(
        [
            (last_bar.get_x(), last_top_y),
            (last_bar.get_x() + last_bar.get_width(), last_top_y),
            (tail_bot_w / 2, last_top_y + tail_height),
            (-tail_bot_w / 2, last_top_y + tail_height),
        ],
        facecolor=stage_colors[-1],
        edgecolor="none",
        zorder=1,
    )
)

# Value + percentage labels sit right of each bar so narrow stages never overflow
right_offset = max_value * 0.04
for i, patch in enumerate(bars):
    cy = patch.get_y() + patch.get_height() / 2
    x_right = patch.get_x() + patch.get_width()
    ax.text(
        x_right + right_offset,
        cy,
        f"{df[VALUE].iloc[i]:,}  ·  {percentages.iloc[i]:.0f}%",
        ha="left",
        va="center",
        fontsize=10,
        fontweight="medium",
        color=INK,
    )

# Awareness on top: matplotlib's default places the first category at the bottom
ax.invert_yaxis()
ax.set_ylim(n_stages - 1 + tail_height + 0.25, -0.45)

sns.despine(ax=ax, left=True, bottom=True)
ax.set_xticks([])
ax.set_xlabel("")
ax.set_ylabel("")
ax.tick_params(axis="y", labelsize=11, length=0, pad=5)

ax.set_xlim(-max_value * 0.95, max_value * 0.85)

ax.set_title("funnel-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
