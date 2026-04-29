""" anyplot.ai
quiver-basic: Basic Quiver Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 72/100 | Updated: 2026-04-29
"""

import importlib
import os
import sys

import numpy as np


# Remove script dir so 'pygal' resolves to the installed package, not this file
_d = os.path.abspath(os.path.dirname(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _d]
os.chdir(_d)

pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data - Counterclockwise wind rotation around a low-pressure centre
np.random.seed(42)
grid_size = 12
x_range = np.linspace(-3, 3, grid_size)
y_range = np.linspace(-3, 3, grid_size)
X, Y = np.meshgrid(x_range, y_range)
x_flat = X.flatten()
y_flat = Y.flatten()

# u = -y, v = x produces a circular rotation field
U = -y_flat
V = x_flat
magnitude = np.sqrt(U**2 + V**2)
max_mag = magnitude.max()
norm_mag = magnitude / max_mag

arrow_scale = 0.12
U_scaled = U * arrow_scale
V_scaled = V * arrow_scale

head_ratio = 0.4
head_angle = 0.55

num_bins = 5
wind_labels = ["Calm", "Light", "Moderate", "Fresh", "Strong"]
bin_colors = OKABE_ITO[:num_bins]

arrow_groups = {i: [] for i in range(num_bins)}

for i in range(len(x_flat)):
    if magnitude[i] < 0.05:
        continue

    x1, y1 = x_flat[i], y_flat[i]
    x2, y2 = x1 + U_scaled[i], y1 + V_scaled[i]

    arrow_len = np.sqrt(U_scaled[i] ** 2 + V_scaled[i] ** 2)
    head_size = arrow_len * head_ratio

    angle = np.arctan2(V_scaled[i], U_scaled[i])
    x_left = x2 - head_size * np.cos(angle - head_angle)
    y_left = y2 - head_size * np.sin(angle - head_angle)
    x_right = x2 - head_size * np.cos(angle + head_angle)
    y_right = y2 - head_size * np.sin(angle + head_angle)

    bin_idx = min(int(norm_mag[i] * num_bins), num_bins - 1)

    arrow_groups[bin_idx].extend([(x1, y1), (x2, y2), None])
    arrow_groups[bin_idx].extend([(x2, y2), (x_left, y_left), None])
    arrow_groups[bin_idx].extend([(x2, y2), (x_right, y_right), None])

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=bin_colors,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Plot
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    stroke=True,
    stroke_style={"width": 20},
    show_dots=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    title="quiver-basic · pygal · anyplot.ai",
    x_title="Longitude (degrees)",
    y_title="Latitude (degrees)",
    show_x_guides=True,
    show_y_guides=True,
    range=(-3.8, 3.8),
    xrange=(-3.8, 3.8),
)

for i in range(num_bins):
    if arrow_groups[i]:
        chart.add(wind_labels[i], arrow_groups[i])

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
