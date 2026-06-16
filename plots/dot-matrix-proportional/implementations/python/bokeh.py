""" anyplot.ai
dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 84/100 | Created: 2026-05-08
"""

import os as _os
import sys


# Prevent this file (bokeh.py) from shadowing the real bokeh package.
# When Python runs a script, it inserts the script's directory into sys.path[0].
# Since this file IS named bokeh.py, that directory entry must be removed first.
_here = _os.path.dirname(_os.path.abspath(__file__))
sys.path = [p for p in sys.path if _os.path.abspath(p) != _here]
del _here, _os

import os
import time
from pathlib import Path

from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (position 1 = brand green, always first series)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Exercise Frequency Survey, 200 respondents
categories = ["Daily", "3–5 times/week", "1–2 times/week", "Rarely / Never"]
counts = [52, 74, 46, 28]
N_COLS = 20
N_ROWS = 10  # 20 × 10 = 200 total dots

# Build per-dot color list (filled left-to-right, top-to-bottom)
dot_colors = []
for i, cnt in enumerate(counts):
    dot_colors.extend([IMPRINT[i]] * cnt)

# Compute grid coordinates (row 0 displayed at top → y = N_ROWS-1)
xs, ys, colors = [], [], []
idx = 0
for row in range(N_ROWS):
    for col in range(N_COLS):
        xs.append(col)
        ys.append(N_ROWS - 1 - row)
        colors.append(dot_colors[idx])
        idx += 1

# Figure — landscape canvas
p = figure(
    width=4800,
    height=2700,
    title="dot-matrix-proportional  ·  bokeh  ·  anyplot.ai",
    toolbar_location=None,
    x_range=Range1d(-0.8, N_COLS - 0.2),
    y_range=Range1d(-0.6, N_ROWS - 0.3),
)

# Draw one renderer per category; collect legend items manually
legend_items = []
total = sum(counts)
renderers = []
for i, (cat, cnt) in enumerate(zip(categories, counts, strict=True)):
    mask = [j for j, c in enumerate(colors) if c == IMPRINT[i]]
    pct = round(cnt / total * 100)
    src = ColumnDataSource(
        data={
            "x": [xs[j] for j in mask],
            "y": [ys[j] for j in mask],
            "category": [cat] * len(mask),
            "count": [cnt] * len(mask),
            "pct": [pct] * len(mask),
        }
    )
    r = p.scatter("x", "y", source=src, color=IMPRINT[i], size=140, line_color=PAGE_BG, line_width=2)
    renderers.append(r)
    legend_items.append(LegendItem(label=f"{cat}  ({cnt} · {pct}%)", renderers=[r]))

hover = HoverTool(renderers=renderers, tooltips=[("Category", "@category"), ("Count", "@count"), ("Share", "@pct%")])

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "28pt"
p.title.text_color = INK
p.title.align = "center"

p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.add_tools(hover)

# Legend in right panel (outside plot area so no overlap with data)
legend = Legend(
    items=legend_items,
    title=f"n = {total} respondents",
    title_text_font_size="20pt",
    title_text_color=INK,
    background_fill_color=ELEVATED_BG,
    border_line_color=INK_SOFT,
    label_text_color=INK_SOFT,
    label_text_font_size="22pt",
    glyph_height=55,
    glyph_width=55,
    spacing=18,
    padding=25,
)
p.add_layout(legend, "right")

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
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
