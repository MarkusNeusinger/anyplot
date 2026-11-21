"""anyplot.ai
timeline-basic: Event Timeline
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os
import sys
import textwrap
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
    scale_x_datetime,
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

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
EVENT = "Event"  # role: event
CATEGORY = "Phase"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("events.csv", parse_dates=["Date"])
df = pd.DataFrame(
    {
        DATE: pd.to_datetime(
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
        EVENT: [
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
        CATEGORY: [
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
)

# Plot: reads only df and the constants above
df = df.sort_values(DATE).reset_index(drop=True)

# Alternate labels above and below the axis; markers keep their exact dates
side = pd.Series([1 if i % 2 == 0 else -1 for i in range(len(df))])
df["y_point"] = side * 0.35
df["y_label"] = side * 0.65
df["label"] = df[EVENT].map(lambda text: "\n".join(textwrap.wrap(text, width=12)))
df_above = df[side == 1]
df_below = df[side == -1]

# The timeline axis, a little longer than the first and last event
span = pd.Timedelta(days=20)
axis_line = pd.DataFrame({"x": [df[DATE].min() - span], "xend": [df[DATE].max() + span]})

plot = (
    ggplot(df, aes(x=DATE))
    # Connectors from the axis to each marker
    + geom_segment(aes(xend=DATE, y=0, yend="y_point"), color=INK_SOFT, size=0.4, alpha=0.5)
    # Timeline axis line
    + geom_segment(aes(x="x", xend="xend", y=0, yend=0), data=axis_line, color=INK_SOFT, size=0.8, inherit_aes=False)
    # Event markers, one per event at its date
    + geom_point(aes(y="y_point", color=CATEGORY), size=3)
    # Event labels above and below the axis
    + geom_text(aes(y="y_label", label="label"), data=df_above, size=7, color=INK, va="bottom", lineheight=0.9)
    + geom_text(aes(y="y_label", label="label"), data=df_below, size=7, color=INK, va="top", lineheight=0.9)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=df[CATEGORY].unique().tolist())
    + scale_x_datetime(date_breaks="1 month", date_labels="%b")
    + scale_y_continuous(limits=(-1.2, 1.2))
    + labs(title="timeline-basic · python · plotnine · anyplot.ai", x=f"{DATE} (2024)", y="", color=CATEGORY)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=12, ha="center", color=INK),
        axis_title_x=element_text(size=10, color=INK),
        axis_text_x=element_text(size=8, color=INK_SOFT),
        axis_text_y=element_blank(),
        axis_ticks_major_y=element_blank(),
        axis_line_y=element_blank(),
        panel_grid_major_y=element_blank(),
        panel_grid_minor_y=element_blank(),
        panel_grid_major_x=element_line(color=INK_SOFT, alpha=0.1, size=0.3),
        panel_grid_minor_x=element_blank(),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position="bottom",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
