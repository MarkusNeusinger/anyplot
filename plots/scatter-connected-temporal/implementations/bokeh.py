"""pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-13
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Label, LinearColorMapper
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

# Temporal index for color gradient
time_index = np.arange(n, dtype=float)

source = ColumnDataSource(
    data={"unemployment": unemployment, "inflation": inflation, "year": years.astype(str), "time_index": time_index}
)

# Color mapper for temporal gradient (light blue to deep navy)
color_mapper = LinearColorMapper(
    palette=["#a8c8e8", "#7bafd4", "#5296c0", "#306998", "#1d4f72", "#0e3555"], low=0, high=n - 1
)

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

# Connecting lines between consecutive points (temporal path)
for i in range(n - 1):
    frac = i / (n - 1)
    alpha = 0.3 + 0.5 * frac
    line_source = ColumnDataSource(
        data={"x": [unemployment[i], unemployment[i + 1]], "y": [inflation[i], inflation[i + 1]]}
    )
    color_idx = int(frac * 5)
    colors = ["#a8c8e8", "#7bafd4", "#5296c0", "#306998", "#1d4f72", "#0e3555"]
    p.line(x="x", y="y", source=line_source, line_width=4, line_color=colors[color_idx], line_alpha=alpha)

# Scatter points with temporal color gradient
p.scatter(
    x="unemployment",
    y="inflation",
    source=source,
    size=30,
    color=transform("time_index", color_mapper),
    alpha=0.9,
    line_color="white",
    line_width=2,
)

# Annotate key time points
annotations = {
    0: ("1990 ▸", -100, 15),
    9: ("1999", -20, 18),
    19: ("2009", 15, -25),
    25: ("2015", 15, 12),
    30: ("2020", 15, -18),
    32: ("2022", 15, 18),
    33: ("◂ 2023", 30, -10),
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
