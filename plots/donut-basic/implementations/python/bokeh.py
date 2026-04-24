"""anyplot.ai
donut-basic: Basic Donut Chart
Library: bokeh | Python 3.13
Quality: pending | Updated: 2026-04-24
"""

import os
from math import cos, pi, sin

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure
from bokeh.transform import cumsum


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito categorical palette (first segment is always brand green)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]

# Data — Annual budget allocation by department (USD thousands)
categories = ["Engineering", "Operations", "Marketing", "Sales", "Support"]
values = [480, 210, 155, 125, 55]
total = sum(values)

angles = [v / total * 2 * pi for v in values]
percentages = [f"{v / total * 100:.1f}%" for v in values]

source = ColumnDataSource(
    data={"category": categories, "value": values, "angle": angles, "color": OKABE_ITO[: len(categories)]}
)

# Plot — square canvas for circular shapes
p = figure(
    width=3600,
    height=3600,
    title="Budget by Department · donut-basic · bokeh · anyplot.ai",
    toolbar_location=None,
    tools="",
    x_range=(-1.4, 1.4),
    y_range=(-1.4, 1.4),
)

p.annular_wedge(
    x=0,
    y=0,
    inner_radius=0.55,
    outer_radius=1.0,
    start_angle=cumsum("angle", include_zero=True),
    end_angle=cumsum("angle"),
    line_color=PAGE_BG,
    line_width=6,
    fill_color="color",
    legend_field="category",
    source=source,
)

# Percentage labels on each segment (Bokeh: angle 0 = 3 o'clock, CCW)
cumulative_starts = np.cumsum([0.0] + angles[:-1])
for pct, start, ang in zip(percentages, cumulative_starts, angles, strict=True):
    mid = start + ang / 2
    label_radius = 0.78
    x = label_radius * cos(mid)
    y = label_radius * sin(mid)
    p.add_layout(
        Label(
            x=x,
            y=y,
            text=pct,
            text_font_size="44pt",
            text_color="#F0EFE8",
            text_font_style="bold",
            text_align="center",
            text_baseline="middle",
        )
    )

# Center metric
p.add_layout(
    Label(
        x=0,
        y=0.13,
        text="Total budget",
        text_font_size="40pt",
        text_color=INK_SOFT,
        text_align="center",
        text_baseline="middle",
    )
)
p.add_layout(
    Label(
        x=0,
        y=-0.10,
        text=f"${total:,}K",
        text_font_size="96pt",
        text_color=INK,
        text_font_style="bold",
        text_align="center",
        text_baseline="middle",
    )
)

# Style — theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "56pt"
p.title.text_color = INK
p.title.align = "center"
p.title.text_font_style = "normal"

p.axis.visible = False
p.grid.visible = False

p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = None
p.legend.label_text_color = INK_SOFT
p.legend.label_text_font_size = "36pt"
p.legend.location = "top_right"
p.legend.spacing = 18
p.legend.padding = 24
p.legend.glyph_height = 60
p.legend.glyph_width = 60

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)
