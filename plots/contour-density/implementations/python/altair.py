""" anyplot.ai
contour-density: Density Contour Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 73/100 | Updated: 2026-11-21
"""

import os
import sys
from pathlib import Path


script_dir = str(Path(__file__).parent)
while script_dir in sys.path:
    sys.path.remove(script_dir)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402
from scipy.stats import gaussian_kde  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GRID_SIZE = 80  # KDE evaluation grid points per axis
GRID_MARGIN = 0.1  # grid extends this share of each variable's range beyond the data
DENSITY = "Density"  # derived column holding the estimated density

# Columns: set these to your table's column names
TEMPERATURE = "Temperature (°C)"  # role: x
HUMIDITY = "Humidity (%)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("climate.csv")
np.random.seed(42)
temp1 = np.random.normal(15, 4, 150)
humidity1 = np.random.normal(30, 8, 150)
temp2 = np.random.normal(25, 5, 200)
humidity2 = np.random.normal(55, 10, 200)
temp3 = np.random.normal(38, 4, 150)
humidity3 = np.random.normal(75, 8, 150)
df = pd.DataFrame(
    {TEMPERATURE: np.concatenate([temp1, temp2, temp3]), HUMIDITY: np.concatenate([humidity1, humidity2, humidity3])}
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

points = df[[TEMPERATURE, HUMIDITY]].dropna()
kde = gaussian_kde(points.to_numpy().T)
spans = points.max() - points.min()
x_grid = np.linspace(
    points[TEMPERATURE].min() - GRID_MARGIN * spans[TEMPERATURE],
    points[TEMPERATURE].max() + GRID_MARGIN * spans[TEMPERATURE],
    GRID_SIZE,
)
y_grid = np.linspace(
    points[HUMIDITY].min() - GRID_MARGIN * spans[HUMIDITY],
    points[HUMIDITY].max() + GRID_MARGIN * spans[HUMIDITY],
    GRID_SIZE,
)
xx, yy = np.meshgrid(x_grid, y_grid)
z = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
grid = pd.DataFrame({TEMPERATURE: xx.ravel(), HUMIDITY: yy.ravel(), DENSITY: z.ravel()})

x_step = x_grid[1] - x_grid[0]
y_step = y_grid[1] - y_grid[0]
x_domain = [float(x_grid[0] - x_step), float(x_grid[-1] + x_step)]
y_domain = [float(y_grid[0] - y_step), float(y_grid[-1] + y_step)]

# Imprint sequential colormap: strongest color marks the highest density
IMPRINT_SEQ = ["#009E73", "#4467A3"]

axis_style = {
    "labelFontSize": 10,
    "titleFontSize": 12,
    "grid": False,
    "tickCount": 8,
    "labelColor": INK_SOFT,
    "titleColor": INK,
    "domainColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart = (
    alt.Chart(grid)
    .mark_rect()
    .encode(
        x=alt.X(
            TEMPERATURE.translate(ESCAPE),
            type="quantitative",
            bin=alt.Bin(step=float(x_step)),
            scale=alt.Scale(domain=x_domain),
            title=TEMPERATURE,
            axis=alt.Axis(**axis_style),
        ),
        y=alt.Y(
            HUMIDITY.translate(ESCAPE),
            type="quantitative",
            bin=alt.Bin(step=float(y_step)),
            scale=alt.Scale(domain=y_domain),
            title=HUMIDITY,
            axis=alt.Axis(**axis_style),
        ),
        color=alt.Color(
            f"mean({DENSITY.translate(ESCAPE)})",
            type="quantitative",
            scale=alt.Scale(range=IMPRINT_SEQ),
            title=DENSITY,
            legend=alt.Legend(
                titleFontSize=12,
                labelFontSize=10,
                gradientLength=200,
                gradientThickness=14,
                titleColor=INK,
                labelColor=INK_SOFT,
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
            ),
        ),
    )
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(text="contour-density · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) the PNG up to the canonical 3200 x 1800 canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds target {TW}x{TH}; shrink width/height")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
