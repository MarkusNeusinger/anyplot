""" pyplots.ai
parallel-basic: Basic Parallel Coordinates Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 83/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - Iris dataset for parallel coordinates visualization
# 15 samples per species across 4 dimensions (sepal/petal length/width)
iris_data = {
    "Setosa": [
        [5.1, 3.5, 1.4, 0.2],
        [4.9, 3.0, 1.4, 0.2],
        [4.7, 3.2, 1.3, 0.2],
        [4.6, 3.1, 1.5, 0.2],
        [5.0, 3.6, 1.4, 0.2],
        [5.4, 3.9, 1.7, 0.4],
        [4.6, 3.4, 1.4, 0.3],
        [5.0, 3.4, 1.5, 0.2],
        [4.4, 2.9, 1.4, 0.2],
        [4.9, 3.1, 1.5, 0.1],
        [5.4, 3.7, 1.5, 0.2],
        [4.8, 3.4, 1.6, 0.2],
        [4.8, 3.0, 1.4, 0.1],
        [4.3, 3.0, 1.1, 0.1],
        [5.8, 4.0, 1.2, 0.2],
    ],
    "Versicolor": [
        [7.0, 3.2, 4.7, 1.4],
        [6.4, 3.2, 4.5, 1.5],
        [6.9, 3.1, 4.9, 1.5],
        [5.5, 2.3, 4.0, 1.3],
        [6.5, 2.8, 4.6, 1.5],
        [5.7, 2.8, 4.5, 1.3],
        [6.3, 3.3, 4.7, 1.6],
        [4.9, 2.4, 3.3, 1.0],
        [6.6, 2.9, 4.6, 1.3],
        [5.2, 2.7, 3.9, 1.4],
        [5.0, 2.0, 3.5, 1.0],
        [5.9, 3.0, 4.2, 1.5],
        [6.0, 2.2, 4.0, 1.0],
        [6.1, 2.9, 4.7, 1.4],
        [5.6, 2.9, 3.6, 1.3],
    ],
    "Virginica": [
        [6.3, 3.3, 6.0, 2.5],
        [5.8, 2.7, 5.1, 1.9],
        [7.1, 3.0, 5.9, 2.1],
        [6.3, 2.9, 5.6, 1.8],
        [6.5, 3.0, 5.8, 2.2],
        [7.6, 3.0, 6.6, 2.1],
        [4.9, 2.5, 4.5, 1.7],
        [7.3, 2.9, 6.3, 1.8],
        [6.7, 2.5, 5.8, 1.8],
        [7.2, 3.6, 6.1, 2.5],
        [6.5, 3.2, 5.1, 2.0],
        [6.4, 2.7, 5.3, 1.9],
        [6.8, 3.0, 5.5, 2.1],
        [5.7, 2.5, 5.0, 2.0],
        [5.8, 2.8, 5.1, 2.4],
    ],
}

# Compute min/max for each dimension across all species (for normalization)
all_values = [[row[i] for species in iris_data.values() for row in species] for i in range(4)]
mins = [min(col) for col in all_values]
maxs = [max(col) for col in all_values]

# Species colors - Python Blue, Python Yellow, and complementary teal (colorblind-friendly)
species_colors = {"Setosa": "#306998", "Versicolor": "#FFD43B", "Virginica": "#4ECDC4"}
species_list = list(iris_data.keys())

# Build color list - one color per series added to the chart
# Order: 3 legend entries (mean lines) first, then 45 observation lines grouped by species
color_list = [species_colors[s] for s in species_list]  # 3 mean line colors
for species_name in species_list:  # 45 observation colors (15 per species)
    color_list.extend([species_colors[species_name]] * len(iris_data[species_name]))

# Create custom style for 4800x2700 px output with larger fonts and visible grids
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#888888",  # Darker for better grid visibility
    colors=tuple(color_list),
    title_font_size=84,
    label_font_size=56,
    major_label_font_size=52,
    legend_font_size=52,
    value_font_size=36,
    opacity=0.55,
    opacity_hover=1.0,
    guide_stroke_color="#AAAAAA",  # Explicit grid line color for visibility
    major_guide_stroke_color="#888888",  # Major grid lines more visible
)

# Create line chart to simulate parallel coordinates
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="parallel-basic · pygal · pyplots.ai\nIris Flower Measurements Across Species",
    x_title="Dimensions",
    y_title="Normalized Value (0-1)",
    show_dots=True,
    dots_size=14,
    stroke_style={"width": 3},
    show_y_guides=True,
    show_x_guides=True,
    x_label_rotation=0,
    legend_at_bottom=True,
    legend_box_size=52,
    truncate_legend=-1,
    range=(0, 1),
    margin=150,
    spacing=50,
    margin_right=200,
    show_legend=True,
)

# X-axis labels for dimensions
chart.x_labels = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]

# Add mean lines for each species - these have labels and appear in the legend
# Mean lines are thicker (width=6) to distinguish from individual observations
for species_name in species_list:
    rows = iris_data[species_name]
    mean_row = [sum(row[i] for row in rows) / len(rows) for i in range(4)]
    normalized_mean = [(mean_row[i] - mins[i]) / (maxs[i] - mins[i]) for i in range(4)]
    chart.add(species_name, normalized_mean, stroke_style={"width": 6})

# Add each observation as a separate line without legend entry
for species_name in species_list:
    for row in iris_data[species_name]:
        normalized = [(row[i] - mins[i]) / (maxs[i] - mins[i]) for i in range(4)]
        # Allow interruptions prevents secondary adding to legend
        chart.add(None, normalized, stroke_style={"width": 3}, allow_interruptions=True)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
