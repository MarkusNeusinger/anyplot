""" anyplot.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-22
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LabelSet, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: a single series uses position 1
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SOURCE = "Exporter"  # role: edges
TARGET = "Importer"  # role: nodes
WEIGHT = "Trade volume (B USD)"  # role: weight

# Data: replace this block with your own edge list, for example df = pd.read_csv("edges.csv")
# Trade network between 15 countries, one row per trade relationship
df = pd.DataFrame(
    [
        ("USA", "China", 580),
        ("USA", "Germany", 180),
        ("USA", "Japan", 220),
        ("USA", "UK", 130),
        ("USA", "Canada", 620),
        ("USA", "Mexico", 680),
        ("USA", "S. Korea", 170),
        ("China", "Japan", 340),
        ("China", "S. Korea", 290),
        ("China", "Germany", 220),
        ("China", "Australia", 180),
        ("China", "Singapore", 120),
        ("China", "India", 110),
        ("Germany", "UK", 160),
        ("Germany", "France", 180),
        ("Germany", "Netherlands", 200),
        ("Germany", "Switzerland", 140),
        ("UK", "France", 110),
        ("France", "Netherlands", 90),
        ("Japan", "S. Korea", 85),
        ("India", "Singapore", 55),
        ("Singapore", "Australia", 70),
        ("Canada", "Mexico", 80),
        ("USA", "Brazil", 95),
        ("Brazil", "India", 40),
    ],
    columns=[SOURCE, TARGET, WEIGHT],
)

# Plot: reads only df and the constants above
countries = list(pd.unique(df[[SOURCE, TARGET]].to_numpy().ravel()))
n_nodes = len(countries)
index = {name: i for i, name in enumerate(countries)}
src = df[SOURCE].map(index).to_numpy()
tgt = df[TARGET].map(index).to_numpy()
weights = df[WEIGHT].to_numpy(dtype=float)
w_min, w_max = np.nanmin(weights), np.nanmax(weights)

# Force-directed layout: all nodes repel, edges attract in proportion to their weight
rng = np.random.default_rng(42)
positions = rng.random((n_nodes, 2)) * 10
for _ in range(200):
    diff = positions[:, None, :] - positions[None, :, :]
    dist = np.linalg.norm(diff, axis=2) + 0.1
    forces = (diff / dist[..., None] ** 2 * 2).sum(axis=1)
    pull = (positions[tgt] - positions[src]) * 0.04 * (weights / np.nanmean(weights))[:, None]
    np.add.at(forces, src, pull)
    np.add.at(forces, tgt, -pull)
    positions += forces * 0.1

# Fill a landscape canvas: each axis spans [-1, 1], x stretched by the 16:9 aspect
positions -= positions.mean(axis=0)
positions /= np.abs(positions).max(axis=0)
ASPECT = 16 / 9
positions[:, 0] *= ASPECT
node_x, node_y = positions[:, 0], positions[:, 1]

# Weighted degree sizes the nodes
weighted_degree = np.zeros(n_nodes)
np.add.at(weighted_degree, src, weights)
np.add.at(weighted_degree, tgt, weights)
wd_span = np.ptp(weighted_degree) or 1.0
node_sizes = 60 + (weighted_degree - weighted_degree.min()) / wd_span * 80


def edge_width(w):
    """Line width in px: thinnest edge 3, thickest 18, linear in the weight."""
    return 3 + (w - w_min) / ((w_max - w_min) or 1.0) * 15


def edge_alpha(w):
    """Heavier edges are more opaque, so thin ones stay visible but quiet."""
    return 0.35 + (w - w_min) / ((w_max - w_min) or 1.0) * 0.45


edge_source = ColumnDataSource(
    {
        "x0": node_x[src],
        "y0": node_y[src],
        "x1": node_x[tgt],
        "y1": node_y[tgt],
        "width": edge_width(weights),
        "alpha": edge_alpha(weights),
    }
)
node_source = ColumnDataSource(
    {
        "x": node_x,
        "y": node_y,
        "size": node_sizes,
        "name": countries,
        "lift": node_sizes / 2 + 8,
        "degree": [f"{int(wd):,}" for wd in weighted_degree],
    }
)

pad = 0.2
p = figure(
    width=3200,
    height=1800,
    title="network-weighted · python · bokeh · anyplot.ai",
    tools="",
    toolbar_location=None,
    x_range=Range1d(node_x.min() - pad * ASPECT, node_x.max() + pad * ASPECT),
    y_range=Range1d(node_y.min() - pad, node_y.max() + pad),
    min_border_top=110,
    min_border_bottom=40,
    min_border_left=40,
    min_border_right=40,
)

# Style
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.title.text_color = INK
p.title.text_font_size = "50pt"
p.title.align = "center"

# Edges first, so nodes and labels sit on top
p.segment(
    x0="x0",
    y0="y0",
    x1="x1",
    y1="y1",
    source=edge_source,
    line_width="width",
    line_alpha="alpha",
    line_color=IMPRINT_PALETTE[0],
    line_cap="round",
)

nodes_renderer = p.scatter(
    x="x",
    y="y",
    source=node_source,
    size="size",
    fill_color=IMPRINT_PALETTE[0],
    fill_alpha=0.9,
    line_color=INK_SOFT,
    line_width=4,
)
p.add_tools(HoverTool(renderers=[nodes_renderer], tooltips=[("Country", "@name"), (f"Total {WEIGHT}", "@degree")]))
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="name",
        source=node_source,
        text_font_size="26pt",
        text_font_style="bold",
        text_align="center",
        text_baseline="bottom",
        y_offset="lift",
        text_color=INK,
    )
)

# Legend: sample edges drawn with the same width function as the data edges
legend_x = node_x.min() - pad * ASPECT * 0.85
legend_y = node_y.min() + 0.45
p.text(
    x=[legend_x],
    y=[legend_y],
    text=[WEIGHT],
    text_font_size="34pt",
    text_font_style="bold",
    text_color=INK,
    text_baseline="middle",
)
for k, w in enumerate([w_min, (w_min + w_max) / 2, w_max]):
    y_pos = legend_y - 0.16 - k * 0.13
    p.segment(
        x0=[legend_x],
        y0=[y_pos],
        x1=[legend_x + 0.3],
        y1=[y_pos],
        line_width=edge_width(w),
        line_alpha=edge_alpha(w),
        line_color=IMPRINT_PALETTE[0],
        line_cap="round",
    )
    p.text(
        x=[legend_x + 0.38],
        y=[y_pos],
        text=[f"{w:,.0f}"],
        text_font_size="30pt",
        text_baseline="middle",
        text_color=INK_SOFT,
    )
p.text(
    x=[legend_x],
    y=[legend_y - 0.16 - 3 * 0.13],
    text=["Node size: total trade volume"],
    text_font_size="28pt",
    text_font_style="italic",
    text_baseline="middle",
    text_color=INK_SOFT,
)

# Save HTML (interactive artifact) and screenshot it for the PNG
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
