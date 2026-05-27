""" anyplot.ai
icicle-basic: Basic Icicle Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
"""

import os
import time
from pathlib import Path

from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - File system hierarchy with nested folders and file sizes
nodes = [
    {"name": "Root", "parent": None, "value": 0},
    {"name": "Documents", "parent": "Root", "value": 0},
    {"name": "Media", "parent": "Root", "value": 0},
    {"name": "Code", "parent": "Root", "value": 0},
    {"name": "Reports", "parent": "Documents", "value": 350},
    {"name": "Contracts", "parent": "Documents", "value": 250},
    {"name": "Notes", "parent": "Documents", "value": 150},
    {"name": "Images", "parent": "Media", "value": 500},
    {"name": "Videos", "parent": "Media", "value": 800},
    {"name": "Audio", "parent": "Media", "value": 300},
    {"name": "Python", "parent": "Code", "value": 400},
    {"name": "JavaScript", "parent": "Code", "value": 350},
    {"name": "Data", "parent": "Code", "value": 200},
]

# Build lookup and children map
node_dict = {n["name"]: n for n in nodes}
children = {n["name"]: [] for n in nodes}
for n in nodes:
    if n["parent"]:
        children[n["parent"]].append(n["name"])


# Calculate leaf values for parent nodes (sum of children) - inline recursion
def calc_value(name):
    if children[name]:
        return sum(calc_value(c) for c in children[name])
    return node_dict[name]["value"]


for n in nodes:
    n["computed_value"] = calc_value(n["name"])


# Assign levels (depth in tree) - inline recursion
def assign_level(name, level):
    node_dict[name]["level"] = level
    for c in children[name]:
        assign_level(c, level + 1)


assign_level("Root", 0)
max_level = max(n["level"] for n in nodes)

# Assign colors by level using Okabe-Ito palette
level_colors = []
for i in range(max_level + 1):
    level_colors.append(IMPRINT[i % len(IMPRINT)])


# Calculate icicle layout (horizontal, top-down)
def layout_icicle(name, x_start, x_end, rects):
    node = node_dict[name]
    level = node["level"]

    rect = {
        "name": name,
        "level": level,
        "x_start": x_start,
        "x_end": x_end,
        "y_start": max_level - level,
        "y_end": max_level - level + 1,
        "value": node["computed_value"],
        "color": level_colors[min(level, len(level_colors) - 1)],
    }
    rects.append(rect)

    if children[name]:
        total_child_value = sum(node_dict[c]["computed_value"] for c in children[name])
        current_x = x_start
        for c in children[name]:
            child_value = node_dict[c]["computed_value"]
            child_width = (x_end - x_start) * (child_value / total_child_value)
            layout_icicle(c, current_x, current_x + child_width, rects)
            current_x += child_width


rects = []
layout_icicle("Root", 0, 100, rects)

# Prepare data for Bokeh
x_centers = [(r["x_start"] + r["x_end"]) / 2 for r in rects]
y_centers = [(r["y_start"] + r["y_end"]) / 2 for r in rects]
widths = [r["x_end"] - r["x_start"] for r in rects]
heights = [0.95 for r in rects]
colors = [r["color"] for r in rects]
names = [r["name"] for r in rects]
values = [r["value"] for r in rects]

source = ColumnDataSource(
    data={
        "x": x_centers,
        "y": y_centers,
        "width": widths,
        "height": heights,
        "color": colors,
        "name": names,
        "value": values,
    }
)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="icicle-basic · bokeh · anyplot.ai",
    x_range=(-12, 102),
    y_range=(-0.3, max_level + 0.8),
    tools="",
    toolbar_location=None,
)

# Draw rectangles
p.rect(
    x="x",
    y="y",
    width="width",
    height="height",
    source=source,
    fill_color="color",
    line_color=INK_SOFT,
    line_width=3,
    fill_alpha=0.9,
)

# Add labels for rectangles with sufficient width
for r in rects:
    rect_width = r["x_end"] - r["x_start"]
    x_center = (r["x_start"] + r["x_end"]) / 2
    y_center = (r["y_start"] + r["y_end"]) / 2

    if rect_width > 4:
        font_size = "24pt" if rect_width > 20 else ("20pt" if rect_width > 10 else "16pt")
        label_text = r["name"]
        if r["level"] > 0 and rect_width > 6:
            label_text = f"{r['name']} ({r['value']} MB)"

        label = Label(
            x=x_center,
            y=y_center,
            text=label_text,
            text_align="center",
            text_baseline="middle",
            text_font_size=font_size,
            text_color=INK,
        )
        p.add_layout(label)

# Styling
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.title.align = "center"

# Hide axes
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Theme-adaptive background and outline
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Add level labels on the left
level_labels = ["Root", "Categories", "Subcategories"]
for i, label_text in enumerate(level_labels[: max_level + 1]):
    label = Label(
        x=-1,
        y=max_level - i + 0.5,
        text=label_text,
        text_align="right",
        text_baseline="middle",
        text_font_size="20pt",
        text_color=INK_SOFT,
    )
    p.add_layout(label)

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
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
