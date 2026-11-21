"""anyplot.ai
parallel-categories-basic: Basic Parallel Categories Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-13
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names, in axis order
DIMENSIONS = ["Channel", "Category", "Outcome"]  # role: dimension_
CHANNEL, PRODUCT, OUTCOME = DIMENSIONS

# Data: replace this block with your own table, one row per observation,
# for example df = pd.read_csv("purchases.csv")
rng = np.random.default_rng(42)
channel_names = ["Online", "Store", "Mobile"]
product_names = ["Electronics", "Clothing", "Home"]
outcome_names = ["Purchased", "Returned", "Exchanged"]
product_given_channel = {"Online": [0.5, 0.3, 0.2], "Store": [0.2, 0.5, 0.3], "Mobile": [0.6, 0.25, 0.15]}
outcome_given_product = {"Electronics": [0.7, 0.2, 0.1], "Clothing": [0.6, 0.25, 0.15], "Home": [0.85, 0.1, 0.05]}
rows = []
for channel in rng.choice(channel_names, size=500, p=[0.45, 0.35, 0.20]):
    product = rng.choice(product_names, p=product_given_channel[channel])
    outcome = rng.choice(outcome_names, p=outcome_given_product[product])
    rows.append((channel, product, outcome))
df = pd.DataFrame(rows, columns=DIMENSIONS)

# Plot: reads only df and the constants above
total = len(df)
x_positions = {dim: i * 1.5 for i, dim in enumerate(DIMENSIONS)}
box_half = 0.06

# Layout: categories of each axis ordered by size, stacked from the bottom
segments = {}
for dim in DIMENSIONS:
    counts = df[dim].value_counts()
    top = 0.0
    for cat, count in counts.items():
        segments[(dim, cat)] = {"bottom": top, "top": top + count / total}
        top += count / total

# Ribbon colors follow the categories of the first dimension
first_cats = list(df[CHANNEL].value_counts().index)
color_of = {cat: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, cat in enumerate(first_cats)}


def bezier(t, a, b, c1, c2):
    """Cubic bezier from a to b with control points c1 and c2."""
    return a * (1 - t) ** 3 + 3 * c1 * t * (1 - t) ** 2 + 3 * c2 * t**2 * (1 - t) + b * t**3


t = np.linspace(0, 1, 30)
ribbons = {cat: {"xs": [], "ys": []} for cat in first_cats}
for left_dim, right_dim in zip(DIMENSIONS[:-1], DIMENSIONS[1:], strict=True):
    flows = (
        df.groupby(list(dict.fromkeys([CHANNEL, left_dim, right_dim]))).size().reset_index(name="n").to_dict("records")
    )
    # Stack ribbons in each segment ordered by the category at the other end, which limits crossings
    left_start, left_fill, right_fill = {}, {}, {}
    for flow in sorted(flows, key=lambda f: (f[right_dim], f[CHANNEL])):
        left_cat = flow[left_dim]
        start = left_fill.get(left_cat, segments[(left_dim, left_cat)]["bottom"])
        left_fill[left_cat] = start + flow["n"] / total
        left_start[(flow[CHANNEL], left_cat, flow[right_dim])] = start
    for flow in sorted(flows, key=lambda f: (f[left_dim], f[CHANNEL])):
        right_cat, height = flow[right_dim], flow["n"] / total
        start = right_fill.get(right_cat, segments[(right_dim, right_cat)]["bottom"])
        right_fill[right_cat] = start + height
        begin = left_start[(flow[CHANNEL], flow[left_dim], right_cat)]
        x1, x2 = x_positions[left_dim], x_positions[right_dim]
        xm = (x1 + x2) / 2
        curve_x = bezier(t, x1, x2, xm, xm)
        top_edge = bezier(t, begin + height, start + height, begin + height, start + height)
        bottom_edge = bezier(t, begin, start, begin, start)
        ribbons[flow[CHANNEL]]["xs"].append(np.concatenate([curve_x, curve_x[::-1]]).tolist())
        ribbons[flow[CHANNEL]]["ys"].append(np.concatenate([top_edge, bottom_edge[::-1]]).tolist())

p = figure(
    width=3200,
    height=1800,
    title="parallel-categories-basic · python · bokeh · anyplot.ai",
    x_range=(-0.85, 3.85),
    y_range=(-0.13, 1.14),
    tools="",
    toolbar_location=None,
    min_border_left=40,
    min_border_right=40,
    min_border_top=110,
    min_border_bottom=40,
)

for cat in first_cats:
    p.patches(
        xs="xs",
        ys="ys",
        source=ColumnDataSource(ribbons[cat]),
        fill_color=color_of[cat],
        fill_alpha=0.7,
        line_color=color_of[cat],
        line_alpha=0.9,
        line_width=1,
        legend_label=str(cat),
    )

# Category segments with labels: left of each axis, right of the last one
seg = pd.DataFrame(
    [
        {
            "dim": dim,
            "cat": cat,
            "left": x_positions[dim] - box_half,
            "right": x_positions[dim] + box_half,
            "bottom": s["bottom"],
            "top": s["top"],
            "mid": (s["bottom"] + s["top"]) / 2,
        }
        for (dim, cat), s in segments.items()
    ]
)
seg["label_x"] = np.where(seg["dim"] == DIMENSIONS[-1], seg["right"] + 0.05, seg["left"] - 0.05)
seg_source = ColumnDataSource(seg)
p.quad(
    left="left",
    right="right",
    bottom="bottom",
    top="top",
    source=seg_source,
    fill_color=INK_SOFT,
    fill_alpha=0.3,
    line_color=INK_SOFT,
    line_width=2,
)
for side, align in (("left", "right"), ("right", "left")):
    mask = (seg["dim"] == DIMENSIONS[-1]) == (side == "right")
    p.add_layout(
        LabelSet(
            x="label_x",
            y="mid",
            text="cat",
            source=ColumnDataSource(seg[mask]),
            text_font_size="30pt",
            text_color=INK,
            text_align=align,
            text_baseline="middle",
        )
    )

# Dimension names above the axes
dim_source = ColumnDataSource({"x": list(x_positions.values()), "text": DIMENSIONS, "y": [1.03] * len(DIMENSIONS)})
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=dim_source,
        text_font_size="38pt",
        text_font_style="bold",
        text_color=INK,
        text_align="center",
        text_baseline="bottom",
    )
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

p.legend.title = f"Ribbon color: {CHANNEL}"
p.legend.location = "bottom_center"
p.legend.orientation = "horizontal"
p.legend.label_text_font_size = "30pt"
p.legend.title_text_font_size = "30pt"
p.legend.label_text_color = INK_SOFT
p.legend.title_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.glyph_width = 50
p.legend.glyph_height = 40
p.legend.spacing = 20
p.legend.padding = 18

# Save HTML, then screenshot it with headless Chrome
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
