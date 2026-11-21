""" anyplot.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LinearColorMapper
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import make_moons
from sklearn.neighbors import KNeighborsClassifier


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per class in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MESH_POINTS = 400  # mesh resolution along the longer feature axis
MARGIN = 0.15  # share of each feature's range added around the points

# Columns: set these to your table's column names
FEATURE_1 = "Feature 1"  # role: X1
FEATURE_2 = "Feature 2"  # role: X2
CLASS = "Class"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("points.csv")
X, y = make_moons(n_samples=200, noise=0.25, random_state=42)
df = pd.DataFrame({FEATURE_1: X[:, 0], FEATURE_2: X[:, 1], CLASS: [f"Class {c}" for c in y]})

# Plot: reads only df and the constants above
df = df.dropna(subset=[FEATURE_1, FEATURE_2, CLASS]).reset_index(drop=True)
classes = list(df[CLASS].unique())
features = df[[FEATURE_1, FEATURE_2]].to_numpy(dtype=float)
labels = df[CLASS].map({c: i for i, c in enumerate(classes)}).to_numpy()

clf = KNeighborsClassifier(n_neighbors=min(15, len(df))).fit(features, labels)
predicted = clf.predict(features)
df["Predicted"] = [classes[i] for i in predicted]
df["Wrong"] = predicted != labels

# Mesh over the padded feature plane
lo = features.min(axis=0)
hi = features.max(axis=0)
pad = (hi - lo) * MARGIN
lo, hi = lo - pad, hi + pad
step = (hi - lo).max() / MESH_POINTS
xx, yy = np.meshgrid(np.arange(lo[0], hi[0], step), np.arange(lo[1], hi[1], step))
Z = clf.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

p = figure(
    width=3200,
    height=1800,
    title="contour-decision-boundary · python · bokeh · anyplot.ai",
    x_axis_label=FEATURE_1,
    y_axis_label=FEATURE_2,
    tools="",
    toolbar_location=None,
    x_range=(lo[0], hi[0]),
    y_range=(lo[1], hi[1]),
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Predicted regions: one Imprint color per class, translucent so the points stay strongest
region_mapper = LinearColorMapper(palette=IMPRINT_PALETTE[: max(len(classes), 2)], low=0, high=len(classes) - 1)
p.image(
    image=[Z.astype(float)],
    x=lo[0],
    y=lo[1],
    dw=hi[0] - lo[0],
    dh=hi[1] - lo[1],
    color_mapper=region_mapper,
    alpha=0.28,
)

# Training points at their true class, outlined in the page ink so they read on every region
tips = [
    (FEATURE_1, f"@{{{FEATURE_1}}}{{0.2f}}"),
    (FEATURE_2, f"@{{{FEATURE_2}}}{{0.2f}}"),
    ("True class", f"@{{{CLASS}}}"),
    ("Predicted", "@Predicted"),
]
point_layers = []
for i, cls in enumerate(classes):
    rows = ColumnDataSource(df[df[CLASS] == cls])
    layer = p.scatter(
        x=FEATURE_1,
        y=FEATURE_2,
        source=rows,
        size=26,
        fill_color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        line_color=INK,
        line_width=2.5,
        fill_alpha=0.95,
        legend_label=f"{cls} (true)",
    )
    point_layers.append(layer)
p.add_tools(HoverTool(tooltips=tips, renderers=point_layers))

# Misclassified training points get an X on top
wrong = ColumnDataSource(df[df["Wrong"]])
if df["Wrong"].any():
    p.scatter(
        x=FEATURE_1,
        y=FEATURE_2,
        source=wrong,
        marker="x",
        size=44,
        line_color=INK,
        line_width=6,
        legend_label="Misclassified",
    )

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.legend.location = "top_right"
p.legend.label_text_font_size = "30pt"
p.legend.label_text_color = INK_SOFT
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.padding = 18
p.legend.spacing = 10
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.92
p.legend.border_line_color = INK_SOFT

# Save HTML and screenshot it with headless Chrome
output_file(f"plot-{THEME}.html")
save(p)

W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
