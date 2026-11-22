""" anyplot.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LinearColorMapper, Range1d, Span, Whisker
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
IMPORTANCE = "Mean decrease in model score"  # role: importance_mean
STD = "Std. deviation across shuffles"  # role: importance_std

# Data: replace this block with your own table, for example df = pd.read_csv("importance.csv")
df = pd.DataFrame(
    {
        FEATURE: [
            "Square Footage",
            "Number of Bedrooms",
            "Neighborhood Score",
            "Year Built",
            "Lot Size",
            "Distance to City Center",
            "Number of Bathrooms",
            "Garage Capacity",
            "School Rating",
            "Crime Index",
            "Property Tax Rate",
            "Previous Sale Price",
            "Days on Market",
            "Walk Score",
            "Public Transit Access",
        ],
        IMPORTANCE: [
            0.182,
            0.145,
            0.128,
            0.095,
            0.078,
            0.065,
            0.052,
            0.041,
            0.035,
            0.028,
            0.018,
            0.012,
            0.005,
            -0.003,
            -0.008,
        ],
        STD: [0.025, 0.022, 0.020, 0.018, 0.015, 0.014, 0.012, 0.011, 0.010, 0.009, 0.008, 0.007, 0.006, 0.005, 0.004],
    }
)

# Plot: reads only df and the constants above
# Ascending order: bokeh draws the first category at the bottom, so the largest lands on top
table = df.sort_values(IMPORTANCE, ascending=True).reset_index(drop=True)
table["upper"] = table[IMPORTANCE] + table[STD]
table["lower"] = table[IMPORTANCE] - table[STD]
source = ColumnDataSource(table)

# Imprint sequential ramp (single polarity): weakest bars blue, strongest bars green
SEQ_START, SEQ_END = "#4467A3", "#009E73"


def lerp_hex(c0, c1, t):
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b, strict=True))


seq256 = [lerp_hex(SEQ_START, SEQ_END, t / 255) for t in range(256)]
mapper = LinearColorMapper(palette=seq256, low=table[IMPORTANCE].min(), high=table[IMPORTANCE].max())

span = table["upper"].max() - table["lower"].min()
p = figure(
    x_range=Range1d(table["lower"].min() - span * 0.04, table["upper"].max() + span * 0.06),
    width=3200,
    height=1800,
    y_range=[str(f) for f in table[FEATURE]],
    x_axis_label=IMPORTANCE,
    title="bar-permutation-importance · python · bokeh · anyplot.ai",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=560,
    min_border_top=110,
    min_border_right=100,
)

p.hbar(
    y=FEATURE,
    right=IMPORTANCE,
    left=0,
    height=0.7,
    source=source,
    fill_color={"field": IMPORTANCE, "transform": mapper},
    line_color=INK_SOFT,
    line_width=2,
)

p.add_layout(
    Whisker(
        source=source,
        base=FEATURE,
        upper="upper",
        lower="lower",
        dimension="width",
        line_color=INK,
        line_width=4,
        upper_head=None,
        lower_head=None,
    )
)

# Zero reference line over the full height of the plot area
p.add_layout(Span(location=0, dimension="height", line_color=INK, line_width=3, line_dash="dashed"))

p.add_tools(
    HoverTool(
        tooltips=[
            (FEATURE, f"@{{{FEATURE}}}"),
            (IMPORTANCE, f"@{{{IMPORTANCE}}}{{0.000}}"),
            (STD, f"@{{{STD}}}{{0.000}}"),
        ]
    )
)

# Style
p.title.text_font_size = "50pt"
p.title.text_font_style = "bold"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_style = "normal"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = None
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_color = None
p.outline_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Save HTML + PNG
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
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
