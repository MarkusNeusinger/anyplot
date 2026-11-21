"""anyplot.ai
circlepacking-basic: Circle Packing Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LabelSet, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: one position per hierarchy level, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
ID = "id"  # role: id
PARENT = "parent"  # role: parent
VALUE = "Value (M$)"  # role: value
LABEL = "label"  # role: label
LEVEL = "Level"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("hierarchy.csv")
# Portfolio composition by asset class (in millions); only leaf rows carry a value
df = pd.DataFrame(
    [
        ("Portfolio", None, 0, "Portfolio", "Portfolio"),
        ("Equities", "Portfolio", 0, "Equities", "Asset Class"),
        ("US-Large-Cap", "Equities", 450, "US Large Cap", "Investment"),
        ("US-Mid-Cap", "Equities", 280, "US Mid Cap", "Investment"),
        ("US-Small-Cap", "Equities", 170, "US Small Cap", "Investment"),
        ("Intl-Dev", "Equities", 320, "Intl Dev", "Investment"),
        ("Emerging", "Equities", 180, "Emerging", "Investment"),
        ("Fixed-Income", "Portfolio", 0, "Fixed Income", "Asset Class"),
        ("US-Govt", "Fixed-Income", 250, "US Govt", "Investment"),
        ("Corp-Bonds", "Fixed-Income", 180, "Corp Bonds", "Investment"),
        ("Int-Bonds", "Fixed-Income", 120, "Intl Bonds", "Investment"),
        ("High-Yield", "Fixed-Income", 100, "High Yield", "Investment"),
        ("Real-Assets", "Portfolio", 0, "Real Assets", "Asset Class"),
        ("Real-Estate", "Real-Assets", 200, "Real Estate", "Investment"),
        ("Commodities", "Real-Assets", 90, "Commodities", "Investment"),
        ("Infrastructure", "Real-Assets", 110, "Infrastructure", "Investment"),
        ("Alternatives", "Portfolio", 0, "Alternatives", "Asset Class"),
        ("Hedge-Funds", "Alternatives", 150, "Hedge Funds", "Investment"),
        ("Private-Equity", "Alternatives", 130, "Private Equity", "Investment"),
        ("Crypto", "Alternatives", 40, "Crypto", "Investment"),
    ],
    columns=[ID, PARENT, VALUE, LABEL, LEVEL],
)

# Plot: reads only df and the constants above
# Build tree structure
nodes = {
    row[ID]: {
        "key": row[ID],
        "up": row[PARENT] if pd.notna(row[PARENT]) else None,
        "amount": 0.0 if pd.isna(row[VALUE]) else float(row[VALUE]),
        "name": row[LABEL],
        "kind": row[LEVEL],
        "children": [],
        "x": 0.0,
        "y": 0.0,
        "r": 0.0,
        "depth": 0,
    }
    for _, row in df.iterrows()
}
# A row without a known parent is a root; several roots share one unnamed top circle
tops = [n for n in nodes.values() if n["up"] not in nodes]
for node in nodes.values():
    if node["up"] in nodes:
        nodes[node["up"]]["children"].append(node)
if len(tops) == 1:
    root = tops[0]
else:
    root = {"key": None, "up": None, "amount": 0.0, "name": "", "kind": "", "children": tops, "x": 0.0, "y": 0.0}
    root.update(r=0.0, depth=0)
    nodes["virtual root"] = root


# Depth of every node, walking down from the root
stack = [root]
while stack:
    current = stack.pop()
    for child in current["children"]:
        child["depth"] = current["depth"] + 1
        stack.append(child)

scale_factor = 12
padding = 2.5 * scale_factor

# Leaf radius from area: r ~ sqrt(value)
for node in nodes.values():
    if not node["children"]:
        node["r"] = np.sqrt(node["amount"]) * scale_factor
max_leaf_r = max(n["r"] for n in nodes.values() if not n["children"])
# A leaf without a positive value still gets a sliver so the packing stays defined
for node in nodes.values():
    if not node["children"]:
        node["r"] = max(node["r"], 0.02 * max_leaf_r, 1e-3)

# Compute layout bottom-up
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

                    if best_score == float("inf"):
                        # No tangent slot between two placed circles: walk outward along rays until free
                        ox = sum(children[m]["x"] for m in range(i)) / i
                        oy = sum(children[m]["y"] for m in range(i)) / i
                        found = False
                        for dist in np.arange(0.0, 10 * max_leaf_r * n_children, 0.5 * scale_factor):
                            for ang in np.linspace(0, 2 * np.pi, 72, endpoint=False):
                                px, py = ox + dist * np.cos(ang), oy + dist * np.sin(ang)
                                if all(
                                    np.hypot(px - children[m]["x"], py - children[m]["y"])
                                    >= ci["r"] + children[m]["r"] - 1e-6
                                    for m in range(i)
                                ):
                                    best_pos = (px, py)
                                    found = True
                                    break
                            if found:
                                break
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

            node["r"] = enc_r + padding

# Position children relative to parent (top-down)
stack = [(root, 0.0, 0.0)]
while stack:
    current, px, py = stack.pop()
    current["x"] = px
    current["y"] = py
    for child in current["children"]:
        stack.append((child, px + child["x"], py + child["y"]))

# Collect all nodes, drawn outermost first so children sit on top of their parents
all_circles = sorted(nodes.values(), key=lambda n: (n["depth"], -n["r"]))

# Color by depth level
level_names = list(dict.fromkeys(n["kind"] for n in all_circles))


def alpha_for(depth):
    return 0.6 if depth == 0 else (0.65 if depth == 1 else 0.75)


circle_source = ColumnDataSource(
    data={
        "x": [n["x"] for n in all_circles],
        "y": [n["y"] for n in all_circles],
        "radius": [n["r"] for n in all_circles],
        "color": [IMPRINT_PALETTE[n["depth"] % len(IMPRINT_PALETTE)] for n in all_circles],
        "alpha": [alpha_for(n["depth"]) for n in all_circles],
        "line_width": [3 if n["depth"] == 0 else 2 for n in all_circles],
        LABEL: [n["name"] for n in all_circles],
        LEVEL: [n["kind"] for n in all_circles],
        VALUE: [n["amount"] for n in all_circles],
    }
)

# Square canvas, the natural shape for packed circles
W, H = 2400, 2400
p = figure(
    frame_width=W - 200,
    frame_height=H - 200,
    title="circlepacking-basic · python · bokeh · anyplot.ai",
    match_aspect=True,
    toolbar_location=None,
    tools="",
    min_border_top=160,
    min_border_bottom=40,
    min_border_left=100,
    min_border_right=100,
)

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

# Hover: name, level and value of every circle
hover = HoverTool(
    tooltips=[("Name", f"@{{{LABEL}}}"), (LEVEL, f"@{{{LEVEL}}}"), (VALUE, f"@{{{VALUE}}}{{0}}")],
    renderers=[circles_glyph],
    mode="mouse",
)
p.add_tools(hover)

# Legend: one entry per hierarchy level (off-screen proxy glyphs carry the colors)
legend_items = []
for i, name in enumerate(level_names):
    proxy = p.circle(
        x=[0],
        y=[0],
        radius=[1],
        fill_color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        fill_alpha=0.7,
        line_color=INK_SOFT,
        visible=False,
    )
    legend_items.append(LegendItem(label=str(name), renderers=[proxy]))

legend = Legend(items=legend_items, location="top_right", label_text_font_size="24pt", glyph_height=40, glyph_width=40)
legend.background_fill_color = ELEVATED_BG
legend.background_fill_alpha = 0.95
legend.border_line_color = INK_SOFT
legend.label_text_color = INK_SOFT
legend.padding = 15
legend.spacing = 10
p.add_layout(legend)

# Labels: larger leaves at their center, asset classes near the top of their circle
label_data = {"x": [], "y": [], LABEL: []}
for node in all_circles:
    if not node["children"] and node["r"] >= 0.25 * max_leaf_r:
        label_data["x"].append(node["x"])
        label_data["y"].append(node["y"])
        label_data[LABEL].append(node["name"])
    elif node["depth"] == 1 and node["children"]:
        # Free spot: the point near the rim with the most clearance from the circle's children
        spots = [
            (node["x"] + 0.68 * node["r"] * np.cos(a), node["y"] + 0.68 * node["r"] * np.sin(a))
            for a in np.linspace(0, 2 * np.pi, 120, endpoint=False)
        ]
        sx, sy = max(
            spots, key=lambda s: min(np.hypot(s[0] - c["x"], s[1] - c["y"]) - c["r"] for c in node["children"])
        )
        label_data["x"].append(sx)
        label_data["y"].append(sy)
        label_data[LABEL].append(node["name"])

label_set = LabelSet(
    x="x",
    y="y",
    text=LABEL,
    source=ColumnDataSource(label_data),
    text_align="center",
    text_baseline="middle",
    text_font_size="22pt",
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

# Square ranges around the root circle with a small margin
extent = root["r"] * 1.08
p.x_range.start = -extent
p.x_range.end = extent
p.y_range.start = -extent
p.y_range.end = extent

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
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
