""" pyplots.ai
pdp-basic: Partial Dependence Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import Band, ColumnDataSource, Span
from bokeh.plotting import figure
from sklearn.datasets import make_friedman1
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Data - Train a model and compute partial dependence
np.random.seed(42)

# Use Friedman #1 dataset which has known non-linear relationships
X, y = make_friedman1(n_samples=500, n_features=5, noise=0.5, random_state=42)

# Train a gradient boosting model
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
model.fit(X, y)

# Compute partial dependence for feature 0 (has sin relationship)
feature_idx = 0
grid_resolution = 100

# Compute partial dependence using sklearn
pdp_results = partial_dependence(model, X, features=[feature_idx], kind="both", grid_resolution=grid_resolution)

# Extract values
avg_predictions = pdp_results["average"][0]
individual_predictions = pdp_results["individual"][0]  # ICE lines
grid_values = pdp_results["grid_values"][0]

# Calculate confidence interval (percentiles of ICE lines)
lower_bound = np.percentile(individual_predictions, 10, axis=0)
upper_bound = np.percentile(individual_predictions, 90, axis=0)

# Center partial dependence at zero for easier interpretation
center_val = avg_predictions.mean()
avg_centered = avg_predictions - center_val
lower_centered = lower_bound - center_val
upper_centered = upper_bound - center_val

# Get training data distribution for rug plot
rug_x = X[:, feature_idx]

# Create data source for main line and band
source = ColumnDataSource(data={"x": grid_values, "y": avg_centered, "lower": lower_centered, "upper": upper_centered})

# Create data source for rug plot - position at bottom of plot area
y_min = lower_centered.min() - 1.5
rug_source = ColumnDataSource(data={"x": rug_x, "y": np.full_like(rug_x, y_min + 0.3)})

# Create figure with proper sizing
p = figure(
    width=4800,
    height=2700,
    title="pdp-basic · bokeh · pyplots.ai",
    x_axis_label="Feature X₀ Value",
    y_axis_label="Partial Dependence (centered)",
)

# Add confidence band
band = Band(
    base="x",
    lower="lower",
    upper="upper",
    source=source,
    fill_color="#306998",
    fill_alpha=0.25,
    line_color="#306998",
    line_alpha=0.4,
)
p.add_layout(band)

# Add horizontal line at y=0 for reference
zero_line = Span(location=0, dimension="width", line_color="#555555", line_width=3, line_dash="dashed", line_alpha=0.6)
p.add_layout(zero_line)

# Add invisible patch for confidence band legend entry
p.patch([], [], fill_color="#306998", fill_alpha=0.25, line_color="#306998", line_alpha=0.4, legend_label="80% CI")

# Add main PDP line
p.line("x", "y", source=source, line_width=5, line_color="#306998", legend_label="Average PD")

# Add rug plot for data distribution
p.scatter(
    "x",
    "y",
    source=rug_source,
    size=25,
    color="#FFD43B",
    alpha=0.6,
    line_width=3,
    angle=1.5708,
    marker="dash",
    legend_label="Data Distribution",
)

# Text styling - scaled for 4800x2700 px canvas
p.title.text_font_size = "56pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "32pt"
p.yaxis.major_label_text_font_size = "32pt"

# Axis styling
p.xaxis.axis_line_width = 3
p.yaxis.axis_line_width = 3
p.xaxis.major_tick_line_width = 3
p.yaxis.major_tick_line_width = 3
p.xaxis.minor_tick_line_width = 2
p.yaxis.minor_tick_line_width = 2

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Legend styling
p.legend.location = "bottom_right"
p.legend.label_text_font_size = "32pt"
p.legend.background_fill_alpha = 0.9
p.legend.border_line_alpha = 0.5
p.legend.border_line_width = 2
p.legend.glyph_height = 50
p.legend.glyph_width = 50
p.legend.spacing = 20
p.legend.padding = 25
p.legend.margin = 40

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Save
export_png(p, filename="plot.png")
