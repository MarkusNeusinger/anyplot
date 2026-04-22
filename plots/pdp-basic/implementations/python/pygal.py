""" pyplots.ai
pdp-basic: Partial Dependence Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-31
"""

import numpy as np
import pygal
from pygal.style import Style
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Generate data and train model
np.random.seed(42)
X, y = make_regression(n_samples=500, n_features=5, noise=10, random_state=42)
model = GradientBoostingRegressor(n_estimators=50, max_depth=3, random_state=42)
model.fit(X, y)

# Calculate partial dependence for feature 0 (Room Size)
feature_idx = 0
pdp_result = partial_dependence(model, X, features=[feature_idx], kind="average", grid_resolution=100)
feature_values = pdp_result["grid_values"][0]
pd_values = pdp_result["average"][0]

# Calculate confidence interval using individual predictions
pdp_individual = partial_dependence(model, X, features=[feature_idx], kind="individual", grid_resolution=100)
individual_preds = pdp_individual["individual"][0]
pd_std = np.std(individual_preds, axis=0)
ci_lower = pd_values - 1.96 * pd_std / np.sqrt(len(X))
ci_upper = pd_values + 1.96 * pd_std / np.sqrt(len(X))

# Custom style for pyplots - significantly increased font sizes for 4800x2700
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#2E7D32", "#1565C0", "#D32F2F"),
    font_family="sans-serif",
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    tooltip_font_size=36,
    value_label_font_size=36,
)

# Create XY chart for PDP line plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="pdp-basic · pygal · pyplots.ai",
    x_title="Room Size (standardized)",
    y_title="Partial Dependence",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=30,
    show_dots=False,
    stroke_style={"width": 6},
    show_x_guides=True,
    show_y_guides=True,
    dots_size=8,
    margin=50,
    margin_bottom=200,
)

# Create XY data points for main PDP line
pdp_points = [(float(x), float(y)) for x, y in zip(feature_values, pd_values, strict=True)]

# Create confidence interval points
ci_upper_points = [(float(x), float(y)) for x, y in zip(feature_values, ci_upper, strict=True)]
ci_lower_points = [(float(x), float(y)) for x, y in zip(feature_values, ci_lower, strict=True)]

# Add data series
chart.add("Partial Dependence", pdp_points, stroke_style={"width": 8})
chart.add("95% CI Upper", ci_upper_points, stroke_style={"width": 3, "dasharray": "10,5"})
chart.add("95% CI Lower", ci_lower_points, stroke_style={"width": 3, "dasharray": "10,5"})

# Add rug plot as discrete points along x-axis showing training data distribution
# Sample 40 points from the training data for rug display
rug_indices = np.random.choice(len(X), size=min(40, len(X)), replace=False)
rug_x_values = X[rug_indices, feature_idx]
y_min = float(np.min(pd_values) - 0.15 * (np.max(pd_values) - np.min(pd_values)))
rug_points = [(float(x), y_min) for x in sorted(rug_x_values)]
chart.add("Training Data (rug)", rug_points, stroke=False, dots_size=25)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
