""" pyplots.ai
donut-basic: Basic Donut Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

from math import pi

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure
from bokeh.transform import cumsum


# Data - Portfolio allocation by asset class
categories = ["Technology", "Healthcare", "Finance", "Energy", "Retail"]
values = [35, 25, 20, 12, 8]
total = sum(values)

# Calculate angles for donut segments
data = {
    "category": categories,
    "value": values,
    "angle": [v / total * 2 * pi for v in values],
    "percentage": [f"{v / total * 100:.1f}%" for v in values],
}

# Cumulative angles for label positioning
cumulative = np.cumsum([0] + data["angle"][:-1]).tolist()
data["start_angle"] = cumulative
data["end_angle"] = np.cumsum(data["angle"]).tolist()

# Colors - Python Blue as primary, then colorblind-safe palette
colors = ["#306998", "#FFD43B", "#4ECDC4", "#FF6B6B", "#95E1D3"]
data["color"] = colors

source = ColumnDataSource(data=data)

# Create figure (square format for circular chart)
p = figure(
    width=3600,
    height=3600,
    title="donut-basic · bokeh · pyplots.ai",
    toolbar_location=None,
    tools="",
    x_range=(-1.4, 1.8),
    y_range=(-1.3, 1.3),
)

# Draw donut using annular wedge
p.annular_wedge(
    x=0,
    y=0,
    inner_radius=0.45,
    outer_radius=0.95,
    start_angle=cumsum("angle", include_zero=True),
    end_angle=cumsum("angle"),
    line_color="white",
    line_width=4,
    fill_color="color",
    source=source,
)

# Add percentage labels on segments
for pct, start, end, color in zip(data["percentage"], data["start_angle"], data["end_angle"], colors, strict=True):
    mid_angle = (start + end) / 2
    # Position labels at middle of the ring
    label_radius = 0.70
    # Adjust angle to start from top and go clockwise
    x = label_radius * np.cos(mid_angle - pi / 2 + pi)
    y = label_radius * np.sin(mid_angle - pi / 2 + pi)

    # Use white text for dark backgrounds, dark for light backgrounds
    text_color = "white" if color in ["#306998", "#FF6B6B", "#4ECDC4"] else "#333333"

    label = Label(
        x=x,
        y=y,
        text=pct,
        text_font_size="26pt",
        text_color=text_color,
        text_font_style="bold",
        text_align="center",
        text_baseline="middle",
    )
    p.add_layout(label)

# Add center text showing total
center_label = Label(
    x=0, y=0.08, text="Total", text_font_size="32pt", text_color="#555555", text_align="center", text_baseline="middle"
)
p.add_layout(center_label)

center_value = Label(
    x=0,
    y=-0.12,
    text=str(total),
    text_font_size="48pt",
    text_color="#306998",
    text_font_style="bold",
    text_align="center",
    text_baseline="middle",
)
p.add_layout(center_value)

# Add legend entries on the right
legend_x = 1.20
legend_y_start = 0.6
legend_spacing = 0.24

for i, (cat, val, color) in enumerate(zip(categories, values, colors, strict=True)):
    y_pos = legend_y_start - i * legend_spacing
    # Color box
    p.rect(x=legend_x, y=y_pos, width=0.10, height=0.10, fill_color=color, line_color=None)
    # Label text
    legend_label = Label(
        x=legend_x + 0.10,
        y=y_pos,
        text=f"{cat} ({val}%)",
        text_font_size="22pt",
        text_color="#333333",
        text_align="left",
        text_baseline="middle",
    )
    p.add_layout(legend_label)

# Style
p.title.text_font_size = "36pt"
p.title.text_color = "#333333"
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None
p.background_fill_color = None
p.border_fill_color = None

# Save
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
