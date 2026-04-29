""" anyplot.ai
quiver-basic: Basic Quiver Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 77/100 | Updated: 2026-04-29
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

# Data — counterclockwise wind rotation around a low-pressure centre (u=-y, v=x)
np.random.seed(42)
grid_size = 8  # 8×8 = 64 arrows, well-spaced for discrete legibility
x_range = np.linspace(-3, 3, grid_size)
y_range = np.linspace(-3, 3, grid_size)
X, Y = np.meshgrid(x_range, y_range)
x_flat = X.flatten()
y_flat = Y.flatten()

U = -y_flat
V = x_flat
magnitude = np.sqrt(U**2 + V**2)
max_mag = magnitude.max()
norm_mag = magnitude / max_mag

arrow_scale = 0.22
U_scaled = U * arrow_scale
V_scaled = V * arrow_scale

head_ratio = 0.40
head_angle = 0.55

num_bins = 3
wind_labels = ["Calm / Light", "Moderate", "Fresh / Strong"]
bin_colors = OKABE_ITO[:num_bins]

# Build each arrow as an isolated 9-item segment group, collected per bin
arrow_bins = [[] for _ in range(num_bins)]
for i in range(len(x_flat)):
    if magnitude[i] < 0.01:
        continue
    x1, y1 = x_flat[i], y_flat[i]
    x2, y2 = x1 + U_scaled[i], y1 + V_scaled[i]
    arrow_len = np.sqrt(U_scaled[i] ** 2 + V_scaled[i] ** 2)
    head_size = arrow_len * head_ratio
    angle = np.arctan2(V_scaled[i], U_scaled[i])
    xl = x2 - head_size * np.cos(angle - head_angle)
    yl = y2 - head_size * np.sin(angle - head_angle)
    xr = x2 - head_size * np.cos(angle + head_angle)
    yr = y2 - head_size * np.sin(angle + head_angle)
    bin_idx = min(int(norm_mag[i] * num_bins), num_bins - 1)
    # Each arrow = shaft + two barb segments, each terminated with None
    arrow_bins[bin_idx].append([(x1, y1), (x2, y2), None, (x2, y2), (xl, yl), None, (x2, y2), (xr, yr), None])

# Shuffle arrow order within each bin to break the spatial row-order band patterns
# that make consecutive arrows appear visually connected even with None breaks
rng = np.random.RandomState(42)
arrow_series = []
for i in range(num_bins):
    arrows = arrow_bins[i][:]
    rng.shuffle(arrows)
    flat = []
    for arrow in arrows:
        flat.extend(arrow)
    arrow_series.append(flat)

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

# Plot — thinner strokes (10 vs 20) + dot markers at each segment endpoint
# clearly distinguish 64 discrete arrow positions rather than sweeping bands
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    stroke=True,
    stroke_style={"width": 10},
    show_dots=True,
    dot_size=4,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    title="quiver-basic · pygal · anyplot.ai",
    x_title="Longitude (degrees)",
    y_title="Latitude (degrees)",
    show_x_guides=True,
    show_y_guides=True,
    range=(-3.8, 3.8),
    xrange=(-3.8, 3.8),
)

for i in range(num_bins):
    if arrow_series[i]:
        chart.add(wind_labels[i], arrow_series[i], allow_interruptions=True)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
