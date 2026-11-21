"""anyplot.ai
facet-grid: Faceted Grid Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-13
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column, gridplot
from bokeh.models import ColumnDataSource, HoverTool, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per region in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SPEND = "Marketing spend ($K)"  # role: x
SALES = "Sales ($K)"  # role: y
SEASON = "Season"  # role: col_facet
REGION = "Region"  # role: row_facet

# Data: replace this block with your own table, for example df = pd.read_csv("sales.csv")
rng = np.random.default_rng(42)
regions = ["North", "South", "East"]
seasons = ["Spring", "Summer", "Fall", "Winter"]
base_spend = {"North": 20, "South": 30, "East": 25}
base_sales = {"North": 50, "South": 70, "East": 60}
season_factor = {"Spring": 1.0, "Summer": 1.3, "Fall": 0.9, "Winter": 0.7}
frames = []
for region in regions:
    for season in seasons:
        spend = rng.normal(base_spend[region], 5, 25)
        sales = base_sales[region] * season_factor[season] + spend * 0.8 + rng.normal(0, 8, 25)
        frames.append(pd.DataFrame({SPEND: spend, SALES: sales, SEASON: season, REGION: region}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
row_levels = list(df[REGION].unique())
col_levels = list(df[SEASON].unique())
region_color = {level: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, level in enumerate(row_levels)}

# Shared scales: one pair of ranges for every panel, padded around the full data
x_pad = (df[SPEND].max() - df[SPEND].min()) * 0.05
y_pad = (df[SALES].max() - df[SALES].min()) * 0.05
x_range = Range1d(df[SPEND].min() - x_pad, df[SPEND].max() + x_pad)
y_range = Range1d(df[SALES].min() - y_pad, df[SALES].max() + y_pad)

FRAME_W, FRAME_H = 655, 388
panels = []
for r, region in enumerate(row_levels):
    row_panels = []
    for c, season in enumerate(col_levels):
        subset = df[(df[REGION] == region) & (df[SEASON] == season)]
        first_col = c == 0
        last_row = r == len(row_levels) - 1
        p = figure(
            frame_width=FRAME_W,
            frame_height=FRAME_H,
            x_range=x_range,
            y_range=y_range,
            title=f"{region} · {season}",
            x_axis_label=SPEND if last_row else None,
            y_axis_label=SALES if first_col else None,
            tools="",
            toolbar_location=None,
            min_border_left=190 if first_col else 100,
            min_border_bottom=170 if last_row else 80,
            min_border_top=10,
            min_border_right=15,
        )
        scatter = p.scatter(
            x=SPEND,
            y=SALES,
            source=ColumnDataSource(subset),
            size=14,
            color=region_color[region],
            alpha=0.75,
            line_color=PAGE_BG,
            line_width=1,
        )
        p.add_tools(
            HoverTool(
                renderers=[scatter],
                tooltips=[
                    (REGION, f"@{{{REGION}}}"),
                    (SEASON, f"@{{{SEASON}}}"),
                    (SPEND, f"@{{{SPEND}}}{{0.0}}"),
                    (SALES, f"@{{{SALES}}}{{0.0}}"),
                ],
            )
        )

        # Facet strip as the panel title
        p.title.text_font_size = "22pt"
        p.title.text_font_style = "bold"
        p.title.text_color = INK
        p.title.align = "left"

        p.xaxis.axis_label_text_font_size = "26pt"
        p.yaxis.axis_label_text_font_size = "26pt"
        p.xaxis.major_label_text_font_size = "20pt"
        p.yaxis.major_label_text_font_size = "20pt"
        p.xaxis.axis_label_text_color = INK
        p.yaxis.axis_label_text_color = INK
        p.xaxis.axis_label_text_font_style = "normal"
        p.yaxis.axis_label_text_font_style = "normal"
        p.xaxis.major_label_text_color = INK_SOFT
        p.yaxis.major_label_text_color = INK_SOFT
        p.xaxis.axis_line_color = INK_SOFT
        p.yaxis.axis_line_color = INK_SOFT
        p.xaxis.major_tick_line_color = INK_SOFT
        p.yaxis.major_tick_line_color = INK_SOFT
        p.xaxis.minor_tick_line_color = None
        p.yaxis.minor_tick_line_color = None
        p.xaxis.ticker.desired_num_ticks = 5
        p.yaxis.ticker.desired_num_ticks = 5

        p.background_fill_color = PAGE_BG
        p.border_fill_color = PAGE_BG
        p.outline_line_color = INK_SOFT
        p.xgrid.grid_line_color = INK
        p.ygrid.grid_line_color = INK
        p.xgrid.grid_line_alpha = 0.15
        p.ygrid.grid_line_alpha = 0.15

        row_panels.append(p)
    panels.append(row_panels)

grid = gridplot(panels, toolbar_location=None, merge_tools=False)

# Figure title and one legend for the whole figure, each in a slim bare figure
W, H = 3200, 1800


def bare_figure(height):
    f = figure(width=W, height=height, x_range=(0, 1), y_range=(0, 1), tools="", toolbar_location=None)
    f.axis.visible = False
    f.grid.visible = False
    f.background_fill_color = PAGE_BG
    f.border_fill_color = PAGE_BG
    f.outline_line_color = None
    return f


title_fig = bare_figure(90)
title_fig.title = "facet-grid · python · bokeh · anyplot.ai"
title_fig.title.align = "center"
title_fig.title.text_font_size = "34pt"
title_fig.title.text_color = INK

legend_fig = bare_figure(70)
for level in row_levels:
    legend_fig.scatter(x=[-1], y=[-1], size=30, color=region_color[level], legend_label=str(level))
legend_fig.legend.title = REGION
legend_fig.legend.orientation = "horizontal"
legend_fig.legend.location = "center"
legend_fig.legend.label_text_font_size = "20pt"
legend_fig.legend.title_text_font_size = "20pt"
legend_fig.legend.label_text_color = INK_SOFT
legend_fig.legend.title_text_color = INK
legend_fig.legend.background_fill_color = PAGE_BG
legend_fig.legend.border_line_color = None
legend_fig.legend.glyph_height = 30
legend_fig.legend.glyph_width = 30
legend_fig.legend.spacing = 40

layout = column(title_fig, grid, legend_fig)

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
driver.execute_script(f'document.documentElement.style.background = "{PAGE_BG}"')
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
