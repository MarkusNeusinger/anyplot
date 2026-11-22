"""anyplot.ai
ternary-density: Ternary Density Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-19
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential density ramp is built from positions 1 and 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]

# Columns: set these to your table's column names
SAND = "Sand (%)"  # role: component_a
SILT = "Silt (%)"  # role: component_b
CLAY = "Clay (%)"  # role: component_c

# Data: replace this block with your own table, for example df = pd.read_csv("sediments.csv")
np.random.seed(42)
n_per_cluster = 400

# Cluster 1: sandy sediment (high sand, low clay)
c1_sand = np.random.beta(12, 2, n_per_cluster) * 80 + 15
c1_clay = np.random.beta(2, 8, n_per_cluster) * (100 - c1_sand) * 0.3
c1_silt = 100 - c1_sand - c1_clay

# Cluster 2: silty sediment (high silt)
c2_silt = np.random.beta(10, 2, n_per_cluster) * 70 + 25
c2_sand = np.random.beta(3, 6, n_per_cluster) * (100 - c2_silt) * 0.7
c2_clay = 100 - c2_silt - c2_sand

# Cluster 3: clay-rich sediment (high clay)
c3_clay = np.random.beta(8, 3, n_per_cluster) * 60 + 30
c3_sand = np.random.beta(2, 5, n_per_cluster) * (100 - c3_clay) * 0.5
c3_silt = 100 - c3_clay - c3_sand

# Combine and normalize to exact 100%
sand = np.clip(np.concatenate([c1_sand, c2_sand, c3_sand]), 0.1, 99.8)
silt = np.clip(np.concatenate([c1_silt, c2_silt, c3_silt]), 0.1, 99.8)
clay = np.clip(np.concatenate([c1_clay, c2_clay, c3_clay]), 0.1, 99.8)
total = sand + silt + clay
df = pd.DataFrame({SAND: sand / total * 100, SILT: silt / total * 100, CLAY: clay / total * 100})

# Plot: reads only df and the constants above
# Ternary → Cartesian: first component at (0, 0), second at (1, 0), third at the apex
sqrt3_2 = np.sqrt(3) / 2
parts = df[[SAND, SILT, CLAY]].dropna()
shares = parts.to_numpy() / parts.sum(axis=1).to_numpy()[:, None]
x_pts = 0.5 * (2 * shares[:, 1] + shares[:, 2])
y_pts = sqrt3_2 * shares[:, 2]

# KDE on the transformed coordinates, automatic bandwidth (Scott's rule)
grid_res = 160
x_grid = np.linspace(0, 1, grid_res)
y_grid = np.linspace(0, sqrt3_2, grid_res)
xx, yy = np.meshgrid(x_grid, y_grid)
kde = gaussian_kde(np.vstack([x_pts, y_pts]), bw_method="scott")
density = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)

# Triangle mask (half-plane method)
margin = 0.004
inside = (yy >= -margin) & (np.sqrt(3) * xx + yy <= np.sqrt(3) + margin) & (yy - np.sqrt(3) * xx <= margin)

# Cell half-widths for mark_rect; cells overlap their neighbours slightly so no seams show
dx = (x_grid[1] - x_grid[0]) / 2
dy = (y_grid[1] - y_grid[0]) / 2
rows, cols = np.nonzero(inside)
density_df = pd.DataFrame(
    {
        "x1": xx[rows, cols] - dx,
        "x2": xx[rows, cols] + dx * 1.6,
        "y1": yy[rows, cols] - dy,
        "y2": yy[rows, cols] + dy * 1.6,
        "density": density[rows, cols],
    }
)

# Triangle outline vertices
triangle_df = pd.DataFrame({"x": [0, 1, 0.5, 0], "y": [0, 0, sqrt3_2, 0], "order": [0, 1, 2, 3]})

# Ternary grid lines (10% intervals for all three components)
grid_lines = []
for i in range(1, 10):
    frac = i / 10
    y_val = frac * sqrt3_2
    grid_lines += [
        {"x": y_val / np.sqrt(3), "y": y_val, "line": f"h{i}", "o": 0},
        {"x": 1 - y_val / np.sqrt(3), "y": y_val, "line": f"h{i}", "o": 1},
        {"x": frac, "y": 0, "line": f"s{i}", "o": 0},
        {"x": frac / 2, "y": frac * sqrt3_2, "line": f"s{i}", "o": 1},
        {"x": 1 - frac, "y": 0, "line": f"t{i}", "o": 0},
        {"x": 1 - frac / 2, "y": frac * sqrt3_2, "line": f"t{i}", "o": 1},
    ]
grid_df = pd.DataFrame(grid_lines)

# Vertex labels, each placed outside its corner
labels_df = pd.DataFrame({"x": [-0.03, 1.03, 0.5], "y": [-0.05, -0.05, sqrt3_2 + 0.05], "label": [SAND, SILT, CLAY]})

# Shared scale domains so every layer lines up (equal units on both axes)
X_DOMAIN = [-0.1, 1.1]
Y_DOMAIN = [-0.1, 1.1]
x_scale = alt.Scale(domain=X_DOMAIN, nice=False)
y_scale = alt.Scale(domain=Y_DOMAIN, nice=False)

heatmap = (
    alt.Chart(density_df)
    .mark_rect()
    .encode(
        x=alt.X("x1:Q", scale=x_scale, axis=None),
        x2=alt.X2("x2:Q"),
        y=alt.Y("y1:Q", scale=y_scale, axis=None),
        y2=alt.Y2("y2:Q"),
        color=alt.Color(
            "density:Q",
            scale=alt.Scale(range=IMPRINT_SEQ),
            legend=alt.Legend(title="Density", titleFontSize=12, labelFontSize=10, orient="right", gradientLength=140),
        ),
    )
)

triangle = (
    alt.Chart(triangle_df)
    .mark_line(color=INK, strokeWidth=2)
    .encode(x=alt.X("x:Q", scale=x_scale, axis=None), y=alt.Y("y:Q", scale=y_scale, axis=None), order="order:O")
)

# Grid sits above the density so it stays visible where the density is high
grid = (
    alt.Chart(grid_df)
    .mark_line(color=INK, strokeWidth=0.6, opacity=0.3)
    .encode(
        x=alt.X("x:Q", scale=x_scale, axis=None), y=alt.Y("y:Q", scale=y_scale, axis=None), detail="line:N", order="o:O"
    )
)

labels = (
    alt.Chart(labels_df)
    .mark_text(fontSize=14, fontWeight="bold", color=INK)
    .encode(x=alt.X("x:Q", scale=x_scale, axis=None), y=alt.Y("y:Q", scale=y_scale, axis=None), text="label:N")
)

title = "Sediment Composition · ternary-density · python · altair · anyplot.ai"
title_size = max(11, round(16 * min(1.0, 67 / len(title))))

chart = (
    alt.layer(heatmap, grid, triangle, labels)
    .properties(background=PAGE_BG, width=440, height=440, title=alt.Title(title, fontSize=title_size, color=INK))
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=8)
)

# Save: square canvas, padded (never cropped) to exactly 2400 x 2400
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
TW, TH = 2400, 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
