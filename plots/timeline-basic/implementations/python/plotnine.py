""" anyplot.ai
timeline-basic: Event Timeline
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-11
"""

import os
import sys
from pathlib import Path


# Remove current directory from path to avoid importing local plotnine.py
current_dir = str(Path(__file__).parent)
sys.path = [p for p in sys.path if p != current_dir and p != ""]

import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    element_blank,
    element_line,
    element_rect,
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Software development project milestones with varied timing
data = {
    "date": pd.to_datetime(
        [
            "2024-01-08",
            "2024-02-15",
            "2024-03-08",
            "2024-04-12",
            "2024-05-20",
            "2024-06-10",
            "2024-07-18",
            "2024-08-05",
            "2024-09-22",
            "2024-10-15",
            "2024-11-08",
            "2024-12-20",
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

# Category colors - using Okabe-Ito palette
category_colors = {
    "Planning": IMPRINT[0],
    "Development": IMPRINT[1],
    "Testing": IMPRINT[2],
    "Release": IMPRINT[3],
}

# Create timeline plot
plot = (
    ggplot(df, aes(x="date", y=0))
    # Vertical connector lines from axis to points
    + geom_segment(aes(x="date", xend="date", y=0, yend="y_point"), color=INK_SOFT, size=0.8, alpha=0.5)
    # Timeline axis line
    + geom_segment(
        aes(x=df["date"].min() - pd.Timedelta(days=20), xend=df["date"].max() + pd.Timedelta(days=20), y=0, yend=0),
        color=INK_SOFT,
        size=1.5,
    )
    # Event points on the timeline
    + geom_point(aes(x="date", y="y_point", color="category"), size=5)
    # Event labels above the axis
    + geom_text(data=df_above, mapping=aes(x="date", y="y_label", label="event"), size=11, color=INK, va="bottom")
    # Event labels below the axis
    + geom_text(data=df_below, mapping=aes(x="date", y="y_label", label="event"), size=11, color=INK, va="top")
    # Styling
    + scale_color_manual(values=category_colors)
    + scale_y_continuous(limits=(-1.2, 1.2))
    + labs(title="timeline-basic · plotnine · anyplot.ai", x="Project Timeline 2024", y="", color="Phase")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=24, ha="center", color=INK),
        axis_title_x=element_text(size=20, color=INK),
        axis_text_x=element_text(size=16, color=INK_SOFT),
        axis_text_y=element_blank(),
        axis_ticks_major_y=element_blank(),
        axis_line_y=element_blank(),
        panel_grid_major_y=element_blank(),
        panel_grid_minor_y=element_blank(),
        panel_grid_major_x=element_line(color=INK_SOFT, alpha=0.1, size=0.3),
        panel_grid_minor_x=element_blank(),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_position="bottom",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
