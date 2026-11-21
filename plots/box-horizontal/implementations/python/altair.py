"""anyplot.ai
box-horizontal: Horizontal Box Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
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

# Imprint palette: position 1 for the single series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Columns: set these to your table's column names
SERVICE = "Service type"  # role: categories
RESPONSE = "Response time (ms)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
rng = np.random.default_rng(42)
# service: (mean, std, number of outliers)
profiles = {
    "Database Query": (120, 40, 5),
    "API Gateway": (85, 25, 3),
    "Authentication": (45, 15, 2),
    "File Storage": (200, 60, 4),
    "Cache Lookup": (15, 8, 2),
    "Email Service": (150, 50, 3),
}
services, times = [], []
for name, (mean, std, n_outliers) in profiles.items():
    body = np.clip(rng.normal(mean, std, 50), 5, None)
    tail = rng.uniform(mean + 3 * std, mean + 5 * std, n_outliers)
    values = np.concatenate([body, tail])
    services += [name] * len(values)
    times += list(values)
df = pd.DataFrame({SERVICE: services, RESPONSE: times})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
order = df.groupby(SERVICE)[RESPONSE].median().sort_values().index.tolist()

chart = (
    alt.Chart(df)
    .mark_boxplot(
        size=22,
        box=alt.MarkConfig(color=BRAND, stroke=INK_SOFT, strokeWidth=0.8),
        median=alt.MarkConfig(color=INK, size=22),
        outliers=alt.MarkConfig(color=BRAND, size=40, stroke=INK_SOFT, strokeWidth=0.6),
        ticks=alt.MarkConfig(color=INK_SOFT, size=10),
        rule=alt.MarkConfig(color=INK_SOFT),
    )
    .encode(
        x=alt.X(RESPONSE.translate(ESCAPE), type="quantitative", title=RESPONSE, scale=alt.Scale(zero=False)),
        y=alt.Y(SERVICE.translate(ESCAPE), type="nominal", title=SERVICE, sort=order),
        tooltip=[
            alt.Tooltip(SERVICE.translate(ESCAPE), title=SERVICE),
            alt.Tooltip(RESPONSE.translate(ESCAPE), title=RESPONSE),
        ],
    )
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("box-horizontal · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.12,
        labelColor=INK_SOFT,
        labelFontSize=10,
        titleColor=INK,
        titleFontSize=12,
        labelLimit=300,
    )
    .configure_title(color=INK)
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .interactive()
)

# Save: pad (never crop) to the 3200 x 1800 target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TW}x{TH}; shrink width/height")
if img.size != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
