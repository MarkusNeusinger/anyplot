"""anyplot.ai
timeline-basic: Event Timeline
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Project timeline"  # role: date
EVENT = "Event"  # role: event
CATEGORY = "Project phase"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("events.csv", parse_dates=[DATE])
df = pd.DataFrame(
    {
        DATE: pd.to_datetime(
            [
                "2024-01-08",
                "2024-02-25",
                "2024-04-20",
                "2024-05-30",
                "2024-07-15",
                "2024-09-10",
                "2024-10-20",
                "2024-12-15",
            ]
        ),
        EVENT: [
            "Project Kickoff",
            "Requirements Done",
            "Alpha Release",
            "Beta Launch",
            "User Testing",
            "Bug Fixes",
            "Final Review",
            "Go Live",
        ],
        CATEGORY: ["Planning", "Planning", "Development", "Development", "Testing", "Testing", "Release", "Release"],
    }
)

# Plot: reads only df and the constants above
categories = list(df[CATEGORY].drop_duplicates())
category_colors = {cat: IMPRINT_PALETTE[i] for i, cat in enumerate(categories)}
colors = df[CATEGORY].map(category_colors)

# Labels alternate above (+) and below (-) the axis; the height is layout only
side = pd.Series([1 if i % 2 == 0 else -1 for i in range(len(df))], index=df.index)
heights = side * 0.3

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.axhline(y=0, color=INK_SOFT, linewidth=1.5, zorder=1, alpha=0.4)

for date, height, color in zip(df[DATE], heights, colors, strict=True):
    ax.plot([date, date], [0, height], color=color, linewidth=1.5, zorder=2, alpha=0.8)

ax.scatter(df[DATE], heights, c=colors, s=90, zorder=3, edgecolors=PAGE_BG, linewidths=1.0)

for date, event, height, color in zip(df[DATE], df[EVENT], heights, colors, strict=True):
    above = height > 0
    ax.annotate(
        event,
        xy=(date, height),
        xytext=(0, 9 if above else -9),
        textcoords="offset points",
        ha="center",
        va="bottom" if above else "top",
        fontsize=9,
        fontweight="bold",
        color=INK,
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": ELEVATED_BG,
            "edgecolor": color,
            "linewidth": 1.0,
            "alpha": 0.95,
        },
    )

for date, height in zip(df[DATE], heights, strict=True):
    above = height > 0
    ax.annotate(
        date.strftime("%b %d"),
        xy=(date, 0),
        xytext=(0, -8 if above else 8),
        textcoords="offset points",
        ha="center",
        va="top" if above else "bottom",
        fontsize=7,
        color=INK_SOFT,
    )

legend_handles = [
    ax.scatter([], [], c=color, s=60, label=cat, edgecolors=PAGE_BG, linewidths=1.0)
    for cat, color in category_colors.items()
]
leg = ax.legend(handles=legend_handles, loc="upper right", fontsize=8, title=CATEGORY, title_fontsize=9, frameon=True)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK)

ax.set_xlim(df[DATE].min() - pd.Timedelta(days=40), df[DATE].max() + pd.Timedelta(days=40))
ax.set_ylim(-0.6, 0.6)

ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
ax.tick_params(axis="x", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

ax.yaxis.set_visible(False)
for spine in ("left", "right", "top"):
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color(INK_SOFT)
ax.spines["bottom"].set_linewidth(0.8)

ax.set_title("timeline-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=12)
ax.set_xlabel(DATE, fontsize=10, color=INK, labelpad=6)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
