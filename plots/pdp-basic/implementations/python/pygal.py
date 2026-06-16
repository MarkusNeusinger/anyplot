""" anyplot.ai
pdp-basic: Partial Dependence Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pygal
from pygal.style import Style
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Generate data and train model
np.random.seed(42)
X, y = make_regression(n_samples=500, n_features=5, noise=10, random_state=42)
model = GradientBoostingRegressor(n_estimators=50, max_depth=3, random_state=42)
model.fit(X, y)

# Calculate partial dependence for feature 0
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

# Custom style for theme-adaptive rendering
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Create XY chart for PDP line plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="pdp-basic · pygal · anyplot.ai",
    x_title="Feature Value (standardized)",
    y_title="Partial Dependence",
    show_legend=True,
    legend_at_bottom=True,
    show_dots=False,
    stroke_style={"width": 4},
    show_x_guides=True,
    show_y_guides=True,
    dots_size=6,
    margin_bottom=150,
)

# Create XY data points for main PDP line
pdp_points = [(float(x), float(y)) for x, y in zip(feature_values, pd_values, strict=True)]

# Create confidence interval points
ci_upper_points = [(float(x), float(y)) for x, y in zip(feature_values, ci_upper, strict=True)]
ci_lower_points = [(float(x), float(y)) for x, y in zip(feature_values, ci_lower, strict=True)]

# Add data series
chart.add("Partial Dependence", pdp_points, stroke_style={"width": 5})
chart.add("95% CI Upper", ci_upper_points, stroke_style={"width": 2, "dasharray": "8,4"})
chart.add("95% CI Lower", ci_lower_points, stroke_style={"width": 2, "dasharray": "8,4"})

# Add rug plot showing training data distribution
rug_indices = np.random.choice(len(X), size=min(40, len(X)), replace=False)
rug_x_values = X[rug_indices, feature_idx]
y_min = float(np.min(pd_values) - 0.15 * (np.max(pd_values) - np.min(pd_values)))
rug_points = [(float(x), y_min) for x in sorted(rug_x_values)]
chart.add("Training Data (rug)", rug_points, stroke=False, dots_size=5)

# Save as PNG and HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
