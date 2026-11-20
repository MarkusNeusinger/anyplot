"""anyplot.ai
scatter-matrix: Scatter Plot Matrix
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column, gridplot
from bokeh.models import ColumnDataSource, Div, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
EDGE = "#FFFFFF" if THEME == "light" else "#2A2A27"

# Imprint palette (first series always #009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column names
VARIABLES = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]  # role: variables
SPECIES = "Species"  # role: group

# Data - Iris-like dataset with 4 variables and 3 species
np.random.seed(42)
df = pd.DataFrame(
    {
        VARIABLES[0]: np.concatenate(
            [np.random.normal(5.0, 0.35, 50), np.random.normal(5.9, 0.52, 50), np.random.normal(6.6, 0.64, 50)]
        ),
        VARIABLES[1]: np.concatenate(
            [np.random.normal(3.4, 0.38, 50), np.random.normal(2.8, 0.31, 50), np.random.normal(3.0, 0.32, 50)]
        ),
        VARIABLES[2]: np.concatenate(
            [np.random.normal(1.5, 0.17, 50), np.random.normal(4.3, 0.47, 50), np.random.normal(5.6, 0.55, 50)]
        ),
        VARIABLES[3]: np.concatenate(
            [np.random.normal(0.2, 0.10, 50), np.random.normal(1.3, 0.20, 50), np.random.normal(2.0, 0.27, 50)]
        ),
        SPECIES: np.repeat(["Setosa", "Versicolor", "Virginica"], 50),
    }
)

# Plot
variables = VARIABLES
groups = list(df[SPECIES].unique())
n_vars = len(variables)

# Square canvas: 2400 x 2400 = title strip + n_vars x n_vars cells
CANVAS = 2400
TITLE_H = 110
cell_w = CANVAS // n_vars
cell_h = (CANVAS - TITLE_H) // n_vars

# One shared range per variable, used by its column (x) and its row (y)
ranges = {}
for v in variables:
    lo, hi = df[v].min(), df[v].max()
    pad = (hi - lo) * 0.06
    ranges[v] = (lo - pad, hi + pad)

grid = []
for i, row_var in enumerate(variables):
    row = []
    for j, col_var in enumerate(variables):
        p = figure(
            width=cell_w,
            height=cell_h,
            x_range=Range1d(*ranges[col_var]),
            x_axis_label=col_var if i == n_vars - 1 else None,
            y_axis_label=row_var if j == 0 else None,
            tools="",
            toolbar_location=None,
            min_border_left=150 if j == 0 else 60,
            min_border_bottom=130 if i == n_vars - 1 else 40,
            min_border_top=20,
            min_border_right=20,
        )

        if i == j:
            # Diagonal: stacked-by-species histogram of the variable
            bins = np.linspace(*ranges[col_var], 21)
            for k, sp in enumerate(groups):
                hist, edges = np.histogram(df.loc[df[SPECIES] == sp, col_var].dropna(), bins=bins)
                p.quad(
                    top=hist,
                    bottom=0,
                    left=edges[:-1],
                    right=edges[1:],
                    fill_color=IMPRINT_PALETTE[k % len(IMPRINT_PALETTE)],
                    line_color=PAGE_BG,
                    line_width=1.5,
                    alpha=0.75,
                    legend_label=str(sp),
                )
            p.y_range.start = 0
            if i == 0:
                p.legend.title = SPECIES
                p.legend.location = "top_right"
                p.legend.label_text_font_size = "20pt"
                p.legend.title_text_font_size = "20pt"
                p.legend.title_text_color = INK
                p.legend.glyph_height = 22
                p.legend.glyph_width = 22
                p.legend.spacing = 6
                p.legend.background_fill_color = ELEVATED_BG
                p.legend.background_fill_alpha = 0.9
                p.legend.border_line_color = INK_SOFT
                p.legend.label_text_color = INK_SOFT
            else:
                p.legend.visible = False
        else:
            # Off-diagonal: scatter coloured by species, same colours in every cell
            p.y_range = Range1d(*ranges[row_var])
            for k, sp in enumerate(groups):
                rows = ColumnDataSource(df[df[SPECIES] == sp])
                p.scatter(
                    x=col_var,
                    y=row_var,
                    source=rows,
                    size=9,
                    alpha=0.6,
                    fill_color=IMPRINT_PALETTE[k % len(IMPRINT_PALETTE)],
                    line_color=EDGE,
                    line_width=0.6,
                )

        # Theme chrome
        p.background_fill_color = PAGE_BG
        p.border_fill_color = PAGE_BG
        p.outline_line_width = 0
        for axis in (p.xaxis, p.yaxis):
            axis.axis_label_text_color = INK
            axis.major_label_text_color = INK_SOFT
            axis.axis_line_color = INK_SOFT
            axis.major_tick_line_color = INK_SOFT
            axis.minor_tick_line_color = None
            axis.axis_label_text_font_size = "26pt"
            axis.axis_label_text_font_style = "normal"
            axis.major_label_text_font_size = "17pt"
            axis.ticker.desired_num_ticks = 4
        for g in (p.xgrid, p.ygrid):
            g.grid_line_color = INK
            g.grid_line_alpha = 0.08

        row.append(p)
    grid.append(row)

title = Div(
    text="scatter-matrix · python · bokeh · anyplot.ai",
    width=CANVAS,
    height=TITLE_H,
    styles={
        "color": INK,
        "background": PAGE_BG,
        "font-size": "40px",
        "font-weight": "500",
        "padding": "30px 0 0 60px",
        "box-sizing": "border-box",
    },
)
layout = column(title, gridplot(grid, toolbar_location=None, merge_tools=False), background=PAGE_BG)

# Save HTML
output_file(f"plot-{THEME}.html")
save(layout)

# Screenshot with headless Chrome
W, H = CANVAS, CANVAS
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
