""" anyplot.ai
errorbar-basic: Basic Error Bar Plot
Library: bokeh 3.9.0 | Python 3.14.4
Quality: 88/100 | Updated: 2026-04-25
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label, TeeHead, Whisker
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito categorical palette (positions 1-6)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9"]

# Data — experimental measurements with associated uncertainties
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]
means = np.array([25.3, 38.7, 42.1, 35.8, 48.2, 31.5])

# Asymmetric errors — Treatment C has highest variability, Treatment D has highest mean
lower_errors = np.array([2.1, 3.5, 2.8, 6.5, 4.8, 2.5])
upper_errors = np.array([2.1, 3.5, 2.8, 2.8, 2.2, 2.5])

upper = means + upper_errors
lower = means - lower_errors
colors = OKABE_ITO[: len(categories)]

source = ColumnDataSource(
    data={"categories": categories, "means": means, "upper": upper, "lower": lower, "colors": colors}
)

# Plot
p = figure(
    width=4800,
    height=2700,
    x_range=categories,
    title="errorbar-basic · bokeh · anyplot.ai",
    x_axis_label="Experimental Group",
    y_axis_label="Response Value (units)",
    toolbar_location=None,
    tools="",
)

# Error bars (Whisker with TeeHead caps) — one whisker per group so each can take its own color
for cat, up, lo, col in zip(categories, upper, lower, colors, strict=True):
    grp_source = ColumnDataSource(data={"x": [cat], "upper": [up], "lower": [lo]})
    whisker = Whisker(
        base="x",
        upper="upper",
        lower="lower",
        source=grp_source,
        line_color=col,
        line_width=5,
        upper_head=TeeHead(size=40, line_color=col, line_width=5),
        lower_head=TeeHead(size=40, line_color=col, line_width=5),
    )
    p.add_layout(whisker)

# Mean markers — colored per group
p.scatter(x="categories", y="means", source=source, size=28, color="colors", line_color=PAGE_BG, line_width=2)

# Annotation: highlight highest variability (Treatment C, index 3)
focus_idx = int(np.argmax(lower_errors + upper_errors))
focus_label = Label(
    x=focus_idx,
    y=float(lower[focus_idx]),
    x_units="data",
    y_units="data",
    x_offset=24,
    y_offset=-12,
    text="highest variability",
    text_color=INK_MUTED,
    text_font_size="20pt",
    text_font_style="italic",
)
p.add_layout(focus_label)

# Style — background and outline
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Title
p.title.text_color = INK
p.title.text_font_size = "36pt"
p.title.text_font_style = "normal"
p.title.align = "left"

# Axis labels
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.axis_label_text_font_style = "normal"
p.yaxis.axis_label_text_font_style = "normal"

# Tick labels
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"

# Axis lines and ticks
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Subtle y-grid only
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_color = None

# Y-range trimmed to data — eliminates dead space below
y_min = float(min(lower))
y_max = float(max(upper))
y_pad = (y_max - y_min) * 0.15
p.y_range.start = max(0.0, y_min - y_pad)
p.y_range.end = y_max + y_pad

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html", title="errorbar-basic · bokeh · anyplot.ai")
save(p)
