"""anyplot.ai
streamline-basic: Basic Streamline Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os
import sys


# Remove this file's directory from sys.path so `import pygal` resolves to the
# installed package, not this script (which shares the same name).
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _this_dir]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402
from scipy.interpolate import RegularGridInterpolator  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per orbit group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SEED_RINGS = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)  # seed radii as a share of the domain half-width
LAP = 1.03  # trace this many laps of the seed circle, so each closed loop just closes
STEP = 0.02  # integration step in data units
EDGE = 0.875  # streamlines stop at this share of the domain half-width

# Columns: set these to your table's column names
X = "X Position"  # role: x
Y = "Y Position"  # role: y
U = "Horizontal velocity"  # role: u
V = "Vertical velocity"  # role: v

# Data: replace this block with your own table, for example df = pd.read_csv("field.csv")
# Vortex flow with radial decay on a 41 x 41 grid: u = -y * k(r), v = x * k(r)
grid = np.linspace(-4, 4, 41)
gx, gy = np.meshgrid(grid, grid)
decay = 1.0 / (1.0 + 0.1 * np.hypot(gx, gy))
df = pd.DataFrame({X: gx.ravel(), Y: gy.ravel(), U: (-gy * decay).ravel(), V: (gx * decay).ravel()})

# Plot: reads only df and the constants above
xs = np.sort(df[X].dropna().unique())
ys = np.sort(df[Y].dropna().unique())
field = df.groupby([Y, X])[[U, V]].mean().reindex(pd.MultiIndex.from_product([ys, xs]))
u_grid = field[U].to_numpy().reshape(len(ys), len(xs))
v_grid = field[V].to_numpy().reshape(len(ys), len(xs))
u_interp = RegularGridInterpolator((ys, xs), u_grid, bounds_error=False, fill_value=np.nan)
v_interp = RegularGridInterpolator((ys, xs), v_grid, bounds_error=False, fill_value=np.nan)

half_width = float(max(np.abs(xs).max(), np.abs(ys).max()))
limit = half_width * EDGE


def trace(x0, y0, length):
    """Follow the field from (x0, y0) with unit-speed midpoint steps until the edge or a stall."""

    def direction(px, py):
        u = float(u_interp((py, px)))
        v = float(v_interp((py, px)))
        speed = np.hypot(u, v)
        return (u / speed, v / speed) if np.isfinite(speed) and speed >= 0.001 else None

    points = [(x0, y0)]
    x, y = x0, y0
    for _ in range(int(length / STEP)):
        d = direction(x, y)
        if d is None:
            break
        mid = direction(x + 0.5 * STEP * d[0], y + 0.5 * STEP * d[1])
        if mid is None:
            break
        x, y = x + STEP * mid[0], y + STEP * mid[1]
        if abs(x) > limit or abs(y) > limit:
            break
        points.append((x, y))
    return points


# One series per seed ring: a single streamline each, so no separators are needed
series = {}
for ring in SEED_RINGS:
    radius = ring * half_width
    line = trace(radius, 0.0, 2 * np.pi * radius * LAP)
    if len(line) > 10:
        series[f"r = {radius:.1f}"] = line

# Style
title = "streamline-basic · python · pygal · anyplot.ai"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=4,
)

chart = pygal.XY(
    style=custom_style,
    width=3200,
    height=1800,
    stroke=True,
    show_dots=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    title=title,
    x_title=X,
    y_title=Y,
    show_x_guides=False,
    show_y_guides=False,
    xrange=(float(xs.min()), float(xs.max())),
    range=(float(ys.min()), float(ys.max())),
)
for name, points in series.items():
    chart.add(name, points)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
