""" pyplots.ai
gantt-basic: Basic Gantt Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-27
"""

from datetime import datetime

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
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
        datetime(2025, 3, 14),
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

# Python-inspired color palette
colors = {
    "Planning": "#306998",  # Python Blue
    "Design": "#FFD43B",  # Python Yellow
    "Development": "#4B8BBE",  # Light Python Blue
    "QA": "#646464",  # Gray
    "Deployment": "#28A745",  # Green
}

# Current date marker
today = datetime(2025, 2, 10)

# Create the Gantt chart
plot = (
    ggplot(df, aes(x="start", xend="end", y="task", yend="task", color="category"))
    + geom_segment(size=12, lineend="butt")
    + geom_vline(xintercept=today, linetype="dashed", color="#E74C3C", size=1.5)
    + scale_color_manual(values=colors)
    + scale_y_discrete(limits=df["task"].tolist()[::-1])
    + labs(title="gantt-basic \u00b7 plotnine \u00b7 pyplots.ai", x="Date", y="Task", color="Phase")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, face="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16, rotation=45, ha="right"),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color="#CCCCCC", size=0.5, alpha=0.5),
    )
)

# Save the plot
plot.save("plot.png", dpi=300, width=16, height=9)
