"""anyplot.ai
pie-basic: Basic Pie Chart
Library: bokeh 3.10.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-28
"""

import math
import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Label, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
OTHERS = "Others"  # semantic: the rest of the market takes the muted anchor
SLICE_LABEL = "#F0EFE8"  # near-white on dark fills
SLICE_LABEL_DARK = "#1A1A17"  # dark ink on light fills (lavender, the dark-theme muted anchor)
EXPLODE_R = 0.06  # offset of the emphasized slice

# Columns: set these to your table's column names
COMPANY = "Cloud provider"  # role: category
SHARE = "Market share (%)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("shares.csv")
# Cloud infrastructure market share (2024)
df = pd.DataFrame({COMPANY: ["AWS", "Azure", "Google Cloud", "Alibaba", "Others"], SHARE: [33, 23, 11, 4, 29]})

# Plot: reads only df and the constants above
categories = list(df[COMPANY])
values = list(df[SHARE])
colors = [
    INK_MUTED if str(c) == OTHERS else IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, c in enumerate(categories)
]


def label_ink(fill):
    """Dark ink on light fills, near-white on dark fills (relative luminance)."""
    r, g, b = (
        (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
        for c in (int(fill[k : k + 2], 16) / 255 for k in (1, 3, 5))
    )
    return SLICE_LABEL_DARK if 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.18 else SLICE_LABEL


label_colors = [label_ink(c) for c in colors]

total = sum(values)
percentages = [v / total * 100 for v in values]
angles = [v / total * 2 * math.pi for v in values]

# Start/end angles (clockwise from top)
start_angles = []
end_angles = []
current = math.pi / 2
for a in angles:
    start_angles.append(current)
    current -= a
    end_angles.append(current)

mid_angles = [(s + e) / 2 for s, e in zip(start_angles, end_angles, strict=True)]

# Explode the largest slice for emphasis
explode_idx = int(df[SHARE].idxmax())
offsets_x = [0.0] * len(categories)
offsets_y = [0.0] * len(categories)
offsets_x[explode_idx] = EXPLODE_R * math.cos(mid_angles[explode_idx])
offsets_y[explode_idx] = EXPLODE_R * math.sin(mid_angles[explode_idx])

# Title sizing — scale down only if longer than 67-char baseline
title = "pie-basic · python · bokeh · anyplot.ai"
title_pt = round(50 * (67 / len(title))) if len(title) > 67 else 50

# Figure — 2400×2400 square (canonical for symmetric plots like pie charts)
W, H = 2400, 2400
radius = 0.95

p = figure(
    width=W,
    height=H,
    title=title,
    x_range=(-1.2, 1.2),
    y_range=(-1.05, 1.1),
    toolbar_location=None,
    min_border_bottom=200,
    min_border_left=60,
    min_border_top=130,
    min_border_right=60,
)

# Wedges
source = ColumnDataSource(
    data={"x": offsets_x, "y": offsets_y, "start": start_angles, "end": end_angles, "color": colors}
)
renderers = p.wedge(
    x="x",
    y="y",
    radius=radius,
    start_angle="start",
    end_angle="end",
    direction="clock",
    fill_color="color",
    line_color=PAGE_BG,
    line_width=4,
    source=source,
)

# Percentage labels
label_r = radius * 0.62
for i in range(len(categories)):
    lx = label_r * math.cos(mid_angles[i]) + offsets_x[i]
    ly = label_r * math.sin(mid_angles[i]) + offsets_y[i]
    p.add_layout(
        Label(
            x=lx,
            y=ly,
            text=f"{percentages[i]:.0f}%",
            text_font_size="34pt",
            text_color=label_colors[i],
            text_font_style="bold",
            text_align="center",
            text_baseline="middle",
        )
    )

# Legend with category names and percentages
legend_items = [
    LegendItem(label=f"{categories[i]} ({percentages[i]:.0f}%)", renderers=[renderers], index=i)
    for i in range(len(categories))
]
legend = Legend(
    items=legend_items,
    location="center",
    orientation="horizontal",
    label_text_font_size="34pt",
    label_text_color=INK_SOFT,
    glyph_width=40,
    glyph_height=40,
    spacing=30,
    padding=20,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.9,
    border_line_color=INK_SOFT,
)
p.add_layout(legend, "below")

# Styling
p.title.text_font_size = f"{title_pt}pt"
p.title.align = "center"
p.title.text_color = INK
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = PAGE_BG
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Save HTML (interactive catalog artifact)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome; the viewport is pinned to W×H via CDP.
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
    "--force-device-scale-factor=1",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
