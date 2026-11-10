"""anyplot.ai
sparkline-basic: Basic Sparkline
Library: altair 6.0.0 | Python 3.13.11
Quality: 78/100 | Updated: 2026-05-03
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

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DAY = "Day"  # role: extra
USERS = "Active users"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("users.csv")
# 75 consecutive days of a product's user trend: S-shaped adoption, a viral
# launch spike, weekly engagement rhythm and noise
np.random.seed(42)
day = np.arange(75)
adoption = 40 + 60 * (1 - np.exp(-day / 20)) ** 2
spike = 18 * np.exp(-((day - 25) ** 2) / 8)
weekly = 3 * np.sin(2 * np.pi * day / 5)
noise = np.random.randn(day.size) * 1.5
df = pd.DataFrame({DAY: day, USERS: adoption + spike + weekly + noise})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
x = alt.X(DAY.translate(ESCAPE), type="quantitative", title=None, axis=None)
y = alt.Y(USERS.translate(ESCAPE), type="quantitative", title=None, axis=None, scale=alt.Scale(zero=False))

# Min and max dots, placed exactly on the line
extremes = df.loc[[df[USERS].idxmin(), df[USERS].idxmax()]].assign(Mark=["min", "max"])

fill = alt.Chart(df).mark_area(color=IMPRINT_PALETTE[0], opacity=0.15).encode(x=x, y=y)
line = alt.Chart(df).mark_line(color=IMPRINT_PALETTE[0], strokeWidth=2).encode(x=x, y=y)
dots = (
    alt.Chart(extremes)
    .mark_circle(size=140)
    .encode(
        x=x,
        y=y,
        color=alt.Color(
            "Mark:N",
            legend=None,
            scale=alt.Scale(domain=["min", "max"], range=[IMPRINT_PALETTE[1], IMPRINT_PALETTE[3]]),
        ),
    )
)

chart = (
    (fill + line + dots)
    .properties(
        width=760,
        height=152,  # 5:1 aspect
        background=PAGE_BG,
        title=alt.Title("sparkline-basic · python · altair · anyplot.ai", fontSize=18, color=INK),
    )
    .configure_view(strokeWidth=0)
)

# Save, then pad (never crop) to the canonical 3200 x 1800 canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
canvas.save(f"plot-{THEME}.png")
