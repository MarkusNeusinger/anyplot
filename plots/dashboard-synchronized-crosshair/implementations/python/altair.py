""" anyplot.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-23
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

# anyplot palette positions 1–3
COLOR_PRICE = "#009E73"
COLOR_VOLUME = "#9418DB"
COLOR_INDICATOR = "#B71D27"

# Data — stock market: price, volume, momentum indicator
np.random.seed(42)
n_points = 200
dates = pd.date_range("2024-01-01", periods=n_points, freq="B")

returns = np.random.normal(0.001, 0.02, n_points)
price = 100 * np.cumprod(1 + returns)

raw_volume = np.random.uniform(1e6, 3e6, n_points)
volume = raw_volume * (1 + np.abs(returns) * 20)

raw_momentum = 50 + np.cumsum(np.random.normal(0, 5, n_points))
indicator = np.clip(raw_momentum, 0, 100)

df = pd.DataFrame({"date": dates, "price": price, "volume": volume, "indicator": indicator})

# Shared selections
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["date"], empty=False)
# Synchronized zoom/pan — same parameter name across all views links them in Vega-Lite
zoom = alt.selection_interval(bind="scales", encodings=["x"])

# X encodings: axis hidden on top charts, labeled on bottom chart only
x_hidden = alt.X("date:T", axis=alt.Axis(labels=False, ticks=False, domain=False, title=None))
x_labeled = alt.X("date:T", title="Trading Date", axis=alt.Axis(format="%b %Y", labelFontSize=10, titleFontSize=12))

# Price chart (top) — green line, zero=False so actual range fills the height
base_p = alt.Chart(df).encode(x=x_hidden)

price_chart = alt.layer(
    base_p.mark_line(color=COLOR_PRICE, strokeWidth=2)
    .encode(
        y=alt.Y(
            "price:Q", title="Price ($)", scale=alt.Scale(zero=False), axis=alt.Axis(labelFontSize=10, titleFontSize=12)
        ),
        tooltip=[
            alt.Tooltip("date:T", format="%Y-%m-%d", title="Date"),
            alt.Tooltip("price:Q", format="$.2f", title="Price"),
        ],
    )
    .add_params(zoom),
    base_p.mark_point(color=COLOR_PRICE, size=80, filled=True).encode(
        y=alt.Y("price:Q", scale=alt.Scale(zero=False)), opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    ),
    base_p.mark_rule(color=INK_SOFT, strokeWidth=1.5)
    .encode(opacity=alt.condition(nearest, alt.value(0.7), alt.value(0)))
    .add_params(nearest),
).properties(width=620, height=90, title=alt.Title("Price", anchor="start", fontSize=12))

# Volume chart (middle) — purple bars with synchronized crosshair
base_v = alt.Chart(df).encode(x=x_hidden)

volume_chart = alt.layer(
    base_v.mark_bar(color=COLOR_VOLUME, opacity=0.7)
    .encode(
        y=alt.Y("volume:Q", title="Volume", axis=alt.Axis(labelFontSize=10, titleFontSize=12, format="~s")),
        tooltip=[
            alt.Tooltip("date:T", format="%Y-%m-%d", title="Date"),
            alt.Tooltip("volume:Q", format=",.0f", title="Volume"),
        ],
    )
    .add_params(zoom),
    base_v.mark_rule(color=INK_SOFT, strokeWidth=1.5)
    .encode(opacity=alt.condition(nearest, alt.value(0.7), alt.value(0)))
    .add_params(nearest),
).properties(width=620, height=70, title=alt.Title("Volume", anchor="start", fontSize=12))

# Momentum indicator chart (bottom) — red line with reference zones and labeled x-axis
base_i = alt.Chart(df).encode(x=x_labeled)

# Semi-transparent zone shading: oversold (<30) and overbought (>70) bands for storytelling
zone_df = pd.DataFrame({"x1": [dates[0], dates[0]], "x2": [dates[-1], dates[-1]], "y1": [0, 70], "y2": [30, 100]})
zone_bg = (
    alt.Chart(zone_df).mark_rect(color=COLOR_INDICATOR, opacity=0.08).encode(x="x1:T", x2="x2:T", y="y1:Q", y2="y2:Q")
)

overbought_line = (
    alt.Chart(pd.DataFrame({"y": [70]})).mark_rule(color=INK_SOFT, strokeDash=[4, 4], strokeWidth=1.0).encode(y="y:Q")
)
oversold_line = (
    alt.Chart(pd.DataFrame({"y": [30]})).mark_rule(color=INK_SOFT, strokeDash=[4, 4], strokeWidth=1.0).encode(y="y:Q")
)

indicator_chart = alt.layer(
    zone_bg,
    base_i.mark_line(color=COLOR_INDICATOR, strokeWidth=2)
    .encode(
        y=alt.Y(
            "indicator:Q",
            title="Momentum",
            scale=alt.Scale(domain=[0, 100]),
            axis=alt.Axis(labelFontSize=10, titleFontSize=12),
        ),
        tooltip=[
            alt.Tooltip("date:T", format="%Y-%m-%d", title="Date"),
            alt.Tooltip("indicator:Q", format=".1f", title="Momentum"),
        ],
    )
    .add_params(zoom),
    base_i.mark_point(color=COLOR_INDICATOR, size=80, filled=True).encode(
        y=alt.Y("indicator:Q"), opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    ),
    overbought_line,
    oversold_line,
    base_i.mark_rule(color=INK_SOFT, strokeWidth=1.5)
    .encode(opacity=alt.condition(nearest, alt.value(0.7), alt.value(0)))
    .add_params(nearest),
).properties(width=620, height=70, title=alt.Title("Momentum Indicator", anchor="start", fontSize=12))

# Compose and configure
TITLE = "dashboard-synchronized-crosshair · python · altair · anyplot.ai"

chart = (
    alt.vconcat(price_chart, volume_chart, indicator_chart, spacing=10)
    .properties(background=PAGE_BG, title=alt.Title(TITLE, fontSize=16, anchor="middle"))
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        grid=True,
    )
    .configure_axisX(grid=False)
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save PNG and pad to exact 3200 × 1800 target
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
