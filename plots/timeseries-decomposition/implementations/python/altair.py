"""anyplot.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image
from statsmodels.tsa.seasonal import seasonal_decompose


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: one position per component, in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
PERIOD = 12  # seasonal cycle length in observations (monthly data, yearly cycle)
COMPONENTS = ["Original", "Trend", "Seasonal", "Residual"]

# Columns: set these to your table's column names
DATE = "Month"  # role: date
PASSENGERS = "Passengers (thousands)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("passengers.csv")
rng = np.random.default_rng(42)
months = pd.date_range("2018-01-01", periods=96, freq="MS")
step = np.arange(len(months))
passengers = np.linspace(100, 180, len(months)) + 30 * np.sin(2 * np.pi * step / 12) + rng.normal(0, 8, len(months))
df = pd.DataFrame({DATE: months, PASSENGERS: passengers})

# Plot: reads only df and the constants above
series = df.set_index(DATE)[PASSENGERS]
period = max(2, min(PERIOD, len(series) // 2))  # the method needs two full cycles
result = seasonal_decompose(series.interpolate(limit_direction="both"), model="additive", period=period)
wide = pd.DataFrame(
    {"Original": series, "Trend": result.trend, "Seasonal": result.seasonal, "Residual": result.resid}
).reset_index()
long = wide.melt(id_vars=DATE, var_name="component", value_name="value")

ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
date_field = DATE.translate(ESCAPE)

title = "timeseries-decomposition · python · altair · anyplot.ai"
title_size = round(16 * min(1.0, 67 / len(title)))

lines = (
    alt.Chart(long)
    .mark_line(strokeWidth=1.8)
    .encode(
        x=alt.X(
            date_field, type="temporal", title=DATE, axis=alt.Axis(format="%b %Y", tickCount=8, labelAngle=0, grid=True)
        ),
        y=alt.Y("value", type="quantitative", title=None, scale=alt.Scale(zero=False)),
        color=alt.Color(
            "component",
            type="nominal",
            sort=COMPONENTS,
            scale=alt.Scale(domain=COMPONENTS, range=IMPRINT_PALETTE),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip(date_field, type="temporal", title=DATE),
            alt.Tooltip("value", type="quantitative", title=PASSENGERS, format=".1f"),
            alt.Tooltip("component", type="nominal", title="Component"),
        ],
    )
    .properties(width=560, height=72)
)

chart = (
    lines.facet(
        row=alt.Row(
            "component",
            type="nominal",
            sort=COMPONENTS,
            title=None,
            header=alt.Header(labelFontSize=11, labelFontWeight="bold", labelOrient="left", labelPadding=8),
        ),
        spacing=14,
    )
    .resolve_scale(y="independent")
    .properties(background=PAGE_BG, title=alt.Title(title, fontSize=title_size, anchor="middle", color=INK))
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.12,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_header(labelColor=INK)
    .configure_title(color=INK)
    .interactive()
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) the PNG to the canonical landscape canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds target {TW}x{TH}; shrink width/height")
if img.size != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
