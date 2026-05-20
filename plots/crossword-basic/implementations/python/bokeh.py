"""anyplot.ai
crossword-basic: Crossword Puzzle Grid
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-20
"""

import sys
from pathlib import Path


_script_dir = str(Path(__file__).parent.absolute())
sys.path = [p for p in sys.path if p != _script_dir and p != ""]

import os  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, HoverTool, LabelSet  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
# Warmer off-white for entry cells — avoids harsh pure-white against the warm page background
CELL_BG = "#FFFDF6" if THEME == "light" else "#FFFFFF"

# Data — 15x15 crossword grid with 180-degree rotational symmetry
np.random.seed(42)
grid_size = 15
grid = np.zeros((grid_size, grid_size), dtype=int)

black_positions = [
    (0, 4),
    (0, 10),
    (1, 4),
    (1, 10),
    (2, 7),
    (3, 0),
    (3, 6),
    (3, 11),
    (3, 12),
    (4, 5),
    (4, 9),
    (5, 3),
    (5, 8),
    (5, 13),
    (6, 2),
    (6, 7),
    (6, 12),
    (7, 0),
    (7, 6),
    (7, 8),
    (7, 14),
]

for r, c in black_positions:
    grid[r, c] = 1
    grid[grid_size - 1 - r, grid_size - 1 - c] = 1

# Clue numbering: cells that start an across or down word
numbers = {}
clue_num = 1
for r in range(grid_size):
    for c in range(grid_size):
        if grid[r, c] == 1:
            continue
        starts_across = (c == 0 or grid[r, c - 1] == 1) and (c < grid_size - 1 and grid[r, c + 1] == 0)
        starts_down = (r == 0 or grid[r - 1, c] == 1) and (r < grid_size - 1 and grid[r + 1, c] == 0)
        if starts_across or starts_down:
            numbers[(r, c)] = clue_num
            clue_num += 1

# Separate cell data for rendering, hover, and clue number labels
white_x, white_y = [], []
black_x, black_y = [], []
numbered_x, numbered_y, numbered_label = [], [], []
label_x, label_y, label_text = [], [], []

for r in range(grid_size):
    for c in range(grid_size):
        y = grid_size - 1 - r  # flip so row 0 is at top
        if grid[r, c] == 0:
            white_x.append(c)
            white_y.append(y)
            if (r, c) in numbers:
                numbered_x.append(c)
                numbered_y.append(y)
                numbered_label.append(f"Clue {numbers[(r, c)]}")
                label_x.append(c - 0.43)
                label_y.append(y + 0.18)
                label_text.append(str(numbers[(r, c)]))
        else:
            black_x.append(c)
            black_y.append(y)

# Plot — square canvas for 1:1 cell aspect ratio
p = figure(
    width=2400,
    height=2400,
    title="crossword-basic · python · bokeh · anyplot.ai",
    x_range=(-0.6, grid_size - 0.4),
    y_range=(-0.6, grid_size - 0.4),
    toolbar_location=None,
    min_border_bottom=80,
    min_border_left=80,
    min_border_top=110,
    min_border_right=50,
)

p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "50pt"
p.title.align = "center"
p.title.text_color = INK

# White entry cells — warm off-white fill to complement the page surface
white_source = ColumnDataSource(data={"x": white_x, "y": white_y})
p.rect(
    x="x", y="y", source=white_source, width=0.96, height=0.96, fill_color=CELL_BG, line_color=INK_SOFT, line_width=1.5
)

# Transparent overlay on numbered cells — hover targets without visual double-drawing
numbered_source = ColumnDataSource(data={"x": numbered_x, "y": numbered_y, "label": numbered_label})
numbered_renderer = p.rect(x="x", y="y", source=numbered_source, width=0.96, height=0.96, fill_alpha=0, line_alpha=0)
hover = HoverTool(renderers=[numbered_renderer], tooltips=[("", "@label")])
p.add_tools(hover)

# Black blocking cells
black_source = ColumnDataSource(data={"x": black_x, "y": black_y})
p.rect(
    x="x",
    y="y",
    source=black_source,
    width=0.96,
    height=0.96,
    fill_color="#111110",
    line_color="#111110",
    line_width=1.5,
)

# Outer perimeter border — thicker frame gives the puzzle a polished, bounded appearance
p.rect(x=7, y=7, width=15.0, height=15.0, fill_alpha=0, line_color=INK, line_width=5)

# Clue numbers via LabelSet — idiomatic Bokeh, batched from ColumnDataSource
label_source = ColumnDataSource(data={"lx": label_x, "ly": label_y, "lt": label_text})
labels = LabelSet(
    x="lx", y="ly", text="lt", source=label_source, text_font_size="20pt", text_font_style="bold", text_color=INK_SOFT
)
p.add_layout(labels)

# Save HTML (interactive artifact)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot via headless Chrome (export_png not used — snap driver conflict)
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
