""" pyplots.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-04
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Arrow, ColumnDataSource, Label, Legend, LegendItem, NormalHead, Range1d, Span
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

# Color palette — colorblind-safe, high contrast on white background
color_map = {"5th Root of Unity": "#306998", "Arbitrary": "#D4762C", "Conjugate Pair": "#2AA198", "Product": "#C4386B"}

# Marker sizes — visual hierarchy: roots of unity are the focal point
size_map = {"5th Root of Unity": 28, "Arbitrary": 20, "Conjugate Pair": 24, "Product": 26}

colors = [color_map[c] for c in categories]

# Plot
p = figure(
    width=3600,
    height=3600,
    title="scatter-complex-plane · bokeh · pyplots.ai",
    x_axis_label="Real Axis",
    y_axis_label="Imaginary Axis",
    match_aspect=True,
    tools="pan,wheel_zoom,box_zoom,reset,hover,save",
)

p.x_range = Range1d(-3.8, 3.8)
p.y_range = Range1d(-3.8, 3.8)

# Unit circle
theta = np.linspace(0, 2 * np.pi, 200)
circle_x = np.cos(theta)
circle_y = np.sin(theta)
unit_circle_renderer = p.line(
    circle_x.tolist(), circle_y.tolist(), line_color="#999999", line_dash="dashed", line_width=3, line_alpha=0.5
)

# Axes through origin — subtle but visible
origin_x = Span(location=0, dimension="width", line_color="#555555", line_width=2, line_alpha=0.7)
origin_y = Span(location=0, dimension="height", line_color="#555555", line_width=2, line_alpha=0.7)
p.add_layout(origin_x)
p.add_layout(origin_y)

# Vectors from origin to each point — alpha varies by category for hierarchy
alpha_map = {"5th Root of Unity": 0.7, "Arbitrary": 0.5, "Conjugate Pair": 0.6, "Product": 0.65}
for i, (rx, iy) in enumerate(zip(real_parts, imag_parts, strict=True)):
    cat = categories[i]
    p.add_layout(
        Arrow(
            end=NormalHead(size=18, fill_color=colors[i], line_color=colors[i]),
            x_start=0,
            y_start=0,
            x_end=rx,
            y_end=iy,
            line_color=colors[i],
            line_width=2.5,
            line_alpha=alpha_map[cat],
        )
    )

# Scatter points by category with hover tooltips
legend_items = []
for cat, color in color_map.items():
    idx = [i for i, c in enumerate(categories) if c == cat]
    src = ColumnDataSource(
        data={
            "x": [real_parts[i] for i in idx],
            "y": [imag_parts[i] for i in idx],
            "label": [labels[i] for i in idx],
            "category": [cat] * len(idx),
            "magnitude": [abs(all_points[i]) for i in idx],
            "angle_deg": [np.degrees(np.angle(all_points[i])) for i in idx],
        }
    )
    r = p.scatter(
        x="x", y="y", source=src, size=size_map[cat], color=color, line_color="white", line_width=2.5, alpha=0.95
    )
    legend_items.append(LegendItem(label=cat, renderers=[r]))

# Smart label placement — offset based on angle from origin to avoid overlap
for i, (rx, iy, lbl) in enumerate(zip(real_parts, imag_parts, labels, strict=True)):
    angle = np.arctan2(iy, rx)
    cat = categories[i]
    # Larger radial offset for roots of unity (clustered near origin on unit circle)
    dist = 28 if cat == "5th Root of Unity" else 22
    # Position label radially outward from origin
    ox = dist * np.cos(angle)
    oy = dist * np.sin(angle)
    # Adjust for readability: labels in left half shift further left
    if rx < -0.5:
        ox -= 10
    if abs(iy) < 0.5 and rx > 0:
        oy += 14
    # Extra nudge for bottom roots of unity to avoid crowding
    if cat == "5th Root of Unity" and iy < -0.3:
        oy -= 12
    p.add_layout(
        Label(
            x=rx,
            y=iy,
            text=lbl,
            x_offset=ox,
            y_offset=oy,
            text_font_size="20pt",
            text_color="#333333",
            text_font_style="normal",
        )
    )

# Legend — inside plot area, clean styling
unit_circle_item = LegendItem(label="Unit Circle", renderers=[unit_circle_renderer])
legend = Legend(
    items=[unit_circle_item] + legend_items,
    location="top_left",
    label_text_font_size="22pt",
    glyph_width=40,
    glyph_height=40,
    spacing=12,
    padding=20,
    margin=20,
    background_fill_alpha=0.9,
    background_fill_color="white",
    border_line_color=None,
)
p.add_layout(legend)

# Style — publication-quality refinement with larger fonts for 3600×3600
p.title.text_font_size = "38pt"
p.title.text_font_style = "normal"
p.title.text_color = "#222222"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"
p.xaxis.major_label_text_color = "#666666"
p.yaxis.major_label_text_color = "#666666"

# Clean axis styling — subtle lines, no minor ticks
p.xaxis.axis_line_color = "#aaaaaa"
p.yaxis.axis_line_color = "#aaaaaa"
p.xaxis.axis_line_width = 1
p.yaxis.axis_line_width = 1
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = "#aaaaaa"
p.yaxis.major_tick_line_color = "#aaaaaa"

# Grid — subtle, solid thin lines
p.grid.grid_line_alpha = 0.15
p.grid.grid_line_dash = "solid"
p.grid.grid_line_color = "#999999"
p.outline_line_color = None
p.background_fill_color = "#ffffff"
p.border_fill_color = "#ffffff"

# Hover tooltips — distinctive Bokeh feature
p.hover.tooltips = [
    ("Point", "@label"),
    ("Category", "@category"),
    ("|z|", "@magnitude{0.00}"),
    ("arg(z)", "@angle_deg{0.0}°"),
]
p.hover.mode = "mouse"

# Toolbar — visible for Bokeh interactivity
p.toolbar_location = "right"
p.toolbar.autohide = True

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Complex Plane · Argand Diagram")
