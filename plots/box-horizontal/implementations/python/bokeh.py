""" pyplots.ai
box-horizontal: Horizontal Box Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import FactorRange
from bokeh.plotting import figure


# Data - Response times (ms) by service type
np.random.seed(42)

categories = ["Cache Layer", "API Gateway", "Authentication", "Database Query", "File Storage"]

# Generate different distributions for each service (sorted by median)
data = {
    "Cache Layer": np.random.normal(15, 5, 80),
    "API Gateway": np.random.normal(45, 12, 80),
    "Authentication": np.concatenate([np.random.normal(65, 15, 75), [130, 145, 150]]),  # Outliers
    "Database Query": np.concatenate([np.random.normal(120, 30, 80), [220, 240]]),  # Some slow queries
    "File Storage": np.random.normal(200, 50, 80),
}

# Calculate box plot statistics for each category
stats = {}
outliers_x = []
outliers_y = []

for cat in categories:
    values = data[cat]
    q1 = np.percentile(values, 25)
    q2 = np.percentile(values, 50)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    upper_fence = q3 + 1.5 * iqr
    lower_fence = q1 - 1.5 * iqr

    # Whiskers extend to furthest data point within fence
    mask = (values >= lower_fence) & (values <= upper_fence)
    upper = values[mask].max() if mask.any() else q3
    lower = values[mask].min() if mask.any() else q1

    # Find outliers
    outlier_mask = (values < lower_fence) | (values > upper_fence)
    for o in values[outlier_mask]:
        outliers_x.append(o)
        outliers_y.append(cat)

    stats[cat] = {"q1": q1, "q2": q2, "q3": q3, "upper": upper, "lower": lower}

# Create figure with categorical y-axis (horizontal orientation)
p = figure(
    width=4800,
    height=2700,
    y_range=FactorRange(*categories),
    x_axis_label="Response Time (ms)",
    y_axis_label="Service Type",
    title="box-horizontal · bokeh · pyplots.ai",
)

# Colors
box_color = "#306998"
median_color = "#FFD43B"
whisker_color = "#444444"

# Box and whisker dimensions
box_height = 0.6
cap_height = 0.3

for cat in categories:
    s = stats[cat]

    # Draw box (IQR)
    p.hbar(
        y=[cat],
        left=[s["q1"]],
        right=[s["q3"]],
        height=box_height,
        fill_color=box_color,
        fill_alpha=0.7,
        line_color="#1a3a5c",
        line_width=2,
    )

    # Draw median line
    p.hbar(
        y=[cat],
        left=[s["q2"] - 1],
        right=[s["q2"] + 1],
        height=box_height,
        fill_color=median_color,
        line_color=median_color,
        line_width=0,
    )

    # Draw whiskers (horizontal lines from box to whisker ends)
    p.hbar(y=[cat], left=[s["lower"]], right=[s["q1"]], height=0.02, fill_color=whisker_color, line_color=whisker_color)
    p.hbar(y=[cat], left=[s["q3"]], right=[s["upper"]], height=0.02, fill_color=whisker_color, line_color=whisker_color)

    # Draw whisker caps (vertical lines at whisker ends)
    p.hbar(
        y=[cat],
        left=[s["lower"] - 0.5],
        right=[s["lower"] + 0.5],
        height=cap_height,
        fill_color=whisker_color,
        line_color=whisker_color,
    )
    p.hbar(
        y=[cat],
        left=[s["upper"] - 0.5],
        right=[s["upper"] + 0.5],
        height=cap_height,
        fill_color=whisker_color,
        line_color=whisker_color,
    )

# Draw outliers
if outliers_x:
    p.scatter(
        x=outliers_x, y=outliers_y, size=15, fill_color="white", line_color=box_color, line_width=2, marker="circle"
    )

# Style settings
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = [6, 4]

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Axis styling
p.xaxis.axis_line_color = "#666666"
p.yaxis.axis_line_color = "#666666"

# Save
export_png(p, filename="plot.png")
