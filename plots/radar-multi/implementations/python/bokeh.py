"""anyplot.ai
radar-multi: Multi-Series Radar Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-07
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, LabelSet, Legend
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GRID_STEP = 20  # value interval between the gridline rings

# Columns: set these to your table's column names
ATTRIBUTE = "Attribute"  # role: category
SCORE = "Score"  # role: value
PRODUCT = "Product"  # role: series

# Data: replace this block with your own table, for example df = pd.read_csv("products.csv")
attributes = ["Performance", "Reliability", "Features", "Support", "Price Value", "Ease of Use"]
scores = {
    "Product A": [85, 90, 75, 80, 70, 88],
    "Product B": [70, 75, 95, 85, 80, 72],
    "Product C": [92, 65, 80, 70, 95, 78],
}
df = pd.DataFrame(
    {
        PRODUCT: [name for name in scores for _ in attributes],
        ATTRIBUTE: attributes * len(scores),
        SCORE: [v for values in scores.values() for v in values],
    }
)

# Plot: reads only df and the constants above
categories = list(df[ATTRIBUTE].unique())
products = list(df[PRODUCT].unique())
n_categories = len(categories)

# Axes start at the top and run clockwise
angles = np.pi / 2 - np.linspace(0, 2 * np.pi, n_categories, endpoint=False)

# Value scale: rings at regular intervals up to the next step above the data
raw_step = df[SCORE].max() / 5
magnitude = 10 ** np.floor(np.log10(raw_step))
grid_step = np.ceil(raw_step / magnitude) * magnitude
grid_values = [grid_step * k for k in range(1, int(np.ceil(df[SCORE].max() / grid_step)) + 1)]
top = grid_values[-1]
view = top * 1.4

p = figure(
    width=2400,
    height=2400,
    title="radar-multi · python · bokeh · anyplot.ai",
    x_range=(-view, view),
    y_range=(-view, view),
    tools="",
    toolbar_location=None,
)

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.axis.visible = False
p.grid.visible = False

# Circular gridlines
theta = np.linspace(0, 2 * np.pi, 100)
for gv in grid_values:
    p.line(gv * np.cos(theta), gv * np.sin(theta), line_color=INK_SOFT, line_width=2, line_alpha=0.4)

# Radial spokes
for angle in angles:
    p.line(
        [0, top * 1.05 * np.cos(angle)],
        [0, top * 1.05 * np.sin(angle)],
        line_color=INK_SOFT,
        line_width=2,
        line_alpha=0.3,
    )

# Axis labels at the outer edge
label_source = ColumnDataSource(
    data={"x": top * 1.25 * np.cos(angles), "y": top * 1.25 * np.sin(angles), "text": categories}
)
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=label_source,
        text_font_size="24pt",
        text_align="center",
        text_baseline="middle",
        text_color=INK,
        text_font_style="bold",
    )
)

# Grid value labels along the first spoke
p.text(
    x=[gv * np.cos(angles[0]) + top * 0.1 for gv in grid_values],
    y=[gv * np.sin(angles[0]) + top * 0.1 for gv in grid_values],
    text=[f"{gv:g}" for gv in grid_values],
    text_font_size="20pt",
    text_color=INK_SOFT,
    text_alpha=0.9,
)

# One closed polygon per series
legend_items = []
for idx, product in enumerate(products):
    values = df[df[PRODUCT] == product].set_index(ATTRIBUTE)[SCORE].reindex(categories).to_numpy(dtype=float)
    x_vals = np.append(values * np.cos(angles), values[0] * np.cos(angles[0]))
    y_vals = np.append(values * np.sin(angles), values[0] * np.sin(angles[0]))
    fill_renderer = p.patch(
        x_vals,
        y_vals,
        fill_color=IMPRINT_PALETTE[idx],
        fill_alpha=0.25,
        line_color=IMPRINT_PALETTE[idx],
        line_width=4,
        line_alpha=0.9,
    )
    p.scatter(
        x_vals[:-1], y_vals[:-1], size=22, fill_color=IMPRINT_PALETTE[idx], line_color=PAGE_BG, line_width=3, alpha=0.9
    )
    legend_items.append((str(product), [fill_renderer]))

legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="22pt",
    glyph_height=40,
    glyph_width=40,
    spacing=20,
    padding=25,
    background_fill_color=PAGE_BG,
    background_fill_alpha=0.85,
    border_line_color=INK_SOFT,
    label_text_color=INK_SOFT,
)
p.add_layout(legend, "center")

p.title.text_font_size = "32pt"
p.title.align = "center"
p.title.text_color = INK

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
W, H = 2400, 2400
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
