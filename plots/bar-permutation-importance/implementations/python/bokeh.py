""" pyplots.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Whisker
from bokeh.palettes import Blues9
from bokeh.plotting import figure
from bokeh.transform import linear_cmap


# Data: Simulated permutation importance results for a housing price model
np.random.seed(42)

features = [
    "Square Footage",
    "Number of Bedrooms",
    "Neighborhood Score",
    "Year Built",
    "Lot Size",
    "Distance to City Center",
    "Number of Bathrooms",
    "Garage Capacity",
    "School Rating",
    "Crime Index",
    "Property Tax Rate",
    "Previous Sale Price",
    "Days on Market",
    "Walk Score",
    "Public Transit Access",
]

# Generate importance values (higher = more important)
# Some features clearly important, some moderate, some low/negative
importance_mean = np.array(
    [0.182, 0.145, 0.128, 0.095, 0.078, 0.065, 0.052, 0.041, 0.035, 0.028, 0.018, 0.012, 0.005, -0.003, -0.008]
)

# Standard deviations (variability across shuffles)
importance_std = np.array(
    [0.025, 0.022, 0.020, 0.018, 0.015, 0.014, 0.012, 0.011, 0.010, 0.009, 0.008, 0.007, 0.006, 0.005, 0.004]
)

# Sort by importance (highest first)
sort_idx = np.argsort(importance_mean)[::-1]
features_sorted = [features[i] for i in sort_idx]
importance_mean_sorted = importance_mean[sort_idx]
importance_std_sorted = importance_std[sort_idx]

# Reverse for plotting (highest at top)
features_plot = features_sorted[::-1]
importance_mean_plot = importance_mean_sorted[::-1]
importance_std_plot = importance_std_sorted[::-1]

# Create data source
source = ColumnDataSource(
    data={
        "features": features_plot,
        "importance": importance_mean_plot,
        "std": importance_std_plot,
        "upper": importance_mean_plot + importance_std_plot,
        "lower": importance_mean_plot - importance_std_plot,
    }
)

# Create figure with categorical y-axis
p = figure(
    width=4800,
    height=2700,
    y_range=features_plot,
    x_axis_label="Mean Decrease in Model Score",
    title="bar-permutation-importance · bokeh · pyplots.ai",
)

# Color mapper for bars (darker = more important)
mapper = linear_cmap(
    field_name="importance",
    palette=Blues9[::-1],  # Reverse so darker = higher
    low=min(importance_mean_plot),
    high=max(importance_mean_plot),
)

# Draw horizontal bars
p.hbar(
    y="features",
    right="importance",
    left=0,
    height=0.7,
    source=source,
    fill_color=mapper,
    line_color="#1f4e79",
    line_width=2,
)

# Add error bars (whiskers)
whisker = Whisker(
    source=source,
    base="features",
    upper="upper",
    lower="lower",
    dimension="width",
    line_color="#333333",
    line_width=3,
    upper_head=None,
    lower_head=None,
)
p.add_layout(whisker)

# Add vertical reference line at x=0
p.line(x=[0, 0], y=[-1, len(features_plot)], line_color="#333333", line_width=2, line_dash="dashed")

# Styling
p.title.text_font_size = "32pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.xgrid.grid_line_color = "#cccccc"
p.xgrid.grid_line_alpha = 0.4
p.ygrid.grid_line_color = None

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.outline_line_width = 2

# Background
p.background_fill_color = "#fafafa"

# Save outputs
export_png(p, filename="plot.png")
