""" pyplots.ai
pie-basic: Basic Pie Chart
Library: bokeh 3.8.2 | Python 3.14.0
Quality: 90/100 | Created: 2025-12-23
"""

import math

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label, Legend, LegendItem
from bokeh.plotting import figure


# Data - Cloud infrastructure market share (2024)
categories = ["AWS", "Azure", "Google Cloud", "Alibaba", "Others"]
values = [33, 23, 11, 4, 29]

# Compute angles and percentages
total = sum(values)
percentages = [v / total * 100 for v in values]
angles = [v / total * 2 * math.pi for v in values]

# Start/end angles (clockwise from top)
start_angles = []
end_angles = []
current = math.pi / 2
for a in angles:
    start_angles.append(current)
    current -= a
    end_angles.append(current)

mid_angles = [(s + e) / 2 for s, e in zip(start_angles, end_angles, strict=True)]

# Explode the largest slice (AWS) for emphasis
explode_idx = 0
explode_r = 0.06
offsets_x = [0.0] * len(categories)
offsets_y = [0.0] * len(categories)
offsets_x[explode_idx] = explode_r * math.cos(mid_angles[explode_idx])
offsets_y[explode_idx] = explode_r * math.sin(mid_angles[explode_idx])

# Colors - Python Blue first, colorblind-safe palette (no red-green adjacency)
colors = ["#306998", "#FFD43B", "#8E44AD", "#E67E22", "#2980B9"]

# Create figure (3600 x 3600 px square)
radius = 0.88
p = figure(
    width=3600,
    height=3600,
    title="pie-basic · bokeh · pyplots.ai",
    x_range=(-1.3, 1.3),
    y_range=(-1.1, 1.1),
    tools="",
    toolbar_location=None,
)

# Draw wedges using ColumnDataSource for idiomatic bokeh
source = ColumnDataSource(
    data={"x": offsets_x, "y": offsets_y, "start": start_angles, "end": end_angles, "color": colors}
)
renderers = p.wedge(
    x="x",
    y="y",
    radius=radius,
    start_angle="start",
    end_angle="end",
    direction="clock",
    fill_color="color",
    line_color="white",
    line_width=5,
    source=source,
)

# Percentage labels on each slice
label_r = radius * 0.6
for i in range(len(categories)):
    lx = label_r * math.cos(mid_angles[i]) + offsets_x[i]
    ly = label_r * math.sin(mid_angles[i]) + offsets_y[i]
    text_color = "#333333" if colors[i] == "#FFD43B" else "white"
    p.add_layout(
        Label(
            x=lx,
            y=ly,
            text=f"{percentages[i]:.0f}%",
            text_font_size="36pt",
            text_color=text_color,
            text_font_style="bold",
            text_align="center",
            text_baseline="middle",
        )
    )

# Annotation: callout for AWS as market leader
aws_callout_angle = mid_angles[0]
aws_callout_r = radius + 0.18
p.add_layout(
    Label(
        x=aws_callout_r * math.cos(aws_callout_angle) + offsets_x[0],
        y=aws_callout_r * math.sin(aws_callout_angle) + offsets_y[0],
        text="▲ Market Leader",
        text_font_size="24pt",
        text_color="#306998",
        text_font_style="bold",
        text_align="center",
        text_baseline="bottom",
    )
)

# Annotation: callout for 'Others' being surprisingly large
others_callout_angle = mid_angles[4]
others_callout_r = radius + 0.16
p.add_layout(
    Label(
        x=others_callout_r * math.cos(others_callout_angle) + offsets_x[4],
        y=others_callout_r * math.sin(others_callout_angle) + offsets_y[4],
        text="Long-tail rivals ≈ Azure",
        text_font_size="22pt",
        text_color="#666666",
        text_font_style="italic",
        text_align="center",
        text_baseline="top",
    )
)

# Subtitle annotation for context
p.add_layout(
    Label(
        x=0,
        y=-1.0,
        text="Top 4 providers control 71% of the $280B global cloud market",
        text_font_size="22pt",
        text_color="#777777",
        text_align="center",
        text_baseline="top",
    )
)

# Legend with category names and percentages
legend_items = [
    LegendItem(label=f"{categories[i]} ({percentages[i]:.0f}%)", renderers=[renderers], index=i)
    for i in range(len(categories))
]
legend = Legend(
    items=legend_items,
    location="center",
    orientation="horizontal",
    label_text_font_size="28pt",
    glyph_width=45,
    glyph_height=45,
    spacing=40,
    padding=20,
    background_fill_alpha=0.0,
    border_line_color=None,
)
p.add_layout(legend, "below")

# Styling
p.title.text_font_size = "40pt"
p.title.align = "center"
p.title.text_color = "#2C3E50"
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None
p.background_fill_color = "#FAFBFC"
p.border_fill_color = "#FAFBFC"
p.min_border_top = 20
p.min_border_bottom = 10

# Save
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
