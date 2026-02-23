""" pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 83/100 | Updated: 2026-02-23
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, LabelSet
from bokeh.plotting import figure


# Data - department budgets (in millions)
np.random.seed(42)
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

# Calculate radii from values (scale by area for accurate perception)
max_radius = 380
radii = np.sqrt(values) / np.sqrt(max(values)) * max_radius

# Circle packing simulation - position circles without overlap
n = len(radii)
center_x, center_y = 2400, 1400

# Start with random positions near center
x_pos = center_x + (np.random.rand(n) - 0.5) * 1000
y_pos = center_y + (np.random.rand(n) - 0.5) * 600

# Force-directed packing iterations
padding = 10
margin = 100
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

    # Keep circles inside canvas bounds
    for i in range(n):
        x_pos[i] = np.clip(x_pos[i], radii[i] + margin, 4800 - radii[i] - margin)
        y_pos[i] = np.clip(y_pos[i], radii[i] + margin, 2700 - radii[i] - margin)

# Re-center the packed group within the canvas
x_min = min(x_pos[i] - radii[i] for i in range(n))
x_max = max(x_pos[i] + radii[i] for i in range(n))
y_min = min(y_pos[i] - radii[i] for i in range(n))
y_max = max(y_pos[i] + radii[i] for i in range(n))
x_shift = (4800 - (x_min + x_max)) / 2
y_shift = (2700 - (y_min + y_max)) / 2
x_pos += x_shift
y_pos += y_shift

# Color palette - cohesive blues/teals, all dark enough for white text
palette = [
    "#306998",
    "#2A5F8F",
    "#1B4F72",
    "#1A5276",
    "#2E86C1",
    "#21618C",
    "#2874A6",
    "#1F618D",
    "#2980B9",
    "#1B6B93",
    "#1C6EA4",
    "#256D85",
    "#2471A3",
    "#1A5276",
    "#154360",
]
# Sort indices by value descending so largest bubbles get most distinct colors
sorted_idx = np.argsort(values)[::-1]
colors = [""] * n
for rank, idx in enumerate(sorted_idx):
    colors[idx] = palette[rank]

# Prepare data source
source = ColumnDataSource(
    data={
        "x": x_pos,
        "y": y_pos,
        "radius": radii,
        "category": categories,
        "value": values,
        "color": colors,
        "budget_text": [f"${v}M" for v in values],
    }
)

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

# Add hover tool with formatted tooltips
hover = HoverTool(tooltips=[("Department", "@category"), ("Budget", "@budget_text")])
p.add_tools(hover)

# Draw circles
p.circle(
    x="x", y="y", radius="radius", source=source, fill_color="color", fill_alpha=0.88, line_color="white", line_width=3
)

# Add labels to circles (only for larger circles)
large_indices = [i for i in range(n) if radii[i] > 200]
label_source = ColumnDataSource(
    data={
        "x": [x_pos[i] for i in large_indices],
        "y": [y_pos[i] for i in large_indices],
        "text": [categories[i] for i in large_indices],
        "value_text": [f"${values[i]}M" for i in large_indices],
    }
)

labels = LabelSet(
    x="x",
    y="y",
    text="text",
    source=label_source,
    text_align="center",
    text_baseline="middle",
    text_font_size="24pt",
    text_color="white",
    text_font_style="bold",
    y_offset=15,
)
p.add_layout(labels)

value_labels = LabelSet(
    x="x",
    y="y",
    text="value_text",
    source=label_source,
    text_align="center",
    text_baseline="middle",
    text_font_size="20pt",
    text_color="rgba(255, 255, 255, 0.85)",
    y_offset=-20,
)
p.add_layout(value_labels)

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

# Save
export_png(p, filename="plot.png")
