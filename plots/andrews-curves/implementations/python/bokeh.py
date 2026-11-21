"""anyplot.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import load_iris
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
VARIABLES = ["Sepal length (cm)", "Sepal width (cm)", "Petal length (cm)", "Petal width (cm)"]  # role: variable_
SPECIES = "Species"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
iris = load_iris()
df = pd.DataFrame(iris.data, columns=VARIABLES)
df[SPECIES] = pd.Categorical.from_codes(iris.target, ["Setosa", "Versicolor", "Virginica"]).astype(str)

# Plot: reads only df and the constants above
# Normalize variables to similar scales before the Fourier transformation
scaled = StandardScaler().fit_transform(df[VARIABLES].to_numpy(dtype=float))

# Andrews basis: f(t) = x1/sqrt(2) + x2 sin(t) + x3 cos(t) + x4 sin(2t) + ...
t_values = np.linspace(-np.pi, np.pi, 400)
basis = np.empty((len(VARIABLES), len(t_values)))
for i in range(len(VARIABLES)):
    if i == 0:
        basis[i] = 1 / np.sqrt(2)
    elif i % 2 == 1:
        basis[i] = np.sin((i // 2 + 1) * t_values)
    else:
        basis[i] = np.cos((i // 2) * t_values)
curves = scaled @ basis

p = figure(
    width=3200,
    height=1800,
    title="andrews-curves · python · bokeh · anyplot.ai",
    x_axis_label="t (radians)",
    y_axis_label="f(t)",
    background_fill_color=PAGE_BG,
    border_fill_color=PAGE_BG,
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
p.outline_line_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

legend_items = []
for i, (species, rows) in enumerate(df.groupby(SPECIES, sort=False).indices.items()):
    source = ColumnDataSource(
        {"xs": [t_values] * len(rows), "ys": [curves[r] for r in rows], SPECIES: [species] * len(rows)}
    )
    lines = p.multi_line(xs="xs", ys="ys", source=source, line_color=IMPRINT_PALETTE[i], line_alpha=0.4, line_width=3)
    legend_items.append((str(species), [lines]))

p.add_tools(HoverTool(tooltips=[(SPECIES, f"@{{{SPECIES}}}")]))

legend = Legend(items=legend_items, location="top_right")
legend.title = SPECIES
legend.title_text_font_size = "34pt"
legend.title_text_color = INK
legend.label_text_font_size = "34pt"
legend.label_text_color = INK_SOFT
legend.background_fill_color = ELEVATED_BG
legend.background_fill_alpha = 0.95
legend.border_line_color = INK_SOFT
legend.glyph_width = 60
legend.glyph_height = 40
p.add_layout(legend, "right")

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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
