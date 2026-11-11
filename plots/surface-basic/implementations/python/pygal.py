""" anyplot.ai
surface-basic: Basic 3D Surface Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-11
"""

import os
import pathlib
import sys


# pygal.py would shadow the pygal package when run from its own directory
script_dir = str(pathlib.Path(__file__).parent)
sys.path = [p for p in sys.path if p != script_dir and p != "."]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette (position 1 is the brand green) and the sequential ramp built from it
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SEQ_START, SEQ_END = "#009E73", "#4467A3"


def lerp_hex(c0, c1, t):
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(p + (q - p) * t):02X}" for p, q in zip(a, b, strict=True))


# Constants
AZIMUTH = np.radians(35)  # view rotation about the vertical axis
ELEVATION = np.radians(32)  # oblique angle: peaks and valleys both visible
Z_SCALE = 3.0  # drawn height of one z unit, in x/y grid units
N_BINS = 12  # colour steps of the height ramp

# Columns: set these to your table's column names
X_COL = "x"  # role: x
Y_COL = "y"  # role: y
Z_COL = "z"  # role: z

# Data: replace this block with your own long table, for example df = pd.read_csv("surface.csv")
grid = np.linspace(-5, 5, 31)
gx, gy = np.meshgrid(grid, grid)
df = pd.DataFrame(
    {X_COL: gx.ravel(), Y_COL: gy.ravel(), Z_COL: np.sin(np.sqrt(gx**2 + gy**2)).ravel() * np.cos(gx.ravel() * 0.5)}
)

# Plot: reads only df and the constants above
Zt = df.pivot_table(index=Y_COL, columns=X_COL, values=Z_COL, sort=True)
x, y = Zt.columns.to_numpy(float), Zt.index.to_numpy(float)
X, Y = np.meshgrid(x, y)
Z = Zt.to_numpy(float)
z_lo, z_hi = float(np.nanmin(Z)), float(np.nanmax(Z))
x_lo, x_hi, y_lo, y_hi = x.min(), x.max(), y.min(), y.max()


def project(px, py, pz):
    """Oblique projection of data coordinates onto the screen plane."""
    xr = px * np.cos(AZIMUTH) - py * np.sin(AZIMUTH)
    depth = px * np.sin(AZIMUTH) + py * np.cos(AZIMUTH)
    return xr, depth * np.sin(ELEVATION) + pz * Z_SCALE * np.cos(ELEVATION)


U, V = project(X, Y, Z)
ramp = [lerp_hex(SEQ_START, SEQ_END, i / (N_BINS - 1)) for i in range(N_BINS)]


def tick(v):
    """Tick text: one decimal, no negative zero."""
    return f"{round(v, 1) + 0:g}"


def bin_of(z):
    return int(np.clip((z - z_lo) / (z_hi - z_lo) * N_BINS, 0, N_BINS - 1))


# Mesh: every grid edge is its own two-point series coloured by its mean height, drawn far to near
edges = []
for i in range(Z.shape[0]):
    for j in range(Z.shape[1]):
        for di, dj in ((0, 1), (1, 0)):
            k, m = i + di, j + dj
            if k < Z.shape[0] and m < Z.shape[1]:
                zm = (Z[i, j] + Z[k, m]) / 2
                if np.isfinite(zm):
                    depth = (X[i, j] + X[k, m]) * np.sin(AZIMUTH) / 2 + (Y[i, j] + Y[k, m]) * np.cos(AZIMUTH) / 2
                    edges.append((depth, bin_of(zm), [(U[i, j], V[i, j]), (U[k, m], V[k, m])]))
edges.sort(key=lambda e: -e[0])

# Axes: base box edges, a z axis on the left corner, ticks with labels (each a two-point series)
z_floor = z_lo
corners = [(x_lo, y_lo), (x_hi, y_lo), (x_hi, y_hi), (x_lo, y_hi)]
base = [project(cx, cy, z_floor) for cx, cy in corners]
left = min(range(4), key=lambda c: base[c][0])
zx, zy = corners[left]
axis_segs = [[base[c], base[(c + 1) % 4]] for c in range(4)]
axis_segs.append([project(zx, zy, z_floor), project(zx, zy, z_hi)])

