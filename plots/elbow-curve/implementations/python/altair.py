"""anyplot.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
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

# Imprint palette: position 1 is the single-series brand color
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
K_VALUES = "Number of clusters (k)"  # role: k_values
INERTIA = "Inertia (within-cluster sum of squares)"  # role: inertia

# Data: replace this block with your own table, for example df = pd.read_csv("inertia.csv")
np.random.seed(42)
ks = list(range(1, 12))
inertias = []
for k in ks:
    decay = 5000 * np.exp(-0.35 * (k - 1)) + 200
    inertias.append(max(decay + np.random.uniform(-50, 50), 150))
df = pd.DataFrame({K_VALUES: ks, INERTIA: inertias})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
k_field = K_VALUES.translate(ESCAPE)
inertia_field = INERTIA.translate(ESCAPE)

# Elbow: the point farthest from the chord joining the first and last points (normalised axes)
nx = (df[K_VALUES] - df[K_VALUES].min()) / (df[K_VALUES].max() - df[K_VALUES].min())
ny = (df[INERTIA] - df[INERTIA].min()) / (df[INERTIA].max() - df[INERTIA].min())
elbow_df = df.loc[[(nx + ny - 1).abs().idxmax()]]
elbow_k = int(elbow_df[K_VALUES].iloc[0])

x = alt.X(
    k_field,
    type="quantitative",
    title=K_VALUES,
    scale=alt.Scale(domain=[df[K_VALUES].min() - 0.5, df[K_VALUES].max() + 0.5], nice=False),
    axis=alt.Axis(values=df[K_VALUES].tolist(), format="d"),
)
y = alt.Y(
    inertia_field, type="quantitative", title=INERTIA, scale=alt.Scale(domain=[0, df[INERTIA].max() * 1.1], nice=False)
)

line = alt.Chart(df).mark_line(color=IMPRINT_PALETTE[0], strokeWidth=2.5).encode(x=x, y=y)
points = (
    alt.Chart(df)
    .mark_point(size=110, color=IMPRINT_PALETTE[0], filled=True, opacity=1)
    .encode(x=x, y=y, tooltip=[alt.Tooltip(k_field, title=K_VALUES), alt.Tooltip(inertia_field, title=INERTIA)])
)
elbow_point = (
    alt.Chart(elbow_df)
    .mark_point(size=280, color=PAGE_BG, filled=True, stroke=IMPRINT_PALETTE[0], strokeWidth=3, opacity=1)
    .encode(x=x, y=y)
)
elbow_text = (
    alt.Chart(elbow_df)
    .mark_text(align="left", baseline="bottom", dx=14, dy=-10, fontSize=13, fontWeight="bold", color=INK)
    .encode(x=x, y=y, text=alt.value(f"Optimal k = {elbow_k}"))
)

chart = (
    (line + points + elbow_point + elbow_text)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("elbow-curve · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_axis(
        labelFontSize=11,
        titleFontSize=13,
        gridColor=INK,
        gridOpacity=0.1,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_title(color=INK)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the 3200 x 1800 landscape target
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
