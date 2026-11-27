"""anyplot.ai
heatmap-basic: Basic Heatmap
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint diverging ramp for fields: matte red -> page color -> blue
IMPRINT_DIV = ["#AE3030", PAGE_BG, "#4467A3"]

# Constants
LABEL_CONTRAST = 0.55  # |value| above this fills a cell dark enough for light cell text

# Columns: set these to your table's column names
X_VARIABLE = "Variable (column)"  # role: x
Y_VARIABLE = "Weather variable"  # role: y
CORRELATION = "Correlation"  # role: value

# Data: replace this block with your own matrix, for example df = pd.read_csv("corr.csv", index_col=0)
np.random.seed(42)
variables = [
    "Temperature",
    "Humidity",
    "Wind Speed",
    "Pressure",
    "Visibility",
    "Cloud Cover",
    "Precipitation",
    "UV Index",
]
raw = np.random.randn(200, len(variables))
raw[:, 1] += raw[:, 0] * 0.6  # Humidity ~ Temperature
raw[:, 5] += raw[:, 1] * 0.7  # Cloud Cover ~ Humidity
raw[:, 6] += raw[:, 5] * 0.65  # Precipitation ~ Cloud Cover
raw[:, 4] -= raw[:, 5] * 1.2  # Visibility inversely ~ Cloud Cover
raw[:, 7] -= raw[:, 5] * 0.7  # UV Index inversely ~ Cloud Cover
raw[:, 7] += raw[:, 0] * 0.5  # UV Index ~ Temperature
raw[:, 3] -= raw[:, 0] * 0.4  # Pressure inversely ~ Temperature
raw[:, 2] += raw[:, 3] * 0.3  # Wind Speed ~ Pressure
df = pd.DataFrame(np.corrcoef(raw.T).round(2), index=variables, columns=variables)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
labels = list(df.columns)
cells = df.rename_axis(index=Y_VARIABLE, columns=X_VARIABLE).stack().rename(CORRELATION).reset_index()
limit = float(np.nanmax(np.abs(df.to_numpy())))

x_enc = alt.X(X_VARIABLE.translate(ESCAPE), type="nominal", title=None, sort=labels)
y_enc = alt.Y(Y_VARIABLE.translate(ESCAPE), type="nominal", title=Y_VARIABLE, sort=labels)
value = alt.datum[CORRELATION.translate(ESCAPE)]

heatmap = (
    alt.Chart(cells)
    .mark_rect(stroke=PAGE_BG, strokeWidth=1.5)
    .encode(
        x=x_enc.axis(labelAngle=-45, orient="top", labelPadding=6, labelFontSize=12),
        y=y_enc.axis(labelPadding=6, labelFontSize=12, titleFontSize=13, titlePadding=8),
        color=alt.Color(
            CORRELATION.translate(ESCAPE),
            type="quantitative",
            title=CORRELATION,
            scale=alt.Scale(range=IMPRINT_DIV, domain=[-limit, limit], domainMid=0, interpolate="rgb"),
            legend=alt.Legend(
                titleFontSize=12,
                labelFontSize=11,
                gradientLength=240,
                gradientThickness=14,
                titlePadding=6,
                padding=8,
                offset=10,
                format="+.1f",
            ),
        ),
        tooltip=[
            alt.Tooltip(X_VARIABLE.translate(ESCAPE), title=X_VARIABLE),
            alt.Tooltip(Y_VARIABLE.translate(ESCAPE), title=Y_VARIABLE),
            alt.Tooltip(CORRELATION.translate(ESCAPE), title=CORRELATION, format=".2f"),
        ],
    )
)

# Cell numbers: light on saturated cells, ink on pale ones; always light on the dark page
if THEME == "light":
    text_color = (
        alt.when((value > LABEL_CONTRAST * limit) | (value < -LABEL_CONTRAST * limit))
        .then(alt.value("#FFFFFF"))
        .otherwise(alt.value(INK))
    )
else:
    text_color = alt.value(INK)

text = (
    alt.Chart(cells)
    .mark_text(fontSize=11, fontWeight="bold")
    .encode(
        x=x_enc,
        y=y_enc,
        text=alt.Text(CORRELATION.translate(ESCAPE), type="quantitative", format=".2f"),
        color=text_color,
    )
)

chart = (
    (heatmap + text)
    .properties(
        width=600,
        height=600,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title("heatmap-basic · python · altair · anyplot.ai", fontSize=16, color=INK, anchor="start"),
    )
    .configure_axis(grid=False, domainColor=INK_SOFT, tickColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
