""" anyplot.ai
timeline-basic: Event Timeline
Library: pygal 3.1.3 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per project phase in order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Constants
STEM_LEVELS = (1.0, 2.0)  # connector lengths in layout units; the vertical offset carries no data

# Columns: set these to your table's column names
DATE = "Milestone date"  # role: date
EVENT = "Milestone"  # role: event
PHASE = "Project phase"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("milestones.csv")
df = pd.DataFrame(
    {
        DATE: pd.to_datetime(
            [
                "2024-01-15",
                "2024-02-10",
                "2024-03-20",
                "2024-04-25",
                "2024-06-15",
                "2024-08-01",
                "2024-09-10",
                "2024-10-20",
            ]
        ),
        EVENT: [
            "Project Kickoff",
            "Requirements Complete",
            "Architecture Design",
            "Development Start",
            "Alpha Release",
            "Beta Release",
            "User Acceptance",
            "Production Launch",
        ],
        PHASE: ["Planning", "Planning", "Design", "Development", "Development", "Testing", "Testing", "Deployment"],
    }
)

# Plot: reads only df and the constants above
events = df.dropna(subset=[DATE]).sort_values(DATE)
events = events.assign(**{DATE: events[DATE].dt.date, EVENT: events[EVENT].fillna("").astype(str)})
phases = events[PHASE].dropna().unique().tolist()

# Labels alternate above and below the axis; stems cycle the levels so close neighbours on one side clear each other
side = [1 if i % 2 == 0 else -1 for i in range(len(events))]
stem = [s * STEM_LEVELS[(i // 2) % len(STEM_LEVELS)] for i, s in enumerate(side)]
span = max(STEM_LEVELS) + 1

start = min(events[DATE])
end = max(events[DATE])
month_ticks = pd.date_range(pd.Timestamp(start).replace(day=1), pd.Timestamp(end) + pd.offsets.MonthBegin(1), freq="MS")
tick_step = max(1, len(month_ticks) // 12)

title = "Software Project Milestones · timeline-basic · python · pygal · anyplot.ai"
title_size = max(44, round(66 * min(1.0, 67 / len(title))))

# Series order: axis line, connectors, one series per phase, event names, dates — colors follow the same order
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(INK_SOFT, INK_MUTED, *(IMPRINT_PALETTE[i] for i in range(len(phases))), INK, INK_SOFT),
    value_colors=(None, None, *(None for _ in phases), INK, INK_SOFT),
    opacity="1",  # legend swatches match the solid markers they explain
    title_font_size=title_size,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=0,
    value_label_font_size=38,
    tooltip_font_size=36,
)

chart = pygal.DateLine(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=DATE,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    range=(-span, span),
    xrange=(month_ticks[0].date(), month_ticks[-1].date()),
    x_value_formatter=lambda d: d.strftime("%b %Y"),
    x_label_rotation=0,
    legend_at_bottom=True,
    legend_at_bottom_columns=len(phases),
    legend_box_size=36,
    truncate_legend=-1,
    print_labels=True,
    allow_interruptions=True,
    dots_size=24,
    margin=60,
    # Labels centre on their stem; the frame line at the plot's left edge carries no data on a timeline, so it is hidden
    css=[
        "file://style.css",
        "file://graph.css",
        "inline:.text-overlay text.label{text-anchor:middle}.axis > .line{stroke-opacity:0}",
    ],
)
chart.x_labels = [t.date() for t in month_ticks[::tick_step]]

chart.add(None, [(start, 0), (end, 0)], stroke=True, show_dots=False, stroke_style={"width": 5})

connectors = []
for d, h in zip(events[DATE], stem, strict=True):
    connectors += [(d, 0), (d, h), None]
chart.add(None, connectors, stroke=True, show_dots=False, stroke_style={"width": 3})

for phase in phases:
    chart.add(phase, [(d, 0) for d in events.loc[events[PHASE] == phase, DATE]], stroke=False)

chart.add(
    None,
    [
        {"value": (d, h + 0.5 * s), "label": name}
        for d, name, h, s in zip(events[DATE], events[EVENT], stem, side, strict=True)
    ],
    stroke=False,
    dots_size=0,
)
chart.add(
    None,
    [
        {"value": (d, h + 0.22 * s), "label": d.strftime("%b %d")}
        for d, h, s in zip(events[DATE], stem, side, strict=True)
    ],
    stroke=False,
    dots_size=0,
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
