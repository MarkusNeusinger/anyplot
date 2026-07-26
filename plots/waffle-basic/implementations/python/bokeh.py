"""anyplot.ai
waffle-basic: Basic Waffle Chart
Library: bokeh 3.9.2 | Python 3.13.12
Quality: 88/100 | Updated: 2026-07-26
"""

import os
import time
from pathlib import Path

from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (first series always brand green)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - survey results on renewable energy adoption
categories = ["Solar", "Wind", "Hydro", "Geothermal"]
values = [48, 25, 18, 9]  # Percentages summing to 100
leader = categories[0]  # highest share drives the focal-point emphasis below

# Build waffle grid (10x10 = 100 squares, one square per percentage point)
grid_size = 10
total_squares = grid_size * grid_size

square_categories = []
for cat, val in zip(categories, values, strict=True):
    square_categories.extend([cat] * val)

# Create grid coordinates (fill left-to-right, bottom-to-top)
x_coords = [idx % grid_size for idx in range(total_squares)]
y_coords = [idx // grid_size for idx in range(total_squares)]

# Title — mandated format, fontsize scaled to the exact rendered length
title = "Renewable Energy Sources · waffle-basic · python · bokeh · anyplot.ai"
title_fontsize = round(50 * (67 / len(title) if len(title) > 67 else 1.0))
title_fontsize = max(title_fontsize, 34)

# Create figure — width/height are the TOTAL canvas (bokeh.md "Canvas — hard rule")
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_range=(-1.15, grid_size - 1 + 1.15),
    y_range=(-1.15, grid_size - 1 + 1.15),
    tools="",
    toolbar_location=None,
    min_border_top=140,
    min_border_bottom=60,
    min_border_left=60,
    min_border_right=60,
)

# Framing card behind the grid — a light compositional touch that gives the
# waffle a sense of place on the canvas instead of loose floating squares.
card_center = (grid_size - 1) / 2
card_span = grid_size - 1 + 1.5
p.rect(
    x=card_center,
    y=card_center,
    width=card_span,
    height=card_span,
    fill_color=ELEVATED_BG,
    line_color=INK_SOFT,
    line_width=1.5,
)

# Draw squares with a small gap between them, one renderer per category so
# hover + legend can target each group independently.
square_size = 0.88
renderers = []
for i, (cat, color) in enumerate(zip(categories, IMPRINT_PALETTE, strict=True)):
    indices = [j for j, c in enumerate(square_categories) if c == cat]
    cat_source = ColumnDataSource(
        data={
            "x": [x_coords[j] for j in indices],
            "y": [y_coords[j] for j in indices],
            "category": [cat] * len(indices),
            "percentage": [values[i]] * len(indices),
        }
    )
    r = p.rect(
        x="x",
        y="y",
        width=square_size,
        height=square_size,
        source=cat_source,
        fill_color=color,
        fill_alpha=1.0 if cat == leader else 0.85,  # focal-point emphasis on the leading share
        line_color=PAGE_BG,
        line_width=2.5,
    )
    renderers.append((f"{cat} ({values[i]}%)", [r]))

# Hover tool
hover = HoverTool(tooltips=[("Category", "@category"), ("Percentage", "@percentage%")])
p.add_tools(hover)

# Legend — click an entry to toggle its squares on/off
legend = Legend(items=[LegendItem(label=label, renderers=rends) for label, rends in renderers])
legend.title = "Category (share)"
legend.title_text_font_size = "24pt"
legend.title_text_color = INK_SOFT
legend.label_text_font_size = "34pt"
legend.glyph_height = 50
legend.glyph_width = 50
legend.spacing = 16
legend.padding = 24
legend.location = "top_right"
legend.background_fill_color = ELEVATED_BG
legend.border_line_color = INK_SOFT
legend.label_text_color = INK_SOFT
legend.click_policy = "hide"
p.add_layout(legend, "right")

# Style the title
p.title.text_font_size = f"{title_fontsize}pt"
p.title.align = "center"
p.title.text_color = INK

# Hide axes — a waffle chart carries no axis meaning
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome — Selenium 4 / Selenium Manager auto-resolves
# a working driver. Do NOT use bokeh.io.export_png (requires a chromedriver
# binary that isn't reliably available in this environment).
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
# Pin the viewport exactly via CDP — headless Chrome's --window-size sets the
# OUTER window, which still reserves a phantom title-bar height even headless,
# so innerHeight (and the screenshot) comes out short of H without this.
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
