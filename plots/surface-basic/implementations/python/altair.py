"""anyplot.ai
surface-basic: Basic 3D Surface Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-05
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
ELEVATION = 25  # camera elevation in degrees
AZIMUTH = 45  # camera azimuth in degrees
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

# Columns: set these to your table's column names
X = "x"  # role: x
Y = "y"  # role: y
Z = "z"  # role: z

# Data: replace this block with your own long table of x, y, z, for example df = pd.read_csv("surface.csv")
grid = np.linspace(-3, 3, 50)
gx, gy = np.meshgrid(grid, grid)
df = pd.DataFrame({X: gx.ravel(), Y: gy.ravel(), Z: (np.sin(gx) * np.cos(gy)).ravel()})

# Plot: reads only df and the constants above
xs = np.sort(df[X].unique())
ys = np.sort(df[Y].unique())
surface = df.pivot_table(index=Y, columns=X, values=Z).reindex(index=ys, columns=xs).to_numpy()
gx, gy = np.meshgrid(xs, ys)

# Oblique projection: rotate about the vertical axis, then tilt towards the viewer
elev, azim = np.radians(ELEVATION), np.radians(AZIMUTH)
depth = gx * np.sin(azim) + gy * np.cos(azim)
screen_x = gx * np.cos(azim) - gy * np.sin(azim)
screen_y = depth * np.sin(elev) + surface * np.cos(elev)


def corners(a):
    """Stack the four corners of every grid cell: shape (4, rows-1, cols-1)."""
    return np.stack([a[:-1, :-1], a[:-1, 1:], a[1:, :-1], a[1:, 1:]])


# One rectangle per grid cell, widened slightly so neighbours leave no seams
cell_x, cell_y = corners(screen_x), corners(screen_y)
seam = 0.1 * np.median(np.diff(xs))
cells = pd.DataFrame(
    {
        "x1": cell_x.min(axis=0).ravel() - seam,
        "x2": cell_x.max(axis=0).ravel() + seam,
        "y1": cell_y.min(axis=0).ravel() - seam,
        "y2": cell_y.max(axis=0).ravel() + seam,
        Z: corners(surface).mean(axis=0).ravel(),
        "depth": corners(depth).mean(axis=0).ravel(),
    }
)
# Painter's algorithm: far cells first, nearer cells paint over them
cells = cells.sort_values("depth", ascending=False).reset_index(drop=True)
cells["order"] = cells.index

axis_style = {
    "labelFontSize": 18,
    "titleFontSize": 22,
    "labelColor": INK_SOFT,
    "titleColor": INK,
    "domainColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridColor": INK,
    "gridOpacity": 0.1,
}

chart = (
    alt.Chart(cells)
    .mark_rect(strokeWidth=0.3, stroke=INK_SOFT, strokeOpacity=0.15)
    .encode(
        x=alt.X("x1", type="quantitative", title=f"{X} (projected, {AZIMUTH}° view)", axis=alt.Axis(**axis_style)),
        y=alt.Y("y1", type="quantitative", title=f"{Z} (height)", axis=alt.Axis(**axis_style)),
        x2="x2",
        y2="y2",
        color=alt.Color(
            Z.translate(ESCAPE),
            type="quantitative",
            title=Z,
            scale=alt.Scale(range=[IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]),
            legend=alt.Legend(
                titleFontSize=20,
                labelFontSize=16,
                labelColor=INK_SOFT,
                titleColor=INK,
                gradientLength=240,
                gradientThickness=22,
            ),
        ),
        order=alt.Order("order", type="quantitative"),
        tooltip=[
            alt.Tooltip(Z.translate(ESCAPE), type="quantitative", title=Z, format=".3f"),
            alt.Tooltip("x1", type="quantitative", title=f"{X} (projected)", format=".2f"),
            alt.Tooltip("y1", type="quantitative", title=f"{Z} (projected)", format=".2f"),
        ],
    )
    .add_params(alt.selection_interval(bind="scales"))
    .properties(
        width=620,
        height=320,
        title=alt.Title("surface-basic · python · altair · anyplot.ai", fontSize=24, color=INK),
        background=PAGE_BG,
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
)

# Save outputs, padded (never cropped) to the 3200 x 1800 target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
img.thumbnail((TW, TH))  # long column names can widen the chart: scale down, never crop
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
