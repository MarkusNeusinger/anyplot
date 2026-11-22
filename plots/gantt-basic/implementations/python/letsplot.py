"""anyplot.ai
gantt-basic: Basic Gantt Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-10
"""

import os
from datetime import datetime

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TASK = "Task"  # role: task
CATEGORY = "Phase"  # role: category
START = "Start"  # role: start
END = "End"  # role: end

# Data: replace this block with your own table, for example df = pd.read_csv("tasks.csv", parse_dates=[START, END])
df = pd.DataFrame(
    {
        TASK: [
            "Requirements Gathering",
            "System Design",
            "UI/UX Design",
            "Backend Development",
            "Frontend Development",
            "Database Setup",
            "API Integration",
            "Unit Testing",
            "Integration Testing",
            "User Acceptance Testing",
            "Documentation",
            "Deployment",
        ],
        CATEGORY: [
            "Planning",
            "Planning",
            "Design",
            "Development",
            "Development",
            "Development",
            "Development",
            "Testing",
            "Testing",
            "Testing",
            "Documentation",
            "Deployment",
        ],
        START: [
            datetime(2025, 1, 6),
            datetime(2025, 1, 13),
            datetime(2025, 1, 20),
            datetime(2025, 1, 27),
            datetime(2025, 2, 3),
            datetime(2025, 1, 27),
            datetime(2025, 2, 17),
            datetime(2025, 2, 10),
            datetime(2025, 2, 24),
            datetime(2025, 3, 3),
            datetime(2025, 2, 17),
            datetime(2025, 3, 10),
        ],
        END: [
            datetime(2025, 1, 10),
            datetime(2025, 1, 17),
            datetime(2025, 1, 31),
            datetime(2025, 2, 14),
            datetime(2025, 2, 21),
            datetime(2025, 2, 7),
            datetime(2025, 2, 28),
            datetime(2025, 2, 21),
            datetime(2025, 3, 7),
            datetime(2025, 3, 14),
            datetime(2025, 3, 7),
            datetime(2025, 3, 14),
        ],
    }
)

# Plot: reads only df and the constants above
# lets-plot draws on a numeric axis: days since the first start, labelled with calendar dates
origin = df[START].min()
df = df.sort_values(START, ascending=False, kind="stable").reset_index(drop=True)
df["start_day"] = (df[START] - origin).dt.days
df["end_day"] = (df[END] - origin).dt.days
df["row"] = range(len(df))
# Stand-in for the current date: the start of the task two thirds down the start-sorted schedule
today = df[START].sort_values().iloc[len(df) * 2 // 3]
today_day = (today - origin).days

tick_days = list(range(0, int(df["end_day"].max()) + 1, 7))
tick_labels = [(origin + pd.Timedelta(days=d)).strftime("%b %d") for d in tick_days]
categories = list(dict.fromkeys(df.sort_values(START)[CATEGORY]))

plot = (
    ggplot(df, aes(x="start_day", y="row"))
    + geom_segment(aes(xend="end_day", yend="row", color=CATEGORY), size=5.5, alpha=0.9)
    + geom_vline(xintercept=today_day, color=INK_SOFT, size=0.8, linetype="dashed")
    + scale_y_continuous(breaks=list(df["row"]), labels=list(df[TASK]), expand=[0.05, 0.05])
    + scale_x_continuous(name=f"Date ({origin.year})", breaks=tick_days, labels=tick_labels)
    + scale_color_manual(values=IMPRINT_PALETTE[: len(categories)], limits=categories, name=CATEGORY)
    + labs(title="gantt-basic · python · letsplot · anyplot.ai", y=TASK)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=16, color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=11, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_position="right",
        panel_grid_major_x=element_line(color=RULE, size=0.3),
        panel_grid_major_y=element_line(color=RULE, size=0.2),
        panel_grid_minor=element_blank(),
    )
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
