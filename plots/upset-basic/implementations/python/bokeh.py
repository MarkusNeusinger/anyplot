"""anyplot.ai
upset-basic: UpSet Plot for Multi-Set Intersection Analysis
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-11-21
"""

import os
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, FixedTicker, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: a single series uses the first position
BRAND = "#009E73"

# Constants
MAX_INTERSECTIONS = 12  # the largest intersections shown, in descending order

# Columns: set these to your table's column names
ELEMENT = "element"  # role: element
SETS = "sets"  # role: sets

# Data: genes from 6 genomic differential expression experiments, one row per gene
# listing the experiments it is differentially expressed in. Replace this block
# with your own table, for example df = pd.read_csv("genes.csv") with the sets of each row joined by commas.
np.random.seed(42)
n_genes = 800
experiments = ["Exp A", "Exp B", "Exp C", "Exp D", "Exp E", "Exp F"]
membership_probs = [0.38, 0.33, 0.27, 0.30, 0.24, 0.21]
membership = np.zeros((n_genes, len(experiments)), dtype=bool)
for j, prob in enumerate(membership_probs):
    membership[:, j] = np.random.rand(n_genes) < prob
for i in range(n_genes):
    if not membership[i].any():
        membership[i, np.random.randint(len(experiments))] = True
df = pd.DataFrame(
    {
        ELEMENT: [f"gene_{i + 1:04d}" for i in range(n_genes)],
        SETS: [", ".join(experiments[j] for j in np.where(row)[0]) for row in membership],
    }
)

# Plot: reads only df and the constants above
memberships = df[SETS].dropna().map(lambda cell: frozenset(part.strip() for part in cell.split(",")))
set_names = sorted(set().union(*memberships))
n_sets = len(set_names)
set_sizes = [sum(name in sig for sig in memberships) for name in set_names]

intersections = Counter(memberships).most_common(MAX_INTERSECTIONS)
n_inter = len(intersections)
inter_counts = [count for _, count in intersections]
max_count = max(inter_counts)

# y positions: first set at the top, last at the bottom
set_y = {name: n_sets - 1 - i for i, name in enumerate(set_names)}

# Shared axis ranges keep the three panels aligned
x_range = Range1d(-0.5, n_inter - 0.5)
y_range = Range1d(-0.5, n_sets - 0.5)

W_SETS, W_MATRIX = 733, 2467
H_BAR, H_MATRIX = 600, 1200
BORDER_LEFT, BORDER_RIGHT = 280, 40

# === DOT MATRIX (bottom right) ===
p_matrix = figure(
    width=W_MATRIX,
    height=H_MATRIX,
    x_range=x_range,
    y_range=y_range,
    toolbar_location=None,
    min_border_left=BORDER_LEFT,
    min_border_right=BORDER_RIGHT,
    min_border_top=20,
    min_border_bottom=150,
)
p_matrix.background_fill_color = PAGE_BG
p_matrix.border_fill_color = PAGE_BG
p_matrix.outline_line_color = PAGE_BG

# Inactive (hollow) dots
inactive_x, inactive_y = [], []
for col_idx, (sig, _) in enumerate(intersections):
    for name in set_names:
        if name not in sig:
            inactive_x.append(col_idx)
            inactive_y.append(set_y[name])

p_matrix.scatter(
    x=inactive_x,
    y=inactive_y,
    size=22,
    marker="circle",
    fill_alpha=0,
    line_color=INK_MUTED,
    line_alpha=0.40,
    line_width=2,
)

# Connecting lines between active sets in each column
seg_x, seg_y0, seg_y1 = [], [], []
for col_idx, (sig, _) in enumerate(intersections):
    if len(sig) > 1:
        ys = [set_y[name] for name in sig]
        seg_x.append(col_idx)
        seg_y0.append(min(ys))
        seg_y1.append(max(ys))

p_matrix.segment(x0=seg_x, x1=seg_x, y0=seg_y0, y1=seg_y1, line_color=BRAND, line_width=10, alpha=0.75)

# Active (filled) dots on top
active_x, active_y = [], []
for col_idx, (sig, _) in enumerate(intersections):
    for name in sig:
        active_x.append(col_idx)
        active_y.append(set_y[name])

p_matrix.scatter(
    x=active_x, y=active_y, size=28, marker="circle", fill_color=BRAND, line_color=PAGE_BG, line_width=2, alpha=0.95
)

y_ticks = list(range(n_sets))
p_matrix.yaxis.ticker = FixedTicker(ticks=y_ticks)
p_matrix.yaxis.major_label_overrides = {set_y[name]: name for name in set_names}
p_matrix.yaxis.major_label_text_font_size = "30pt"
p_matrix.yaxis.major_label_text_color = INK_SOFT
p_matrix.yaxis.axis_line_color = INK_SOFT
p_matrix.yaxis.major_tick_line_color = None
p_matrix.yaxis.minor_tick_line_color = None

