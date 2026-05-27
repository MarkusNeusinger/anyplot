""" anyplot.ai
timeline-basic: Event Timeline
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-11
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
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

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

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

# Create month breaks for x-axis
month_breaks = [0, 31, 59, 90, 121, 152, 182, 213, 244, 274, 305, 335]
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Create plot
plot = (
    ggplot(events)
    # Timeline axis (horizontal line at y=0)
    + geom_hline(yintercept=0, color=INK_SOFT, size=1.5)
    # Vertical connectors from axis to event points
    + geom_segment(
        mapping=aes(x="date_num", xend="date_num", yend="y_offset", color="category"), y=0, size=1.2, alpha=0.7
    )
    # Event points
    + geom_point(mapping=aes(x="date_num", y="y_offset", color="category"), size=6, alpha=0.9)
    # Event labels (positioned at label_y)
    + geom_text(mapping=aes(x="date_num", y="label_y", label="event"), size=10, color=INK)
    # Color scale using Okabe-Ito palette
    + scale_color_manual(values=IMPRINT, name="Phase")
    # Axis configuration - use simple month labels with padding
    + scale_x_continuous(name="Month (2024)", breaks=month_breaks, labels=month_labels, limits=[-15, 365])
    + scale_y_continuous(limits=[-2.2, 2.2])
    # Labels
    + labs(title="timeline-basic · letsplot · anyplot.ai", y="")
    # Theme
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=24, color=INK),
        axis_title_x=element_text(size=20, color=INK),
        axis_text_x=element_text(size=16, color=INK_SOFT),
        axis_text_y=element_blank(),
        axis_ticks_y=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.5),
        axis_line_y=element_blank(),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700 px) and HTML
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
