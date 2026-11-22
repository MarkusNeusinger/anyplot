""" anyplot.ai
gantt-basic: Basic Gantt Chart
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_segment,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    scale_y_discrete,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TASK = "Task"  # role: task
START = "Start"  # role: start
END = "End"  # role: end
CATEGORY = "Phase"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("schedule.csv")
df = pd.DataFrame(
    {
        TASK: [
            "Requirements",
            "UI Design",
            "Backend Architecture",
            "Database Setup",
            "API Development",
            "Frontend Development",
            "Integration",
            "Testing",
            "Documentation",
            "Deployment",
        ],
        START: pd.to_datetime(
            [
                "2025-01-06",
                "2025-01-13",
                "2025-01-13",
                "2025-01-20",
                "2025-01-27",
                "2025-02-03",
                "2025-02-17",
                "2025-02-24",
                "2025-03-03",
                "2025-03-10",
            ]
        ),
        END: pd.to_datetime(
            [
                "2025-01-17",
                "2025-01-31",
                "2025-01-24",
                "2025-02-07",
                "2025-02-21",
                "2025-02-28",
                "2025-03-07",
                "2025-03-14",
                "2025-03-14",
                "2025-03-21",
            ]
        ),
        CATEGORY: [
            "Planning",
            "Design",
            "Design",
            "Development",
            "Development",
            "Development",
            "Development",
            "QA",
            "QA",
            "Deployment",
        ],
    }
)

# Plot: reads only df and the constants above
# Order tasks by start date, first task at the top
df = df.sort_values(START, kind="stable")
tasks = df[TASK].dropna().unique().tolist()
df[TASK] = pd.Categorical(df[TASK], categories=tasks, ordered=True)

# Current date marker: the midpoint of the schedule
today = df[START].min() + (df[END].max() - df[START].min()) / 2

plot = (
    ggplot(df, aes(x=START, xend=END, y=TASK, yend=TASK, color=CATEGORY))
    + geom_segment(size=6)
    + geom_vline(xintercept=today, linetype="dashed", color=INK, size=0.75, alpha=0.5)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=df[CATEGORY].unique().tolist())
    + scale_y_discrete(limits=tasks[::-1])
    + labs(title="gantt-basic · python · plotnine · anyplot.ai", x="Date")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=12, face="bold", color=INK),
        axis_title_x=element_text(size=10, color=INK),
        axis_title_y=element_text(size=10, color=INK),
        axis_text_x=element_text(size=8, rotation=45, ha="right", color=INK_SOFT),
        axis_text_y=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.25),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color=INK, size=0.15, alpha=0.10),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
