""" pyplots.ai
box-horizontal: Horizontal Box Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 68/100 | Created: 2025-12-30
"""

import numpy as np
import pygal
from pygal.style import Style


# Create HorizontalBox dynamically (pygal doesn't include it natively)
# This uses pygal's standard mixin pattern for horizontal chart variants
HorizontalBox = type("HorizontalBox", (pygal.graph.horizontal.HorizontalGraph, pygal.graph.box.Box), {})

# Data - Response times for different service types (in milliseconds)
np.random.seed(42)
categories = ["Database Query", "API Gateway", "Authentication", "File Upload", "Image Processing"]
data = {
    "Database Query": np.random.lognormal(3.5, 0.6, 80),
    "API Gateway": np.random.lognormal(3.2, 0.4, 80),
    "Authentication": np.random.lognormal(3.8, 0.5, 80),
    "File Upload": np.random.lognormal(4.2, 0.7, 80),
    "Image Processing": np.random.lognormal(4.5, 0.6, 80),
}

# Add outliers with more moderate values to avoid excessive whitespace
data["Database Query"] = np.append(data["Database Query"], [180, 220, 280])
data["File Upload"] = np.append(data["File Upload"], [350, 420])
data["Image Processing"] = np.append(data["Image Processing"], [450, 520, 580])

# Custom style using PyPlots colors - scaled for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#4CAF50", "#FF5722", "#9C27B0"),
    title_font_size=60,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=36,
    value_font_size=32,
)

# Create horizontal box chart with category labels displayed on y-axis
chart = HorizontalBox(
    width=4800,
    height=2700,
    style=custom_style,
    title="box-horizontal · pygal · pyplots.ai",
    x_title="Response Time (ms)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=30,
    show_y_guides=True,
    show_x_guides=False,
    margin=50,
    margin_left=400,
    margin_bottom=200,
    spacing=60,
    box_mode="tukey",
    truncate_label=-1,
    truncate_legend=-1,
    dots_size=8,
)

# Set category labels on y-axis (in horizontal mode, x_labels display on the y-axis)
chart.x_labels = categories

# Add data for each category (legend entries match the x_labels for cross-referencing)
for category in categories:
    chart.add(category, data[category].tolist())

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
