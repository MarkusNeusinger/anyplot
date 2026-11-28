"""anyplot.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: altair 6.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-06-02
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Imprint palette: diverging ends, cold -> blue (position 3), warm -> red (position 5)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLD, WARM = IMPRINT_PALETTE[2], IMPRINT_PALETTE[4]

# Columns: set these to your table's column names
YEAR = "Year"  # role: year
ANOMALY = "Temperature anomaly (°C)"  # role: anomaly

# Data: replace this block with your own table, for example df = pd.read_csv("anomalies.csv")
# Synthetic global temperature anomalies (1850-2024) mimicking the HadCRUT pattern
np.random.seed(42)
years = np.arange(1850, 2025)
baseline_trend = np.piecewise(
    years.astype(float),
    [years < 1910, (years >= 1910) & (years < 1980), years >= 1980],
    [lambda y: -0.2 + (y - 1850) * (-0.001), lambda y: -0.3 + (y - 1910) * 0.005, lambda y: 0.05 + (y - 1980) * 0.022],
)
df = pd.DataFrame({YEAR: years, ANOMALY: baseline_trend + np.random.normal(0, 0.08, len(years))})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
limit = df[ANOMALY].abs().max()

# Diverging scale symmetric around zero; the midpoint is the page, so years near zero are the palest
color_scale = alt.Scale(domain=[-limit, limit], domainMid=0, range=[COLD, PAGE_BG, WARM], interpolate="rgb")

# Warming stripes: no axes, labels, ticks or gridlines, one touching stripe per year
stripes = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        x=alt.X(YEAR.translate(ESCAPE), type="ordinal", title=YEAR, axis=None),
        color=alt.Color(ANOMALY.translate(ESCAPE), type="quantitative", title=ANOMALY, scale=color_scale, legend=None),
        tooltip=[
            alt.Tooltip(YEAR.translate(ESCAPE), type="ordinal", title=YEAR),
            alt.Tooltip(ANOMALY.translate(ESCAPE), type="quantitative", title=ANOMALY, format="+.2f"),
        ],
    )
)

chart = (
    stripes.properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title("heatmap-stripes-climate · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_title(color=INK, fontWeight="bold", offset=10)
)

# Save: PNG at 3200x1800, padded (never cropped) if the chart lands off target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
