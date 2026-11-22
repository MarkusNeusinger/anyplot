"""anyplot.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LabelSet, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column names
QUARTER = "Quarter"  # role: category
PRODUCT_LINE = "Product line"  # role: component
REVENUE = "Revenue ($M)"  # role: value

# Data - Quarterly revenue by product line
quarters = ["Q1", "Q2", "Q3", "Q4"]
revenue = {
    "Electronics": [45, 52, 48, 68],
    "Clothing": [32, 38, 55, 72],
    "Home & Garden": [28, 42, 38, 35],
    "Sports": [18, 25, 32, 45],
}
df = pd.DataFrame(
    [
        {QUARTER: quarter, PRODUCT_LINE: line, REVENUE: values[i]}
        for line, values in revenue.items()
        for i, quarter in enumerate(quarters)
    ]
)

# Plot
quarter_order = list(df[QUARTER].unique())
lines = list(df[PRODUCT_LINE].unique())
wide = df.pivot(index=QUARTER, columns=PRODUCT_LINE, values=REVENUE).reindex(quarter_order)[lines].fillna(0)
totals = wide.sum(axis=1)

p = figure(
    x_range=quarter_order,
    width=3200,
    height=1800,
    title="bar-stacked-labeled · python · bokeh · anyplot.ai",
    x_axis_label=QUARTER,
    y_axis_label=REVENUE,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

bottoms = pd.Series(0.0, index=wide.index)
for i, line in enumerate(lines):
    values = wide[line]
    source = ColumnDataSource(
        {
            QUARTER: quarter_order,
            REVENUE: values.tolist(),
            "bottom": bottoms.tolist(),
            "top": (bottoms + values).tolist(),
            PRODUCT_LINE: [line] * len(quarter_order),
        }
    )
    bars = p.vbar(
        x=QUARTER,
        top="top",
        bottom="bottom",
        width=0.7,
        source=source,
        color=IMPRINT_PALETTE[i],
        legend_label=str(line),
        line_color=PAGE_BG,
        line_width=3,
    )
    p.add_tools(
        HoverTool(
            renderers=[bars],
            tooltips=[
                (QUARTER, f"@{{{QUARTER}}}"),
                (PRODUCT_LINE, f"@{{{PRODUCT_LINE}}}"),
                (REVENUE, f"@{{{REVENUE}}}"),
            ],
        )
    )
    bottoms = bottoms + values

# Total labels above each complete stack
label_source = ColumnDataSource({"x": quarter_order, "y": totals.tolist(), "text": [f"${t:,.0f}M" for t in totals]})
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=label_source,
        y_offset=8,
        text_font_size="40pt",
        text_font_style="bold",
        text_color=INK,
        text_align="center",
        text_baseline="bottom",
    )
)

# Axis range leaves room above the tallest stack for its label
p.y_range = Range1d(0, totals.max() * 1.15)

# Text sizes
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

# Axis chrome
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

# Legend
p.legend.title = PRODUCT_LINE
p.legend.title_text_font_size = "30pt"
p.legend.title_text_color = INK
p.legend.location = "top_left"
p.legend.label_text_font_size = "30pt"
p.legend.label_text_color = INK_SOFT
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.spacing = 12
p.legend.padding = 20
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.95
p.legend.border_line_color = INK_SOFT

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome (Selenium)
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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
