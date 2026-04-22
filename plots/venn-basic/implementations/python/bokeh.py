""" pyplots.ai
venn-basic: Venn Diagram
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-29
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import HoverTool, Label
from bokeh.plotting import figure, output_file, save


# Data - Three sets representing product feature categories
set_labels = ["Product A", "Product B", "Product C"]
set_sizes = [100, 80, 60]  # Total sizes
# Overlaps: AB=30, AC=20, BC=25, ABC=10
only_a = 100 - 30 - 20 + 10  # 60
only_b = 80 - 30 - 25 + 10  # 35
only_c = 60 - 20 - 25 + 10  # 25
only_ab = 30 - 10  # 20
only_ac = 20 - 10  # 10
only_bc = 25 - 10  # 15
abc = 10

# Circle parameters for 3-set Venn diagram
radius = 0.35
centers = [
    (-0.2, 0.15),  # A - top left
    (0.2, 0.15),  # B - top right
    (0.0, -0.2),  # C - bottom center
]

# Create figure with proper sizing and hover tool
p = figure(
    width=4800,
    height=2700,
    title="venn-basic · bokeh · pyplots.ai",
    x_range=(-1, 1),
    y_range=(-0.8, 0.8),
    tools="hover",
    toolbar_location=None,
)

# Colors with transparency
colors = ["#306998", "#FFD43B", "#4DAF4A"]  # Python Blue, Python Yellow, Green
alpha = 0.4

# Generate circle points inline (KISS - no helper function)
n_points = 100
theta = np.linspace(0, 2 * np.pi, n_points)

# Draw the three circles as patches with hover tooltips
for i, (cx, cy) in enumerate(centers):
    x_pts = (cx + radius * np.cos(theta)).tolist()
    y_pts = (cy + radius * np.sin(theta)).tolist()
    p.patch(
        x_pts,
        y_pts,
        fill_color=colors[i],
        fill_alpha=alpha,
        line_color=colors[i],
        line_width=4,
        line_alpha=0.8,
        name=f"set_{i}",
    )

# Configure hover tool for interactivity
hover = p.select({"type": HoverTool})
hover.tooltips = [("Set", "@name"), ("Region", "Hover over numbers for details")]
hover.mode = "mouse"

# Add set labels with total sizes outside circles
label_positions = [
    (-0.55, 0.50, set_labels[0], f"n={set_sizes[0]}"),  # A - top left
    (0.55, 0.50, set_labels[1], f"n={set_sizes[1]}"),  # B - top right
    (0.0, -0.62, set_labels[2], f"n={set_sizes[2]}"),  # C - bottom
]

for lx, ly, text, size_text in label_positions:
    label = Label(
        x=lx,
        y=ly,
        text=text,
        text_font_size="32pt",
        text_font_style="bold",
        text_align="center",
        text_baseline="middle",
        text_color="#333333",
    )
    p.add_layout(label)
    # Add set size below the label
    size_label = Label(
        x=lx,
        y=ly - 0.08,
        text=size_text,
        text_font_size="24pt",
        text_align="center",
        text_baseline="middle",
        text_color="#666666",
    )
    p.add_layout(size_label)

# Add region counts
# Positions for each region (calculated manually for clarity)
region_labels = [
    # (x, y, count, description)
    (-0.35, 0.25, str(only_a), "Only A"),  # Only A
    (0.35, 0.25, str(only_b), "Only B"),  # Only B
    (0.0, -0.38, str(only_c), "Only C"),  # Only C
    (0.0, 0.28, str(only_ab), "A∩B"),  # A ∩ B only
    (-0.18, -0.08, str(only_ac), "A∩C"),  # A ∩ C only
    (0.18, -0.08, str(only_bc), "B∩C"),  # B ∩ C only
    (0.0, 0.05, str(abc), "A∩B∩C"),  # A ∩ B ∩ C
]

for rx, ry, count, _desc in region_labels:
    count_label = Label(
        x=rx,
        y=ry,
        text=count,
        text_font_size="36pt",
        text_font_style="bold",
        text_align="center",
        text_baseline="middle",
        text_color="#222222",
    )
    p.add_layout(count_label)

# Style the figure - larger title for 4800x2700 canvas
p.title.text_font_size = "48pt"
p.title.align = "center"

# Remove axes for cleaner look (Venn diagrams don't need axes)
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

# Set background
p.background_fill_color = "white"
p.border_fill_color = "white"

# Save as PNG and HTML
export_png(p, filename="plot.png")
output_file("plot.html", title="venn-basic · bokeh · pyplots.ai")
save(p)
