"""anyplot.ai
gantt-basic: Basic Gantt Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TASK = "Task"  # role: task
START = "Start"  # role: start
END = "End"  # role: end
CATEGORY = "Phase"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("tasks.csv", parse_dates=[START, END])
df = pd.DataFrame(
    {
        TASK: [
            "Requirements Analysis",
            "System Design",
            "Database Setup",
            "Backend Development",
            "Frontend Development",
            "API Integration",
            "Unit Testing",
            "Integration Testing",
            "User Acceptance Testing",
            "Documentation",
            "Deployment Prep",
            "Go Live",
        ],
        START: pd.to_datetime(
            [
                "2025-01-06",
                "2025-01-13",
                "2025-01-27",
                "2025-02-03",
                "2025-02-10",
                "2025-03-03",
                "2025-03-10",
                "2025-03-24",
                "2025-04-07",
                "2025-03-17",
                "2025-04-14",
                "2025-04-28",
            ]
        ),
        END: pd.to_datetime(
            [
                "2025-01-17",
                "2025-01-31",
                "2025-02-07",
                "2025-03-07",
                "2025-03-14",
                "2025-03-21",
                "2025-03-28",
                "2025-04-11",
                "2025-04-18",
                "2025-04-11",
                "2025-04-25",
                "2025-05-02",
            ]
        ),
        CATEGORY: ["Planning"] * 2 + ["Development"] * 4 + ["Testing"] * 3 + ["Deployment"] * 3,
    }
)

# Plot: reads only df and the constants above
tasks = df.sort_values(START).reset_index(drop=True)
categories = list(df[CATEGORY].drop_duplicates())
category_colors = {cat: IMPRINT_PALETTE[i] for i, cat in enumerate(categories)}

# "Today" marker: mid-project, for demonstration
today = df[START].min() + (df[END].max() - df[START].min()) / 2

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# One bar per task, earliest start on top
for i, row in tasks.iterrows():
    ax.barh(
        i,
        (row[END] - row[START]).days,
        left=row[START],
        height=0.6,
        color=category_colors[row[CATEGORY]],
        edgecolor=PAGE_BG,
        linewidth=0.5,
        alpha=0.9,
    )
ax.invert_yaxis()
ax.set_yticks(range(len(tasks)), tasks[TASK])

# X-axis: dates
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.tick_params(axis="x", rotation=45)
ax.set_xlim(df[START].min() - pd.Timedelta(days=3), df[END].max() + pd.Timedelta(days=3))

ax.axvline(today, color=INK_MUTED, linewidth=1.5, linestyle="--", zorder=5)

# Style
ax.set_xlabel(f"Project Timeline ({df[START].min().year})", fontsize=10, color=INK)
ax.set_ylabel("Project Tasks", fontsize=10, color=INK)
ax.set_title("gantt-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)

ax.grid(True, axis="x", alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Legend: categories plus the Today line
legend_elements = [Patch(facecolor=color, edgecolor=INK_SOFT, label=cat) for cat, color in category_colors.items()]
legend_elements.append(Line2D([0], [0], color=INK_MUTED, linewidth=1.5, linestyle="--", label="Today"))
leg = ax.legend(handles=legend_elements, loc="upper right", fontsize=8, framealpha=0.95, fancybox=True)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
for text in leg.get_texts():
    text.set_color(INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
