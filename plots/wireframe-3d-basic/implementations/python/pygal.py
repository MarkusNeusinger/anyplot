""" anyplot.ai
wireframe-3d-basic: Basic 3D Wireframe Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 85/100 | Created: 2026-05-06
"""

import os
import sys

import numpy as np


# Remove current directory from path to avoid importing local pygal.py
sys.path = [p for p in sys.path if not (p == "" or p == "." or p.endswith("implementations/python"))]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")


def isometric_project(x, y, z):
    """Project 3D coordinates to 2D isometric view."""
    angle = np.pi / 6
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)
    x2d = x * cos_a - y * cos_a
    y2d = z + (x * sin_a + y * sin_a) * 0.5
    return x2d, y2d


custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=2,
)

np.random.seed(42)
grid_size = 30
x = np.linspace(-5, 5, grid_size)
y = np.linspace(-5, 5, grid_size)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X**2 + Y**2))

chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="wireframe-3d-basic · pygal · anyplot.ai",
    x_title="X Axis",
    y_title="Z Axis",
    show_legend=False,
    dots_size=1,
    stroke_width=1,
)

line_series = []

for i in range(grid_size):
    for j in range(grid_size - 1):
        x1, y1, z1 = X[i, j], Y[i, j], Z[i, j]
        x2, y2, z2 = X[i, j + 1], Y[i, j + 1], Z[i, j + 1]
        px1, py1 = isometric_project(x1, y1, z1)
        px2, py2 = isometric_project(x2, y2, z2)
        line_series.append(((px1, py1), (px2, py2)))

for i in range(grid_size - 1):
    for j in range(grid_size):
        x1, y1, z1 = X[i, j], Y[i, j], Z[i, j]
        x2, y2, z2 = X[i + 1, j], Y[i + 1, j], Z[i + 1, j]
        px1, py1 = isometric_project(x1, y1, z1)
        px2, py2 = isometric_project(x2, y2, z2)
        line_series.append(((px1, py1), (px2, py2)))

for idx, (p1, p2) in enumerate(line_series):
    chart.add(f"Line {idx}", [p1, p2])

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
