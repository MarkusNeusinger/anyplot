"""anyplot.ai
bar-stacked: Stacked Bar Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-09
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (first series always #009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
WEEKDAY = "Weekday"  # role: category
CHANNEL = "Traffic channel"  # role: component
SESSIONS = "Sessions (thousands)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
sessions = {
    "Organic search": [48, 52, 55, 53, 47, 36, 33],
    "Direct": [30, 32, 31, 33, 29, 24, 22],
    "Social": [14, 15, 17, 18, 22, 27, 29],
    "Email": [18, 21, 16, 12, 9, 5, 7],
}
df = pd.DataFrame(
    {
        WEEKDAY: days * len(sessions),
        CHANNEL: [channel for channel in sessions for _ in days],
        SESSIONS: [value for values in sessions.values() for value in values],
    }
)

# Plot: reads only df and the constants above
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
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Components in the data's order, largest overall at the bottom of every stack
channel_order = df.groupby(CHANNEL, sort=False)[SESSIONS].sum().sort_values(ascending=False).index.tolist()
day_order = list(dict.fromkeys(df[WEEKDAY]))
plot_df = df.assign(
    **{
        WEEKDAY: pd.Categorical(df[WEEKDAY], categories=day_order, ordered=True),
        CHANNEL: pd.Categorical(df[CHANNEL], categories=channel_order, ordered=True),
    }
)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.histplot(
    data=plot_df,
    x=WEEKDAY,
    weights=SESSIONS,
    hue=CHANNEL,
    hue_order=channel_order,
    multiple="stack",
    palette=IMPRINT_PALETTE[: len(channel_order)],
    shrink=0.7,
    edgecolor=PAGE_BG,
    linewidth=0.8,
    alpha=1,
    ax=ax,
)

# Total labels above each complete stack
totals = df.groupby(WEEKDAY, sort=False)[SESSIONS].sum().reindex(day_order)
for i, total in enumerate(totals):
    ax.text(
        i,
        total + totals.max() * 0.015,
        f"{total:g}",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color=INK,
    )

# Style
ax.set_title(
    "Website sessions by channel · bar-stacked · python · seaborn · anyplot.ai",
    fontsize=12,
    fontweight="bold",
    color=INK,
    loc="left",
)
ax.set_xlabel(WEEKDAY, fontsize=10, color=INK)
ax.set_ylabel(SESSIONS, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_ylim(0, totals.max() * 1.12)
ax.yaxis.grid(True, linewidth=0.6)
ax.xaxis.grid(False)
ax.set_axisbelow(True)
sns.despine(ax=ax)

legend = ax.get_legend()
legend.set_title(CHANNEL)
legend.get_title().set_fontsize(9)
legend.get_title().set_color(INK)
for text in legend.get_texts():
    text.set_fontsize(8)
    text.set_color(INK)
legend.set_bbox_to_anchor((1.02, 1))
legend.set_loc("upper left")
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)

fig.subplots_adjust(left=0.08, right=0.78, top=0.92, bottom=0.11)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
