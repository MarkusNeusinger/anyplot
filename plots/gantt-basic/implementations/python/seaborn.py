"""anyplot.ai
gantt-basic: Basic Gantt Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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

# Constants
TODAY = "2026-05-10"  # current-date marker of the schedule

# Columns: set these to your table's column names
TASK = "Task"  # role: task
START = "Start"  # role: start
END = "End"  # role: end
CATEGORY = "Phase"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("schedule.csv")
df = pd.DataFrame(
    {
        TASK: [
            "Site Preparation",
            "Foundation Work",
            "Structural Framing",
            "Roofing",
            "Exterior Walls",
            "Interior Framing",
            "Electrical Work",
            "Plumbing Installation",
            "HVAC Installation",
            "Drywall & Finishing",
            "Painting",
            "Final Inspection",
        ],
        START: pd.to_datetime(
            [
                "2026-02-15",
                "2026-02-22",
                "2026-03-15",
                "2026-04-12",
                "2026-03-22",
                "2026-04-19",
                "2026-05-03",
                "2026-05-03",
                "2026-05-10",
                "2026-05-17",
                "2026-06-07",
                "2026-06-21",
            ]
        ),
        END: pd.to_datetime(
            [
                "2026-02-21",
                "2026-03-14",
                "2026-04-11",
                "2026-05-02",
                "2026-04-18",
                "2026-05-02",
                "2026-05-16",
                "2026-05-30",
                "2026-05-23",
                "2026-06-06",
                "2026-06-20",
                "2026-06-28",
            ]
        ),
        CATEGORY: [
            "Foundation",
            "Foundation",
            "Structure",
            "Structure",
            "Exterior",
            "Interior",
            "Systems",
            "Systems",
            "Systems",
            "Finishing",
            "Finishing",
            "Finalization",
        ],
    }
)

# Plot: reads only df and the constants above
df = df.sort_values(START, kind="stable").reset_index(drop=True)
df["duration"] = (df[END] - df[START]).dt.days
start_num = mdates.date2num(df[START])

categories = list(df[CATEGORY].unique())
category_palette = {cat: IMPRINT_PALETTE[i] for i, cat in enumerate(categories)}

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.barplot(
    data=df,
    y=TASK,
    x="duration",
    order=df[TASK],
    hue=CATEGORY,
    hue_order=categories,
    palette=category_palette,
    orient="h",
    dodge=False,
    errorbar=None,
    width=0.7,
    edgecolor=PAGE_BG,
    linewidth=0.8,
    legend=False,
    ax=ax,
)

# Move each drawn bar to its task's start date (skip the empty bars of absent hue levels)
for bar in ax.patches:
    if bar.get_width() > 0:
        row = int(round(bar.get_y() + bar.get_height() / 2))
        bar.set_x(start_num[row])

# Date axis
ax.xaxis_date()
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.set_xlim(start_num.min() - 3, mdates.date2num(df[END]).max() + 3)

# Current-date line
ax.axvline(mdates.date2num(pd.Timestamp(TODAY)), color=INK, linestyle="--", linewidth=1.4, alpha=0.8)

# Style
ax.set_title("gantt-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)
ax.set_xlabel("Timeline", fontsize=10)
ax.set_ylabel(TASK, fontsize=10)
ax.tick_params(axis="x", labelsize=8, rotation=45)
ax.tick_params(axis="y", labelsize=8)
ax.grid(axis="x", linewidth=0.5)
ax.set_axisbelow(True)
sns.despine(ax=ax)

legend_handles = [Patch(facecolor=category_palette[c], edgecolor=INK_SOFT, linewidth=0.5, label=c) for c in categories]
legend_handles.append(Line2D([0], [0], color=INK, linestyle="--", linewidth=1.4, label="Today"))
ax.legend(handles=legend_handles, loc="upper right", fontsize=8, title=CATEGORY, title_fontsize=8, framealpha=0.95)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
