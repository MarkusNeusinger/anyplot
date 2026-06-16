""" anyplot.ai
ice-basic: Individual Conditional Expectation (ICE) Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 79/100 | Created: 2026-05-07
"""

import importlib
import os
import sys

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor


# Prevent self-import: this file is named pygal.py, which shadows the package.
# Remove the script directory from sys.path before loading the pygal package.
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _this_dir]

pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

ICE_COLOR = "#009E73"  # Okabe-Ito position 1 — ICE lines
PDP_COLOR = "#C475FD"  # Okabe-Ito position 2 — PDP line

# Data: house price predictions from GradientBoostingRegressor
np.random.seed(42)
n_obs = 50
n_grid = 75  # spec recommends 50-100 grid points

sqft = np.random.normal(1800, 450, n_obs).clip(700, 3600)
bedrooms = np.random.randint(2, 6, n_obs)
location_score = np.random.uniform(0.2, 1.0, n_obs)
price = 100_000 + 130 * sqft + 9_000 * bedrooms + 180_000 * location_score + np.random.normal(0, 18_000, n_obs)

sqft_grid = np.linspace(700, 3600, n_grid)

X = np.column_stack([sqft, bedrooms, location_score])
model = GradientBoostingRegressor(n_estimators=200, max_depth=4, random_state=42)
model.fit(X, price)

ice_curves = np.zeros((n_obs, n_grid))
for i in range(n_obs):
    X_ice = np.tile([sqft[i], bedrooms[i], location_score[i]], (n_grid, 1))
    X_ice[:, 0] = sqft_grid
    ice_curves[i] = model.predict(X_ice) / 1_000  # convert to $K

pdp_curve = ice_curves.mean(axis=0)

# Style: ICE lines use brand green, PDP uses vermillion
colors_tuple = (ICE_COLOR,) * n_obs + (PDP_COLOR,)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=colors_tuple,
    title_font_size=28,
    label_font_size=22,  # style-guide: 22px for pixel-based libraries
    major_label_font_size=18,  # style-guide: 18px for pixel-based libraries
    legend_font_size=18,
    value_font_size=16,
    stroke_width=3,
)

# Plot — cubic interpolation gives smooth ICE curves (pygal-native feature)
chart = pygal.Line(
    style=custom_style,
    width=4800,
    height=2700,
    title="ice-basic · pygal · anyplot.ai",
    x_title="Square Footage",
    y_title="Predicted Price ($ thousands)",
    show_dots=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    show_y_guides=True,
    show_x_guides=False,
    interpolate="cubic",
    x_label_rotation=30,
)

# x-axis: label every 10th grid point to avoid crowding (75 total)
x_labels = [""] * n_grid
step = max(1, n_grid // 7)
for idx in range(0, n_grid, step):
    x_labels[idx] = str(int(sqft_grid[idx]))
chart.x_labels = x_labels

# ICE lines — first labeled "ICE Curves" for legend entry; remaining unlabeled
chart.add("ICE Curves", [round(float(v), 1) for v in ice_curves[0]], stroke_style={"width": 2, "opacity": 0.3})
for i in range(1, n_obs):
    chart.add("", [round(float(v), 1) for v in ice_curves[i]], stroke_style={"width": 2, "opacity": 0.3})

# PDP line — bold, fully opaque, labeled
chart.add(
    "Partial Dependence (PDP)", [round(float(v), 1) for v in pdp_curve], stroke_style={"width": 14, "opacity": 1.0}
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
