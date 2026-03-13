"""pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-13
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, Label, LinearColorMapper, NumeralTickFormatter
from bokeh.palettes import Blues256, linear_palette
from bokeh.plotting import figure
from bokeh.transform import transform


# Data - US unemployment rate vs inflation rate (1990-2023, stylized)
np.random.seed(42)
years = np.arange(1990, 2024)
n = len(years)

# Stylized Phillips curve dynamics with realistic patterns
unemployment = np.array(
    [
        5.6,
        6.8,
        7.5,
        6.9,
        6.1,
        5.6,
        5.4,
        4.9,
        4.5,
        4.2,  # 1990s recovery
        4.0,
        4.7,
        5.8,
        6.0,
        5.5,
        5.1,
        4.6,
        4.6,
        5.8,
        9.3,  # 2000s + GFC
        9.6,
        8.9,
        8.1,
        7.4,
        6.2,
        5.3,
        4.9,
        4.4,
        3.9,
        3.7,  # 2010s recovery
        8.1,
        5.4,
        3.6,
        3.6,  # COVID + recovery
    ]
)

inflation = np.array(
    [
        5.4,
        4.2,
        3.0,
        3.0,
        2.6,
        2.8,
        3.0,
        2.3,
        1.6,
        2.2,  # 1990s
        3.4,
        2.8,
        1.6,
        2.3,
        2.7,
        3.4,
        3.2,
        2.8,
        3.8,
        -0.4,  # 2000s
        1.6,
        3.2,
        2.1,
        1.5,
        1.6,
        0.1,
        1.3,
        2.1,
        2.4,
        1.8,  # 2010s
        1.2,
        4.7,
        8.0,
        4.1,  # 2020s
    ]
)

# Single shared palette for both lines and scatter points
palette = list(reversed(linear_palette(Blues256, n)))

source = ColumnDataSource(data={"unemployment": unemployment, "inflation": inflation, "year_val": years.astype(float)})

# Color mapper using actual year values so ColorBar displays years
color_mapper = LinearColorMapper(palette=palette, low=1990, high=2023)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="US Phillips Curve Dynamics (1990-2023) · scatter-connected-temporal · bokeh · pyplots.ai",
    x_axis_label="Unemployment Rate (%)",
    y_axis_label="Inflation Rate (%)",
    toolbar_location=None,
    x_range=(2.5, 11.0),
    y_range=(-1.5, 9.5),
)

# Connecting lines using multi_line (idiomatic Bokeh)
xs = [[unemployment[i], unemployment[i + 1]] for i in range(n - 1)]
ys = [[inflation[i], inflation[i + 1]] for i in range(n - 1)]
line_colors = [palette[i] for i in range(n - 1)]
line_alphas = [0.5 + 0.5 * (i / (n - 2)) for i in range(n - 1)]

line_source = ColumnDataSource(data={"xs": xs, "ys": ys, "colors": line_colors, "alphas": line_alphas})
p.multi_line(xs="xs", ys="ys", source=line_source, line_width=5, line_color="colors", line_alpha="alphas")

# Scatter points with temporal color gradient
p.scatter(
    x="unemployment",
    y="inflation",
    source=source,
    size=30,
    color=transform("year_val", color_mapper),
    alpha=0.9,
    line_color="white",
    line_width=3,
)

# ColorBar showing year-to-color mapping
color_bar = ColorBar(
    color_mapper=color_mapper,
    location=(0, 0),
    title="Year",
    title_text_font_size="28pt",
    title_text_color="#444444",
    major_label_text_font_size="24pt",
    major_label_text_color="#555555",
    label_standoff=16,
    width=40,
    padding=30,
    formatter=NumeralTickFormatter(format="0"),
    major_tick_line_color=None,
    bar_line_color=None,
    ticker=BasicTicker(desired_num_ticks=5),
)
p.add_layout(color_bar, "right")

# Annotate key time points
annotations = {
    0: ("1990 \u25b8", -100, 15),
    9: ("1999", -20, 18),
    19: ("2009", 15, -25),
    25: ("2015", 15, 12),
    30: ("2020", 15, -18),
    32: ("2022", 15, 18),
    33: ("\u25c2 2023", 30, -10),
}

for idx, (label_text, x_offset, y_offset) in annotations.items():
    label = Label(
        x=unemployment[idx],
        y=inflation[idx],
        text=label_text,
        text_font_size="32pt",
        text_color="#333333",
        text_font_style="bold",
        x_offset=x_offset,
        y_offset=y_offset,
    )
    p.add_layout(label)

# Title styling
p.title.text_font_size = "56pt"
p.title.text_color = "#333333"

# Axis styling
p.xaxis.axis_label_text_font_size = "48pt"
p.yaxis.axis_label_text_font_size = "48pt"
p.xaxis.major_label_text_font_size = "36pt"
p.yaxis.major_label_text_font_size = "36pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

# Clean axis styling
p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Grid
p.grid.grid_line_alpha = 0.15
p.grid.grid_line_width = 2
p.grid.grid_line_color = "#888888"

# Background
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "white"
p.outline_line_color = None

# Save
export_png(p, filename="plot.png")
