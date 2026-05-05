""" anyplot.ai
surface-basic: Basic 3D Surface Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 68/100 | Created: 2026-05-05
"""

import os
import pathlib
import sys


# noqa: E402 - sys.path modification required before imports to avoid pygal name shadowing
script_dir = str(pathlib.Path(__file__).parent)
sys.path = [p for p in sys.path if p != script_dir and p != "."]

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
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
    value_font_size=14,
    stroke_width=2,
)

np.random.seed(42)
x = np.linspace(-5, 5, 35)
y = np.linspace(-5, 5, 35)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X**2 + Y**2)) * np.cos(X * 0.5)

z_min, z_max = Z.min(), Z.max()
norm = Normalize(vmin=z_min, vmax=z_max)

z_binned = (norm(Z.flatten()) * 6).astype(int)
z_binned = np.clip(z_binned, 0, 6)

xy_pairs = list(zip(X.flatten(), Y.flatten(), z_binned, strict=False))

chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="surface-basic · pygal · anyplot.ai",
    x_title="X Axis",
    y_title="Y Axis",
    show_legend=True,
    dots_size=6,
    stroke=False,
)

for bin_idx in range(7):
    points = [(x, y) for x, y, z in xy_pairs if z == bin_idx]
    if points:
        chart.add(f"Height {bin_idx}", points)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
