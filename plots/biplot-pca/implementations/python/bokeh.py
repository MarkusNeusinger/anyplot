"""anyplot.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-17
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SEPAL_LENGTH = "Sepal length (cm)"  # role: features
SEPAL_WIDTH = "Sepal width (cm)"  # role: extra
PETAL_LENGTH = "Petal length (cm)"  # role: extra
PETAL_WIDTH = "Petal width (cm)"  # role: extra
SPECIES = "Species"  # role: labels

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
iris = load_iris()
df = pd.DataFrame(iris.data, columns=[SEPAL_LENGTH, SEPAL_WIDTH, PETAL_LENGTH, PETAL_WIDTH])
df[SPECIES] = iris.target_names[iris.target]

# Plot: reads only df and the constants above
FEATURES = [SEPAL_LENGTH, SEPAL_WIDTH, PETAL_LENGTH, PETAL_WIDTH]
clean = df.dropna(subset=FEATURES)
X_scaled = StandardScaler().fit_transform(clean[FEATURES])
pca = PCA(n_components=2)
scores = pca.fit_transform(X_scaled)
loadings = pca.components_.T
explained_var = pca.explained_variance_ratio_ * 100

# One common factor scales all loading arrows to sit alongside the scores
loading_scale = np.abs(scores).max() * 0.9 / np.abs(loadings).max()
loadings_scaled = loadings * loading_scale

# Axis ranges from the scores with a margin
pad_x = 0.12 * np.ptp(scores[:, 0])
pad_y = 0.12 * np.ptp(scores[:, 1])
x_range = (
    min(scores[:, 0].min(), loadings_scaled[:, 0].min()) - pad_x,
    max(scores[:, 0].max(), loadings_scaled[:, 0].max()) + pad_x,
)
y_range = (
    min(scores[:, 1].min(), loadings_scaled[:, 1].min()) - pad_y,
    max(scores[:, 1].max(), loadings_scaled[:, 1].max()) + pad_y,
)

p = figure(
    width=3200,
    height=1800,
    title="biplot-pca · python · bokeh · anyplot.ai",
    x_axis_label=f"PC1 ({explained_var[0]:.1f}% of variance)",
    y_axis_label=f"PC2 ({explained_var[1]:.1f}% of variance)",
    x_range=x_range,
    y_range=y_range,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
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

# Origin reference lines
p.line(x=list(x_range), y=[0, 0], line_width=3, line_color=INK_SOFT, line_alpha=0.3, line_dash="dashed")
p.line(x=[0, 0], y=list(y_range), line_width=3, line_color=INK_SOFT, line_alpha=0.3, line_dash="dashed")

# Observation scores by group
plot_df = pd.DataFrame({"pc1": scores[:, 0], "pc2": scores[:, 1], SPECIES: clean[SPECIES].to_numpy()})
for i, group in enumerate(plot_df[SPECIES].unique()):
    rows = ColumnDataSource(plot_df[plot_df[SPECIES] == group])
    p.scatter(
        x="pc1",
        y="pc2",
        source=rows,
        size=24,
        alpha=0.7,
        color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        legend_label=str(group),
    )

p.legend.title = SPECIES
p.legend.title_text_font_size = "30pt"
p.legend.title_text_color = INK
p.legend.label_text_font_size = "30pt"
p.legend.label_text_color = INK_SOFT
p.legend.location = "top_left"
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = INK_SOFT
p.legend.border_line_alpha = 0.5

# Label heights start at each arrow tip; near-parallel arrows get their labels spread apart
label_y = loadings_scaled[:, 1].copy()
min_gap = 0.07 * (y_range[1] - y_range[0])
order = np.argsort(label_y)
for lower, upper in zip(order[:-1], order[1:], strict=True):
    deficit = min_gap - (label_y[upper] - label_y[lower])
    if deficit > 0:
        label_y[lower] -= deficit / 2
        label_y[upper] += deficit / 2

# Loading arrows, each labeled at its tip and pushed outward along its own direction
for name, (x_end, y_end), text_y in zip(FEATURES, loadings_scaled, label_y, strict=True):
    p.add_layout(
        Arrow(
            end=VeeHead(size=36, fill_color=INK_SOFT, line_color=INK_SOFT),
            x_start=0,
            y_start=0,
            x_end=x_end,
            y_end=y_end,
            line_width=5,
            line_color=INK_SOFT,
        )
    )
    direction = np.array([x_end, y_end]) / np.hypot(x_end, y_end)
    p.add_layout(
        Label(
            x=x_end,
            y=text_y,
            x_offset=float(direction[0] * 30),
            y_offset=float(direction[1] * 30 - 14),
            text=name,
            text_font_size="30pt",
            text_font_style="bold",
            text_color=INK,
            background_fill_color=PAGE_BG,
            background_fill_alpha=0.75,
            text_align="left" if direction[0] >= 0 else "right",
        )
    )

# Save HTML + PNG via headless Chrome
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
