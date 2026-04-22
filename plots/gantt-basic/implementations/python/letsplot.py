""" pyplots.ai
gantt-basic: Basic Gantt Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-27
"""

import os
from datetime import datetime

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Software Development Project
tasks_data = {
    "task": [
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
    "category": [
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
    "start": [
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
    "end": [
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

df = pd.DataFrame(tasks_data)

# Convert dates to numeric for plotting (days since project start)
project_start = datetime(2025, 1, 6)
df["start_days"] = [(d - project_start).days for d in df["start"]]
df["end_days"] = [(d - project_start).days for d in df["end"]]
df["duration"] = df["end_days"] - df["start_days"]

# Order tasks by start date and assign y positions
df = df.sort_values("start_days", ascending=False).reset_index(drop=True)
df["y_pos"] = range(len(df))

# Create the Gantt chart using horizontal bars (geom_segment)
plot = (
    ggplot(df, aes(x="start_days", y="y_pos", color="category"))
    + geom_segment(aes(xend="end_days", yend="y_pos"), size=12, alpha=0.85)
    + geom_point(size=4, shape=15)  # Start markers
    + geom_point(aes(x="end_days"), size=4, shape=15)  # End markers
    + scale_y_continuous(breaks=list(df["y_pos"]), labels=list(df["task"]), expand=[0.05, 0.05])
    + scale_x_continuous(
        name="Project Timeline (Days from Start)",
        breaks=[0, 7, 14, 21, 28, 35, 42, 49, 56, 63, 70],
        labels=[
            "Week 1",
            "Week 2",
            "Week 3",
            "Week 4",
            "Week 5",
            "Week 6",
            "Week 7",
            "Week 8",
            "Week 9",
            "Week 10",
            "Week 11",
        ],
    )
    + scale_color_manual(values=["#306998", "#FFD43B", "#22C55E", "#EF4444", "#8B5CF6", "#06B6D4"], name="Phase")
    + labs(title="gantt-basic · letsplot · pyplots.ai", x="Project Timeline", y="Tasks")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title_x=element_text(size=22),
        axis_title_y=element_text(size=22),
        axis_text_x=element_text(size=16, angle=45),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major_x=element_line(color="#E5E5E5", size=0.5),
        panel_grid_major_y=element_line(color="#F5F5F5", size=0.3),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", scale=3, path=".")

# Save interactive HTML version
ggsave(plot, "plot.html", path=".")

# Clean up lets-plot-images folder if created
if os.path.exists("lets-plot-images"):
    import shutil

    shutil.rmtree("lets-plot-images")
