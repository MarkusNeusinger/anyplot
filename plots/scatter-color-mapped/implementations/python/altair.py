"""anyplot.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-08
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
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"

# Imprint palette: sequential colormap for single-polarity intensity
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]

# Columns: set these to your table's column names
X_POSITION = "X Position (units)"  # role: x
Y_POSITION = "Y Position (units)"  # role: y
INTENSITY = "Intensity (a.u.)"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("readings.csv")
# Simulated temperature readings at spatial locations, in three clusters
rng = np.random.default_rng(42)
x = np.concatenate([rng.normal(20, 8, 50), rng.normal(60, 10, 50), rng.normal(40, 12, 50)])
y = np.concatenate([rng.normal(30, 8, 50), rng.normal(70, 10, 50), rng.normal(50, 15, 50)])
raw = 0.3 * x + 0.5 * y + rng.normal(0, 8, len(x))
intensity = (raw - raw.min()) / (raw.max() - raw.min()) * 100
df = pd.DataFrame({X_POSITION: x, Y_POSITION: y, INTENSITY: intensity})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
x_field, y_field, c_field = (c.translate(ESCAPE) for c in (X_POSITION, Y_POSITION, INTENSITY))

chart = (
    alt.Chart(df)
    .mark_circle(size=90, opacity=0.85, strokeWidth=0.8, stroke=INK_SOFT)
    .encode(
        x=alt.X(x_field, type="quantitative", title=X_POSITION, scale=alt.Scale(nice=True)),
        y=alt.Y(y_field, type="quantitative", title=Y_POSITION, scale=alt.Scale(nice=True)),
        color=alt.Color(
            c_field,
            type="quantitative",
            title=INTENSITY,
            scale=alt.Scale(range=IMPRINT_SEQ),
            legend=alt.Legend(gradientLength=220, gradientThickness=16),
        ),
        tooltip=[
            alt.Tooltip(f, type="quantitative", title=t)
            for f, t in ((x_field, X_POSITION), (y_field, Y_POSITION), (c_field, INTENSITY))
        ],
    )
    .properties(
        width=620,
        height=320,
        title=alt.Title("scatter-color-mapped · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
        background=PAGE_BG,
    )
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        gridOpacity=0.1,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_view(stroke=INK_SOFT, strokeWidth=0, fill=PAGE_BG)
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
        padding=8,
        cornerRadius=4,
    )
)

# Save
TW, TH = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds target {TW}x{TH}")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
