"""anyplot.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: x
SOURCES = ["Solar", "Wind", "Hydro"]  # role: y
LOWER = ["Solar lower", "Wind lower", "Hydro lower"]  # role: y_lower
UPPER = ["Solar upper", "Wind upper", "Hydro upper"]  # role: y_upper
SOURCE = "Energy source"  # role: category
UNIT = "Energy Consumption (GWh)"  # axis title for the shared unit

# Data: replace this block with your own table, for example df = pd.read_csv("energy.csv")
# One row per quarter; each source has its own value and its own (unstacked) interval.
np.random.seed(42)
n = 24
solar = 50 + np.linspace(0, 80, n) + np.random.normal(0, 5, n)  # growing, widening uncertainty
solar_half = 5 + np.linspace(0, 15, n)
wind = 80 + 20 * np.sin(np.linspace(0, 6 * np.pi, n)) + np.random.normal(0, 3, n)  # seasonal
wind_half = np.full(n, 10.0)
hydro = 60 + np.random.normal(0, 2, n)  # stable, low uncertainty
hydro_half = np.full(n, 5.0)

df = pd.DataFrame(
    {
        QUARTER: pd.date_range("2020-01-01", periods=n, freq="QE"),
        SOURCES[0]: solar,
        SOURCES[1]: wind,
        SOURCES[2]: hydro,
        LOWER[0]: solar - solar_half,
        LOWER[1]: wind - wind_half,
        LOWER[2]: hydro - hydro_half,
        UPPER[0]: solar + solar_half,
        UPPER[1]: wind + wind_half,
        UPPER[2]: hydro + hydro_half,
    }
)

# Plot: reads only df and the constants above
# Stack: each series sits on the cumulative total of the series below it
tops = df[SOURCES].cumsum(axis=1)
bottoms = tops - df[SOURCES]

p = figure(
    width=3200,
    height=1800,
    title="area-stacked-confidence · python · bokeh · anyplot.ai",
    x_axis_label=QUARTER,
    y_axis_label=UNIT,
    x_axis_type="datetime",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

hover_renderers = []
for i, name in enumerate(SOURCES):
    lo, hi = LOWER[i], UPPER[i]
    color = IMPRINT_PALETTE[i]
    src = ColumnDataSource(
        {
            "x": df[QUARTER],
            "base": bottoms[name].to_numpy(),
            "top": tops[name].to_numpy(),
            "band_lo": (bottoms[name] + df[lo]).to_numpy(),
            "band_hi": (bottoms[name] + df[hi]).to_numpy(),
            "value": df[name].to_numpy(),
        }
    )
    layer = p.varea(
        x="x", y1="base", y2="top", source=src, fill_color=color, fill_alpha=0.6, legend_label=name, name=name
    )
    # Confidence band around the series' stacked edge, same hue, semi-transparent
    p.varea(x="x", y1="band_lo", y2="band_hi", source=src, fill_color=color, fill_alpha=0.3)
    p.line(x="x", y="band_lo", source=src, line_color=color, line_width=2, line_alpha=0.55, line_dash="dashed")
    p.line(x="x", y="band_hi", source=src, line_color=color, line_width=2, line_alpha=0.55, line_dash="dashed")
    # Stacked central value
    p.line(x="x", y="top", source=src, line_color=color, line_width=5)
    hover_renderers.append(layer)

p.add_tools(
    HoverTool(
        renderers=hover_renderers,
        tooltips=[(SOURCE, "$name"), (QUARTER, "@x{%F}"), (UNIT, "@value{0.0}")],
        formatters={"@x": "datetime"},
    )
)

# Legend: layers, with the band meaning in the title
p.legend.title = "Shaded band = lower to upper bound"
p.legend.location = "top_left"
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.title_text_color = INK
p.legend.label_text_font_size = "30pt"
p.legend.title_text_font_size = "28pt"
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.padding = 18
p.legend.spacing = 10

# Theme-adaptive styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_color = INK
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

p.y_range.start = 0
p.y_range.end = float(np.nanmax(bottoms.to_numpy() + df[UPPER].to_numpy())) * 1.15

# Save output
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
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
