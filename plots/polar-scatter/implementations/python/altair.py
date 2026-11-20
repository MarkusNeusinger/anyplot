"""anyplot.ai
polar-scatter: Polar Scatter Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
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

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]  # one label every 45 degrees, clockwise from north
RADIAL_STEPS = 4  # number of radial gridline rings

# Columns: set these to your table's column names
DIRECTION = "Wind direction (°)"  # role: theta
SPEED = "Wind speed (m/s)"  # role: radius
TIME_OF_DAY = "Time of day"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
np.random.seed(42)
n_points = 120
n_third = n_points // 3

# Prevailing winds: north-westerly mornings (strong), south-easterly afternoons, scattered evenings
morning_dir = np.random.normal(315, 25, n_third)
afternoon_dir = np.random.normal(135, 30, n_third)
evening_dir = np.random.uniform(0, 360, n_points - 2 * n_third)

speed = np.zeros(n_points)
speed[:n_third] = np.random.gamma(4, 2.5, n_third)
speed[n_third : 2 * n_third] = np.random.gamma(3, 2, n_third)
speed[2 * n_third :] = np.random.gamma(2, 1.5, n_points - 2 * n_third)

df = pd.DataFrame(
    {
        DIRECTION: np.concatenate([morning_dir, afternoon_dir, evening_dir]) % 360,
        SPEED: np.clip(speed, 1, 20),
        TIME_OF_DAY: ["Morning"] * n_third + ["Afternoon"] * n_third + ["Evening"] * (n_points - 2 * n_third),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
categories = list(df[TIME_OF_DAY].unique())

# Compass convention: 0° at north, increasing clockwise; radius starts at zero in the centre
step = np.ceil(df[SPEED].max() / RADIAL_STEPS / 5) * 5
rim = step * RADIAL_STEPS
reach = rim * 1.3
theta = np.deg2rad(df[DIRECTION])
points_df = df.assign(px=df[SPEED] * np.sin(theta), py=df[SPEED] * np.cos(theta))

ring_angles = np.linspace(0, 2 * np.pi, 181)
rings_df = pd.DataFrame(
    [
        {"gx": r * np.sin(t), "gy": r * np.cos(t), "ring": r, "order": i}
        for r in np.arange(1, RADIAL_STEPS + 1) * step
        for i, t in enumerate(ring_angles)
    ]
)

spoke_deg = np.arange(0, 360, 45)
spokes_df = pd.DataFrame(
    [
        {"gx": rim * np.sin(np.deg2rad(a)) * k, "gy": rim * np.cos(np.deg2rad(a)) * k, "spoke": int(a), "order": k}
        for a in spoke_deg
        for k in (0, 1)
    ]
)

angle_labels_df = pd.DataFrame(
    {
        "gx": rim * 1.14 * np.sin(np.deg2rad(spoke_deg)),
        "gy": rim * 1.14 * np.cos(np.deg2rad(spoke_deg)),
        "label": [f"{name} {a}°" for name, a in zip(COMPASS, spoke_deg, strict=True)],
    }
)

# Radial tick labels sit along the 22.5° spoke between N and NE, clear of the markers' main clusters
tick_angle = np.deg2rad(22.5)
radius_labels_df = pd.DataFrame(
    {
        "gx": np.arange(1, RADIAL_STEPS + 1) * step * np.sin(tick_angle),
        "gy": np.arange(1, RADIAL_STEPS + 1) * step * np.cos(tick_angle),
        "label": [f"{r:g} m/s" for r in np.arange(1, RADIAL_STEPS + 1) * step],
    }
)

x_enc = alt.X("gx:Q", axis=None, scale=alt.Scale(domain=[-reach, reach]))
y_enc = alt.Y("gy:Q", axis=None, scale=alt.Scale(domain=[-reach, reach]))

grid_rings = (
    alt.Chart(rings_df)
    .mark_line(strokeWidth=1.2, opacity=0.22, color=INK_SOFT)
    .encode(x=x_enc, y=y_enc, detail="ring:N", order="order:Q")
)
grid_spokes = (
    alt.Chart(spokes_df)
    .mark_line(strokeWidth=1.2, opacity=0.22, color=INK_SOFT)
    .encode(x=x_enc, y=y_enc, detail="spoke:N", order="order:Q")
)
angle_text = (
    alt.Chart(angle_labels_df)
    .mark_text(fontSize=11, fontWeight="bold", color=INK)
    .encode(x=x_enc, y=y_enc, text="label:N")
)
radius_text = (
    alt.Chart(radius_labels_df)
    .mark_text(fontSize=9, align="left", dx=3, dy=-3, color=INK_SOFT)
    .encode(x=x_enc, y=y_enc, text="label:N")
)

markers = (
    alt.Chart(points_df)
    .mark_point(size=42, filled=True, opacity=0.7, stroke=PAGE_BG, strokeWidth=0.6)
    .encode(
        x=alt.X("px:Q", axis=None, scale=alt.Scale(domain=[-reach, reach])),
        y=alt.Y("py:Q", axis=None, scale=alt.Scale(domain=[-reach, reach])),
        color=alt.Color(
            TIME_OF_DAY.translate(ESCAPE),
            type="nominal",
            title=TIME_OF_DAY,
            sort=None,
            scale=alt.Scale(domain=categories, range=IMPRINT_PALETTE),
        ),
        tooltip=[
            alt.Tooltip(DIRECTION.translate(ESCAPE), type="quantitative", title=DIRECTION, format=".1f"),
            alt.Tooltip(SPEED.translate(ESCAPE), type="quantitative", title=SPEED, format=".1f"),
            alt.Tooltip(TIME_OF_DAY.translate(ESCAPE), type="nominal", title=TIME_OF_DAY),
        ],
    )
)

chart = (
    alt.layer(grid_rings, grid_spokes, angle_text, radius_text, markers)
    .properties(
        width=440,
        height=440,
        background=PAGE_BG,
        title=alt.Title("polar-scatter · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(
        titleFontSize=12,
        labelFontSize=11,
        symbolSize=120,
        orient="bottom",
        direction="horizontal",
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        titleColor=INK,
        labelColor=INK_SOFT,
        padding=6,
    )
    .interactive()
)

# Output: PNG padded (never cropped) to the 2400 x 2400 square canvas, plus the interactive HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TARGET = 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET or img.height > TARGET:
    raise SystemExit(f"vl-convert produced {img.width}x{img.height}, exceeds {TARGET}x{TARGET}; shrink width/height")
canvas = Image.new("RGB", (TARGET, TARGET), PAGE_BG)
canvas.paste(img, ((TARGET - img.width) // 2, (TARGET - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
