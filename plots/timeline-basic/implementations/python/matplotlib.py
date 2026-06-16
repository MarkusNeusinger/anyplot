""" anyplot.ai
timeline-basic: Event Timeline
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-11
"""

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

np.random.seed(42)
events = pd.DataFrame(
    {
        "date": pd.to_datetime(
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
        "event": [
            "Project Kickoff",
            "Requirements Done",
            "Alpha Release",
            "Beta Launch",
            "User Testing",
            "Bug Fixes",
            "Final Review",
            "Go Live",
        ],
        "category": ["Planning", "Planning", "Development", "Development", "Testing", "Testing", "Release", "Release"],
    }
)

category_colors = {
    "Planning": IMPRINT[0],
    "Development": IMPRINT[1],
    "Testing": IMPRINT[2],
    "Release": IMPRINT[3],
}
colors = [category_colors[cat] for cat in events["category"]]

fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.axhline(y=0, color=INK_SOFT, linewidth=2, zorder=1, alpha=0.4)

levels = np.tile([1, -1], len(events) // 2 + 1)[: len(events)]
level_heights = levels * 0.3

for date, height, color in zip(events["date"], level_heights, colors, strict=True):
    ax.plot([date, date], [0, height], color=color, linewidth=2.5, zorder=2, alpha=0.8)

ax.scatter(events["date"], level_heights, c=colors, s=300, zorder=3, edgecolors=PAGE_BG, linewidths=1.5)

for date, event, height, color in zip(events["date"], events["event"], level_heights, colors, strict=True):
    va = "bottom" if height > 0 else "top"
    offset = 0.08 if height > 0 else -0.08
    ax.annotate(
        event,
        xy=(date, height),
        xytext=(0, offset * 300),
        textcoords="offset points",
        ha="center",
        va=va,
        fontsize=14,
        fontweight="bold",
        color=INK,
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": ELEVATED_BG,
            "edgecolor": color,
            "linewidth": 1.5,
            "alpha": 0.95,
        },
    )

for date, height in zip(events["date"], level_heights, strict=True):
    ax.annotate(
        date.strftime("%b %d"),
        xy=(date, 0),
        xytext=(0, -20 if height > 0 else 20),
        textcoords="offset points",
        ha="center",
        va="top" if height > 0 else "bottom",
        fontsize=12,
        color=INK_SOFT,
    )

legend_handles = [
    plt.scatter([], [], c=color, s=200, label=cat, edgecolors=PAGE_BG, linewidths=1.5)
    for cat, color in category_colors.items()
]
leg = ax.legend(
    handles=legend_handles, loc="upper right", fontsize=14, title="Project Phase", title_fontsize=16, frameon=True
)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    plt.setp(leg.get_texts(), color=INK_SOFT)
    leg.get_title().set_color(INK)

ax.set_xlim(events["date"].min() - pd.Timedelta(days=40), events["date"].max() + pd.Timedelta(days=40))
ax.set_ylim(-0.6, 0.6)

ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
ax.tick_params(axis="x", labelsize=14, colors=INK_SOFT, labelcolor=INK_SOFT)

ax.yaxis.set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["top"].set_visible(False)
ax.spines["bottom"].set_color(INK_SOFT)
ax.spines["bottom"].set_linewidth(0.8)

ax.set_title("timeline-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)

ax.set_xlabel("Project Timeline", fontsize=20, color=INK, labelpad=10)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
