"""anyplot.ai
icicle-basic: Basic Icicle Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Imprint palette: all eight positions, one per hierarchy level in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
DARK_TEXT = "#1A1A17"  # label colors sit on the fill, so they do not change with the theme
LIGHT_TEXT = "#FAF8F1"

# Columns: set these to your table's column names
NAME = "Name"  # role: name
PARENT = "Parent"  # role: parent
VALUE = "Size (MB)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("folders.csv")
# File system: folders have no value of their own, files carry their size.
df = pd.DataFrame(
    {
        NAME: [
            "Root",
            "Documents",
            "Media",
            "Code",
            "Reports",
            "Contracts",
            "Notes",
            "Images",
            "Videos",
            "Audio",
            "Python",
            "JavaScript",
            "Data",
        ],
        PARENT: [None, "Root", "Root", "Root"] + ["Documents"] * 3 + ["Media"] * 3 + ["Code"] * 3,
        VALUE: [None] * 4 + [350, 250, 150, 500, 800, 300, 400, 350, 200],
    }
)

# Plot: reads only df and the constants above
known = set(df[NAME])
children = {name: [] for name in known}
roots = []
for name, parent in zip(df[NAME], df[PARENT], strict=True):
    if pd.notna(parent) and parent in known:
        children[parent].append(name)
    else:
        roots.append(name)
own_value = dict(zip(df[NAME], df[VALUE], strict=True))


def total(name):
    """A node's size: its own value for a leaf, the sum of its children otherwise."""
    if children[name]:
        return sum(total(child) for child in children[name])
    return own_value[name]


rows = []


def layout(name, level, left, right):
    """Place a node in row `level`; its children share its extent in proportion to their sizes."""
    rows.append({"name": name, "level": level, "left": left, "right": right, "size": total(name)})
    cursor = left
    for child in children[name]:
        span = (right - left) * total(child) / total(name)
        layout(child, level + 1, cursor, cursor + span)
        cursor += span


span_total = sum(total(r) for r in roots)
cursor = 0.0
for r in roots:
    layout(r, 0, cursor, cursor + total(r))
    cursor += total(r)

tree = pd.DataFrame(rows)
n_levels = tree["level"].max() + 1
W, H = 3200, 1800
BORDER_X = 60
px_per_unit = (W - 2 * BORDER_X) / span_total


def label_for(row):
    """Largest font that fits the rectangle; empty text for nodes without room."""
    text = f"{row['name']} ({row['size']:g})" if row["level"] > 0 else str(row["name"])
    room = (row["right"] - row["left"]) * px_per_unit * 0.9
    for pt in (40, 34, 30, 26, 22, 18):
        if len(text) * pt * 1.333 * 0.58 <= room:
            return text, f"{pt}pt"
    return "", "18pt"


labels = tree.apply(label_for, axis=1, result_type="expand")
fills = [IMPRINT_PALETTE[level] for level in tree["level"]]


def text_color(fill):
    """Dark or light label, whichever contrasts more with the fill."""
    r, g, b = (int(fill[i : i + 2], 16) / 255 for i in (1, 3, 5))
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return DARK_TEXT if lum > 0.2 else LIGHT_TEXT


source = ColumnDataSource(
    {
        "x": (tree["left"] + tree["right"]) / 2,
        "y": n_levels - 1 - tree["level"],
        "w": tree["right"] - tree["left"],
        "fill": fills,
        "node": tree["name"],
        "size": tree["size"],
        "label": labels[0],
        "font": labels[1],
        "ink": [text_color(f) for f in fills],
    }
)

p = figure(
    width=W,
    height=H,
    title="icicle-basic · python · bokeh · anyplot.ai",
    x_range=(0, span_total),
    y_range=(-0.5, n_levels - 0.5),
    tools="hover",
    tooltips=[("Node", "@node"), (VALUE, "@size")],
    toolbar_location=None,
    min_border_top=130,
    min_border_bottom=60,
    min_border_left=BORDER_X,
    min_border_right=BORDER_X,
)
rects = p.rect(x="x", y="y", width="w", height=1, source=source, fill_color="fill", line_color=PAGE_BG, line_width=4)
p.text(
    x="x",
    y="y",
    text="label",
    text_font_size="font",
    text_color="ink",
    text_align="center",
    text_baseline="middle",
    source=source,
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

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
