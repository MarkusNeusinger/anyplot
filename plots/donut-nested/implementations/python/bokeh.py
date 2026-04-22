""" pyplots.ai
donut-nested: Nested Donut Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

from math import pi

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data: Budget allocation by department and expense categories
# Inner ring: Departments
# Outer ring: Expense categories within each department
data = {
    "Engineering": {"Salaries": 450, "Equipment": 120, "Training": 80, "Cloud": 150},
    "Marketing": {"Advertising": 280, "Events": 90, "Content": 60},
    "Sales": {"Salaries": 320, "Travel": 85, "Tools": 45},
    "Operations": {"Facilities": 180, "IT Support": 95, "Utilities": 55},
}

# Colors: Use consistent color families per parent (Python Blue based palette)
color_palettes = {
    "Engineering": ["#306998", "#4a88b5", "#6ba8d2", "#8dc8ef"],  # Blues
    "Marketing": ["#FFD43B", "#ffe066", "#ffeb99", "#fff5cc"],  # Yellows
    "Sales": ["#2d8659", "#4ba376", "#6bc093", "#8bddb0"],  # Greens
    "Operations": ["#8b4d6e", "#a8698a", "#c585a6", "#e2a1c2"],  # Purples
}

# Calculate totals and angles
dept_totals = {dept: sum(cats.values()) for dept, cats in data.items()}
total = sum(dept_totals.values())

# Build data for inner ring (departments)
inner_start_angle = []
inner_end_angle = []
inner_colors = []
inner_labels = []
inner_values = []
inner_x = []
inner_y = []

# Build data for outer ring (categories)
outer_start_angle = []
outer_end_angle = []
outer_colors = []
outer_labels = []
outer_values = []
outer_x = []
outer_y = []

# Inner ring radii
inner_radius_outer = 0.6
inner_radius_inner = 0.35

# Outer ring radii
outer_radius_outer = 0.9
outer_radius_inner = 0.65

current_angle = pi / 2  # Start at top

for dept, categories in data.items():
    dept_total = dept_totals[dept]
    dept_angle = 2 * pi * (dept_total / total)

    # Inner ring segment
    inner_start_angle.append(current_angle)
    inner_end_angle.append(current_angle + dept_angle)
    inner_colors.append(color_palettes[dept][0])
    inner_labels.append(dept)
    inner_values.append(dept_total)

    # Label position for inner ring
    mid_angle = current_angle + dept_angle / 2
    label_radius = (inner_radius_outer + inner_radius_inner) / 2
    inner_x.append(label_radius * np.cos(mid_angle))
    inner_y.append(label_radius * np.sin(mid_angle))

    # Outer ring segments (categories within this department)
    cat_start = current_angle
    for i, (cat, val) in enumerate(categories.items()):
        cat_angle = 2 * pi * (val / total)

        outer_start_angle.append(cat_start)
        outer_end_angle.append(cat_start + cat_angle)
        outer_colors.append(color_palettes[dept][i % len(color_palettes[dept])])
        outer_labels.append(cat)
        outer_values.append(val)

        # Label position for outer ring
        cat_mid_angle = cat_start + cat_angle / 2
        cat_label_radius = (outer_radius_outer + outer_radius_inner) / 2
        outer_x.append(cat_label_radius * np.cos(cat_mid_angle))
        outer_y.append(cat_label_radius * np.sin(cat_mid_angle))

        cat_start += cat_angle

    current_angle += dept_angle

# Create figure (square format for donut)
p = figure(
    width=3600,
    height=3600,
    title="donut-nested · bokeh · pyplots.ai",
    x_range=(-1.3, 1.3),
    y_range=(-1.3, 1.3),
    tools="",
    toolbar_location=None,
)

# Style the figure
p.title.text_font_size = "36pt"
p.title.align = "center"
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None
p.background_fill_color = None
p.border_fill_color = None

# Inner ring (departments)
inner_source = ColumnDataSource(
    data={
        "start_angle": inner_start_angle,
        "end_angle": inner_end_angle,
        "color": inner_colors,
        "label": inner_labels,
        "value": inner_values,
        "x": inner_x,
        "y": inner_y,
    }
)

p.annular_wedge(
    x=0,
    y=0,
    inner_radius=inner_radius_inner,
    outer_radius=inner_radius_outer,
    start_angle="start_angle",
    end_angle="end_angle",
    color="color",
    line_color="white",
    line_width=3,
    source=inner_source,
)

# Outer ring (categories)
outer_source = ColumnDataSource(
    data={
        "start_angle": outer_start_angle,
        "end_angle": outer_end_angle,
        "color": outer_colors,
        "label": outer_labels,
        "value": outer_values,
        "x": outer_x,
        "y": outer_y,
    }
)

p.annular_wedge(
    x=0,
    y=0,
    inner_radius=outer_radius_inner,
    outer_radius=outer_radius_outer,
    color="color",
    line_color="white",
    line_width=2,
    source=outer_source,
)

# Labels for inner ring (departments with values)
inner_label_text = [f"{lbl}\n${val}K" for lbl, val in zip(inner_labels, inner_values, strict=True)]
inner_label_source = ColumnDataSource(data={"x": inner_x, "y": inner_y, "text": inner_label_text})

inner_labels_set = LabelSet(
    x="x",
    y="y",
    text="text",
    source=inner_label_source,
    text_align="center",
    text_baseline="middle",
    text_font_size="18pt",
    text_color="white",
    text_font_style="bold",
)
p.add_layout(inner_labels_set)

# Labels for outer ring (only for larger segments)
outer_label_text = []
outer_label_x = []
outer_label_y = []
for label, value, x, y, start, end in zip(
    outer_labels, outer_values, outer_x, outer_y, outer_start_angle, outer_end_angle, strict=True
):
    segment_angle = abs(end - start)
    # Only label segments larger than 0.25 radians (~14 degrees)
    if segment_angle > 0.25:
        outer_label_text.append(f"{label}\n${value}K")
        outer_label_x.append(x)
        outer_label_y.append(y)

outer_label_source = ColumnDataSource(data={"x": outer_label_x, "y": outer_label_y, "text": outer_label_text})

outer_labels_set = LabelSet(
    x="x",
    y="y",
    text="text",
    source=outer_label_source,
    text_align="center",
    text_baseline="middle",
    text_font_size="14pt",
    text_color="#333333",
)
p.add_layout(outer_labels_set)

# Add center text showing total
p.text(
    x=[0],
    y=[0],
    text=[f"Total\n${total}K"],
    text_align="center",
    text_baseline="middle",
    text_font_size="24pt",
    text_font_style="bold",
    text_color="#306998",
)

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Nested Donut Chart")
