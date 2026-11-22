"""anyplot.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-17
"""

import os
import time
from pathlib import Path

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

# Imprint palette: one position per hierarchy level
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
EDGE_COLUMNS = ["Parent", "Child"]  # role: edges

# Data: replace this block with your own edge list, for example df = pd.read_csv("reports_to.csv")
# Software company org chart, 24 people over 4 management levels (parent -> child)
reports = {
    "CEO": ["VP Engineering", "VP Product", "VP Operations"],
    "VP Engineering": ["Frontend Dir.", "Backend Dir."],
    "VP Product": ["PM Lead", "UX Lead"],
    "VP Operations": ["IT Manager", "HR Manager"],
    "Frontend Dir.": ["FE Dev 1", "FE Dev 2"],
    "Backend Dir.": ["BE Dev 1", "BE Dev 2", "BE Dev 3"],
    "PM Lead": ["PM 1", "PM 2"],
    "UX Lead": ["Designer 1", "Designer 2"],
    "IT Manager": ["IT Support 1", "IT Support 2"],
    "HR Manager": ["HR Spec 1", "HR Spec 2", "Recruiter"],
}
df = pd.DataFrame([(parent, child) for parent, children in reports.items() for child in children], columns=EDGE_COLUMNS)

# Plot: reads only df and the constants above
PARENT, CHILD = EDGE_COLUMNS
# Depth of each node below the root (the one node that is never a child), in order of appearance
root = next(p for p in df[PARENT].unique() if p not in set(df[CHILD]))
depth = {root: 0}
for parent, child in zip(df[PARENT], df[CHILD], strict=True):
    depth[child] = depth[parent] + 1
nodes = pd.DataFrame({"label": list(depth), "level": list(depth.values())})
n_levels = nodes["level"].max() + 1

# Tree layout: one row per level, nodes of a level spread evenly and centered
SPACING = 1.6
Y_STEP = 2.0
nodes["y"] = -nodes["level"] * Y_STEP
children = df.groupby(PARENT, sort=False)[CHILD].apply(list).to_dict()
x_of = {}


def place(name):
    """Leaves take the next slot left to right; a parent sits over the mean of its children."""
    if name not in children:
        x_of[name] = sum(1 for n in x_of if n not in children) * SPACING
    else:
        x_of[name] = sum(place(c) for c in children[name]) / len(children[name])
    return x_of[name]


place(root)
centre = (max(x_of.values()) + min(x_of.values())) / 2
nodes["x"] = [x_of[label] - centre for label in nodes["label"]]
nodes["size"] = 70 - 7 * nodes["level"]
nodes["color"] = [IMPRINT_PALETTE[lvl] for lvl in nodes["level"]]
pos = nodes.set_index("label")[["x", "y"]]

edges = pd.DataFrame(
    {
        "x0": pos.loc[df[PARENT], "x"].to_numpy(),
        "y0": pos.loc[df[PARENT], "y"].to_numpy(),
        "x1": pos.loc[df[CHILD], "x"].to_numpy(),
        "y1": pos.loc[df[CHILD], "y"].to_numpy(),
    }
)

W, H = 3200, 1800
p = figure(
    width=W,
    height=H,
    title="network-hierarchical · python · bokeh · anyplot.ai",
    tools="",
    toolbar_location=None,
    min_border_left=60,
    min_border_right=60,
    min_border_bottom=60,
    min_border_top=110,
    x_range=(nodes["x"].min() - 1.4, nodes["x"].max() + 1.4),
    y_range=(nodes["y"].min() - 1.4, nodes["y"].max() + 1.6),
)
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = PAGE_BG
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Edges: thinner and lighter than the nodes
p.segment(
    x0="x0",
    y0="y0",
    x1="x1",
    y1="y1",
    source=ColumnDataSource(edges),
    line_width=3,
    line_color=INK_SOFT,
    line_alpha=0.45,
)

# Nodes: one renderer per level for the legend
legend_items = []
for lvl in range(n_levels):
    rows = nodes[nodes["level"] == lvl]
    renderer = p.scatter(
        x="x",
        y="y",
        source=ColumnDataSource(rows),
        size="size",
        fill_color="color",
        line_color=INK_SOFT,
        line_width=2,
        alpha=0.95,
    )
    name = f"Level {lvl}: {rows['label'].iloc[0]}" if len(rows) == 1 else f"Level {lvl}"
    legend_items.append(LegendItem(label=name, renderers=[renderer]))

legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="24pt",
    label_text_color=INK_SOFT,
    glyph_height=40,
    glyph_width=40,
    spacing=10,
    padding=22,
    border_line_color=INK_SOFT,
    border_line_width=2,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.95,
)
p.add_layout(legend, "center")

# Labels above their own node
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="label",
        source=ColumnDataSource(nodes),
        text_font_size="22pt",
        text_color=INK,
        text_align="center",
        y_offset=42,
    )
)
p.add_tools(HoverTool(tooltips=[("Role", "@label"), ("Level", "@level")]))

p.title.text_font_size = "44pt"
p.title.text_color = INK
p.title.align = "center"

# Save
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
