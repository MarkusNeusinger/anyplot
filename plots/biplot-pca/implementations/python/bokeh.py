""" anyplot.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-17
"""

import os
import sys
import time
from pathlib import Path


# Prevent local bokeh.py from shadowing bokeh package
if "" in sys.path:
    sys.path.remove("")
if "." in sys.path:
    sys.path.remove(".")

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import Arrow, ColumnDataSource, Label, VeeHead
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first series is ALWAYS #009E73 (brand)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Iris dataset
iris = load_iris()
X = iris.data
y = iris.target
feature_names = ["sepal length", "sepal width", "petal length", "petal width"]
target_names = iris.target_names

# Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# PCA
pca = PCA(n_components=2)
scores = pca.fit_transform(X_scaled)
loadings = pca.components_.T
explained_var = pca.explained_variance_ratio_ * 100

# Scale loadings for visibility
score_max = np.abs(scores).max()
loading_scale = score_max * 0.9 / np.abs(loadings).max()
loadings_scaled = loadings * loading_scale

# Create figure with appropriate range
margin = 1.5
x_range = (scores[:, 0].min() - margin, scores[:, 0].max() + margin)
y_range = (scores[:, 1].min() - margin, scores[:, 1].max() + margin)

p = figure(
    width=4800,
    height=2700,
    title="biplot-pca · bokeh · anyplot.ai",
    x_axis_label=f"PC1 ({explained_var[0]:.1f}%)",
    y_axis_label=f"PC2 ({explained_var[1]:.1f}%)",
    x_range=x_range,
    y_range=y_range,
)

# Style title and axes
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Theme-adaptive styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Plot observation scores by group
for i, name in enumerate(target_names):
    mask = y == i
    source = ColumnDataSource(data={"x": scores[mask, 0], "y": scores[mask, 1]})
    p.scatter(x="x", y="y", source=source, size=20, alpha=0.7, color=IMPRINT[i], legend_label=name)

# Style legend
if p.legend:
    p.legend.location = "top_left"
    p.legend.label_text_font_size = "16pt"
    p.legend.label_text_color = INK_SOFT
    p.legend.background_fill_color = ELEVATED_BG
    p.legend.background_fill_alpha = 0.9
    p.legend.border_line_color = INK_SOFT
    p.legend.border_line_alpha = 0.5

# Draw loading arrows
arrow_color = INK_SOFT

# Custom label offsets for each feature to avoid overlap
label_offsets = {
    "sepal length": (0.4, 0.5),
    "sepal width": (-0.3, 0.4),
    "petal length": (0.5, -0.4),
    "petal width": (0.3, 0.5),
}

for i, name in enumerate(feature_names):
    x_end = loadings_scaled[i, 0]
    y_end = loadings_scaled[i, 1]

    # Add arrow
    p.add_layout(
        Arrow(
            end=VeeHead(size=30, fill_color=arrow_color, line_color=arrow_color),
            x_start=0,
            y_start=0,
            x_end=x_end,
            y_end=y_end,
            line_width=3,
            line_color=arrow_color,
        )
    )

    # Add label with custom offset
    offset_x, offset_y = label_offsets[name]
    label = Label(
        x=x_end + offset_x,
        y=y_end + offset_y,
        text=name,
        text_font_size="16pt",
        text_color=INK_SOFT,
        text_align="center",
    )
    p.add_layout(label)

# Add origin reference lines
p.line(x=[x_range[0], x_range[1]], y=[0, 0], line_width=2, line_color=INK_SOFT, line_alpha=0.3, line_dash="dashed")
p.line(x=[0, 0], y=[y_range[0], y_range[1]], line_width=2, line_color=INK_SOFT, line_alpha=0.3, line_dash="dashed")

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
W, H = 4800, 2700
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
