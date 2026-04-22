""" pyplots.ai
box-grouped: Grouped Box Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 85/100 | Created: 2025-12-25
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Employee performance scores across departments and experience levels
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales"]
experience_levels = ["Junior", "Senior", "Lead"]

# Generate performance distributions with realistic differences
data = {}
# Engineering: Higher scores overall, tight distributions
data[("Engineering", "Junior")] = np.random.normal(72, 8, 50)
data[("Engineering", "Senior")] = np.random.normal(82, 6, 50)
data[("Engineering", "Lead")] = np.random.normal(88, 5, 50)

# Marketing: More variability
data[("Marketing", "Junior")] = np.random.normal(68, 12, 50)
data[("Marketing", "Senior")] = np.random.normal(76, 10, 50)
data[("Marketing", "Lead")] = np.random.normal(84, 8, 50)

# Sales: Widest distributions with outliers
data[("Sales", "Junior")] = np.random.normal(65, 15, 50)
data[("Sales", "Senior")] = np.random.normal(78, 12, 50)
data[("Sales", "Lead")] = np.random.normal(85, 10, 50)

# Add outliers to show box plot features
data[("Engineering", "Junior")] = np.append(data[("Engineering", "Junior")], [45, 95])
data[("Sales", "Senior")] = np.append(data[("Sales", "Senior")], [40, 105])
data[("Marketing", "Lead")] = np.append(data[("Marketing", "Lead")], [60, 100])

# Subcategory colors (colorblind-safe: blue, orange, teal)
subcategory_colors = ("#306998", "#E69F00", "#009E73")

# Build full color tuple: repeat pattern for each department group
all_colors = subcategory_colors * len(departments)

# Custom style for large canvas with increased font sizes
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=all_colors,
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=48,
    value_font_size=32,
    opacity=0.85,
    opacity_hover=1.0,
)

# Create box chart with legend showing only 3 experience levels
# Set y-axis range to focus on actual data range (35-110)
chart = pygal.Box(
    width=4800,
    height=2700,
    style=custom_style,
    title="box-grouped · pygal · pyplots.ai",
    x_title="Department",
    y_title="Performance Score",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=36,
    truncate_legend=-1,
    show_y_guides=True,
    show_x_guides=False,
    margin=80,
    box_mode="tukey",
    x_label_rotation=0,
    range=(35, 110),
    y_labels=[40, 50, 60, 70, 80, 90, 100, 110],
)

# Track which experience levels have been labeled in legend
labeled_levels = set()

# Add the 9 boxes grouped by department
for dept in departments:
    for level in experience_levels:
        values = data[(dept, level)].tolist()
        # Only first occurrence of each experience level gets a legend entry
        if level not in labeled_levels:
            chart.add(level, values)
            labeled_levels.add(level)
        else:
            # Suppress legend entry with None label
            chart.add(None, values)

# X-axis labels: show department name in center of each group
x_labels = ["", "Engineering", "", "", "Marketing", "", "", "Sales", ""]
chart.x_labels = x_labels

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
