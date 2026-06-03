"""anyplot.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 90/100 | Updated: 2026-06-03
"""

import base64
import os
import sys
import time
from pathlib import Path


# Prevent this file (bokeh.py) from shadowing the real bokeh package
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir]

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import (
    BoxAnnotation,
    ColumnDataSource,
    CustomJSTickFormatter,
    FixedTicker,
    HoverTool,
    Label,
    Range1d,
    Title,
)
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette, see prompts/default-style-guide.md
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — canonical order, position 1 always first
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data — fruit production (thousands of tonnes), icon = 5k tonnes
categories = ["Apples", "Oranges", "Bananas", "Grapes", "Mangoes"]
values = [35, 23, 17, 28, 11]
icon_value = 5

# Sort by value descending, assign Imprint colors in ordinal rank order
sorted_data = sorted(zip(categories, values, strict=True), key=lambda x: x[1], reverse=True)
categories = [d[0] for d in sorted_data]
values = [d[1] for d in sorted_data]
colors = IMPRINT_PALETTE[: len(categories)]

# Build icon grid positions
full_x, full_y, full_c, full_cat, full_val = [], [], [], [], []
bg_x, bg_y = [], []
wedge_x, wedge_y, wedge_c, wedge_end = [], [], [], []
n_cats = len(categories)
radius = 0.40

for i, (cat, val, color) in enumerate(zip(categories, values, colors, strict=True)):
    n_full = int(val // icon_value)
    remainder = val % icon_value
    fraction = remainder / icon_value
    y = n_cats - 1 - i

    for j in range(n_full):
        full_x.append(j)
        full_y.append(y)
        full_c.append(color)
        full_cat.append(cat)
        full_val.append(f"{val}k tonnes")

    if fraction > 0:
        bg_x.append(n_full)
        bg_y.append(y)
        wedge_x.append(n_full)
        wedge_y.append(y)
        wedge_c.append(color)
        wedge_end.append(np.pi / 2 - fraction * 2 * np.pi)

# Figure — canonical landscape 3200×1800, toolbar_location=None is mandatory
max_icons = max(int(np.ceil(v / icon_value)) for v in values)

TITLE = "pictogram-basic · python · bokeh · anyplot.ai"
title_n = len(TITLE)
title_fs = f"{round(50 * min(1.0, 67 / title_n))}pt"

p = figure(
    width=3200,
    height=1800,
    x_range=Range1d(-0.65, max_icons + 0.65),
    y_range=Range1d(-0.85, n_cats - 0.15),
    toolbar_location=None,
    title=TITLE,
    min_border_left=240,
    min_border_bottom=120,
    min_border_top=110,
    min_border_right=230,
)

# Subtitle
subtitle = Title(
    text="Fruit Production — Annual output in thousands of tonnes",
    text_font_size="28pt",
    text_color=INK_SOFT,
    align="center",
)
p.add_layout(subtitle, "above")

# Alternating row background bands for readability
for i in range(n_cats):
    if i % 2 == 0:
        band = BoxAnnotation(bottom=i - 0.48, top=i + 0.48, fill_color=ELEVATED_BG, fill_alpha=0.6, level="underlay")
        p.add_layout(band)

# Full icons — circles with page-background stroke for definition
full_source = ColumnDataSource(
    data={"x": full_x, "y": full_y, "color": full_c, "category": full_cat, "value": full_val}
)
circles = p.circle(
    x="x", y="y", radius=radius, source=full_source, color="color", alpha=0.90, line_color=PAGE_BG, line_width=3
)

# Interactive hover tooltip (Bokeh HTML output feature)
hover = HoverTool(renderers=[circles], tooltips=[("Category", "@category"), ("Production", "@value")])
p.add_tools(hover)

# Partial icon backgrounds (muted ghost circles)
if bg_x:
    bg_source = ColumnDataSource(data={"x": bg_x, "y": bg_y})
    p.circle(
        x="x", y="y", radius=radius, source=bg_source, color=INK_SOFT, alpha=0.18, line_color=PAGE_BG, line_width=3
    )

    # Partial icon wedge fills
    wedge_source = ColumnDataSource(data={"x": wedge_x, "y": wedge_y, "color": wedge_c, "end_angle": wedge_end})
    p.wedge(
        x="x",
        y="y",
        radius=radius,
        start_angle=np.pi / 2,
        end_angle="end_angle",
        direction="clock",
        source=wedge_source,
        color="color",
        alpha=0.90,
        line_color=PAGE_BG,
        line_width=3,
    )

# Value labels on the right of each row
for i, (_cat, val) in enumerate(zip(categories, values, strict=True)):
    y = n_cats - 1 - i
    n_icons = int(np.ceil(val / icon_value))
    val_label = Label(
        x=n_icons + 0.18,
        y=y,
        text=f"{val:,}k",
        text_font_size="28pt",
        text_font_style="bold" if i == 0 else "normal",
        text_color=INK if i == 0 else INK_SOFT,
        text_baseline="middle",
        text_align="left",
        x_units="data",
        y_units="data",
    )
    p.add_layout(val_label)

# Legend key
legend_label = Label(
    x=0,
    y=-0.62,
    text="Each ● = 5,000 tonnes",
    text_font_size="26pt",
    text_color=INK_MUTED,
    x_units="data",
    y_units="data",
)
p.add_layout(legend_label)

# Title styling
p.title.text_font_size = title_fs
p.title.align = "center"
p.title.text_color = INK

# Y-axis: category labels
cat_labels = [categories[n_cats - 1 - i] for i in range(n_cats)]
p.yaxis.ticker = FixedTicker(ticks=list(range(n_cats)))
p.yaxis.formatter = CustomJSTickFormatter(args={"labels": cat_labels}, code="return labels[tick] || '';")
p.yaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_style = "bold"
p.yaxis.major_label_text_color = INK

# X-axis: hidden (icon count readable from row widths)
p.xaxis.visible = False

# Remove spines and grid — clean isotype layout
p.outline_line_color = None
p.grid.grid_line_color = None
p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.yaxis.major_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Theme-adaptive background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Save interactive HTML, then screenshot with Selenium (export_png unavailable on this runner)
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
time.sleep(3)

# Use CDP clip to get exactly W×H pixels regardless of Chrome viewport overhead
png_data = driver.execute_cdp_cmd(
    "Page.captureScreenshot", {"format": "png", "clip": {"x": 0, "y": 0, "width": W, "height": H, "scale": 1}}
)
with open(f"plot-{THEME}.png", "wb") as f:
    f.write(base64.b64decode(png_data["data"]))
driver.quit()
