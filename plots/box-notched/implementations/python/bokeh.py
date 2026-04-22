""" pyplots.ai
box-notched: Notched Box Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - Employee performance scores across departments
np.random.seed(42)

categories = ["Engineering", "Sales", "Marketing", "Operations", "HR"]
colors = ["#306998", "#FFD43B", "#5BA352", "#E07C3E", "#9467BD"]

# Generate realistic performance score data with varying distributions
data = {
    "Engineering": np.random.normal(78, 8, 60),  # Higher mean, moderate spread
    "Sales": np.random.normal(72, 12, 55),  # Moderate mean, high variance
    "Marketing": np.random.normal(75, 6, 50),  # Similar to Engineering
    "Operations": np.random.normal(68, 10, 65),  # Lower mean
    "HR": np.random.normal(74, 7, 45),  # Moderate
}

# Add some outliers
data["Sales"] = np.append(data["Sales"], [40, 98, 100])
data["Operations"] = np.append(data["Operations"], [42, 95])

# Compute box plot statistics with notches for each category
box_data = {
    "categories": [],
    "q1": [],
    "q2": [],  # median
    "q3": [],
    "upper": [],
    "lower": [],
    "notch_lower": [],
    "notch_upper": [],
    "colors": [],
}

outlier_data = {"category": [], "value": [], "color": []}

for i, cat in enumerate(categories):
    values = data[cat]
    q1 = np.percentile(values, 25)
    q2 = np.percentile(values, 50)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    n = len(values)

    # Whiskers at 1.5 * IQR
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr

    # Actual whisker positions (within data range)
    lower_whisker = max(lower_fence, values.min())
    upper_whisker = min(upper_fence, values.max())

    # Find values within whisker range for accurate whisker placement
    in_range = values[(values >= lower_fence) & (values <= upper_fence)]
    if len(in_range) > 0:
        lower_whisker = in_range.min()
        upper_whisker = in_range.max()

    # Notch: 95% CI around median = ±1.57 × IQR / √n
    notch_width = 1.57 * iqr / np.sqrt(n)
    notch_lower = q2 - notch_width
    notch_upper = q2 + notch_width

    box_data["categories"].append(cat)
    box_data["q1"].append(q1)
    box_data["q2"].append(q2)
    box_data["q3"].append(q3)
    box_data["upper"].append(upper_whisker)
    box_data["lower"].append(lower_whisker)
    box_data["notch_lower"].append(notch_lower)
    box_data["notch_upper"].append(notch_upper)
    box_data["colors"].append(colors[i])

    # Find outliers
    outliers = values[(values < lower_fence) | (values > upper_fence)]
    for o in outliers:
        outlier_data["category"].append(cat)
        outlier_data["value"].append(o)
        outlier_data["color"].append(colors[i])

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="box-notched · bokeh · pyplots.ai",
    x_range=categories,
    y_axis_label="Performance Score",
    x_axis_label="Department",
)

# Styling - larger sizes for 4800x2700 canvas
p.title.text_font_size = "42pt"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "26pt"
p.yaxis.major_label_text_font_size = "24pt"
p.title.text_font_style = "bold"

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Box width
box_width = 0.6

# Draw each notched box manually
for i, cat in enumerate(categories):
    q1 = box_data["q1"][i]
    q2 = box_data["q2"][i]
    q3 = box_data["q3"][i]
    nl = box_data["notch_lower"][i]
    nu = box_data["notch_upper"][i]
    lower = box_data["lower"][i]
    upper = box_data["upper"][i]
    color = box_data["colors"][i]

    # x position
    x_pos = i
    half_width = box_width / 2
    notch_indent = box_width / 4  # Notch indentation

    # Draw the notched box as a polygon
    # Create the box shape with notches at the median
    xs = [
        cat,  # bottom-left
        cat,  # notch lower-left
        cat,  # notch point left
        cat,  # notch upper-left
        cat,  # top-left
        cat,  # top-right
        cat,  # notch upper-right
        cat,  # notch point right
        cat,  # notch lower-right
        cat,  # bottom-right
    ]

    # Create notched box using quads and patches
    # Lower box (q1 to notch_lower)
    p.quad(
        top=[nl],
        bottom=[q1],
        left=[i - half_width],
        right=[i + half_width],
        fill_color=color,
        fill_alpha=0.85,
        line_color="#333333",
        line_width=3,
    )

    # Upper box (notch_upper to q3)
    p.quad(
        top=[q3],
        bottom=[nu],
        left=[i - half_width],
        right=[i + half_width],
        fill_color=color,
        fill_alpha=0.85,
        line_color="#333333",
        line_width=3,
    )

    # Notch area (narrower section around median)
    notch_xs = [i - half_width, i - half_width, i - notch_indent, i - half_width, i - half_width]
    notch_ys = [nl, nl, q2, nu, nu]

    # Left notch triangle
    p.patch(
        x=[i - half_width, i - notch_indent, i - half_width],
        y=[nl, q2, nu],
        fill_color=color,
        fill_alpha=0.85,
        line_color="#333333",
        line_width=3,
    )

    # Right notch triangle
    p.patch(
        x=[i + half_width, i + notch_indent, i + half_width],
        y=[nl, q2, nu],
        fill_color=color,
        fill_alpha=0.85,
        line_color="#333333",
        line_width=3,
    )

    # Median line
    p.segment(x0=[i - notch_indent], x1=[i + notch_indent], y0=[q2], y1=[q2], line_color="white", line_width=5)

    # Whiskers (vertical lines)
    p.segment(x0=[i], x1=[i], y0=[q3], y1=[upper], line_color="#333333", line_width=3)
    p.segment(x0=[i], x1=[i], y0=[q1], y1=[lower], line_color="#333333", line_width=3)

    # Whisker caps (horizontal lines)
    cap_width = box_width / 3
    p.segment(x0=[i - cap_width], x1=[i + cap_width], y0=[upper], y1=[upper], line_color="#333333", line_width=3)
    p.segment(x0=[i - cap_width], x1=[i + cap_width], y0=[lower], y1=[lower], line_color="#333333", line_width=3)

# Draw outliers
if outlier_data["category"]:
    outlier_source = ColumnDataSource(
        data={"x": outlier_data["category"], "y": outlier_data["value"], "color": outlier_data["color"]}
    )

    p.scatter(
        x="x",
        y="y",
        source=outlier_source,
        size=22,
        fill_color="white",
        line_color="color",
        line_width=4,
        fill_alpha=0.9,
    )

# Background
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "#FFFFFF"

# Toolbar and outline
p.toolbar_location = None
p.outline_line_color = None

# Save outputs
export_png(p, filename="plot.png")
