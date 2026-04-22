""" pyplots.ai
timeline-basic: Event Timeline
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_hline,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Software project milestones (10 events for better readability)
events = pd.DataFrame(
    {
        "date": pd.to_datetime(
            [
                "2024-01-15",
                "2024-02-28",
                "2024-04-01",
                "2024-05-15",
                "2024-06-20",
                "2024-07-25",
                "2024-09-01",
                "2024-10-10",
                "2024-11-15",
                "2024-12-20",
            ]
        ),
        "event": [
            "Project Kickoff",
            "Requirements Done",
            "Design Review",
            "Alpha Release",
            "Beta Testing",
            "Feature Freeze",
            "Release Candidate",
            "Security Audit",
            "Docs Complete",
            "v1.0 Launch",
        ],
        "category": [
            "Planning",
            "Planning",
            "Design",
            "Development",
            "Testing",
            "Development",
            "Release",
            "Testing",
            "Release",
            "Release",
        ],
    }
)

# Convert dates to numeric for plotting and create alternating y positions
events["date_num"] = (events["date"] - events["date"].min()).dt.days
events["y_offset"] = [1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0]
events["label_y"] = [1.5, -1.5, 1.5, -1.5, 1.5, -1.5, 1.5, -1.5, 1.5, -1.5]

# Create month breaks for x-axis (simplified labeling)
month_breaks = [0, 31, 59, 90, 121, 152, 182, 213, 244, 274, 305, 335]
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Create plot
plot = (
    ggplot(events)
    # Timeline axis (horizontal line at y=0)
    + geom_hline(yintercept=0, color="#555555", size=1.5)
    # Vertical connectors from axis to event points
    + geom_segment(
        mapping=aes(x="date_num", xend="date_num", yend="y_offset", color="category"), y=0, size=1.2, alpha=0.7
    )
    # Event points
    + geom_point(mapping=aes(x="date_num", y="y_offset", color="category"), size=6, alpha=0.9)
    # Event labels (positioned at label_y)
    + geom_text(mapping=aes(x="date_num", y="label_y", label="event"), size=9)
    # Color scale
    + scale_color_manual(values=["#306998", "#FFD43B", "#22C55E", "#DC2626", "#8B5CF6"], name="Phase")
    # Axis configuration - use simple month labels with padding
    + scale_x_continuous(name="2024", breaks=month_breaks, labels=month_labels, limits=[-15, 365])
    + scale_y_continuous(limits=[-2.2, 2.2])
    # Labels
    + labs(title="timeline-basic · letsplot · pyplots.ai", y="")
    # Theme
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title_x=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_blank(),
        axis_ticks_y=element_blank(),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700 px)
ggsave(plot, filename="plot.png", path=".", scale=3)

# Save interactive HTML version
ggsave(plot, filename="plot.html", path=".")
