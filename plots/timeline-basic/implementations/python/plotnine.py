""" pyplots.ai
timeline-basic: Event Timeline
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Software development project milestones
data = {
    "date": pd.to_datetime(
        [
            "2024-01-15",
            "2024-02-20",
            "2024-03-10",
            "2024-04-05",
            "2024-05-15",
            "2024-06-20",
            "2024-07-10",
            "2024-08-25",
            "2024-09-15",
            "2024-10-30",
            "2024-11-20",
            "2024-12-15",
        ]
    ),
    "event": [
        "Project Kickoff",
        "Requirements Complete",
        "Architecture Review",
        "Backend Alpha",
        "Frontend Alpha",
        "Integration Testing",
        "Beta Release",
        "User Acceptance",
        "Performance Tuning",
        "Security Audit",
        "Release Candidate",
        "Production Launch",
    ],
    "category": [
        "Planning",
        "Planning",
        "Planning",
        "Development",
        "Development",
        "Testing",
        "Development",
        "Testing",
        "Development",
        "Testing",
        "Release",
        "Release",
    ],
}

df = pd.DataFrame(data)

# Alternate label positions above and below the axis
df["y_offset"] = [1 if i % 2 == 0 else -1 for i in range(len(df))]
df["y_point"] = df["y_offset"] * 0.35
df["y_label"] = df["y_offset"] * 0.65

# Split dataframe for alternating text positions
df_above = df[df["y_offset"] == 1].copy()
df_below = df[df["y_offset"] == -1].copy()

# Category colors - using colorblind-safe palette
category_colors = {
    "Planning": "#306998",  # Python Blue
    "Development": "#FFD43B",  # Python Yellow
    "Testing": "#E69F00",  # Orange
    "Release": "#009E73",  # Green
}

# Create timeline plot
plot = (
    ggplot(df, aes(x="date", y=0))
    # Vertical connector lines from axis to points
    + geom_segment(aes(x="date", xend="date", y=0, yend="y_point"), color="#888888", size=0.8)
    # Timeline axis line
    + geom_segment(
        aes(x=df["date"].min() - pd.Timedelta(days=15), xend=df["date"].max() + pd.Timedelta(days=15), y=0, yend=0),
        color="#333333",
        size=1.5,
    )
    # Event points on the timeline
    + geom_point(aes(x="date", y="y_point", color="category"), size=8)
    # Event labels above the axis
    + geom_text(data=df_above, mapping=aes(x="date", y="y_label", label="event"), size=11, color="#333333", va="bottom")
    # Event labels below the axis
    + geom_text(data=df_below, mapping=aes(x="date", y="y_label", label="event"), size=11, color="#333333", va="top")
    # Styling
    + scale_color_manual(values=category_colors)
    + scale_y_continuous(limits=(-1.2, 1.2))
    + labs(title="timeline-basic · plotnine · pyplots.ai", x="Date", y="", color="Phase")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center"),
        axis_title_x=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_blank(),
        axis_ticks_major_y=element_blank(),
        panel_grid_major_y=element_blank(),
        panel_grid_minor_y=element_blank(),
        panel_grid_major_x=element_line(color="#cccccc", alpha=0.3),
        panel_grid_minor_x=element_blank(),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="bottom",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
