"""anyplot.ai
subplot-grid: Subplot Grid Layout
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

# Imprint palette: all eight positions, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]
SECONDARY = IMPRINT_PALETTE[1]

# Constants
TARGET_GROWTH = 0.4  # the sales target ramps up by this share over the year

# Columns: set these to your table's column names
MONTH = "Month"  # role: extra
REGION = "Region"  # role: extra
UNITS = "Units sold"  # role: x
ORDER_VALUE = "Order value ($)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("orders.csv")
rng = np.random.default_rng(42)
n_orders = 240
regions = ["North", "South", "East", "West", "Central"]
df = pd.DataFrame(
    {
        MONTH: np.repeat(pd.date_range("2024-01", periods=12, freq="MS"), n_orders // 12),
        REGION: rng.choice(regions, n_orders),
        UNITS: rng.integers(100, 1000, n_orders),
    }
)
df[ORDER_VALUE] = (df[UNITS] * rng.lognormal(mean=-2.6, sigma=0.5, size=n_orders)).round(2)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
MONTH_F, REGION_F, UNITS_F, VALUE_F = (c.translate(ESCAPE) for c in (MONTH, REGION, UNITS, ORDER_VALUE))

SALES_TREND = "Monthly sales ($K)"
SALES, TARGET = "Sales", "Target"
SERIES, REGION_MEAN = "Series", "Mean order value ($)"

# Line panel: monthly sales against a linear target ramp
monthly = df.groupby(MONTH, sort=False)[ORDER_VALUE].sum().div(1000).rename(SALES).reset_index()
monthly[TARGET] = np.linspace(monthly[SALES].iloc[0], monthly[SALES].iloc[0] * (1 + TARGET_GROWTH), len(monthly))
monthly = monthly.melt(id_vars=MONTH, var_name=SERIES, value_name=SALES_TREND)

# Bar panel: mean order value per region, highlighting regions above the overall mean
by_region = df.groupby(REGION, sort=False)[ORDER_VALUE].mean().round(1).rename(REGION_MEAN).reset_index()
overall_mean = df[ORDER_VALUE].mean()

PANEL_W, PANEL_H, GAP = 340, 138, 32
FS_AXIS_TITLE, FS_AXIS_LABEL, FS_PANEL = 9, 8, 11


def panel_title(text):
    return alt.Title(text, fontSize=FS_PANEL, anchor="start", offset=6)


scatter = (
    alt.Chart(df)
    .mark_circle(size=24, opacity=0.7, color=BRAND)
    .encode(
        x=alt.X(UNITS_F, type="quantitative", title=UNITS),
        y=alt.Y(VALUE_F, type="quantitative", title=ORDER_VALUE),
        tooltip=[alt.Tooltip(UNITS_F, title=UNITS), alt.Tooltip(VALUE_F, title=ORDER_VALUE)],
    )
    .properties(width=PANEL_W, height=PANEL_H, title=panel_title("Units vs order value"))
)

line = (
    alt.Chart(monthly)
    .mark_line(strokeWidth=2)
    .encode(
        x=alt.X(MONTH_F, type="temporal", title=MONTH, axis=alt.Axis(format="%b")),
        y=alt.Y(SALES_TREND.translate(ESCAPE), type="quantitative", title=SALES_TREND, scale=alt.Scale(zero=False)),
        color=alt.Color(
            SERIES,
            type="nominal",
            sort=None,
            scale=alt.Scale(range=IMPRINT_PALETTE),
            legend=alt.Legend(title=None, orient="top-left", offset=4, padding=3),
        ),
        strokeDash=alt.StrokeDash(
            SERIES, type="nominal", sort=None, scale=alt.Scale(range=[[1, 0], [5, 4]]), legend=None
        ),
    )
    .properties(width=PANEL_W, height=PANEL_H, title=panel_title("Monthly sales vs target"))
)

bar = (
    alt.Chart(by_region)
    .mark_bar(size=34)
    .encode(
        x=alt.X(REGION_F, type="nominal", title=REGION, sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y(REGION_MEAN.translate(ESCAPE), type="quantitative", title=REGION_MEAN),
        color=alt.condition(alt.datum[REGION_MEAN] >= overall_mean, alt.value(BRAND), alt.value(SECONDARY)),
        tooltip=[alt.Tooltip(REGION_F, title=REGION), alt.Tooltip(REGION_MEAN.translate(ESCAPE), title=REGION_MEAN)],
    )
    .properties(width=PANEL_W, height=PANEL_H, title=panel_title("Regional order value"))
)

histogram = (
    alt.Chart(df)
    .mark_bar(opacity=0.85, color=BRAND)
    .encode(
        x=alt.X(VALUE_F, type="quantitative", bin=alt.Bin(maxbins=25), title=ORDER_VALUE),
        y=alt.Y("count()", type="quantitative", title="Orders"),
        tooltip=[alt.Tooltip("count()", title="Orders")],
    )
    .properties(width=PANEL_W, height=PANEL_H, title=panel_title("Order value distribution"))
)

title = "subplot-grid · python · altair · anyplot.ai"
chart = (
    alt.vconcat(
        alt.hconcat(scatter, line, spacing=GAP).resolve_legend(color="independent"),
        alt.hconcat(bar, histogram, spacing=GAP),
        spacing=GAP,
    )
    .properties(background=PAGE_BG, title=alt.Title(title, fontSize=15, anchor="middle", offset=12, color=INK))
    .configure_axis(
        labelFontSize=FS_AXIS_LABEL,
        titleFontSize=FS_AXIS_TITLE,
        gridOpacity=0.10,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, labelFontSize=9, symbolStrokeWidth=2
    )
)

# Output: pad (never crop) to the canonical landscape canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    # Other data can widen the tick labels; re-render the whole chart smaller instead of cropping
    fit = min(TW / img.width, TH / img.height) * 0.99
    chart.save(f"plot-{THEME}.png", scale_factor=4.0 * fit)
    img = Image.open(f"plot-{THEME}.png").convert("RGB")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
