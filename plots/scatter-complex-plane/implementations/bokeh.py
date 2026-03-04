"""pyplots.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-04
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Arrow, ColumnDataSource, Label, Legend, NormalHead, Range1d, Span
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data
roots_of_unity = [np.exp(2j * np.pi * k / 5) for k in range(5)]
arbitrary_points = [2.5 + 1.5j, -1.8 + 2.2j, 1.2 - 2.0j, -2.3 - 1.0j, 3.0 + 0j, 0 + 2.8j]
conjugate_pair = [1.5 + 2j, 1.5 - 2j]
product_point = [(1.5 + 2j) * np.exp(1j * np.pi / 4)]

all_points = roots_of_unity + arbitrary_points + conjugate_pair + product_point
categories = ["5th Root of Unity"] * 5 + ["Arbitrary"] * 6 + ["Conjugate Pair"] * 2 + ["Product"] * 1

real_parts = [z.real for z in all_points]
imag_parts = [z.imag for z in all_points]

labels = []
for z in all_points:
    r_part = f"{z.real:.2f}".rstrip("0").rstrip(".")
    i_part = f"{z.imag:.2f}".rstrip("0").rstrip(".")
    if z.imag == 0:
        labels.append(f"{r_part}")
    elif z.real == 0:
        labels.append(f"{i_part}i")
    elif z.imag > 0:
        labels.append(f"{r_part}+{i_part}i")
    else:
        labels.append(f"{r_part}{i_part}i")

# Color palette
color_map = {"5th Root of Unity": "#306998", "Arbitrary": "#FFD43B", "Conjugate Pair": "#2AA198", "Product": "#E85D75"}
colors = [color_map[c] for c in categories]

# Plot
p = figure(
    width=3600,
    height=3600,
    title="scatter-complex-plane · bokeh · pyplots.ai",
    x_axis_label="Real Axis",
    y_axis_label="Imaginary Axis",
    match_aspect=True,
    tools="pan,wheel_zoom,box_zoom,reset,hover",
    toolbar_location=None,
)

p.x_range = Range1d(-3.8, 3.8)
p.y_range = Range1d(-3.8, 3.8)

# Unit circle
theta = np.linspace(0, 2 * np.pi, 200)
circle_x = np.cos(theta)
circle_y = np.sin(theta)
unit_circle_renderer = p.line(
    circle_x.tolist(), circle_y.tolist(), line_color="#888888", line_dash="dashed", line_width=3, line_alpha=0.6
)

# Axes through origin
origin_x = Span(location=0, dimension="width", line_color="#444444", line_width=2)
origin_y = Span(location=0, dimension="height", line_color="#444444", line_width=2)
p.add_layout(origin_x)
p.add_layout(origin_y)

# Vectors from origin to each point
for i, (rx, iy) in enumerate(zip(real_parts, imag_parts, strict=True)):
    p.add_layout(
        Arrow(
            end=NormalHead(size=16, fill_color=colors[i], line_color=colors[i]),
            x_start=0,
            y_start=0,
            x_end=rx,
            y_end=iy,
            line_color=colors[i],
            line_width=2.5,
            line_alpha=0.5,
        )
    )

# Scatter points by category
renderers = {}
for cat, color in color_map.items():
    idx = [i for i, c in enumerate(categories) if c == cat]
    src = ColumnDataSource(
        data={"x": [real_parts[i] for i in idx], "y": [imag_parts[i] for i in idx], "label": [labels[i] for i in idx]}
    )
    r = p.scatter(x="x", y="y", source=src, size=22, color=color, line_color="white", line_width=2.5, alpha=0.9)
    renderers[cat] = r

# Annotations
for rx, iy, lbl in zip(real_parts, imag_parts, labels, strict=True):
    offset_x = 12
    offset_y = 12
    p.add_layout(
        Label(
            x=rx,
            y=iy,
            text=lbl,
            x_offset=offset_x,
            y_offset=offset_y,
            text_font_size="16pt",
            text_color="#333333",
            text_font_style="normal",
        )
    )

# Legend
legend = Legend(
    items=[
        ("Unit Circle", [unit_circle_renderer]),
        ("5th Roots of Unity", [renderers["5th Root of Unity"]]),
        ("Arbitrary Points", [renderers["Arbitrary"]]),
        ("Conjugate Pair", [renderers["Conjugate Pair"]]),
        ("Product z·e^(iπ/4)", [renderers["Product"]]),
    ],
    location="top_left",
    label_text_font_size="22pt",
    glyph_width=40,
    glyph_height=40,
    spacing=15,
    padding=20,
    background_fill_alpha=0.85,
    background_fill_color="white",
    border_line_color="#cccccc",
    border_line_width=2,
)
p.add_layout(legend, "above")

# Style
p.title.text_font_size = "32pt"
p.title.text_font_style = "normal"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.grid.grid_line_alpha = 0.2
p.grid.grid_line_dash = [6, 4]
p.outline_line_width = 0
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

p.hover.tooltips = [("Point", "@label"), ("Real", "@x{0.00}"), ("Imaginary", "@y{0.00}")]

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Complex Plane · Argand Diagram")
