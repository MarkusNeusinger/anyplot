""" anyplot.ai
circlepacking-basic: Circle Packing Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-11
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LabelSet, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


np.random.seed(42)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette for hierarchy levels
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Build hierarchical data: Portfolio composition by asset class (in millions)
hierarchy = [
    {"id": "Portfolio", "parent": None, "value": 0, "label": "Portfolio"},
    # Equities
    {"id": "Equities", "parent": "Portfolio", "value": 0, "label": "Equities"},
    {"id": "US-Large-Cap", "parent": "Equities", "value": 450, "label": "US Large Cap"},
    {"id": "US-Mid-Cap", "parent": "Equities", "value": 280, "label": "US Mid Cap"},
    {"id": "US-Small-Cap", "parent": "Equities", "value": 170, "label": "US Small Cap"},
    {"id": "Intl-Dev", "parent": "Equities", "value": 320, "label": "Intl Dev"},
    {"id": "Emerging", "parent": "Equities", "value": 180, "label": "Emerging"},
    # Fixed Income
    {"id": "Fixed-Income", "parent": "Portfolio", "value": 0, "label": "Fixed Income"},
    {"id": "US-Govt", "parent": "Fixed-Income", "value": 250, "label": "US Govt"},
    {"id": "Corp-Bonds", "parent": "Fixed-Income", "value": 180, "label": "Corp Bonds"},
    {"id": "Int-Bonds", "parent": "Fixed-Income", "value": 120, "label": "Intl Bonds"},
    {"id": "High-Yield", "parent": "Fixed-Income", "value": 100, "label": "High Yield"},
    # Real Assets
    {"id": "Real-Assets", "parent": "Portfolio", "value": 0, "label": "Real Assets"},
    {"id": "Real-Estate", "parent": "Real-Assets", "value": 200, "label": "Real Estate"},
    {"id": "Commodities", "parent": "Real-Assets", "value": 90, "label": "Commodities"},
    {"id": "Infrastructure", "parent": "Real-Assets", "value": 110, "label": "Infrastructure"},
    # Alternatives
    {"id": "Alternatives", "parent": "Portfolio", "value": 0, "label": "Alternatives"},
    {"id": "Hedge-Funds", "parent": "Alternatives", "value": 150, "label": "Hedge Funds"},
    {"id": "Private-Equity", "parent": "Alternatives", "value": 130, "label": "Private Equity"},
    {"id": "Crypto", "parent": "Alternatives", "value": 40, "label": "Crypto"},
]

# Build tree structure
nodes = {item["id"]: {**item, "children": [], "x": 0.0, "y": 0.0, "r": 0.0, "depth": 0} for item in hierarchy}
root = None
for _node_id, node in nodes.items():
    if node["parent"] is None:
        root = node
    else:
        parent = nodes[node["parent"]]
        parent["children"].append(node)
        node["depth"] = parent["depth"] + 1

scale_factor = 12

# Compute layout bottom-up
for node in nodes.values():
    if not node["children"]:
        node["r"] = np.sqrt(node["value"]) * scale_factor

max_depth = max(n["depth"] for n in nodes.values())

for current_depth in range(max_depth, -1, -1):
    nodes_at_depth = [n for n in nodes.values() if n["depth"] == current_depth and n["children"]]

    for node in nodes_at_depth:
        children = node["children"]
        children.sort(key=lambda c: -c["r"])
        n_children = len(children)

        if n_children == 1:
            children[0]["x"] = 0.0
            children[0]["y"] = 0.0
        elif n_children >= 2:
            c0, c1 = children[0], children[1]
            c0["x"] = 0.0
            c0["y"] = 0.0
            c1["x"] = c0["r"] + c1["r"]
            c1["y"] = 0.0

            if n_children >= 3:
                c2 = children[2]
                d01 = c0["r"] + c1["r"]
                d02 = c0["r"] + c2["r"]
                d12 = c1["r"] + c2["r"]
                x2 = (d02**2 - d12**2 + d01**2) / (2 * d01)
                y2_sq = d02**2 - x2**2
                c2["x"] = x2
                c2["y"] = np.sqrt(max(0, y2_sq))

                for i in range(3, n_children):
                    ci = children[i]
                    best_score = float("inf")
                    best_pos = (0.0, 0.0)

                    for j in range(i):
                        for k in range(j + 1, i):
                            cj, ck = children[j], children[k]
                            dx = ck["x"] - cj["x"]
                            dy = ck["y"] - cj["y"]
                            d = np.sqrt(dx**2 + dy**2)

                            if d < 1e-10:
                                continue

                            r1 = cj["r"] + ci["r"]
                            r2 = ck["r"] + ci["r"]

                            if d > r1 + r2 + 1e-6 or d < abs(r1 - r2) - 1e-6:
                                continue

                            a = (r1**2 - r2**2 + d**2) / (2 * d)
                            h_sq = r1**2 - a**2
                            if h_sq < 0:
                                continue

                            h = np.sqrt(h_sq)
                            mx = cj["x"] + a * dx / d
                            my = cj["y"] + a * dy / d

                            for px, py in [(mx - h * dy / d, my + h * dx / d), (mx + h * dy / d, my - h * dx / d)]:
                                valid = True
                                for m in range(i):
                                    cm = children[m]
                                    dist = np.sqrt((px - cm["x"]) ** 2 + (py - cm["y"]) ** 2)
                                    if dist < ci["r"] + cm["r"] - 1e-6:
                                        valid = False
                                        break

                                if valid:
                                    cx = sum(children[m]["x"] for m in range(i)) / i
                                    cy = sum(children[m]["y"] for m in range(i)) / i
                                    score = np.sqrt((px - cx) ** 2 + (py - cy) ** 2)
                                    if score < best_score:
                                        best_score = score
                                        best_pos = (px, py)

                    ci["x"], ci["y"] = best_pos

        if children:
            min_x = min(c["x"] - c["r"] for c in children)
            max_x = max(c["x"] + c["r"] for c in children)
            min_y = min(c["y"] - c["r"] for c in children)
            max_y = max(c["y"] + c["r"] for c in children)
            cx = (min_x + max_x) / 2
            cy = (min_y + max_y) / 2
            enc_r = max(np.sqrt((c["x"] - cx) ** 2 + (c["y"] - cy) ** 2) + c["r"] for c in children)

            for child in children:
                child["x"] -= cx
                child["y"] -= cy

            node["r"] = enc_r + 30

# Position children relative to parent (top-down)
stack = [(root, 0.0, 0.0)]
while stack:
    current, px, py = stack.pop()
    current["x"] = px
    current["y"] = py
    for child in current["children"]:
        stack.append((child, px + child["x"], py + child["y"]))

# Collect all nodes for plotting
all_circles = []
stack = [root]
while stack:
    current = stack.pop()
    all_circles.append(current)
    stack.extend(current["children"])

# Prepare data for plotting
x_vals = [n["x"] for n in all_circles]
y_vals = [n["y"] for n in all_circles]
radii = [n["r"] for n in all_circles]
depths = [n["depth"] for n in all_circles]
labels = [n["label"] for n in all_circles]
values = [n["value"] for n in all_circles]

# Color by depth using Okabe-Ito palette
colors = [IMPRINT[min(d, 2)] for d in depths]
depth_names = ["Portfolio", "Asset Class", "Investment"]
depth_labels = [depth_names[min(d, 2)] for d in depths]

# Create figure (square aspect)
p = figure(
    width=3600,
    height=3600,
    title="circlepacking-basic · bokeh · anyplot.ai",
    match_aspect=True,
    toolbar_location=None,
    tools="",
)

# Sort by depth and radius for proper layering
sorted_indices = sorted(range(len(all_circles)), key=lambda i: (depths[i], -radii[i]))

# Draw circles with ColumnDataSource for hover
circle_data = {
    "x": [x_vals[i] for i in sorted_indices],
    "y": [y_vals[i] for i in sorted_indices],
    "radius": [radii[i] for i in sorted_indices],
    "color": [colors[i] for i in sorted_indices],
    "alpha": [0.6 if depths[i] == 0 else (0.65 if depths[i] == 1 else 0.75) for i in sorted_indices],
    "line_width": [3 if depths[i] == 0 else 2 for i in sorted_indices],
    "label": [labels[i] for i in sorted_indices],
    "depth_label": [depth_labels[i] for i in sorted_indices],
    "value": [values[i] for i in sorted_indices],
}
circle_source = ColumnDataSource(data=circle_data)

circles_glyph = p.circle(
    x="x",
    y="y",
    radius="radius",
    fill_color="color",
    fill_alpha="alpha",
    line_color=INK_SOFT,
    line_width="line_width",
    source=circle_source,
)

# Add HoverTool for interactivity
hover = HoverTool(
    tooltips=[("Name", "@label"), ("Level", "@depth_label"), ("Value", "@value{0} M$")],
    renderers=[circles_glyph],
    mode="mouse",
)
p.add_tools(hover)

# Create legend for depth colors
legend_items = []
for color, name in zip(IMPRINT[:3], depth_names, strict=True):
    dummy_source = ColumnDataSource(data={"x": [-99999], "y": [-99999], "r": [10]})
    dummy_circle = p.circle(
        x="x", y="y", radius="r", fill_color=color, fill_alpha=0.7, line_color=INK_SOFT, source=dummy_source
    )
    legend_items.append(LegendItem(label=name, renderers=[dummy_circle]))

legend = Legend(items=legend_items, location="top_right", label_text_font_size="24pt", glyph_height=40, glyph_width=40)
legend.background_fill_color = ELEVATED_BG
legend.background_fill_alpha = 0.95
legend.border_line_color = INK_SOFT
legend.label_text_color = INK_SOFT
legend.padding = 15
legend.spacing = 10
p.add_layout(legend)

# Prepare labels for larger circles
label_data = {"x": [], "y": [], "label": []}
for node in all_circles:
    if not node["children"] and node["r"] >= 50:
        label_data["x"].append(node["x"])
        label_data["y"].append(node["y"])
        label_data["label"].append(node["label"])
    elif node["depth"] == 1:
        label_data["x"].append(node["x"])
        label_data["y"].append(node["y"] + node["r"] * 0.7)
        label_data["label"].append(node["label"])

label_source = ColumnDataSource(data=label_data)
label_set = LabelSet(
    x="x",
    y="y",
    text="label",
    source=label_source,
    text_align="center",
    text_baseline="middle",
    text_font_size="26pt",
    text_color=INK,
    text_font_style="bold",
)
p.add_layout(label_set)

# Style with theme-adaptive chrome
p.title.text_font_size = "36pt"
p.title.text_color = INK
p.title.align = "center"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Set axis ranges
extent = root["r"] * 1.08
p.x_range.start = -extent
p.x_range.end = extent
p.y_range.start = -extent
p.y_range.end = extent

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with Selenium
W, H = 3600, 3600
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
