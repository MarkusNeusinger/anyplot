""" anyplot.ai
sankey-basic: Basic Sankey Diagram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-04-30
"""

import os
import sys


_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _script_dir]

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import Label
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first source always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]

# Data - Energy flow from sources to sectors (TWh)
flows = [
    {"source": "Coal", "target": "Industrial", "value": 25},
    {"source": "Coal", "target": "Residential", "value": 10},
    {"source": "Gas", "target": "Residential", "value": 30},
    {"source": "Gas", "target": "Commercial", "value": 20},
    {"source": "Gas", "target": "Industrial", "value": 15},
    {"source": "Nuclear", "target": "Industrial", "value": 18},
    {"source": "Nuclear", "target": "Commercial", "value": 12},
    {"source": "Hydro", "target": "Residential", "value": 8},
    {"source": "Hydro", "target": "Commercial", "value": 7},
    {"source": "Solar", "target": "Residential", "value": 5},
    {"source": "Solar", "target": "Commercial", "value": 6},
]

# Extract unique sources and targets (preserve order)
sources = []
targets = []
for f in flows:
    if f["source"] not in sources:
        sources.append(f["source"])
    if f["target"] not in targets:
        targets.append(f["target"])

# Source colors: Okabe-Ito in canonical order
source_colors = {s: OKABE_ITO[i] for i, s in enumerate(sources)}

# Target node colors: slightly muted variants of INK_SOFT family
target_node_colors = {"Industrial": "#5A6A7A", "Commercial": "#7A6A8A", "Residential": "#6A7A5A"}

# Calculate totals for node sizing
source_totals = {s: sum(f["value"] for f in flows if f["source"] == s) for s in sources}
target_totals = {t: sum(f["value"] for f in flows if f["target"] == t) for t in targets}

# Layout parameters
left_x = 0
right_x = 100
node_width = 8
node_gap = 3
total_height = 100
padding_y = 5

# Calculate node positions for sources (left side)
source_height_total = sum(source_totals.values())
scale_src = (total_height - 2 * padding_y - (len(sources) - 1) * node_gap) / source_height_total

source_nodes = {}
current_y = padding_y
for s in sources:
    height = source_totals[s] * scale_src
    source_nodes[s] = {"x": left_x, "y": current_y, "height": height, "value": source_totals[s]}
    current_y += height + node_gap

# Calculate node positions for targets (right side)
target_height_total = sum(target_totals.values())
scale_tgt = (total_height - 2 * padding_y - (len(targets) - 1) * node_gap) / target_height_total

target_nodes = {}
current_y = padding_y
for t in targets:
    height = target_totals[t] * scale_tgt
    target_nodes[t] = {"x": right_x - node_width, "y": current_y, "height": height, "value": target_totals[t]}
    current_y += height + node_gap

# Track flow offsets for stacking flows at each node
source_offsets = dict.fromkeys(sources, 0.0)
target_offsets = dict.fromkeys(targets, 0.0)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="Energy Flow · sankey-basic · bokeh · anyplot.ai",
    x_range=(-18, 118),
    y_range=(-5, 108),
    tools="",
    toolbar_location=None,
)

# Draw flows using bezier curves
for f in flows:
    src = f["source"]
    tgt = f["target"]
    value = f["value"]

    src_node = source_nodes[src]
    tgt_node = target_nodes[tgt]

    src_flow_height = (value / source_totals[src]) * src_node["height"]
    tgt_flow_height = (value / target_totals[tgt]) * tgt_node["height"]

    x0 = src_node["x"] + node_width
    y0_bottom = src_node["y"] + source_offsets[src]
    y0_top = y0_bottom + src_flow_height

    x1 = tgt_node["x"]
    y1_bottom = tgt_node["y"] + target_offsets[tgt]
    y1_top = y1_bottom + tgt_flow_height

    source_offsets[src] += src_flow_height
    target_offsets[tgt] += tgt_flow_height

    t = np.linspace(0, 1, 60)
    cx0 = x0 + (x1 - x0) * 0.4
    cx1 = x0 + (x1 - x0) * 0.6

    x_path = (1 - t) ** 3 * x0 + 3 * (1 - t) ** 2 * t * cx0 + 3 * (1 - t) * t**2 * cx1 + t**3 * x1
    y_bottom = (1 - t) * y0_bottom + t * y1_bottom
    y_top = (1 - t) * y0_top + t * y1_top

    xs = list(x_path) + list(x_path[::-1])
    ys = list(y_top) + list(y_bottom[::-1])

    p.patch(
        xs,
        ys,
        fill_color=source_colors[src],
        fill_alpha=0.45,
        line_color=source_colors[src],
        line_alpha=0.6,
        line_width=1,
    )

# Draw source nodes (left side)
for s in sources:
    node = source_nodes[s]
    p.quad(
        left=node["x"],
        right=node["x"] + node_width,
        bottom=node["y"],
        top=node["y"] + node["height"],
        fill_color=source_colors[s],
        fill_alpha=0.92,
        line_color=PAGE_BG,
        line_width=2,
    )
    label = Label(
        x=node["x"] - 1.5,
        y=node["y"] + node["height"] / 2,
        text=f"{s} ({node['value']} TWh)",
        text_font_size="22pt",
        text_align="right",
        text_baseline="middle",
        text_color=INK,
        text_font="helvetica",
    )
    p.add_layout(label)

# Draw target nodes (right side)
for t in targets:
    node = target_nodes[t]
    p.quad(
        left=node["x"],
        right=node["x"] + node_width,
        bottom=node["y"],
        top=node["y"] + node["height"],
        fill_color=target_node_colors[t],
        fill_alpha=0.92,
        line_color=PAGE_BG,
        line_width=2,
    )
    label = Label(
        x=node["x"] + node_width + 1.5,
        y=node["y"] + node["height"] / 2,
        text=f"{t} ({node['value']} TWh)",
        text_font_size="22pt",
        text_align="left",
        text_baseline="middle",
        text_color=INK,
        text_font="helvetica",
    )
    p.add_layout(label)

# Style — theme-adaptive chrome
p.title.text_font_size = "32pt"
p.title.text_color = INK
p.title.align = "center"
p.title.text_font = "helvetica"

p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)
