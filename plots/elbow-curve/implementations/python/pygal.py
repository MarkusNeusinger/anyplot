""" pyplots.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import pygal
from pygal.style import Style


# Simulated K-means inertia data showing clear elbow at k=4
# Represents clustering analysis on customer segmentation dataset
k_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
inertias = [4200, 2100, 1200, 680, 580, 510, 460, 420, 390, 365]

# Custom style for pyplots
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#E74C3C"),
    title_font_size=48,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=32,
    value_font_size=24,
    stroke_width=4,
    value_label_font_size=24,
    tooltip_font_size=24,
)

# Create XY chart for line plot with markers
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="elbow-curve · pygal · pyplots.ai",
    x_title="Number of Clusters (k)",
    y_title="Inertia (Within-cluster Sum of Squares)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    show_x_guides=False,
    show_y_guides=True,
    dots_size=12,
    stroke_style={"width": 4, "linecap": "round", "linejoin": "round"},
    truncate_legend=-1,
    x_labels=k_values,
    range=(0, max(inertias) * 1.05),
    include_x_axis=True,
    explicit_size=True,
    margin=50,
    spacing=30,
)

# Prepare data as (x, y) tuples
elbow_data = [(k, inertia) for k, inertia in zip(k_values, inertias, strict=True)]

# Add elbow curve data
chart.add("Inertia", elbow_data, stroke_style={"width": 4})

# Highlight optimal elbow point (k=4 based on the generated data)
elbow_k = 4
elbow_inertia = inertias[elbow_k - 1]
chart.add("Optimal k", [(elbow_k, elbow_inertia)], dots_size=20)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
