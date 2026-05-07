""" anyplot.ai
ice-basic: Individual Conditional Expectation (ICE) Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 76/100 | Created: 2026-05-07
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

ICE_COLOR = "#009E73"  # Okabe-Ito position 1 — ICE lines
PDP_COLOR = "#D55E00"  # Okabe-Ito position 2 — PDP line

# Data: house price predictions from GradientBoostingRegressor
np.random.seed(42)
n_obs = 50
n_grid = 40

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
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Plot
chart = pygal.Line(
    style=custom_style,
    width=4800,
    height=2700,
    title="ice-basic · pygal · anyplot.ai",
    x_title="Square Footage",
    y_title="Predicted Price ($ thousands)",
    show_dots=False,
    legend_at_bottom=True,
    show_y_guides=True,
    show_x_guides=False,
)

# x-axis: label every 4th grid point to avoid crowding
x_labels = [""] * n_grid
for idx in range(0, n_grid, 4):
    x_labels[idx] = str(int(sqft_grid[idx]))
chart.x_labels = x_labels

# ICE lines — empty title '' is falsy in pygal, so these are omitted from the legend
for i in range(n_obs):
    chart.add("", [round(float(v), 1) for v in ice_curves[i]], stroke_style={"width": 3, "opacity": 0.3})

# PDP line — bold, fully opaque, labeled
chart.add(
    "Partial Dependence (PDP)", [round(float(v), 1) for v in pdp_curve], stroke_style={"width": 10, "opacity": 1.0}
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