p_matrix.xaxis.ticker = FixedTicker(ticks=list(range(n_inter)))
p_matrix.xaxis.major_label_text_font_size = "0pt"
p_matrix.xaxis.axis_line_color = INK_SOFT
p_matrix.xaxis.major_tick_line_color = None
p_matrix.xaxis.minor_tick_line_color = None

p_matrix.xgrid.grid_line_color = None
p_matrix.ygrid.ticker = FixedTicker(ticks=y_ticks)
p_matrix.ygrid.grid_line_color = INK
p_matrix.ygrid.grid_line_alpha = 0.08


# === INTERSECTION BAR CHART (top right) ===
p_bar = figure(
    width=W_MATRIX,
    height=H_BAR,
    x_range=x_range,
    y_range=Range1d(0, max_count * 1.18),
    toolbar_location=None,
    title="upset-basic · python · bokeh · anyplot.ai",
    min_border_left=BORDER_LEFT,
    min_border_right=BORDER_RIGHT,
    min_border_top=100,
    min_border_bottom=10,
)
p_bar.background_fill_color = PAGE_BG
p_bar.border_fill_color = PAGE_BG
p_bar.outline_line_color = PAGE_BG

p_bar.vbar(
    x=list(range(n_inter)), top=inter_counts, width=0.55, color=BRAND, alpha=0.85, line_color=PAGE_BG, line_width=1.5
)

label_source = ColumnDataSource(
    {
        "x": list(range(n_inter)),
        "y": [h + max_count * 0.03 for h in inter_counts],
        "text": [str(h) for h in inter_counts],
    }
)
p_bar.text(
    x="x",
    y="y",
    text="text",
    source=label_source,
    text_align="center",
    text_baseline="bottom",
    text_font_size="26pt",
    text_color=INK_SOFT,
)

p_bar.title.text_font_size = "50pt"
p_bar.title.text_color = INK
p_bar.title.align = "center"

p_bar.yaxis.axis_label = "Intersection Size"
p_bar.yaxis.axis_label_text_font_size = "34pt"
p_bar.yaxis.axis_label_text_color = INK
p_bar.yaxis.major_label_text_font_size = "28pt"
p_bar.yaxis.major_label_text_color = INK_SOFT
p_bar.yaxis.axis_line_color = INK_SOFT
p_bar.yaxis.major_tick_line_color = INK_SOFT
p_bar.yaxis.minor_tick_line_color = None

p_bar.xaxis.ticker = FixedTicker(ticks=list(range(n_inter)))
p_bar.xaxis.major_label_text_font_size = "0pt"
p_bar.xaxis.axis_line_color = None
p_bar.xaxis.major_tick_line_color = None
p_bar.xaxis.minor_tick_line_color = None

p_bar.xgrid.grid_line_color = None
p_bar.ygrid.grid_line_color = INK
p_bar.ygrid.grid_line_alpha = 0.10


# === SET SIZE BAR CHART (bottom left) ===
max_set_size = max(set_sizes)
p_sets = figure(
    width=W_SETS,
    height=H_MATRIX,
    x_range=Range1d(max_set_size * 1.20, 0),
    y_range=y_range,
    toolbar_location=None,
    min_border_left=60,
    min_border_right=40,
    min_border_top=20,
    min_border_bottom=150,
)
p_sets.background_fill_color = PAGE_BG
p_sets.border_fill_color = PAGE_BG
p_sets.outline_line_color = PAGE_BG

p_sets.hbar(
    y=[set_y[name] for name in set_names],
    right=set_sizes,
    height=0.5,
    color=BRAND,
    alpha=0.80,
    line_color=PAGE_BG,
    line_width=1.5,
)

p_sets.xaxis.axis_label = "Set Size"
p_sets.xaxis.axis_label_text_font_size = "34pt"
p_sets.xaxis.axis_label_text_color = INK
p_sets.xaxis.major_label_text_font_size = "28pt"
p_sets.xaxis.major_label_text_color = INK_SOFT
p_sets.xaxis.axis_line_color = INK_SOFT
p_sets.xaxis.major_tick_line_color = INK_SOFT
p_sets.xaxis.minor_tick_line_color = None

p_sets.yaxis.visible = False
p_sets.xgrid.grid_line_color = None
p_sets.ygrid.grid_line_color = None


# === CORNER SPACER (top left) ===
p_corner = figure(width=W_SETS, height=H_BAR, x_range=Range1d(0, 1), y_range=Range1d(0, 1), toolbar_location=None)
p_corner.background_fill_color = PAGE_BG
p_corner.border_fill_color = PAGE_BG
p_corner.outline_line_color = PAGE_BG
p_corner.xaxis.visible = False
p_corner.yaxis.visible = False
p_corner.xgrid.grid_line_color = None
p_corner.ygrid.grid_line_color = None


# === Grid Layout ===
grid = gridplot([[p_corner, p_bar], [p_sets, p_matrix]], merge_tools=False, toolbar_location=None)

output_file(f"plot-{THEME}.html")
save(grid)

# Screenshot with headless Chrome via Selenium
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
driver.execute_script(
    f"document.body.style.background = '{PAGE_BG}'; document.documentElement.style.background = '{PAGE_BG}'"
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
