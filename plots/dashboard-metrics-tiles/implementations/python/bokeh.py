"""anyplot.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-21
"""

import os
import sys
import time
from pathlib import Path


# bokeh.py shadows the installed bokeh package when Python adds this file's
# directory to sys.path[0]; remove it so imports resolve to the package.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != _here]
del _here

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column, gridplot
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Status colors are Imprint semantic anchors: green (good), amber (warning), red (critical)
STATUS_COLORS = {"good": IMPRINT_PALETTE[0], "warning": "#DDCC77", "critical": IMPRINT_PALETTE[4]}
FAVORABLE_COLOR = IMPRINT_PALETTE[0]
UNFAVORABLE_COLOR = IMPRINT_PALETTE[4]
SPARKLINE_COLOR = IMPRINT_PALETTE[2]
GRID_COLUMNS = 3  # tiles per row
CANVAS_W, CANVAS_H, TITLE_H = 3200, 1800, 160

# Columns: set these to your table's column names
METRIC = "Metric"  # role: metric_name
VALUE = "Current value"  # role: current_value
HISTORY = "History"  # role: history
CHANGE = "Change (%)"  # role: change_percent
STATUS = "Status"  # role: status
UNIT = "Unit"  # role: extra
LOWER_IS_BETTER = "Lower is better"  # role: extra

# Data: replace this block with your own table, one row per tile; History holds a list per row
np.random.seed(42)
df = pd.DataFrame(
    {
        METRIC: ["CPU Usage", "Memory", "Response Time", "Error Rate", "Throughput", "Active Users"],
        VALUE: [45, 72, 120, 2.4, 1250, 8432],
        UNIT: ["%", "%", "ms", "%", "req/s", ""],
        HISTORY: [
            tuple(np.clip(40 + np.cumsum(np.random.randn(30) * 2), 20, 80)),
            tuple(np.clip(65 + np.cumsum(np.random.randn(30) * 1.5), 50, 90)),
            tuple(np.clip(100 + np.cumsum(np.random.randn(30) * 10), 50, 200)),
            tuple(np.clip(2 + np.cumsum(np.random.randn(30) * 0.3), 0.5, 5)),
            tuple(np.clip(1200 + np.cumsum(np.random.randn(30) * 50), 900, 1500)),
            tuple(np.clip(8000 + np.cumsum(np.random.randn(30) * 200), 7000, 10000)),
        ],
        CHANGE: [-5.2, 8.1, -15.3, 12.5, 3.7, -2.1],
        STATUS: ["good", "warning", "good", "critical", "good", "warning"],
        LOWER_IS_BETTER: [False, False, True, True, False, False],
    }
)