labels = []
for zt in np.linspace(z_lo, z_hi, 4):
    px, py = project(zx, zy, zt)
    axis_segs.append([(px, py), (px - 0.25, py)])
    labels.append({"value": (px - 1.1, py + 0.15), "label": tick(zt)})
px, py = project(zx, zy, z_hi)
labels.append({"value": (px, py + 0.7), "label": Z_COL})

# x ticks along the front-right edge, y ticks along the front-left edge
for t in np.linspace(x_lo, x_hi, 3):
    px, py = project(t, y_lo, z_floor)
    labels.append({"value": (px + 0.3, py - 0.9), "label": f"{t:.2g}"})
mx, my = project((x_lo + x_hi) / 2, y_lo, z_floor)
labels.append({"value": (mx, my - 1.5), "label": X_COL})
for t in np.linspace(y_lo, y_hi, 3):
    px, py = project(x_lo, t, z_floor)
    labels.append({"value": (px - 0.7, py - 0.4), "label": f"{t:.2g}"})
mx, my = project(x_lo, (y_lo + y_hi) / 2, z_floor)
labels.append({"value": (mx - 1.6, my - 0.8), "label": Y_COL})

# Colour bar on the right: each step is a block of parallel lines, labelled at both ends and the middle
u_all = np.concatenate([U.ravel(), [p[0] for p in base]])
v_all = np.concatenate([V.ravel(), [p[1] for p in base]])
bar_u = np.nanmax(u_all) + 1.5
bar_w = 0.6
bar_v0 = np.nanmin(v_all) + 0.8
bar_v1 = np.nanmax(v_all) - 1.2
bar_edges = np.linspace(bar_v0, bar_v1, N_BINS + 1)
bar_labels = [
    {"value": (bar_u + bar_w / 2 + 0.9, bar_v0), "label": tick(z_lo)},
    {"value": (bar_u + bar_w / 2 + 0.9, (bar_v0 + bar_v1) / 2), "label": tick((z_lo + z_hi) / 2)},
    {"value": (bar_u + bar_w / 2 + 0.9, bar_v1), "label": tick(z_hi)},
    {"value": (bar_u, bar_v1 + 0.9), "label": Z_COL},
]
bar_lines = []
for b in range(N_BINS):
    for du in np.linspace(-bar_w / 2, bar_w / 2, 16):
        bar_lines.append((b, [(bar_u + du, bar_edges[b]), (bar_u + du, bar_edges[b + 1])]))

# Style: series colours follow the add() order below
n_series = len(edges) + len(axis_segs) + 1 + len(bar_lines) + 1
style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(ramp[e[1]] for e in edges)
    + (INK_MUTED,) * len(axis_segs)
    + (INK,)
    + tuple(ramp[b] for b, _ in bar_lines)
    + (INK,),
    title_font_size=56,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=44,
    value_colors=(INK,) * n_series,
    stroke_width=4,
    opacity=1.0,
    opacity_hover=1.0,
)

# pygal fixes printed labels at 10px in its stylesheet; raise them to the tick size
label_css = f"inline:.text-overlay text.label {{font-size: 44px !important; fill: {INK} !important;}}"
chart = pygal.XY(
    css=[*pygal.Config().css, label_css],
    style=style,
    width=3200,
    height=1800,
    title="surface-basic · pygal · anyplot.ai",
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    xrange=(np.nanmin(u_all) - 2.0, bar_u + 4.0),
    range=(np.nanmin(v_all) - 2.5, np.nanmax(v_all) + 1.5),
    margin=30,
    show_dots=False,
    stroke=True,
    print_labels=True,
    print_values=False,
)

for n, (_, _, pts) in enumerate(edges):
    chart.add(f"edge {n}", pts, show_dots=False)
for n, seg in enumerate(axis_segs):
    chart.add(f"axis {n}", seg, show_dots=False)
chart.add("axis labels", labels, stroke=False, show_dots=True, dots_size=0.1)
for n, (_, seg) in enumerate(bar_lines):
    chart.add(f"bar {n}", seg, show_dots=False)
chart.add("bar labels", bar_labels, stroke=False, show_dots=True, dots_size=0.1)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
