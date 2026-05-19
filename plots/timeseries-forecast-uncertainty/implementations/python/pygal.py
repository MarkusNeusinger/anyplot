""" anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: pygal 3.1.0 | Python 3.13.13
Quality: 77/100 | Updated: 2026-05-19
"""

import os
import sys


# noqa: E402 - sys.path must be modified before imports to avoid module shadowing
sys.path[:] = [p for p in sys.path if p not in ("", ".", os.path.dirname(__file__))]

import cairosvg  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

BRAND = "#009E73"  # Okabe-Ito position 1
FORECAST_COLOR = "#D55E00"  # Okabe-Ito position 2

# Data
np.random.seed(42)
months = 42  # 36 historical + 6 forecast
dates = pd.date_range("2022-01-01", periods=months, freq="MS")
split_idx = 36

t = np.arange(split_idx)
base = 1000 + 50 * t + 100 * np.sin(2 * np.pi * t / 12)
noise = np.random.normal(0, 30, split_idx)
actual = base + noise

t_forecast = np.arange(split_idx, months)
forecast_base = actual[-1] + 30 * (t_forecast - split_idx)
forecast_values = forecast_base + 50 * np.sin(2 * np.pi * t_forecast / 12)

upper_95 = forecast_values + 150
lower_95 = forecast_values - 150
upper_80 = forecast_values + 100
lower_80 = forecast_values - 100

x_labels = [d.strftime("%b %y") for d in dates]

# CI band rendering strategy (background-erase technique):
#
# pygal fill=True fills from the line DOWN to the x-axis; there is no native
# fill-between-two-lines. We use background erasure:
#   1. upper_95 fill (semi-transparent orange) — covers 0 to upper_95
#   2. lower_95 fill (solid PAGE_BG)           — overwrites area below lower_95
# Net: only the strip between lower_95 and upper_95 remains orange.
#
# CI series carry the actual historical values in the history region so the erase
# fill covers the same area as the orange fill → zero net band in that region.
#
# 80% CI shown as dashed INK boundary lines inside the 95% band; INK (full
# contrast) is more visible than INK_MUTED against the orange background.
#
# pygal's guide-line CSS hardcodes stroke:black, which is invisible on dark
# backgrounds. SVG post-processing fixes regular guides to INK_MUTED and the
# Jan 25 major boundary guide to INK (full contrast).
#
# Series order (→ palette index):
#   0  upper_95 fill    rgba(213,94,0,α)    95% CI orange band  (α=0.25 dark/0.20 light)
#   1  lower_95 erase   PAGE_BG             opaque background erase
#   2  upper_80 line    INK                 80% CI upper dashed boundary
#   3  lower_80 line    INK                 80% CI lower dashed boundary
#   4  historical line  BRAND               solid green line
#   5  forecast line    FORECAST_COLOR      dashed orange line

CI_ALPHA = "0.25" if THEME == "dark" else "0.20"
CI_95_FILL = f"rgba(213, 94, 0, {CI_ALPHA})"

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(CI_95_FILL, PAGE_BG, INK, INK, BRAND, FORECAST_COLOR),
    title_font_size=56,
    label_font_size=42,
    major_label_font_size=36,
    legend_font_size=36,
    value_font_size=30,
    stroke_width=2.5,
)

chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    show_x_guides=False,
    show_y_guides=True,
    show_legend=True,
    legend_at_bottom=True,
    dots_size=2,
    print_values=False,
)

chart.title = "timeseries-forecast-uncertainty · python · pygal · anyplot.ai"
chart.x_title = "Month"
chart.y_title = "Sales ($)"

sparse_labels = [x_labels[i] if i % 6 == 0 else "" for i in range(len(x_labels))]
chart.x_labels = sparse_labels
chart.x_labels_major = ["Jan 25"]

# CI series carry actual values for the historical period so the erase fill
# covers the same area as the orange fill → zero net band in that region.
upper_95_full = list(actual) + list(upper_95)
lower_95_full = list(actual) + list(lower_95)

# Series 0: 95% CI upper fill
chart.add("95% CI", upper_95_full, fill=True, show_legend=True, stroke_dasharray=(0,))
# Series 1: erase area below lower_95 with background colour
chart.add(None, lower_95_full, fill=True, show_legend=False, stroke_dasharray=(0,))

# Series 2 & 3: 80% CI boundaries as dashed lines (forecast period only)
chart.add("80% CI", [None] * split_idx + list(upper_80), fill=False, show_legend=True, stroke_dasharray=(4, 4))
chart.add(None, [None] * split_idx + list(lower_80), fill=False, show_legend=False, stroke_dasharray=(4, 4))

# Series 4: historical solid line
chart.add("Historical (observed)", list(actual) + [None] * (months - split_idx), fill=False, stroke_dasharray=(0,))
# Series 5: forecast dashed line
chart.add("Forecast (projected)", [None] * split_idx + list(forecast_values), fill=False, stroke_dasharray=(5, 5))

# Render SVG and post-process:
# pygal hardcodes stroke:black for guide lines — invisible on dark backgrounds.
# Replace with theme-adaptive colors: INK_MUTED for regular grid, INK for the
# major boundary line at Jan 25 (more prominent with longer dashes + thicker).
svg_bytes = chart.render()
svg_str = svg_bytes.decode("utf-8")
svg_str = svg_str.replace(
    "stroke-dasharray:4,4;stroke:black}", f"stroke-dasharray:4,4;stroke:{INK_MUTED};stroke-opacity:0.5}}"
)
svg_str = svg_str.replace("stroke-dasharray:6,6;stroke:black}", f"stroke-dasharray:8,5;stroke:{INK};stroke-width:1.5}}")

cairosvg.svg2png(bytestring=svg_str.encode(), write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "w") as f:
    f.write(svg_str)
