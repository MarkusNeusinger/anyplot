"""anyplot.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-13
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, raw data first, rolling average second
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
WINDOW = 7  # rolling window length in days

# Columns: set these to your table's column names
DATE = "Date"  # role: date
TEMPERATURE = "Temperature (°C)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("temperature.csv")
np.random.seed(42)
day_of_year = np.arange(180)
# Temperature rises from winter (Jan) toward summer (Jun)
seasonal_trend = 10 + 12 * np.sin(2 * np.pi * (day_of_year - 90) / 365)
noise = np.random.normal(0, 3, 180)
df = pd.DataFrame({DATE: pd.date_range("2024-01-01", periods=180, freq="D"), TEMPERATURE: seasonal_trend + noise})

# Plot: reads only df and the constants above
RAW_LABEL = "Raw Data"
ROLLING_LABEL = f"{WINDOW}-Day Rolling Average"
SERIES = "Series"
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

# Trailing window: the average starts only once WINDOW observations are in
series = df.sort_values(DATE)
rolling = series[TEMPERATURE].rolling(window=WINDOW, min_periods=WINDOW).mean()
long_df = pd.concat(
    [series.assign(**{SERIES: RAW_LABEL}), series.assign(**{TEMPERATURE: rolling, SERIES: ROLLING_LABEL})],
    ignore_index=True,
).dropna(subset=[TEMPERATURE])

title = "line-timeseries-rolling · python · altair · anyplot.ai"
title_fontsize = round(16 * (67 / len(title) if len(title) > 67 else 1.0))

chart = (
    alt.Chart(long_df)
    .mark_line()
    .encode(
        x=alt.X(DATE.translate(ESCAPE), type="temporal", title=DATE, axis=alt.Axis(format="%b %d")),
        y=alt.Y(TEMPERATURE.translate(ESCAPE), type="quantitative", title=TEMPERATURE, scale=alt.Scale(zero=False)),
        color=alt.Color(
            SERIES,
            type="nominal",
            title=None,
            sort=None,
            scale=alt.Scale(domain=[RAW_LABEL, ROLLING_LABEL], range=IMPRINT_PALETTE),
            legend=alt.Legend(orient="top-left", offset=8, padding=6, cornerRadius=3, symbolStrokeWidth=3),
        ),
        strokeWidth=alt.condition(alt.datum[SERIES] == ROLLING_LABEL, alt.value(3), alt.value(1.2)),
        opacity=alt.condition(alt.datum[SERIES] == ROLLING_LABEL, alt.value(1.0), alt.value(0.55)),
        tooltip=[
            alt.Tooltip(DATE.translate(ESCAPE), type="temporal", title=DATE, format="%Y-%m-%d"),
            alt.Tooltip(SERIES, type="nominal", title=SERIES),
            alt.Tooltip(TEMPERATURE.translate(ESCAPE), type="quantitative", title=TEMPERATURE, format=".1f"),
        ],
    )
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        padding={"left": 10, "right": 10, "top": 10, "bottom": 10},
        title=alt.Title(title, fontSize=title_fontsize, fontWeight="bold", anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=None, continuousWidth=620, continuousHeight=320)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.12,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_title(color=INK)
    .configure_legend(
        labelFontSize=10,
        titleFontSize=10,
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .interactive()
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
