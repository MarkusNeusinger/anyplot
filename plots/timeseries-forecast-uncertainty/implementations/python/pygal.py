""" anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-19
"""

import os
import sys


# noqa: E402 - sys.path must be modified before imports to avoid module shadowing
sys.path[:] = [p for p in sys.path if p not in ("", ".", os.path.dirname(__file__))]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

BRAND = "#009E73"  # historical observations
FORECAST_COLOR = "#C475FD"  # forecast line; its bands are translucent tints of the same lavender
BAND_95 = "rgba(196, 117, 253, 0.20)" if THEME == "light" else "rgba(196, 117, 253, 0.22)"
BAND_80 = "rgba(196, 117, 253, 0.45)" if THEME == "light" else "rgba(196, 117, 253, 0.42)"

np.random.seed(42)
months = 42
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

# Plot: months numbered from 1 (no tick at 0, so pygal draws its left spine at the edge)
x = np.arange(1, months + 1)
x_hist, x_fc = x[:split_idx], x[split_idx:]
origin = (float(x_hist[-1]), float(actual[-1]))  # the forecast and its bands start at the last observation

# Bands as polygons between their bounds (upper bound forward, lower bound back), starting at the origin:
# the 80% band, and the two strips of the 95% band outside it, so each colour has exactly one region
fc_x = [origin[0], *x_fc]
band_80 = list(zip(fc_x, [origin[1], *upper_80], strict=True)) + list(zip(fc_x[::-1], [*lower_80[::-1], origin[1]], strict=True))
band_95_upper = list(zip(fc_x, [origin[1], *upper_95], strict=True)) + list(
    zip(fc_x[::-1], [*upper_80[::-1], origin[1]], strict=True)
)
band_95_lower = list(zip(fc_x, [origin[1], *lower_80], strict=True)) + list(
    zip(fc_x[::-1], [*lower_95[::-1], origin[1]], strict=True)
)

STEP = 200
y_lo = np.floor(min(actual.min(), lower_95.min()) / STEP) * STEP
y_hi = np.ceil(max(actual.max(), upper_95.max()) / STEP) * STEP + STEP / 2
forecast_start = float(x_fc[0])
marker = [(forecast_start, y_lo), (forecast_start, y_hi)]

LABEL_FS = 40
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=(INK, BAND_95, BAND_95, BAND_80, INK_SOFT, BRAND, FORECAST_COLOR),
    value_colors=(INK,) * 7,
    opacity=1,
    opacity_hover=1,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=5,
    guide_stroke_color=RULE,
    guide_stroke_dasharray="none",
    major_guide_stroke_color=RULE,
    major_guide_stroke_dasharray="none",
    title_font_size=60,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=42,
    # pygal prints a point's label value_font_size px right of it and 4/3 of that below it;
    # at 0.26 x the label size the text sits vertically centred on its point
    value_font_size=round(0.26 * LABEL_FS),
    value_label_font_size=LABEL_FS,
    tooltip_font_size=34,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="timeseries-forecast-uncertainty · python · pygal · anyplot.ai",
    x_title="Month",
    y_title="Monthly sales ($)",
    show_x_guides=False,
    show_y_guides=True,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,  # one row; pygal counts the untitled series too when it reserves legend rows
    legend_box_size=36,
    truncate_legend=-1,
    xrange=(float(x[0]), float(x[-1]) + 0.5),
    range=(float(y_lo), float(y_hi)),
    print_labels=True,
    print_values=False,
    margin=40,
    spacing=24,
    css=(
        "file://style.css",
        "file://graph.css",
        "inline:.serie-1 .line, .serie-2 .line, .serie-3 .line { stroke-width: 0 !important; }",
        "inline:.serie-4 .line { stroke-width: 3px !important; }",
        "inline:.text-overlay text.label { font-weight: bold; }",
        "inline:.plot_title { font-weight: bold; }",
    ),
)
chart.x_labels = [{"value": int(xi), "label": d.strftime("%b %y")} for xi, d in zip(x, dates, strict=True) if d.month in (1, 7)]

# Label first and bands next, so the lines are drawn on top of the fills
chart.add(None, [{"value": (forecast_start + 0.15, y_hi - STEP / 4), "label": "Forecast →"}], stroke=False, dots_size=0)
chart.add("95% interval", band_95_upper, fill=True, show_dots=False)
chart.add(None, band_95_lower, fill=True, show_dots=False)
chart.add("80% interval", band_80, fill=True, show_dots=False)
chart.add("Forecast start", marker, show_dots=False, stroke_style={"dasharray": "14, 10"})
chart.add("Observed history",list(zip(x_hist, actual, strict=True)), dots_size=5, formatter=lambda p: f"${p[1]:,.0f}")
chart.add(
    "Forecast",
    [origin, *zip(x_fc, forecast_values, strict=True)],
    dots_size=5,
    stroke_style={"dasharray": "22, 12"},
    formatter=lambda p: f"${p[1]:,.0f}",
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
