"""anyplot.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-05-17
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LabelSet, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data: Trade network between 15 countries (billions USD annual trade volume)
np.random.seed(42)

# Define nodes (15 countries/regions)
node_labels = [
    "USA",
    "China",
    "Germany",
    "Japan",
    "UK",
    "France",
    "Canada",
    "Mexico",
    "Brazil",
    "India",
    "S. Korea",
    "Australia",
    "Singapore",
    "Netherlands",
    "Switzerland",
]
n_nodes = len(node_labels)

# Generate weighted edges (trade relationships)
edges = [
    # USA trade partners
    (0, 1, 580),
    (0, 2, 180),
    (0, 3, 220),
    (0, 4, 130),
    (0, 6, 620),
    (0, 7, 680),
    (0, 10, 170),
    # China trade partners
    (1, 3, 340),
    (1, 10, 290),
    (1, 2, 220),
    (1, 11, 180),
    (1, 12, 120),
    (1, 9, 110),
    # European connections
    (2, 4, 160),
    (2, 5, 180),
    (2, 13, 200),
    (2, 14, 140),
    (4, 5, 110),
    (5, 13, 90),
    # Asian connections
    (3, 10, 85),
    (9, 12, 55),
    (12, 11, 70),
    # Americas
    (6, 7, 80),
    (0, 8, 95),
    (8, 9, 40),
]

# Use force-directed layout for node positions
positions = np.random.rand(n_nodes, 2) * 10

for _ in range(100):
    forces = np.zeros((n_nodes, 2))

    # Repulsion between all nodes
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            diff = positions[i] - positions[j]
            dist = np.linalg.norm(diff) + 0.1
            force = diff / (dist**2) * 2
            forces[i] += force
            forces[j] -= force

    # Attraction along edges (weighted)
    for src, tgt, weight in edges:
        diff = positions[tgt] - positions[src]
        dist = np.linalg.norm(diff) + 0.1
        force = diff * 0.01 * (weight / 200)
        forces[src] += force
        forces[tgt] -= force

    positions += forces * 0.1

# Center and scale positions
positions -= positions.mean(axis=0)
positions /= positions.max() * 1.2

node_x = positions[:, 0]
node_y = positions[:, 1]

# Calculate weighted degree for node sizing
weighted_degree = np.zeros(n_nodes)
for src, tgt, weight in edges:
    weighted_degree[src] += weight
    weighted_degree[tgt] += weight

# Normalize node sizes
min_size = 30
max_size = 80
node_sizes = min_size + (weighted_degree - weighted_degree.min()) / (
    weighted_degree.max() - weighted_degree.min() + 0.1
) * (max_size - min_size)

# Prepare edge data
edge_x0, edge_y0, edge_x1, edge_y1 = [], [], [], []
edge_widths = []

# Normalize edge weights to line widths
max_weight = max(e[2] for e in edges)
min_weight = min(e[2] for e in edges)

for src, tgt, weight in edges:
    edge_x0.append(node_x[src])
    edge_y0.append(node_y[src])
    edge_x1.append(node_x[tgt])
    edge_y1.append(node_y[tgt])

    # Scale width: thinnest = 2, thickest = 20
    normalized = (weight - min_weight) / (max_weight - min_weight + 0.1)
    edge_widths.append(2 + normalized * 18)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="network-weighted · bokeh · anyplot.ai",
    x_axis_label="",
    y_axis_label="",
    tools="",
    toolbar_location=None,
)

# Remove axes and grid
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

# Theme-adaptive styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.title.text_color = INK
p.title.text_font_size = "28pt"
p.title.align = "center"

# Set range with padding
padding = 0.15
p.x_range = Range1d(node_x.min() - padding, node_x.max() + padding)
p.y_range = Range1d(node_y.min() - padding, node_y.max() + padding)

# Draw edges with weighted line widths
for i in range(len(edge_x0)):
    normalized = (edge_widths[i] - 2) / 18
    alpha = 0.3 + normalized * 0.5
    p.segment(
        x0=[edge_x0[i]],
        y0=[edge_y0[i]],
        x1=[edge_x1[i]],
        y1=[edge_y1[i]],
        line_width=edge_widths[i],
        line_color=BRAND,
        line_alpha=alpha,
        line_cap="round",
    )

# Create node source with weighted degree
node_source = ColumnDataSource(
    data={
        "x": node_x,
        "y": node_y,
        "size": node_sizes,
        "labels": node_labels,
        "weighted_degree": [f"{int(wd):,}" for wd in weighted_degree],
    }
)

# Draw nodes
nodes_renderer = p.scatter(
    x="x", y="y", source=node_source, size="size", fill_color=BRAND, line_color=INK_SOFT, line_width=3, fill_alpha=0.85
)

# Add hover tool for interactivity
hover = HoverTool(
    renderers=[nodes_renderer], tooltips=[("Country", "@labels"), ("Total Trade (B USD)", "@weighted_degree")]
)
p.add_tools(hover)

# Add node labels
labels = LabelSet(
    x="x",
    y="y",
    text="labels",
    source=node_source,
    text_font_size="16pt",
    text_align="center",
    text_baseline="middle",
    text_color=INK,
    text_font_style="bold",
)
p.add_layout(labels)

# Add legend annotation for edge thickness
legend_x = node_x.min() - padding + 0.03
legend_y = node_y.max() + padding - 0.02

# Legend title
p.text(
    x=[legend_x],
    y=[legend_y],
    text=["Trade Volume (B USD)"],
    text_font_size="22pt",
    text_font_style="bold",
    text_color=INK,
)

# Legend lines showing weight scale
legend_weights = [min_weight, (min_weight + max_weight) / 2, max_weight]
legend_labels = [f"{int(w)} B" for w in legend_weights]
legend_widths = [4, 14, 26]

for i, (lw, label) in enumerate(zip(legend_widths, legend_labels, strict=True)):
    y_pos = legend_y - 0.055 - i * 0.05
    normalized = (lw - 2) / 18
    alpha = 0.3 + normalized * 0.5
    p.segment(
        x0=[legend_x],
        y0=[y_pos],
        x1=[legend_x + 0.12],
        y1=[y_pos],
        line_width=lw,
        line_color=BRAND,
        line_alpha=alpha,
        line_cap="round",
    )
    p.text(
        x=[legend_x + 0.14], y=[y_pos], text=[label], text_font_size="18pt", text_baseline="middle", text_color=INK_SOFT
    )

# Save HTML (interactive artifact)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome for PNG
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
