"""anyplot.ai
hive-basic: Basic Hive Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-07
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per axis group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
NODE = "Module"  # role: nodes
GROUP = "Module type"  # role: axis_attribute
DEGREE = "Degree"  # role: extra
EDGE_ENDS = ["Source", "Target"]  # role: edges

# Data: software module dependency network. Replace this block with your own tables:
# `nodes` holds one row per node (NODE, GROUP, DEGREE) and `df` is the edge list (EDGE_ENDS),
# for example df = pd.read_csv("edges.csv")
nodes = pd.DataFrame(
    {
        NODE: [
            "core_main",
            "core_data",
            "core_config",
            "core_init",
            "core_base",
            "util_io",
            "util_parse",
            "util_cache",
            "util_log",
            "util_helper",
            "util_validate",
            "api_rest",
            "api_graphql",
            "api_cli",
            "api_web",
        ],
        GROUP: ["Core"] * 5 + ["Utility"] * 6 + ["Interface"] * 4,
        DEGREE: [8, 6, 5, 7, 4, 5, 4, 3, 6, 2, 4, 7, 5, 4, 6],
    }
)
df = pd.DataFrame(
    [
        ("core_main", "util_io"),
        ("core_main", "util_log"),
        ("core_main", "util_cache"),
        ("core_data", "util_parse"),
        ("core_data", "util_io"),
        ("core_data", "util_validate"),
        ("core_config", "util_io"),
        ("core_config", "util_parse"),
        ("core_init", "util_log"),
        ("core_init", "util_helper"),
        ("core_base", "util_validate"),
        ("util_io", "api_rest"),
        ("util_io", "api_web"),
        ("util_parse", "api_graphql"),
        ("util_parse", "api_cli"),
        ("util_cache", "api_rest"),
        ("util_cache", "api_graphql"),
        ("util_log", "api_rest"),
        ("util_log", "api_cli"),
        ("util_log", "api_web"),
        ("util_validate", "api_rest"),
        ("util_validate", "api_graphql"),
        ("core_main", "api_rest"),
        ("core_main", "api_web"),
        ("core_data", "api_graphql"),
        ("core_init", "api_cli"),
    ],
    columns=EDGE_ENDS,
)

# Plot: reads only df, nodes and the constants above
W, H = 3200, 1800
groups = list(nodes[GROUP].unique())
n_axes = len(groups)
# Axes start up-right and spread evenly around the center
axis_angles = {g: np.pi / 6 + 2 * np.pi * k / n_axes for k, g in enumerate(groups)}
inner_radius, outer_radius = 300, 1000

# Position rule: along its axis a node sits by degree rank (ties keep data order)
nodes = nodes.assign(
    rank=nodes.groupby(GROUP)[DEGREE].rank(method="first"), count=nodes.groupby(GROUP)[DEGREE].transform("size")
)
radius = inner_radius + (nodes["rank"] - 0.5) / nodes["count"] * (outer_radius - inner_radius)
angle = nodes[GROUP].map(axis_angles)
nodes["x"] = radius * np.cos(angle)
nodes["y"] = radius * np.sin(angle)
pos = nodes.set_index(NODE)

# Node size encodes degree
size_base, size_step = 14, 6
nodes["size"] = size_base + nodes[DEGREE] * size_step

# Ranges: equal scale on both directions, centered on the drawing
label_radius = outer_radius + 170
y_min = min(label_radius * np.sin(a) for a in axis_angles.values()) - 200
y_max = max(label_radius * np.sin(a) for a in axis_angles.values()) + 200
x_half = (y_max - y_min) * W / H / 2

p = figure(
    width=W,
    height=H,
    title="hive-basic · python · bokeh · anyplot.ai",
    x_range=(-x_half, x_half),
    y_range=(y_min, y_max),
    tools="",
    toolbar_location=None,
    min_border_top=110,
    min_border_bottom=40,
    min_border_left=40,
    min_border_right=40,
)
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.axis.visible = False
p.grid.visible = False

# Radial axes with their group labels
for i, g in enumerate(groups):
    a = axis_angles[g]
    p.line(
        [inner_radius * np.cos(a), outer_radius * np.cos(a)],
        [inner_radius * np.sin(a), outer_radius * np.sin(a)],
        line_width=6,
        line_color=IMPRINT_PALETTE[i],
        line_alpha=0.6,
    )
    p.add_layout(
        Label(
            x=label_radius * np.cos(a),
            y=label_radius * np.sin(a),
            text=g,
            text_font_size="36pt",
            text_align="center",
            text_baseline="middle",
            text_color=INK,
            text_font_style="bold",
        )
    )

# Edges as quadratic Bezier curves pulled toward the center, colored by the source axis
t = np.linspace(0, 1, 30)
group_index = {g: i for i, g in enumerate(groups)}
for src, tgt in zip(df[EDGE_ENDS[0]], df[EDGE_ENDS[1]], strict=True):
    s, e = pos.loc[src], pos.loc[tgt]
    cx, cy = (s["x"] + e["x"]) * 0.2, (s["y"] + e["y"]) * 0.2
    curve_x = (1 - t) ** 2 * s["x"] + 2 * (1 - t) * t * cx + t**2 * e["x"]
    curve_y = (1 - t) ** 2 * s["y"] + 2 * (1 - t) * t * cy + t**2 * e["y"]
    p.line(
        curve_x.tolist(),
        curve_y.tolist(),
        line_width=3,
        line_color=IMPRINT_PALETTE[group_index[s[GROUP]]],
        line_alpha=0.4,
    )

# Nodes: one scatter per axis group
for i, g in enumerate(groups):
    p.scatter(
        x="x",
        y="y",
        size="size",
        source=ColumnDataSource(nodes[nodes[GROUP] == g]),
        fill_color=IMPRINT_PALETTE[i],
        line_color=PAGE_BG,
        line_width=3,
        alpha=0.9,
    )

# Node labels beside each node, on the side away from the center
for _, row in nodes.iterrows():
    a = axis_angles[row[GROUP]]
    side = a + np.pi / 2
    dx, dy = np.cos(side), np.sin(side)
    offset = row["size"] / 2 / 0.85 + 25
    p.add_layout(
        Label(
            x=row["x"] + offset * dx,
            y=row["y"] + offset * dy,
            text=row[NODE].split("_", 1)[-1],
            text_font_size="26pt",
            text_align="right" if dx < -0.3 else "left" if dx > 0.3 else "center",
            text_baseline="middle",
            text_color=INK,
        )
    )

# Size legend: lowest, middle and highest degree
legend_x = -x_half * 0.88
legend_y = y_max - 300
p.add_layout(
    Label(
        x=legend_x,
        y=legend_y,
        text=f"Node size = {DEGREE.lower()}",
        text_font_size="30pt",
        text_align="left",
        text_baseline="middle",
        text_color=INK,
        text_font_style="bold",
    )
)
low, high = nodes[DEGREE].min(), nodes[DEGREE].max()
for i, (deg, name) in enumerate(zip([low, (low + high) / 2, high], ["Low", "Medium", "High"], strict=True)):
    item_y = legend_y - 170 - i * 150
    p.scatter(
        [legend_x + 60],
        [item_y],
        size=size_base + deg * size_step,
        fill_color=INK_SOFT,
        line_color=PAGE_BG,
        line_width=2,
        alpha=0.7,
    )
    p.add_layout(
        Label(
            x=legend_x + 180,
            y=item_y,
            text=f"{name} ({deg:g})",
            text_font_size="26pt",
            text_align="left",
            text_baseline="middle",
            text_color=INK_SOFT,
        )
    )

# Save HTML and screenshot it with headless Chrome
output_file(f"plot-{THEME}.html")
save(p)

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
