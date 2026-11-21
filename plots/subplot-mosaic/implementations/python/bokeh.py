""" anyplot.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 77/100 | Updated: 2026-11-21
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, DataRange1d, NumeralTickFormatter
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

# Constants: the mosaic layout, in the spirit of "AAB;CFB;DDD" (one grid cell = one third of the width)
W, H = 3200, 1800
BANNER_H = 80
CELL_W = W // 3
HEIGHT_TOP, HEIGHT_MID, HEIGHT_LOW = 640, 560, 520  # row heights below the banner
PANEL_TEXT = {  # panel key -> title, x label, y label
    "revenue": ("Quarterly revenue overview", "Day", "Revenue ($)"),
    "profit": ("Product profitability", "Units sold", "Profit margin (%)"),
    "sales": ("Sales by category", "Category", "Sales ($)"),
    "satisfaction": ("Customer satisfaction", "Quarter", "Score"),
    "orders": ("Monthly orders, year over year", "Month", "Orders"),
}

# Columns: set these to your table's column names
PANEL = "Panel"  # role: extra
SERIES = "Series"  # role: extra
X = "x"  # role: x
Y = "y"  # role: y

# Data: replace this block with your own table, one row per mark, for example df = pd.read_csv("panels.csv")
np.random.seed(42)
days = np.arange(1, 91)
revenue = 50000 + np.cumsum(np.random.randn(90) * 2000) + days * 300
units_a = np.random.rand(25) * 100
margin_a = units_a * 0.35 + np.random.randn(25) * 4 + 12
units_b = np.random.rand(25) * 100
margin_b = units_b * 0.25 + np.random.randn(25) * 5 + 8
months = np.arange(1, 13)
orders_2023 = [1200, 1400, 1100, 1600, 1800, 2100, 1900, 2200, 2400, 2100, 2300, 2800]
orders_2024 = [1400, 1600, 1350, 1850, 2100, 2400, 2200, 2500, 2700, 2350, 2600, 3100]
panels = [
    ("revenue", "Daily revenue", days, revenue),
    ("profit", "Premium line", units_a, margin_a),
    ("profit", "Standard line", units_b, margin_b),
    ("sales", "Q4 2024 sales", ["Electronics", "Clothing", "Food", "Books"], [45000, 32000, 28000, 18000]),
    ("satisfaction", "Satisfaction score", ["Q1", "Q2", "Q3", "Q4"], [78, 82, 85, 88]),
    ("orders", "2023", months, orders_2023),
    ("orders", "2024", months, orders_2024),
]
df = pd.concat(
    [pd.DataFrame({PANEL: key, SERIES: name, X: xs, Y: ys}) for key, name, xs, ys in panels], ignore_index=True
)


# Plot: reads only df and the constants above
def make_panel(key, width, height, kind):
    rows = df[df[PANEL] == key]
    title, x_label, y_label = PANEL_TEXT[key]
    series = list(rows[SERIES].unique())
    categorical = kind == "bar"
    cats = [str(c) for c in rows[X].unique()] if categorical else []
    p = figure(
        width=width,
        height=height,
        title=title,
        x_axis_label=x_label,
        y_axis_label=y_label,
        x_range=cats or DataRange1d(),
        toolbar_location=None,
        min_border_left=30,
        min_border_right=30,
        min_border_top=10,
        min_border_bottom=85,
    )
    marker_size = {"line": 7, "lines": 14, "scatter": 16, "bar": 0}[kind]
    for i, name in enumerate(series):
        part = rows[rows[SERIES] == name]
        if categorical:
            source = ColumnDataSource(part.astype({X: str, Y: float}))
            p.vbar(x=X, top=Y, source=source, width=0.62, color=IMPRINT_PALETTE[i], alpha=0.9, line_color=PAGE_BG)
            continue
        source = ColumnDataSource(part.astype({X: float, Y: float}))
        if kind in ("line", "lines"):
            p.line(X, Y, source=source, line_width=4, color=IMPRINT_PALETTE[i], legend_label=str(name))
        p.scatter(X, Y, source=source, size=marker_size, color=IMPRINT_PALETTE[i], alpha=0.75, legend_label=str(name))

    # Chrome
    p.background_fill_color = PAGE_BG
    p.border_fill_color = PAGE_BG
    p.outline_line_color = INK_SOFT
    p.title.text_color = INK
    p.title.text_font_size = "24pt"
    for axis in (p.xaxis, p.yaxis):
        axis.axis_label_text_color = INK
        axis.axis_label_text_font_size = "18pt"
        axis.major_label_text_color = INK_SOFT
        axis.major_label_text_font_size = "15pt"
        axis.axis_line_color = INK_SOFT
        axis.major_tick_line_color = INK_SOFT
        axis.minor_tick_line_color = None
    for grid in (p.xgrid, p.ygrid):
        grid.grid_line_color = INK
        grid.grid_line_alpha = 0.10
    p.y_range.start = 0 if categorical else p.y_range.start
    if kind != "scatter":
        p.yaxis.formatter = NumeralTickFormatter(format="0,0")
    if len(series) > 1:
        p.legend.location = "top_left"
        p.legend.label_text_font_size = "15pt"
        p.legend.label_text_color = INK_SOFT
        p.legend.background_fill_color = ELEVATED_BG
        p.legend.border_line_color = INK_SOFT
    elif p.legend:
        p.legend.visible = False
    return p


p_revenue = make_panel("revenue", 2 * CELL_W, HEIGHT_TOP, "line")
p_profit = make_panel("profit", W - 2 * CELL_W, HEIGHT_TOP + HEIGHT_MID, "scatter")
p_sales = make_panel("sales", CELL_W, HEIGHT_MID, "bar")
p_satisfaction = make_panel("satisfaction", CELL_W, HEIGHT_MID, "bar")
p_orders = make_panel("orders", W, HEIGHT_LOW, "lines")

# Title banner: an axis-free figure that carries only the title
banner = figure(
    width=W, height=BANNER_H, title="subplot-mosaic · python · bokeh · anyplot.ai", toolbar_location=None, min_border=0
)
banner.xaxis.visible = False
banner.yaxis.visible = False
banner.xgrid.visible = False
banner.ygrid.visible = False
banner.outline_line_color = None
banner.background_fill_color = PAGE_BG
banner.border_fill_color = PAGE_BG
banner.title.align = "center"
banner.title.text_color = INK
banner.title.text_font_size = "34pt"

# Mosaic: revenue spans two columns, profit spans two rows, orders spans all three columns
layout = column(banner, row(column(p_revenue, row(p_sales, p_satisfaction)), p_profit), p_orders, spacing=0)

# Save: interactive HTML, then a headless Chrome screenshot at the exact canvas size
output_file(f"plot-{THEME}.html")
save(layout)

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
