"""anyplot.ai
bar-stacked: Stacked Bar Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os
import sys
import time
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Remove current directory from sys.path to avoid shadowing bokeh module
current_dir = str(Path(__file__).parent.absolute())
sys.path = [p for p in sys.path if p != current_dir and p != ""]

from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem  # noqa: E402
from bokeh.plotting import figure  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per component in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
MONTH = "Month"  # role: category
SOURCE = "Energy source"  # role: component
ENERGY = "Energy production (GWh)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("energy.csv")
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
production = {
    "Solar": [85, 92, 110, 125, 145, 165, 175, 160, 140, 115, 95, 80],
    "Wind": [120, 130, 125, 110, 95, 85, 80, 90, 105, 125, 140, 145],
    "Hydro": [105, 100, 95, 90, 85, 75, 70, 75, 85, 95, 110, 115],
    "Natural Gas": [65, 60, 55, 50, 45, 40, 35, 40, 50, 60, 70, 80],
}
df = pd.DataFrame(
    {
        MONTH: months * len(production),
        SOURCE: [name for name in production for _ in months],
        ENERGY: [v for values in production.values() for v in values],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=MONTH, columns=SOURCE, values=ENERGY, sort=False)
sources = list(table.columns)
categories = list(table.index)
tops = table.cumsum(axis=1)
bottoms = tops - table

p = figure(
    x_range=categories,
    width=3200,
    height=1800,
    title="bar-stacked · python · bokeh · anyplot.ai",
    x_axis_label=MONTH,
    y_axis_label=ENERGY,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

legend_items = []
for i, src in enumerate(sources):
    rows = ColumnDataSource(
        {
            MONTH: categories,
            "top": tops[src].to_numpy(),
            "bottom": bottoms[src].to_numpy(),
            ENERGY: table[src].to_numpy(),
            SOURCE: [src] * len(categories),
        }
    )
    renderer = p.vbar(
        x=MONTH,
        top="top",
        bottom="bottom",
        width=0.7,
        source=rows,
        color=IMPRINT_PALETTE[i],
        line_color=PAGE_BG,
        line_width=2,
    )
    legend_items.append(LegendItem(label=str(src), renderers=[renderer]))
    p.add_tools(
        HoverTool(
            renderers=[renderer],
            tooltips=[(MONTH, f"@{{{MONTH}}}"), (SOURCE, f"@{{{SOURCE}}}"), (ENERGY, f"@{{{ENERGY}}}{{0}}")],
        )
    )

# Legend beside the plot so it never covers a stack
legend = Legend(
    items=legend_items,
    title=SOURCE,
    title_text_font_size="30pt",
    title_text_color=INK,
    label_text_font_size="30pt",
    label_text_color=INK_SOFT,
    spacing=14,
    padding=20,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.95,
    border_line_color=INK_SOFT,
    glyph_height=36,
    glyph_width=36,
)
p.add_layout(legend, "right")

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.outline_line_color = None

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

p.y_range.start = 0
p.y_range.end = float(tops.to_numpy().max()) * 1.08

# Save
impl_dir = Path(__file__).parent
os.chdir(impl_dir)
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
driver.get(f"file://{(impl_dir / f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(str(impl_dir / f"plot-{THEME}.png"))
driver.quit()
