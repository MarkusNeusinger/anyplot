"""anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: altair 6.1.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-13
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

# Imprint palette: all eight positions, one per direction in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
FILL_SHARE = 0.8  # share of each direction's angular slot that the bar fills
SPOKE_SHARE = 0.5  # value labels sit in the gap between the first two bars

# Columns: set these to your table's column names
DIRECTION = "Wind direction"  # role: direction
FREQUENCY = "Frequency (days)"  # role: frequency

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
# Rows are in compass order, clockwise from north, evenly spaced around the circle.
np.random.seed(42)
base_freq = [12, 8, 10, 6, 9, 18, 22, 16]  # prevailing westerlies
df = pd.DataFrame(
    {
        DIRECTION: ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
        FREQUENCY: [f + np.random.randint(-2, 3) for f in base_freq],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
n_bars = len(df)
slot = 360 / n_bars
bars_df = df.assign(
    bearing=np.arange(n_bars) * slot,
    start=lambda d: d["bearing"] - slot * FILL_SHARE / 2,
    end=lambda d: d["bearing"] + slot * FILL_SHARE / 2,
)

# Radial scale: starts at zero, tops out on a round ring value
top = float(df[FREQUENCY].max())
magnitude = 10 ** np.floor(np.log10(top))
step = next(m * magnitude for m in (1, 2, 5, 10) if m * magnitude >= top / 4)
rim = float(np.ceil(top / step) * step)
ring_values = np.arange(step, rim + step / 2, step)
rings_df = pd.DataFrame({"ring": ring_values, "spoke": slot * SPOKE_SHARE})
labels_df = bars_df.assign(label_radius=rim * 1.13)

# Square view: the polar centre is the view centre, the rim radius is a fixed share of half the side
SIDE = 430
theta_scale = alt.Scale(type="linear", domain=[0, 360])
radius_scale = alt.Scale(type="linear", domain=[0, rim], range=[0, SIDE * 0.38])

rings = (
    alt.Chart(rings_df)
    .mark_arc(filled=False, stroke=INK, strokeWidth=1.2, opacity=0.22)
    .encode(
        theta=alt.Theta(datum=0, type="quantitative", scale=theta_scale),
        theta2=alt.Theta2(datum=360),
        radius=alt.Radius("ring:Q", scale=radius_scale),
        radius2=alt.Radius2(datum=0),
    )
)

bars = (
    alt.Chart(bars_df)
    .mark_arc(stroke=PAGE_BG, strokeWidth=1.5)
    .encode(
        theta=alt.Theta("start:Q", scale=theta_scale),
        theta2=alt.Theta2("end:Q"),
        radius=alt.Radius(FREQUENCY.translate(ESCAPE), type="quantitative", title=FREQUENCY, scale=radius_scale),
        color=alt.Color(
            DIRECTION.translate(ESCAPE),
            type="nominal",
            title=DIRECTION,
            sort=None,
            scale=alt.Scale(range=IMPRINT_PALETTE),
            legend=alt.Legend(
                titleFontSize=13,
                labelFontSize=12,
                orient="right",
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
                labelColor=INK_SOFT,
                titleColor=INK,
                padding=8,
            ),
        ),
        tooltip=[
            alt.Tooltip(DIRECTION.translate(ESCAPE), type="nominal", title=DIRECTION),
            alt.Tooltip(FREQUENCY.translate(ESCAPE), type="quantitative", title=FREQUENCY),
        ],
    )
)

ring_labels = (
    alt.Chart(rings_df)
    .mark_text(fontSize=11, color=INK_SOFT, fontWeight="bold")
    .encode(
        theta=alt.Theta("spoke:Q", scale=theta_scale),
        radius=alt.Radius("ring:Q", scale=radius_scale),
        text=alt.Text("ring:Q", format="d"),
    )
)

direction_labels = (
    alt.Chart(labels_df)
    .mark_text(fontSize=15, fontWeight="bold", color=INK)
    .encode(
        theta=alt.Theta("bearing:Q", scale=theta_scale),
        radius=alt.Radius("label_radius:Q", scale=radius_scale),
        text=alt.Text(DIRECTION.translate(ESCAPE), type="nominal"),
    )
)

chart = (
    alt.layer(rings, bars, ring_labels, direction_labels)
    .properties(
        width=SIDE,
        height=SIDE,
        background=PAGE_BG,
        padding={"left": 8, "right": 8, "top": 8, "bottom": 8},
        title=alt.Title(
            text="polar-bar · python · altair · anyplot.ai",
            subtitle=f"Bar length: {FREQUENCY}, rings every {step:g}",
            fontSize=18,
            subtitleFontSize=12,
            anchor="middle",
            color=INK,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .interactive()
)

# Output
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) the render onto the square 2400 x 2400 canvas
TARGET = 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET or img.height > TARGET:
    raise SystemExit(f"altair render {img.size} exceeds {TARGET}x{TARGET}; shrink SIDE")
canvas = Image.new("RGB", (TARGET, TARGET), PAGE_BG)
canvas.paste(img, ((TARGET - img.width) // 2, (TARGET - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
