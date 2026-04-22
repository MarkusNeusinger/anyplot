""" pyplots.ai
box-grouped: Grouped Box Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Legend, LegendItem
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Employee performance scores across departments by experience level
np.random.seed(42)

categories = ["Sales", "Engineering", "Marketing", "Support"]
subcategories = ["Junior", "Senior", "Lead"]
colors = ["#306998", "#FFD43B", "#4ECDC4"]  # Python Blue, Python Yellow, Teal

# Generate performance data with different distributions per group
data = {}
for cat in categories:
    data[cat] = {}
    for i, sub in enumerate(subcategories):
        # Different base means for departments
        base = {"Sales": 70, "Engineering": 75, "Marketing": 68, "Support": 72}[cat]
        # Experience adds to mean
        exp_bonus = i * 8
        # Generate realistic performance scores (50-100 range)
        n_points = 50
        scores = np.random.normal(base + exp_bonus, 10, n_points)
        scores = np.clip(scores, 40, 100)
        # Add some outliers for visual interest
        if cat == "Engineering" and sub == "Lead":
            scores = np.append(scores, [38, 100, 100])  # Add outliers
        if cat == "Sales" and sub == "Junior":
            scores = np.append(scores, [35, 105])  # Add outliers
        data[cat][sub] = scores


# Calculate box plot statistics
def calc_boxplot_stats(values):
    q1 = np.percentile(values, 25)
    q2 = np.percentile(values, 50)  # median
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    upper_whisker = min(max(values), q3 + 1.5 * iqr)
    lower_whisker = max(min(values), q1 - 1.5 * iqr)
    outliers = values[(values < lower_whisker) | (values > upper_whisker)]
    return {"q1": q1, "q2": q2, "q3": q3, "lower": lower_whisker, "upper": upper_whisker, "outliers": outliers}


# Create figure
p = figure(
    width=4800,
    height=2700,
    x_range=categories,
    y_range=(30, 110),
    title="box-grouped · bokeh · pyplots.ai",
    x_axis_label="Department",
    y_axis_label="Performance Score",
    tools="",
    toolbar_location=None,
)

# Styling
p.title.text_font_size = "36pt"
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Box dimensions
box_width = 0.22
offsets = [-0.28, 0, 0.28]  # Position offsets for subcategories

# Store renderers for legend
legend_items = []

# Draw grouped box plots
for sub_idx, sub in enumerate(subcategories):
    color = colors[sub_idx]
    offset = offsets[sub_idx]

    # Collect data for this subcategory across all categories
    boxes_lower = []
    boxes_upper = []
    boxes_q1 = []
    boxes_q2 = []
    boxes_q3 = []
    x_positions = []
    all_outliers_x = []
    all_outliers_y = []

    for cat_idx, cat in enumerate(categories):
        stats = calc_boxplot_stats(data[cat][sub])
        x_pos = cat_idx + offset
        x_positions.append(x_pos)

        boxes_lower.append(stats["lower"])
        boxes_upper.append(stats["upper"])
        boxes_q1.append(stats["q1"])
        boxes_q2.append(stats["q2"])
        boxes_q3.append(stats["q3"])

        # Collect outliers
        for outlier in stats["outliers"]:
            all_outliers_x.append(x_pos)
            all_outliers_y.append(outlier)

    # Draw whisker stems (vertical lines from lower to upper)
    for i, _cat in enumerate(categories):
        x_pos = x_positions[i]
        # Lower whisker
        p.segment(x0=[x_pos], y0=[boxes_lower[i]], x1=[x_pos], y1=[boxes_q1[i]], line_color="#333333", line_width=3)
        # Upper whisker
        p.segment(x0=[x_pos], y0=[boxes_q3[i]], x1=[x_pos], y1=[boxes_upper[i]], line_color="#333333", line_width=3)
        # Whisker caps
        cap_width = box_width * 0.6
        p.segment(
            x0=[x_pos - cap_width / 2],
            y0=[boxes_lower[i]],
            x1=[x_pos + cap_width / 2],
            y1=[boxes_lower[i]],
            line_color="#333333",
            line_width=3,
        )
        p.segment(
            x0=[x_pos - cap_width / 2],
            y0=[boxes_upper[i]],
            x1=[x_pos + cap_width / 2],
            y1=[boxes_upper[i]],
            line_color="#333333",
            line_width=3,
        )

    # Draw boxes (q1 to q3)
    box_source = ColumnDataSource(data={"x": x_positions, "bottom": boxes_q1, "top": boxes_q3})

    box_renderer = p.vbar(
        x="x",
        width=box_width,
        bottom="bottom",
        top="top",
        source=box_source,
        fill_color=color,
        fill_alpha=0.8,
        line_color="#333333",
        line_width=2,
    )

    # Draw median lines
    for i in range(len(categories)):
        p.segment(
            x0=[x_positions[i] - box_width / 2],
            y0=[boxes_q2[i]],
            x1=[x_positions[i] + box_width / 2],
            y1=[boxes_q2[i]],
            line_color="#333333",
            line_width=4,
        )

    # Draw outliers
    if all_outliers_x:
        p.scatter(
            x=all_outliers_x,
            y=all_outliers_y,
            size=18,
            color=color,
            alpha=0.9,
            line_color="#333333",
            line_width=2,
            marker="circle",
        )

    # Store for legend
    legend_items.append(LegendItem(label=sub, renderers=[box_renderer]))

# Add legend
legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="22pt",
    glyph_width=40,
    glyph_height=40,
    spacing=15,
    padding=20,
    background_fill_alpha=0.8,
    border_line_color="#cccccc",
    border_line_width=2,
)
p.add_layout(legend, "right")

# Adjust x-axis to show category names at correct positions
p.xaxis.major_label_overrides = {cat: cat for cat in categories}

# Save
export_png(p, filename="plot.png")

# Also save HTML for interactive version
save(p, filename="plot.html", resources=CDN, title="box-grouped · bokeh · pyplots.ai")
