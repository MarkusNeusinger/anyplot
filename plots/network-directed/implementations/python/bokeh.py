"""anyplot.ai
network-directed: Directed Network Graph
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-14
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import Arrow, ColumnDataSource, LabelSet, NormalHead
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SOURCE = "Importing module"  # role: edges
TARGET = "Imported module"  # role: extra
SOURCE_GROUP = "Importing group"  # role: extra
TARGET_GROUP = "Imported group"  # role: extra

# Data: replace this block with your own edge list, for example df = pd.read_csv("edges.csv")
core, infra, shared, dev = "Core Modules", "Infrastructure", "Shared Utils", "Development"
group_of = {
    "API": core,
    "Auth": core,
    "Database": core,
    "Models": core,
    "Routes": core,
    "Middleware": core,
    "Cache": infra,
    "Logger": infra,
    "Config": infra,
    "Utils": shared,
    "Validators": shared,
    "Tests": dev,
}
edges = [
    ("API", "Routes"),
    ("API", "Middleware"),
    ("API", "Config"),
    ("Routes", "Auth"),
    ("Routes", "Database"),
    ("Routes", "Models"),
    ("Routes", "Validators"),
    ("Middleware", "Auth"),
    ("Middleware", "Logger"),
    ("Auth", "Database"),
    ("Auth", "Cache"),
    ("Auth", "Config"),
    ("Database", "Config"),
    ("Database", "Logger"),
    ("Cache", "Config"),
    ("Cache", "Logger"),
    ("Models", "Database"),
    ("Models", "Validators"),
    ("Validators", "Utils"),
    ("Tests", "API"),
    ("Tests", "Models"),
    ("Tests", "Utils"),
]
df = pd.DataFrame(
    {
        SOURCE: [s for s, _ in edges],
        TARGET: [t for _, t in edges],
        SOURCE_GROUP: [group_of[s] for s, _ in edges],
        TARGET_GROUP: [group_of[t] for _, t in edges],
    }
)

# Plot: reads only df and the constants above
# Nodes come from the edge list; groups keep their order of first appearance and sit side by side on the ring
node_group = {
    **dict(zip(df[TARGET], df[TARGET_GROUP], strict=True)),
    **dict(zip(df[SOURCE], df[SOURCE_GROUP], strict=True)),
}
groups = list(dict.fromkeys(node_group.values()))
node_ids = sorted(node_group, key=lambda n: groups.index(node_group[n]))

# Canvas 3200 x 1800 with fixed borders, so one data unit is one screen pixel
W, H = 3200, 1800
BORDER_SIDE, BORDER_TOP, BORDER_BOTTOM = 40, 120, 40
frame_w, frame_h = W - 2 * BORDER_SIDE, H - BORDER_TOP - BORDER_BOTTOM

# Elliptical ring layout, groups clustered, first node at the top
angles = np.linspace(0, 2 * np.pi, len(node_ids), endpoint=False) - np.pi / 2
center = np.array([frame_w * 0.44, frame_h * 0.50])
radii = np.array([frame_w * 0.33, frame_h * 0.36])
pos = {n: center + radii * np.array([np.cos(a), np.sin(a)]) for n, a in zip(node_ids, angles, strict=True)}

NODE_SIZE = 170
NODE_R = NODE_SIZE / 2 + 2  # border included: arrowheads stop exactly at the node edge

p = figure(
    width=W,
    height=H,
    title="network-directed · python · bokeh · anyplot.ai",
    x_range=(0, frame_w),
    y_range=(0, frame_h),
    tools="",
    toolbar_location=None,
    min_border_left=BORDER_SIDE,
    min_border_right=BORDER_SIDE,
    min_border_top=BORDER_TOP,
    min_border_bottom=BORDER_BOTTOM,
)
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.outline_line_alpha = 0
p.axis.visible = False
p.grid.visible = False
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"

# Edges: thin, soft lines with one filled arrowhead whose tip touches the target's border
for src, dst in zip(df[SOURCE], df[TARGET], strict=True):
    vec = pos[dst] - pos[src]
    unit = vec / np.hypot(*vec)
    start = pos[src] + unit * NODE_R
    end = pos[dst] - unit * NODE_R
    p.add_layout(
        Arrow(
            end=NormalHead(size=34, fill_color=INK_SOFT, line_color=INK_SOFT, fill_alpha=0.85, line_alpha=0.85),
            x_start=start[0],
            y_start=start[1],
            x_end=end[0],
            y_end=end[1],
            line_color=INK_SOFT,
            line_width=3,
            line_alpha=0.6,
        )
    )

# Nodes: one scatter per group so the legend comes from the data
for i, group in enumerate(groups):
    members = [n for n in node_ids if node_group[n] == group]
    source = ColumnDataSource({"x": [pos[n][0] for n in members], "y": [pos[n][1] for n in members], "label": members})
    p.scatter(
        x="x",
        y="y",
        source=source,
        size=NODE_SIZE,
        fill_color=IMPRINT_PALETTE[i],
        line_color=INK_SOFT,
        line_width=4,
        legend_label=group,
    )
    p.add_layout(
        LabelSet(
            x="x",
            y="y",
            text="label",
            source=source,
            text_font_size="20pt",
            text_font_style="bold",
            text_color="#FFFFFF",
            text_align="center",
            text_baseline="middle",
        )
    )

# Legend
p.legend.location = "top_right"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.label_text_font_size = "28pt"
p.legend.glyph_width = 50
p.legend.glyph_height = 50
p.legend.spacing = 14
p.legend.padding = 24
p.legend.margin = 30

# Write the interactive HTML (also a required catalog artifact)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot it with headless Chrome — Selenium 4 / Selenium Manager
# auto-resolves a working driver for the system Chrome.
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
