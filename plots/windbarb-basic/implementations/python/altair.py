"""anyplot.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: altair | Python 3.13
Quality: pending | Updated: 2026-05-19
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data — synthetic wind observations from a 6×5 grid of weather stations
np.random.seed(42)
x_coords = np.linspace(0, 10, 6)
y_coords = np.linspace(0, 8, 5)
xx, yy = np.meshgrid(x_coords, y_coords)
x = xx.flatten()
y = yy.flatten()
u = np.random.uniform(-30, 30, len(x))
v = np.random.uniform(-25, 25, len(x))

# Force calm conditions and high-wind (pennant) cases for feature coverage
u[0], v[0] = 0.5, 0.3
u[5], v[5] = 1.0, -0.8
u[15], v[15] = 45.0, 35.0  # ~57 kt — one pennant + half barb
u[20], v[20] = 55.0, 10.0  # ~56 kt — one pennant + half barb

wind_speed = np.sqrt(u**2 + v**2)
wind_direction = np.degrees(np.arctan2(-u, -v)) % 360  # FROM direction (meteorological)

df = pd.DataFrame({"x": x, "y": y, "u": u, "v": v, "speed": wind_speed, "direction": wind_direction})
calm_df = df[df["speed"] < 2.5].copy()
barbed_df = df[df["speed"] >= 2.5].copy()

# Staff: line from station toward wind source
SCALE = 0.03
barbed_df = barbed_df.copy()
barbed_df["x2"] = barbed_df["x"] - barbed_df["u"] * SCALE
barbed_df["y2"] = barbed_df["y"] - barbed_df["v"] * SCALE

# Build barb segments and pennant markers per station
barb_records = []
pennant_records = []

for _, row in barbed_df.iterrows():
    spd = row["speed"]
    direction_rad = np.radians(row["direction"])
    ux_s = np.sin(direction_rad)  # unit vector toward wind source
    uy_s = np.cos(direction_rad)
    px_s = -uy_s  # left-perpendicular (Northern Hemisphere convention)
    py_s = ux_s

    staff_len = spd * SCALE
    remaining = spd
    pos_offset = 0.0

    num_pennants = int(remaining // 50)
    for _ in range(min(num_pennants, 3)):
        bpos = 0.85 - pos_offset
        bx = row["x"] + ux_s * staff_len * bpos
        by = row["y"] + uy_s * staff_len * bpos
        pennant_records.append({"x": bx, "y": by, "angle": (row["direction"] + 270) % 360})
        pos_offset += 0.20
    remaining -= num_pennants * 50

    num_full = int(remaining // 10)
    for _ in range(min(num_full, 5)):
        bpos = 0.85 - pos_offset
        bx = row["x"] + ux_s * staff_len * bpos
        by = row["y"] + uy_s * staff_len * bpos
        barb_records.append({"x": bx, "y": by, "x2": bx + px_s * 0.35, "y2": by + py_s * 0.35})
        pos_offset += 0.15
    remaining -= num_full * 10

    if remaining >= 5:
        bpos = 0.85 - pos_offset
        bx = row["x"] + ux_s * staff_len * bpos
        by = row["y"] + uy_s * staff_len * bpos
        barb_records.append({"x": bx, "y": by, "x2": bx + px_s * 0.18, "y2": by + py_s * 0.18})

barb_df = pd.DataFrame(barb_records) if barb_records else pd.DataFrame(columns=["x", "y", "x2", "y2"])
pennant_df = pd.DataFrame(pennant_records) if pennant_records else pd.DataFrame(columns=["x", "y", "angle"])

# Layer 1: Staff lines
staff = (
    alt.Chart(barbed_df)
    .mark_rule(strokeWidth=2.5, color=BRAND)
    .encode(
        x=alt.X("x:Q", title="Longitude (°E)", scale=alt.Scale(domain=[-0.5, 11])),
        y=alt.Y("y:Q", title="Latitude (°N)", scale=alt.Scale(domain=[-0.8, 9])),
        x2="x2:Q",
        y2="y2:Q",
        tooltip=[
            alt.Tooltip("x:Q", title="Longitude", format=".1f"),
            alt.Tooltip("y:Q", title="Latitude", format=".1f"),
            alt.Tooltip("speed:Q", title="Wind Speed (kt)", format=".1f"),
            alt.Tooltip("direction:Q", title="Direction (° from N)", format=".0f"),
        ],
    )
)

# Layer 2: Barb line segments (full and half barbs)
if len(barb_df) > 0:
    barbs = alt.Chart(barb_df).mark_rule(strokeWidth=2.5, color=BRAND).encode(x="x:Q", y="y:Q", x2="x2:Q", y2="y2:Q")
else:
    barbs = alt.Chart(pd.DataFrame({"x": []})).mark_point()

# Layer 3: Pennant markers — filled triangles oriented by wind direction
if len(pennant_df) > 0:
    pennants = (
        alt.Chart(pennant_df)
        .mark_point(shape="triangle", filled=True, size=400, color=BRAND)
        .encode(x="x:Q", y="y:Q", angle=alt.Angle("angle:Q", scale=alt.Scale(domain=[0, 360], range=[0, 360])))
    )
else:
    pennants = alt.Chart(pd.DataFrame({"x": []})).mark_point()

# Layer 4: Calm wind indicators — open circles (< 2.5 kt)
calm_circles = (
    alt.Chart(calm_df)
    .mark_point(shape="circle", filled=False, size=350, stroke=BRAND, strokeWidth=4)
    .encode(
        x="x:Q",
        y="y:Q",
        tooltip=[
            alt.Tooltip("x:Q", title="Longitude", format=".1f"),
            alt.Tooltip("y:Q", title="Latitude", format=".1f"),
            alt.Tooltip("speed:Q", title="Wind Speed (kt)", format=".2f"),
        ],
    )
)

# Chart assembly with theme-adaptive chrome
chart = (
    alt.layer(staff, barbs, pennants, calm_circles)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(
            text="windbarb-basic · python · altair · anyplot.ai",
            subtitle="Half barb = 5 kt  |  Full barb = 10 kt  |  ▲ Pennant = 50 kt  |  ○ Calm < 2.5 kt",
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=18,
        titleFontSize=22,
    )
    .configure_title(color=INK, subtitleColor=INK_SOFT, fontSize=28, subtitleFontSize=20)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
