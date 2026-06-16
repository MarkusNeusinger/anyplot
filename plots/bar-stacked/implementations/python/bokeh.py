""" anyplot.ai
bar-stacked: Stacked Bar Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-09
"""

import os
import sys
import time
from pathlib import Path

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

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Monthly energy consumption by source (in gigawatt-hours)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
sources = ["Solar", "Wind", "Hydro", "Natural Gas"]
colors = IMPRINT

data = {
    "Solar": [85, 92, 110, 125, 145, 165, 175, 160, 140, 115, 95, 80],
    "Wind": [120, 130, 125, 110, 95, 85, 80, 90, 105, 125, 140, 145],
    "Hydro": [105, 100, 95, 90, 85, 75, 70, 75, 85, 95, 110, 115],
    "Natural Gas": [65, 60, 55, 50, 45, 40, 35, 40, 50, 60, 70, 80],
}

# Calculate bottom positions for stacking
bottoms = {src: [0] * len(months) for src in sources}
running_total = [0] * len(months)
for src in sources:
    bottoms[src] = running_total.copy()
    running_total = [r + v for r, v in zip(running_total, data[src], strict=True)]

# Create figure
p = figure(
    x_range=months,
    width=4800,
    height=2700,
    title="bar-stacked · bokeh · anyplot.ai",
    x_axis_label="Month",
    y_axis_label="Energy Production (GWh)",
    toolbar_location=None,
)

# Create stacked bars
legend_items = []
for src, color in zip(sources, colors, strict=True):
    source = ColumnDataSource(
        data={
            "x": months,
            "top": [b + v for b, v in zip(bottoms[src], data[src], strict=True)],
            "bottom": bottoms[src],
            "value": data[src],
            "source": [src] * len(months),
        }
    )
    renderer = p.vbar(
        x="x", top="top", bottom="bottom", width=0.6, source=source, color=color, line_color=PAGE_BG, line_width=1.5
    )
    legend_items.append(LegendItem(label=src, renderers=[renderer]))

    # Add hover tool
    hover = HoverTool(
        renderers=[renderer], tooltips=[("Month", "@x"), ("Source", "@source"), ("Production", "@value{0} GWh")]
    )
    p.add_tools(hover)

# Add legend
legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="18pt",
    spacing=12,
    padding=15,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.95,
    border_line_color=INK_SOFT,
    label_text_color=INK_SOFT,
    glyph_height=28,
    glyph_width=28,
)
p.add_layout(legend)

# Style the plot
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.10
p.ygrid.grid_line_color = INK

# Axis styling
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.outline_line_color = INK_SOFT

# Plot background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Set y-axis range with padding
p.y_range.start = 0
p.y_range.end = max(running_total) * 1.1

# Determine output directory
impl_dir = Path(__file__).parent
os.chdir(impl_dir)

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot to PNG with headless Chrome
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
driver.get(f"file://{(impl_dir / f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(str(impl_dir / f"plot-{THEME}.png"))
driver.quit()
