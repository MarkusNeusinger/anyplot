""" anyplot.ai
dumbbell-basic: Basic Dumbbell Chart
Library: bokeh 3.9.0 | Python 3.14.4
Quality: 88/100 | Updated: 2026-04-26
"""

import os

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito 1 — "Before"
ACCENT = "#D55E00"  # Okabe-Ito 2 — "After"

# Data — Employee satisfaction scores before and after policy changes
# (one department regressed, the rest improved by varying amounts)
categories = [
    "Engineering",
    "Marketing",
    "Sales",
    "Customer Support",
    "Human Resources",
    "Finance",
    "Operations",
    "Research & Development",
]
start_values = [62, 58, 71, 55, 68, 78, 60, 65]
end_values = [78, 74, 82, 70, 85, 72, 73, 88]

# Sort ascending by change so the largest improvements sit at the top
deltas = [e - s for s, e in zip(start_values, end_values, strict=True)]
ordered = sorted(zip(categories, start_values, end_values, deltas, strict=True), key=lambda d: d[3])
categories = [d[0] for d in ordered]
start_values = [d[1] for d in ordered]
end_values = [d[2] for d in ordered]
deltas = [d[3] for d in ordered]

# Plot
p = figure(
    width=4800,
    height=2700,
    y_range=categories,
    x_range=(45, 95),
    title="Employee Satisfaction · dumbbell-basic · bokeh · anyplot.ai",
    x_axis_label="Satisfaction Score",
    y_axis_label="Department",
    background_fill_color=PAGE_BG,
    border_fill_color=PAGE_BG,
    toolbar_location=None,
)

# Connecting segments — thin, subtle, behind the dots
seg_source = ColumnDataSource(
    data={"y": categories, "x_start": start_values, "x_end": end_values, "delta": [f"{d:+d}" for d in deltas]}
)
p.segment(
    x0="x_start", x1="x_end", y0="y", y1="y", source=seg_source, line_color=INK_SOFT, line_alpha=0.45, line_width=4
)

# "Before" dots — Okabe-Ito brand green
before_source = ColumnDataSource(data={"x": start_values, "y": categories, "phase": ["Before"] * len(categories)})
before_glyph = p.scatter(
    x="x",
    y="y",
    source=before_source,
    size=34,
    fill_color=BRAND,
    line_color=PAGE_BG,
    line_width=2,
    legend_label="Before policy changes",
)

# "After" dots — Okabe-Ito vermillion
after_source = ColumnDataSource(data={"x": end_values, "y": categories, "phase": ["After"] * len(categories)})
after_glyph = p.scatter(
    x="x",
    y="y",
    source=after_source,
    size=34,
    fill_color=ACCENT,
    line_color=PAGE_BG,
    line_width=2,
    legend_label="After policy changes",
)

# Hover tooltip (HTML interactivity)
p.add_tools(
    HoverTool(
        renderers=[before_glyph, after_glyph], tooltips=[("Department", "@y"), ("Phase", "@phase"), ("Score", "@x")]
    )
)

# Typography
p.title.text_font_size = "36pt"
p.title.text_color = INK
p.title.text_font_style = "normal"
p.title.align = "center"

p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_label_standoff = 18
p.yaxis.axis_label_standoff = 18

# Spines and ticks — keep an L-shape, suppress chart outline
p.outline_line_color = None
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Grid — subtle vertical guides only
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_color = None

# Legend — placed inside top-left so it never collides with the data range
p.legend.location = "top_left"
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.95
p.legend.border_line_color = INK_SOFT
p.legend.border_line_alpha = 0.4
p.legend.label_text_color = INK_SOFT
p.legend.label_text_font_size = "20pt"
p.legend.spacing = 10
p.legend.padding = 18
p.legend.margin = 24

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html", title="Employee Satisfaction · dumbbell-basic · bokeh · anyplot.ai")
save(p)
