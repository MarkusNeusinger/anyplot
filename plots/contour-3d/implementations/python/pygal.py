"""anyplot.ai
contour-3d: 3D Contour Plot
Library: pygal | Python 3.13
Quality: pending | Created: 2025-05-16
"""

import os
import sys

sys.path = [p for p in sys.path if not p.endswith("python")]  # noqa: E402

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

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
    stroke_width=2,
)

np.random.seed(42)
x = np.linspace(-3, 3, 45)
y = np.linspace(-3, 3, 45)
X, Y = np.meshgrid(x, y)
Z = np.exp(-(X**2 + Y**2) / 2) + 0.3 * np.sin(2 * X) * np.cos(2 * Y)

chart = pygal.XY(
    width=4800,
    height=2700,
    title="contour-3d · pygal · anyplot.ai",
    x_title="X",
    y_title="Y",
    style=custom_style,
    show_legend=True,
    dots_size=5,
    show_x_guides=False,
    show_y_guides=False,
)

z_min, z_max = Z.min(), Z.max()
num_levels = len(OKABE_ITO)
z_levels = np.linspace(z_min, z_max, num_levels + 1)

x_flat = X.flatten()
y_flat = Y.flatten()
z_flat = Z.flatten()

for i in range(num_levels):
    z_low = z_levels[i]
    z_high = z_levels[i + 1]
    mask = (z_flat >= z_low) & (z_flat <= z_high)

    points = [(float(x_flat[j]), float(y_flat[j])) for j in range(len(x_flat)) if mask[j]]

    if points:
        label = f"Level {i + 1}"
        chart.add(label, points, show_dots=True, dots_size=7)

chart.render_to_file(f"plot-{THEME}.svg")
chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