# Plot: reads only df and the constants above
n_rows = -(-len(df) // GRID_COLUMNS)
TILE_WIDTH = CANVAS_W // GRID_COLUMNS
TILE_HEIGHT = (CANVAS_H - TITLE_H) // n_rows
FILL_ALPHA = 0.25 if THEME == "light" else 0.45  # keeps the area visible on the darker tile

tiles = []

for _, row in df.iterrows():
    is_positive_change = row[CHANGE] > 0
    is_favorable = is_positive_change != row[LOWER_IS_BETTER]
    change_color = FAVORABLE_COLOR if is_favorable else UNFAVORABLE_COLOR
    arrow = "▲" if is_positive_change else "▼"
    status_color = STATUS_COLORS.get(row[STATUS], INK_SOFT)

    p = figure(
        width=TILE_WIDTH, height=TILE_HEIGHT, toolbar_location=None, tools="", x_range=(0, 1), y_range=(-0.02, 1.12)
    )

    # Hide axes and grid; apply tile chrome
    p.xaxis.visible = False
    p.yaxis.visible = False
    p.xgrid.visible = False
    p.ygrid.visible = False
    p.outline_line_color = INK_SOFT
    p.background_fill_color = ELEVATED_BG
    p.border_fill_color = PAGE_BG

    # Status bar across top of tile
    p.quad(left=0, right=1, top=1.08, bottom=1.0, fill_color=status_color, line_color=None)

    # Metric name
    p.add_layout(
        Label(
            x=0.5,
            y=0.85,
            text=row[METRIC],
            text_font_size="20pt",
            text_font_style="bold",
            text_color=INK,
            text_align="center",
            text_baseline="middle",
        )
    )

    # Prominent current value
    value_text = f"{row[VALUE]:g}{row[UNIT]}"
    p.add_layout(
        Label(
            x=0.5,
            y=0.63,
            text=value_text,
            text_font_size="42pt",
            text_font_style="bold",
            text_color=INK,
            text_align="center",
            text_baseline="middle",
        )
    )

    # Change indicator with directional arrow
    change_text = f"{arrow} {abs(row[CHANGE]):.1f}%"
    p.add_layout(
        Label(
            x=0.5,
            y=0.43,
            text=change_text,
            text_font_size="22pt",
            text_font_style="bold",
            text_color=change_color,
            text_align="center",
            text_baseline="middle",
        )
    )

    # Sparkline — normalize history to [0.05, 0.33]
    history = pd.to_numeric(pd.Series(list(row[HISTORY])), errors="coerce").to_numpy(dtype=float)
    if np.isfinite(history).any():
        hist_min, hist_max = np.nanmin(history), np.nanmax(history)
        hist_range = hist_max - hist_min if hist_max != hist_min else 1.0
        y_norm = 0.05 + (history - hist_min) / hist_range * 0.28
        x_norm = np.linspace(0.08, 0.92, len(history))

        # Filled area under sparkline
        y_fill = np.concatenate([y_norm, [0.05, 0.05]])
        x_fill = np.concatenate([x_norm, [x_norm[-1], x_norm[0]]])
        p.patch(x_fill, y_fill, fill_color=SPARKLINE_COLOR, fill_alpha=FILL_ALPHA, line_color=None)

        # Sparkline line (thicker for visibility)
        source = ColumnDataSource(data={"x": x_norm, "y": y_norm})
        p.line("x", "y", source=source, line_width=5, line_color=SPARKLINE_COLOR)

        # Endpoint dot marking the current value
        p.scatter(
            x=[x_norm[-1]], y=[y_norm[-1]], size=14, fill_color=SPARKLINE_COLOR, line_color=ELEVATED_BG, line_width=2.5
        )

    tiles.append(p)

# 3x2 grid of tiles — toolbar_location=None is critical: gridplot default toolbar
# adds ~139px above the canvas, shrinking the screenshot height below 1800
grid = gridplot(
    [tiles[i : i + GRID_COLUMNS] for i in range(0, len(tiles), GRID_COLUMNS)], merge_tools=False, toolbar_location=None
)

# Title figure (full canvas width, 160px tall)
title_fig = figure(width=CANVAS_W, height=TITLE_H, toolbar_location=None, tools="", x_range=(0, 1), y_range=(0, 1))
title_fig.xaxis.visible = False
title_fig.yaxis.visible = False
title_fig.xgrid.visible = False
title_fig.ygrid.visible = False
title_fig.outline_line_color = None
title_fig.background_fill_color = PAGE_BG
title_fig.border_fill_color = PAGE_BG

title_fig.add_layout(
    Label(
        x=0.5,
        y=0.5,
        text="dashboard-metrics-tiles · python · bokeh · anyplot.ai",
        text_font_size="50pt",
        text_font_style="bold",
        text_color=INK,
        text_align="center",
        text_baseline="middle",
    )
)

final_layout = column(title_fig, grid)

# Save interactive HTML
output_file(f"plot-{THEME}.html")
save(final_layout)

# Screenshot to PNG via headless Chrome (Selenium 4 / Selenium Manager)
W, H = CANVAS_W, CANVAS_H
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
# --window-size includes browser chrome; use CDP to set exact viewport
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.execute_script(
    f"document.body.style.margin='0'; document.body.style.padding='0';document.body.style.backgroundColor='{PAGE_BG}';"
)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
