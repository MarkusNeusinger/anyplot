""" pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 88/100 | Updated: 2026-02-23
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, LabelSet
from bokeh.plotting import figure


np.random.seed(42)

# Data - department budgets (in millions)
categories = [
    "Engineering",
    "Marketing",
    "Sales",
    "Operations",
    "HR",
    "Finance",
    "R&D",
    "Legal",
    "IT",
    "Customer Support",
    "Product",
    "Design",
    "QA",
    "Data Science",
    "Security",
]
values = [45, 32, 38, 25, 12, 18, 42, 8, 22, 15, 28, 14, 10, 20, 6]

# Calculate radii from values (area-scaled for accurate visual perception)
max_radius = 420
radii = np.sqrt(np.array(values, dtype=float)) / np.sqrt(max(values)) * max_radius

# Circle packing via force-directed simulation
n = len(radii)
center_x, center_y = 2400, 1350
x_pos = center_x + (np.random.rand(n) - 0.5) * 1000
y_pos = center_y + (np.random.rand(n) - 0.5) * 600

padding = 12
for _ in range(800):
    for i in range(n):
        dx = center_x - x_pos[i]
        dy = center_y - y_pos[i]
        x_pos[i] += dx * 0.01
        y_pos[i] += dy * 0.01
    for i in range(n):
        for j in range(i + 1, n):
            dx = x_pos[j] - x_pos[i]
            dy = y_pos[j] - y_pos[i]
            dist = np.sqrt(dx**2 + dy**2) + 0.01
            min_dist = radii[i] + radii[j] + padding
            if dist < min_dist:
                overlap = (min_dist - dist) / 2
                x_pos[i] -= dx / dist * overlap
                y_pos[i] -= dy / dist * overlap
                x_pos[j] += dx / dist * overlap
                y_pos[j] += dy / dist * overlap
    for i in range(n):
        x_pos[i] = np.clip(x_pos[i], radii[i] + 100, 4800 - radii[i] - 100)
        y_pos[i] = np.clip(y_pos[i], radii[i] + 100, 2700 - radii[i] - 100)

# Re-center the packed cluster
x_min = min(x_pos[i] - radii[i] for i in range(n))
x_max = max(x_pos[i] + radii[i] for i in range(n))
y_min = min(y_pos[i] - radii[i] for i in range(n))
y_max = max(y_pos[i] + radii[i] for i in range(n))
x_pos += (4800 - (x_min + x_max)) / 2
y_pos += (2700 - (y_min + y_max)) / 2

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="Department Budgets · bubble-packed · bokeh · pyplots.ai",
    x_range=(0, 4800),
    y_range=(0, 2700),
    tools="",
    toolbar_location=None,
)

# Budget tier palette — 4 distinct hue families, colorblind-safe, dark for white text
tier_defs = [
    (">$35M", "#1B4F72", [i for i in range(n) if values[i] > 35]),
    ("$20\u201335M", "#7D6608", [i for i in range(n) if 20 <= values[i] <= 35]),
    ("$10\u201319M", "#A04000", [i for i in range(n) if 10 <= values[i] < 20]),
    ("<$10M", "#6C3483", [i for i in range(n) if values[i] < 10]),
]

# Render circles by tier — each tier is a separate renderer with Bokeh Legend entry
circle_renderers = []
for tier_name, tier_color, tier_idx in tier_defs:
    src = ColumnDataSource(
        data={
            "x": [x_pos[i] for i in tier_idx],
            "y": [y_pos[i] for i in tier_idx],
            "radius": [radii[i] for i in tier_idx],
            "dept": [categories[i] for i in tier_idx],
            "budget": [f"${values[i]}M" for i in tier_idx],
            "tier": [tier_name for _ in tier_idx],
        }
    )
    r = p.circle(
        x="x",
        y="y",
        radius="radius",
        source=src,
        fill_color=tier_color,
        fill_alpha=0.88,
        line_color="white",
        line_width=3,
        legend_label=tier_name,
    )
    circle_renderers.append(r)

# Adaptive labels for ALL circles — font size scales with radius
brackets = [
    (300, float("inf"), "24pt", "20pt", 20),
    (240, 300, "20pt", "17pt", 16),
    (190, 240, "17pt", "14pt", 14),
    (150, 190, "15pt", "13pt", 12),
    (0, 150, "14pt", "12pt", 10),
]
for min_r, max_r, name_font, val_font, y_off in brackets:
    idx = [i for i in range(n) if min_r <= radii[i] < max_r]
    if not idx:
        continue
    src = ColumnDataSource(
        data={
            "x": [x_pos[i] for i in idx],
            "y": [y_pos[i] for i in idx],
            "name": [categories[i] for i in idx],
            "val": [f"${values[i]}M" for i in idx],
        }
    )
    p.add_layout(
        LabelSet(
            x="x",
            y="y",
            text="name",
            source=src,
            text_align="center",
            text_baseline="middle",
            text_font_size=name_font,
            text_color="white",
            text_font_style="bold",
            y_offset=y_off,
        )
    )
    p.add_layout(
        LabelSet(
            x="x",
            y="y",
            text="val",
            source=src,
            text_align="center",
            text_baseline="middle",
            text_font_size=val_font,
            text_color="rgba(255,255,255,0.85)",
            y_offset=-y_off,
        )
    )

# Style
p.title.text_font_size = "36pt"
p.title.align = "center"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.background_fill_color = "#f8f9fa"
p.border_fill_color = "#f8f9fa"
p.outline_line_color = None

# Legend styling — Bokeh Legend with tier-based entries
p.legend.location = "top_right"
p.legend.label_text_font_size = "24pt"
p.legend.glyph_height = 50
p.legend.glyph_width = 50
p.legend.background_fill_alpha = 0.85
p.legend.background_fill_color = "#f8f9fa"
p.legend.border_line_color = "#dee2e6"
p.legend.border_line_width = 2
p.legend.padding = 20
p.legend.spacing = 12
p.legend.label_standoff = 12

# HoverTool — Bokeh-distinctive interactive feature (preserved for HTML output)
hover = HoverTool(
    tooltips=[("Department", "@dept"), ("Budget", "@budget"), ("Tier", "@tier")], renderers=circle_renderers
)
p.add_tools(hover)

# Save
export_png(p, filename="plot.png")
