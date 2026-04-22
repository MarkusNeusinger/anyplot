""" pyplots.ai
swarm-basic: Basic Swarm Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, output_file, save


# Data - Employee performance scores by department
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "HR"]
n_per_group = [45, 38, 52, 35]

categories = []
values = []

# Generate realistic performance score distributions for each department
for dept, n in zip(departments, n_per_group, strict=True):
    categories.extend([dept] * n)
    if dept == "Engineering":
        # Engineering: higher scores, tight distribution
        scores = np.random.normal(82, 8, n)
    elif dept == "Marketing":
        # Marketing: moderate scores, wider spread
        scores = np.random.normal(75, 12, n)
    elif dept == "Sales":
        # Sales: bimodal - high and low performers
        scores = np.concatenate([np.random.normal(65, 8, n // 2), np.random.normal(88, 6, n - n // 2)])
    else:  # HR
        # HR: moderate scores, some outliers
        scores = np.random.normal(78, 10, n)
        scores[0] = 45  # Low outlier
        scores[1] = 98  # High outlier

    values.extend(np.clip(scores, 30, 100))

values = np.array(values)
categories = np.array(categories)

# Calculate swarm positions (jitter to avoid overlap)
x_jitter = np.zeros(len(values))
jitter_width = 0.35

for dept in departments:
    mask = categories == dept
    dept_values = values[mask]
    n_points = len(dept_values)

    # Sort by value for consistent swarm layout
    sorted_indices = np.argsort(dept_values)
    sorted_values = dept_values[sorted_indices]

    # Calculate jitter based on local density
    jitter = np.zeros(n_points)
    bin_size = 3  # Points within this range compete for space

    for j in range(n_points):
        # Count nearby points
        nearby = np.abs(sorted_values - sorted_values[j]) < bin_size
        nearby_count = np.sum(nearby[:j])
        # Alternate left and right
        direction = 1 if nearby_count % 2 == 0 else -1
        offset = (nearby_count // 2 + 1) * 0.08
        jitter[j] = direction * min(offset, jitter_width)

    # Map back to original order
    inverse_indices = np.argsort(sorted_indices)
    x_jitter[mask] = jitter[inverse_indices]

# Create x positions: category index + jitter
x_positions = np.array([departments.index(cat) + x_jitter[i] for i, cat in enumerate(categories)])

# Assign colors by department
colors = []
color_map = {
    "Engineering": "#306998",  # Python Blue
    "Marketing": "#FFD43B",  # Python Yellow
    "Sales": "#4DAF4A",  # Green
    "HR": "#984EA3",  # Purple
}
for cat in categories:
    colors.append(color_map[cat])

# Create data source
source = ColumnDataSource(data={"x": x_positions, "y": values, "category": categories, "color": colors})

# Create figure (4800 × 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="swarm-basic · bokeh · pyplots.ai",
    x_axis_label="Department",
    y_axis_label="Performance Score (points)",
    x_range=(-0.6, len(departments) - 0.4),
    y_range=(25, 105),
    tools="",
    toolbar_location=None,
)

# Plot swarm points
p.scatter(x="x", y="y", source=source, size=18, color="color", alpha=0.7, line_color="white", line_width=1.5)

# Add mean markers for each category
for i, dept in enumerate(departments):
    mask = categories == dept
    mean_val = np.mean(values[mask])
    p.line(x=[i - 0.3, i + 0.3], y=[mean_val, mean_val], line_width=4, line_color="#333333", line_alpha=0.8)

# Customize x-axis with category labels
p.xaxis.ticker = list(range(len(departments)))
p.xaxis.major_label_overrides = dict(enumerate(departments))

# Styling for 4800x2700 px
p.title.text_font_size = "36pt"
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "26pt"
p.yaxis.axis_label_text_font_size = "26pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.xgrid.visible = False
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = [6, 4]

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"
p.outline_line_color = None

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Save as PNG and HTML
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
