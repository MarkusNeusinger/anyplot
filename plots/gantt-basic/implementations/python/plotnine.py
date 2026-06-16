""" anyplot.ai
gantt-basic: Basic Gantt Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-10
"""

import os
from datetime import datetime

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

# Okabe-Ito palette (5 categories)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data - Software development project schedule
data = {
    "task": [
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
    "start": [
        datetime(2025, 1, 6),
        datetime(2025, 1, 13),
        datetime(2025, 1, 13),
        datetime(2025, 1, 20),
        datetime(2025, 1, 27),
        datetime(2025, 2, 3),
        datetime(2025, 2, 17),
        datetime(2025, 2, 24),
        datetime(2025, 3, 3),
        datetime(2025, 3, 10),
    ],
    "end": [
        datetime(2025, 1, 17),
        datetime(2025, 1, 31),
        datetime(2025, 1, 24),
        datetime(2025, 2, 7),
        datetime(2025, 2, 21),
        datetime(2025, 2, 28),
        datetime(2025, 3, 7),
        datetime(2025, 3, 14),
        datetime(2025, 3, 14),
        datetime(2025, 3, 21),
    ],
    "category": [
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

df = pd.DataFrame(data)

# Order tasks by start date (reversed for bottom-to-top display)
df = df.sort_values("start", ascending=True)
df["task"] = pd.Categorical(df["task"], categories=df["task"].tolist(), ordered=True)

# Map categories to Okabe-Ito colors
category_colors = {
    "Planning": IMPRINT[0],
    "Design": IMPRINT[1],
    "Development": IMPRINT[2],
    "QA": IMPRINT[3],
    "Deployment": IMPRINT[4],
}

# Current date marker
today = datetime(2025, 2, 10)

# Create the Gantt chart
plot = (
    ggplot(df, aes(x="start", xend="end", y="task", yend="task", color="category"))
    + geom_segment(size=12)
    + geom_vline(xintercept=today, linetype="dashed", color=INK, size=1.5, alpha=0.5)
    + scale_color_manual(values=category_colors)
    + scale_y_discrete(limits=df["task"].tolist()[::-1])
    + labs(title="gantt-basic · plotnine · anyplot.ai", x="Date", y="Task", color="Phase")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=24, face="bold", color=INK),
        axis_title_x=element_text(size=20, color=INK),
        axis_title_y=element_text(size=20, color=INK),
        axis_text_x=element_text(size=16, rotation=45, ha="right", color=INK_SOFT),
        axis_text_y=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=14, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.10),
    )
)

# Save the plot
plot.save(f"plot-{THEME}.png", dpi=300, width=16, height=9)
