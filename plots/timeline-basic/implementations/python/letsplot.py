""" anyplot.ai
timeline-basic: Event Timeline
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-21
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

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
EVENT = "Event"  # role: event
PHASE = "Phase"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("events.csv", parse_dates=[DATE])
df = pd.DataFrame(
    {
        DATE: pd.to_datetime(
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
        EVENT: [
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
        PHASE: [
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

# Plot: reads only df and the constants above
df = df.sort_values(DATE).reset_index(drop=True)
start = df[DATE].min()
span = (df[DATE].max() - start).days
df["days"] = (df[DATE] - start).dt.days
side = [1.0 if i % 2 == 0 else -1.0 for i in range(len(df))]  # alternate above / below the axis
df["marker_y"] = side
df["label_y"] = [1.5 * s for s in side]

# One tick per month start, labelled with the month name
month_starts = pd.date_range(start.normalize().replace(day=1), df[DATE].max(), freq="MS")
month_starts = month_starts[month_starts >= start - pd.Timedelta(days=15)]
month_breaks = [(m - start).days for m in month_starts]
month_labels = [m.strftime("%b") for m in month_starts]
years = sorted({str(y) for y in df[DATE].dt.year})
x_title = f"Month ({'–'.join([years[0], years[-1]]) if len(years) > 1 else years[0]})"

plot = (
    ggplot(df)
    # Timeline axis (horizontal line at y=0)
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.75)
    # Vertical connectors from axis to event points
    + geom_segment(aes(x="days", xend="days", yend="marker_y", color=PHASE), y=0, size=0.6, alpha=0.7)
    # Event points
    + geom_point(aes(x="days", y="marker_y", color=PHASE), size=3, alpha=0.9)
    # Event labels
    + geom_text(aes(x="days", y="label_y", label=EVENT), size=5, color=INK)
    + scale_color_manual(values=IMPRINT_PALETTE)
    + scale_x_continuous(name=x_title, breaks=month_breaks, labels=month_labels, limits=[-15, span + 15])
    + scale_y_continuous(limits=[-2.2, 2.2])
    + labs(title="timeline-basic · python · letsplot · anyplot.ai", y="")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=16, color=INK),
        axis_title_x=element_text(size=12, color=INK),
        axis_text_x=element_text(size=10, color=INK_SOFT),
        axis_text_y=element_blank(),
        axis_ticks_y=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.25),
        axis_line_y=element_blank(),
        legend_title=element_text(size=12, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_blank(),
        axis_ticks_x=element_line(color=INK_SOFT, size=0.5),
        panel_grid_minor=element_blank(),
    )
    + ggsize(800, 450)
)

# Save as PNG (scale 4x for 3200x1800 px) and HTML
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
