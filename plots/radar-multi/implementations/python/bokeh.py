""" pyplots.ai
radar-multi: Multi-Series Radar Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, LabelSet, Legend
from bokeh.plotting import figure


# Data - Product comparison across 6 attributes
categories = ["Performance", "Reliability", "Features", "Support", "Price Value", "Ease of Use"]
n_categories = len(categories)

# Three products to compare
products = {
    "Product A": [85, 90, 75, 80, 70, 88],
    "Product B": [70, 75, 95, 85, 80, 72],
    "Product C": [92, 65, 80, 70, 95, 78],
}

# Colors - Python Blue, Python Yellow, and a complementary color
colors = ["#306998", "#FFD43B", "#E57373"]
fill_alphas = [0.25, 0.25, 0.25]

# Calculate angles for each axis (starting from top, going clockwise)
angles = np.linspace(0, 2 * np.pi, n_categories, endpoint=False)
# Rotate to start from top (90 degrees offset)
angles = angles + np.pi / 2

# Create figure with square aspect for radar chart
p = figure(
    width=3600,
    height=3600,
    title="radar-multi · bokeh · pyplots.ai",
    x_range=(-145, 145),
    y_range=(-145, 145),
    tools="",
    toolbar_location=None,
)

# Remove axes and grid for clean radar look
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None

# Draw circular gridlines at 20, 40, 60, 80, 100
grid_values = [20, 40, 60, 80, 100]
for gv in grid_values:
    theta = np.linspace(0, 2 * np.pi, 100)
    x_grid = gv * np.cos(theta)
    y_grid = gv * np.sin(theta)
    p.line(x_grid, y_grid, line_color="#CCCCCC", line_width=2, line_alpha=0.6)

# Draw radial lines from center to each axis
for angle in angles:
    x_line = [0, 105 * np.cos(angle)]
    y_line = [0, 105 * np.sin(angle)]
    p.line(x_line, y_line, line_color="#AAAAAA", line_width=2, line_alpha=0.6)

# Add axis labels at the outer edge
label_radius = 120
label_x = [label_radius * np.cos(a) for a in angles]
label_y = [label_radius * np.sin(a) for a in angles]
label_source = ColumnDataSource(data={"x": label_x, "y": label_y, "text": categories})
labels = LabelSet(
    x="x",
    y="y",
    text="text",
    source=label_source,
    text_font_size="28pt",
    text_align="center",
    text_baseline="middle",
    text_color="#333333",
    text_font_style="bold",
)
p.add_layout(labels)

# Add grid value labels on one axis (shifted for visibility)
for gv in grid_values:
    p.text(
        x=[gv * np.cos(angles[0]) + 8],
        y=[gv * np.sin(angles[0]) + 8],
        text=[str(gv)],
        text_font_size="18pt",
        text_color="#555555",
        text_alpha=0.9,
    )

# Plot each product series
legend_items = []
for idx, (product_name, values) in enumerate(products.items()):
    # Convert values to x, y coordinates
    x_vals = [v * np.cos(a) for v, a in zip(values, angles, strict=True)]
    y_vals = [v * np.sin(a) for v, a in zip(values, angles, strict=True)]

    # Close the polygon
    x_vals.append(x_vals[0])
    y_vals.append(y_vals[0])

    # Draw filled polygon
    fill_renderer = p.patch(
        x_vals,
        y_vals,
        fill_color=colors[idx],
        fill_alpha=fill_alphas[idx],
        line_color=colors[idx],
        line_width=4,
        line_alpha=0.9,
    )

    # Draw points at vertices
    p.scatter(x_vals[:-1], y_vals[:-1], size=22, fill_color=colors[idx], line_color="white", line_width=3, alpha=0.9)

    legend_items.append((product_name, [fill_renderer]))

# Add legend
legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="24pt",
    glyph_height=40,
    glyph_width=40,
    spacing=20,
    padding=25,
    background_fill_alpha=0.85,
    border_line_color="#CCCCCC",
)
p.add_layout(legend, "right")

# Style title
p.title.text_font_size = "36pt"
p.title.align = "center"
p.title.text_color = "#333333"

# Save outputs
export_png(p, filename="plot.png")

# Also save HTML for interactivity
output_file("plot.html", title="radar-multi · bokeh · pyplots.ai")
save(p)
