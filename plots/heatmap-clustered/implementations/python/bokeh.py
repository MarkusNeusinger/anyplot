"""anyplot.ai
heatmap-clustered: Clustered Heatmap
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 88/100 | Updated: 2026-11-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column, row
from bokeh.models import (
    BasicTicker,
    ColorBar,
    ColumnDataSource,
    FixedTicker,
    HoverTool,
    LinearColorMapper,
    PrintfTickFormatter,
    Range1d,
    Spacer,
)
from bokeh.plotting import figure
from bokeh.resources import CDN
from matplotlib.colors import LinearSegmentedColormap, to_hex
from scipy.cluster.hierarchy import dendrogram, linkage
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"


# Imprint diverging ramp (imprint_div): matte red ↔ theme-adaptive midpoint ↔ blue, 256 stops
IMPRINT_DIV = LinearSegmentedColormap.from_list("imprint_div", ["#AE3030", PAGE_BG, "#4467A3"])
IMPRINT_DIV256 = [to_hex(IMPRINT_DIV(t)) for t in np.linspace(0, 1, 256)]

# Columns: set these to your table's labels
GENE = "Gene"  # role: row_labels
SAMPLE = "Sample"  # role: column_labels
EXPRESSION = "Expression (z-score)"  # role: matrix

# Data: replace this block with your own matrix, for example df = pd.read_csv("expression.csv", index_col=0)
np.random.seed(42)
genes = ["CDK1", "CCNB1", "PLK1", "AURKA", "BUB1"]  # cell cycle
genes += ["GAPDH", "LDHA", "PKM", "HK2", "ENO1"]  # metabolism
genes += ["IL6", "TNF", "IFNG", "IL1B", "CXCL8"]  # immune response
genes += ["MYC", "TP53", "BRCA1", "EGFR", "VEGFA"]  # cancer-related
samples = ["T1_A", "T1_B", "T1_C", "T2_A", "T2_B", "T3_A", "T3_B", "T3_C"]  # tumor
samples += ["N1_A", "N1_B", "N1_C", "N2_A", "N2_B", "N2_C", "N2_D"]  # normal

values = np.random.randn(len(genes), len(samples)) * 0.5
values[0:5, 0:8] += 2.0  # cell cycle genes up in tumors
values[0:5, 8:15] -= 1.5
values[5:10, 0:8] += 1.2  # metabolism moderately up in tumors
values[5:10, 8:15] -= 0.8
values[10:15, 0:5] += 1.5  # immune genes: mixed pattern
values[10:15, 5:8] -= 0.5
values[10:15, 8:12] += 0.8
values[10:15, 12:15] -= 1.2
values[15:20, 0:8] += 1.8  # cancer-related genes up in tumors
values[15:20, 8:15] -= 1.0

df = pd.DataFrame(values, index=pd.Index(genes, name=GENE), columns=pd.Index(samples, name=SAMPLE))

# Plot: reads only df and the constants above
matrix = df.to_numpy(dtype=float)
n_rows, n_cols = matrix.shape

# Ward clustering with Euclidean distance; a missing cell is filled with its row mean for clustering only
filled = np.where(np.isnan(matrix), np.nanmean(matrix, axis=1, keepdims=True), matrix)
row_dendro = dendrogram(linkage(filled, method="ward", metric="euclidean"), no_plot=True)
col_dendro = dendrogram(linkage(filled.T, method="ward", metric="euclidean"), no_plot=True)
row_order = row_dendro["leaves"]
col_order = col_dendro["leaves"]
ordered = df.iloc[row_order, col_order]

# First clustered row at the top: row leaf k sits at y = n_rows - 1 - k, column leaf k at x = k
cells = ordered.stack(future_stack=True).rename(EXPRESSION).reset_index()
cells["x"] = cells[SAMPLE].map({label: k for k, label in enumerate(ordered.columns)})
cells["y"] = cells[GENE].map({label: n_rows - 1 - k for k, label in enumerate(ordered.index)})
source = ColumnDataSource(cells)

limit = float(np.ceil(np.nanmax(np.abs(matrix))))
mapper = LinearColorMapper(palette=IMPRINT_DIV256, low=-limit, high=limit, nan_color=PAGE_BG)

# Layout on a 2400 × 2400 canvas: title band, column dendrogram band, then row dendrogram + heatmap
TITLE_H, DENDRO = 140, 340
HEAT_W, HEAT_H = 2400 - DENDRO, 2400 - TITLE_H - DENDRO
# The left border leaves room for the first rotated sample label, which Bokeh otherwise shifts inward
BORDER_LEFT, BORDER_RIGHT, BORDER_TOP, BORDER_BOTTOM = 80, 560, 10, 240

x_range = Range1d(-0.5, n_cols - 0.5)
y_range = Range1d(-0.5, n_rows - 0.5)

heatmap = figure(
    width=HEAT_W,
    height=HEAT_H,
    x_range=x_range,
    y_range=y_range,
    x_axis_label=SAMPLE,
    y_axis_label=GENE,
    y_axis_location="right",
    toolbar_location=None,
    tools="",
    min_border_left=BORDER_LEFT,
    min_border_right=BORDER_RIGHT,
    min_border_top=BORDER_TOP,
    min_border_bottom=BORDER_BOTTOM,
)
cell_glyphs = heatmap.rect(
    x="x",
    y="y",
    width=1,
    height=1,
    source=source,
    fill_color={"field": EXPRESSION, "transform": mapper},
    line_color=PAGE_BG,
    line_width=1.5,
)
heatmap.add_tools(
    HoverTool(
        renderers=[cell_glyphs],
        tooltips=[(GENE, f"@{{{GENE}}}"), (SAMPLE, f"@{{{SAMPLE}}}"), (EXPRESSION, f"@{{{EXPRESSION}}}{{0.00}}")],
    )
)

# Tick labels name each row and column at its own cell
heatmap.xaxis.ticker = FixedTicker(ticks=list(range(n_cols)))
heatmap.xaxis.major_label_overrides = {k: str(label) for k, label in enumerate(ordered.columns)}
heatmap.xaxis.major_label_orientation = np.pi / 4
heatmap.yaxis.ticker = FixedTicker(ticks=list(range(n_rows)))
heatmap.yaxis.major_label_overrides = {n_rows - 1 - k: str(label) for k, label in enumerate(ordered.index)}

for axis in (heatmap.xaxis, heatmap.yaxis):
    axis.axis_label_text_font_size = "42pt"
    axis.axis_label_text_color = INK
    axis.axis_label_text_font_style = "normal"
    axis.major_label_text_font_size = "34pt"
    axis.major_label_text_color = INK_SOFT
    axis.axis_line_color = None
    axis.major_tick_line_color = None
    axis.minor_tick_line_color = None
# Rotated sample labels need a smaller size than the gene labels to keep a gap between neighbours
heatmap.xaxis.major_label_text_font_size = "30pt"
heatmap.grid.grid_line_color = None
heatmap.outline_line_color = None
heatmap.background_fill_color = PAGE_BG
heatmap.border_fill_color = PAGE_BG

color_bar = ColorBar(
    color_mapper=mapper,
    ticker=BasicTicker(desired_num_ticks=7),
    formatter=PrintfTickFormatter(format="%.0f"),
    title=EXPRESSION,
    title_text_font_size="30pt",
    title_text_color=INK,
    title_text_font_style="normal",
    title_standoff=20,
    major_label_text_font_size="30pt",
    major_label_text_color=INK_SOFT,
    major_tick_line_color=None,
    label_standoff=14,
    width=50,
    padding=30,
    bar_line_color=None,
    border_line_color=None,
    background_fill_color=PAGE_BG,
)
heatmap.add_layout(color_bar, "right")

# Column dendrogram (top): scipy places leaf k at 10k + 5, which maps to heatmap column x = k
col_heights = np.array(col_dendro["dcoord"])
col_dendro_fig = figure(
    width=HEAT_W,
    height=DENDRO,
    x_range=x_range,
    y_range=Range1d(0, col_heights.max() * 1.05),
    toolbar_location=None,
    tools="",
    min_border_left=BORDER_LEFT,
    min_border_right=BORDER_RIGHT,
    min_border_top=20,
    min_border_bottom=10,
)
col_dendro_fig.multi_line(
    xs=[list((np.array(xs) - 5) / 10) for xs in col_dendro["icoord"]],
    ys=[list(ys) for ys in col_dendro["dcoord"]],
    line_color=INK_SOFT,
    line_width=3,
)

# Row dendrogram (left), root on the left: leaf k maps to heatmap row y = n_rows - 1 - k
row_heights = np.array(row_dendro["dcoord"])
row_dendro_fig = figure(
    width=DENDRO,
    height=HEAT_H,
    x_range=Range1d(row_heights.max() * 1.05, 0),
    y_range=y_range,
    toolbar_location=None,
    tools="",
    min_border_left=20,
    min_border_right=10,
    min_border_top=BORDER_TOP,
    min_border_bottom=BORDER_BOTTOM,
)
row_dendro_fig.multi_line(
    xs=[list(xs) for xs in row_dendro["dcoord"]],
    ys=[list(n_rows - 1 - (np.array(ys) - 5) / 10) for ys in row_dendro["icoord"]],
    line_color=INK_SOFT,
    line_width=3,
)

for fig in (col_dendro_fig, row_dendro_fig):
    fig.axis.visible = False
    fig.grid.grid_line_color = None
    fig.outline_line_color = None
    fig.background_fill_color = PAGE_BG
    fig.border_fill_color = PAGE_BG

# Title band spanning the full canvas
title = "heatmap-clustered · python · bokeh · anyplot.ai"
title_fig = figure(width=2400, height=TITLE_H, x_range=(0, 1), y_range=(0, 1), toolbar_location=None, tools="")
title_fig.text(
    x=[0.5],
    y=[0.4],
    text=[title],
    text_font_size=f"{round(50 * min(1.0, 67 / len(title)))}pt",
    text_align="center",
    text_baseline="middle",
    text_color=INK,
)
title_fig.axis.visible = False
title_fig.grid.grid_line_color = None
title_fig.outline_line_color = None
title_fig.background_fill_color = PAGE_BG
title_fig.border_fill_color = PAGE_BG

corner = Spacer(width=DENDRO, height=DENDRO, styles={"background-color": PAGE_BG})
layout = column(
    title_fig,
    row(corner, col_dendro_fig, styles={"background-color": PAGE_BG}),
    row(row_dendro_fig, heatmap, styles={"background-color": PAGE_BG}),
    styles={"background-color": PAGE_BG},
)

# Save: interactive HTML, then a headless Chrome screenshot of it
output_file(f"plot-{THEME}.html")
save(layout, resources=CDN, title=title)

W, H = 2400, 2400
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
