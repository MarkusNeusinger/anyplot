"""anyplot.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: altair 6.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-19
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

# Imprint palette: position 1 for calm circles, the sequential ramp for wind speed
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]

# Constants
CALM_KT = 2.5  # winds below this are drawn as an open circle without a staff
PENNANT_KT = 50  # one filled triangle
FULL_KT = 10  # one long barb
HALF_KT = 5  # one short barb
STAFF_LEN = 0.9  # staff length in x-axis units, the same for every barb
FULL_LEN = 0.42  # long barb length, as a share of x-axis units
FEATHER_STEP = 0.14  # spacing of the barbs along the staff, as a share of the staff
VIEW_W, VIEW_H = 620, 320  # inner view size in pixels (canvas contract of the library prompt)

# Columns: set these to your table's column names
LON = "Longitude (°E)"  # role: x
LAT = "Latitude (°N)"  # role: y
U_WIND = "Zonal wind u (kt)"  # role: u
V_WIND = "Meridional wind v (kt)"  # role: v
SPEED = "Wind speed (kt)"  # role: extra
FROM_DEG = "Wind from (° of north)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("winds.csv")
np.random.seed(42)
grid_x, grid_y = np.meshgrid(np.linspace(0, 10, 6), np.linspace(0, 8, 5))
u = np.random.uniform(-30, 30, grid_x.size)
v = np.random.uniform(-25, 25, grid_x.size)

# Force calm conditions and high-wind (pennant) cases for feature coverage
u[0], v[0] = 0.5, 0.3
u[5], v[5] = 1.0, -0.8
u[15], v[15] = 45.0, 35.0  # ~57 kt: one pennant + one half barb
u[20], v[20] = 55.0, 10.0  # ~56 kt: one pennant + one half barb

df = pd.DataFrame({LON: grid_x.ravel(), LAT: grid_y.ravel(), U_WIND: u, V_WIND: v})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
obs = df.copy()
obs[SPEED] = np.hypot(obs[U_WIND], obs[V_WIND])
obs[FROM_DEG] = np.degrees(np.arctan2(-obs[U_WIND], -obs[V_WIND])) % 360  # meteorological FROM direction

# Axis domains from the data, with room for the barbs around the outer stations
x_dom = [obs[LON].min() - 0.8, obs[LON].max() + 1.0]
y_dom = [obs[LAT].min() - 0.9, obs[LAT].max() + 1.0]
# Data units per isotropic unit on y, so barbs keep their true angles on screen
y_per_x = (x_dom[1] - x_dom[0]) / VIEW_W * VIEW_H / (y_dom[1] - y_dom[0])

staff_rows, barb_rows, pennant_rows = [], [], []
for row in obs[obs[SPEED] >= CALM_KT].itertuples(index=False):
    lon, lat, speed, bearing = row[0], row[1], row[4], np.radians(row[5])
    ux, uy = np.sin(bearing), np.cos(bearing)  # unit vector from the station toward the wind source
    px, py = -uy, ux  # perpendicular on the left of the staff (Northern Hemisphere)
    staff_rows.append(
        {"x": lon, "y": lat, "x2": lon + ux * STAFF_LEN, "y2": lat + uy * STAFF_LEN * y_per_x, "speed": speed}
    )

    steps = int(round(speed / HALF_KT))  # speed rounded to the nearest 5 kt
    pennants, rest = divmod(steps * HALF_KT, PENNANT_KT)
    fulls, rest = divmod(rest, FULL_KT)
    halves = int(rest >= HALF_KT)
    slot = 0
    for value_kt, count in ((PENNANT_KT, pennants), (FULL_KT, fulls), (HALF_KT, halves)):
        for _ in range(int(count)):
            t = (1 - 0.04 - slot * FEATHER_STEP) * STAFF_LEN
            bx, by = lon + ux * t, lat + uy * t * y_per_x
            if value_kt >= PENNANT_KT:
                # Triangle with its base on the staff and its apex on the left side, like the barbs
                apex_deg = np.degrees(np.arctan2(px, py)) % 360
                pennant_rows.append(
                    {"x": bx + px * 0.11, "y": by + py * 0.11 * y_per_x, "angle": apex_deg, "speed": speed}
                )
            else:
                length = FULL_LEN * value_kt / FULL_KT
                barb_rows.append(
                    {"x": bx, "y": by, "x2": bx + px * length, "y2": by + py * length * y_per_x, "speed": speed}
                )
            slot += 1

staff_df = pd.DataFrame(staff_rows)
barb_df = pd.DataFrame(barb_rows, columns=["x", "y", "x2", "y2", "speed"])
pennant_df = pd.DataFrame(pennant_rows, columns=["x", "y", "angle", "speed"])
calm_df = obs[obs[SPEED] < CALM_KT]

speed_scale = alt.Scale(range=IMPRINT_SEQ, domain=[0, float(np.ceil(obs[SPEED].max() / 10) * 10)])
speed_color = alt.Color(
    "speed:Q",
    title=SPEED,
    scale=speed_scale,
    legend=alt.Legend(
        title=SPEED, type="gradient", orient="right", gradientLength=140, gradientThickness=12, padding=8
    ),
)
speed_color_quiet = alt.Color("speed:Q", scale=speed_scale, legend=None)
x_axis = alt.X("x:Q", title=LON, scale=alt.Scale(domain=x_dom, nice=False))
y_axis = alt.Y("y:Q", title=LAT, scale=alt.Scale(domain=y_dom, nice=False))

# Layer 1: staffs
staff = (
    alt.Chart(staff_df)
    .mark_rule(strokeWidth=1.8)
    .encode(
        x=x_axis,
        y=y_axis,
        x2="x2:Q",
        y2="y2:Q",
        color=speed_color,
        tooltip=[
            alt.Tooltip("x:Q", title=LON, format=".1f"),
            alt.Tooltip("y:Q", title=LAT, format=".1f"),
            alt.Tooltip("speed:Q", title=SPEED, format=".1f"),
        ],
    )
)

# Layer 2: half and full barbs, all on the left of the staff
barbs = (
    alt.Chart(barb_df)
    .mark_rule(strokeWidth=1.8)
    .encode(x="x:Q", y="y:Q", x2="x2:Q", y2="y2:Q", color=speed_color_quiet)
)

# Layer 3: pennants, filled triangles turned with the wind direction
pennants = (
    alt.Chart(pennant_df)
    .mark_point(shape="triangle", filled=True, size=300, opacity=1)
    .encode(
        x="x:Q",
        y="y:Q",
        angle=alt.Angle("angle:Q", scale=alt.Scale(domain=[0, 360], range=[0, 360]), legend=None),
        color=speed_color_quiet,
    )
)

# Layer 4: calm winds as open circles without a staff
calm_circles = (
    alt.Chart(calm_df)
    .mark_point(shape="circle", filled=False, size=120, stroke=IMPRINT_PALETTE[0], strokeWidth=2.2)
    .encode(
        x=alt.X(LON.translate(ESCAPE), type="quantitative", title=LON),
        y=alt.Y(LAT.translate(ESCAPE), type="quantitative", title=LAT),
        tooltip=[
            alt.Tooltip(LON.translate(ESCAPE), type="quantitative", title=LON, format=".1f"),
            alt.Tooltip(LAT.translate(ESCAPE), type="quantitative", title=LAT, format=".1f"),
            alt.Tooltip(SPEED.translate(ESCAPE), type="quantitative", title=SPEED, format=".2f"),
        ],
    )
)

chart = (
    alt.layer(staff, barbs, pennants, calm_circles)
    .properties(
        width=VIEW_W,
        height=VIEW_H,
        background=PAGE_BG,
        title=alt.Title(
            text="windbarb-basic · python · altair · anyplot.ai",
            subtitle=(
                f"Half barb = {HALF_KT} kt  |  Full barb = {FULL_KT} kt  |  ▲ Pennant = {PENNANT_KT} kt"
                f"  |  ○ Calm < {CALM_KT} kt"
            ),
        ),
    )
    .configure_view(fill=PAGE_BG, stroke="transparent")
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=13,
    )
    .configure_title(color=INK, subtitleColor=INK_SOFT, fontSize=17, subtitleFontSize=11)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=12,
    )
)

# Output: pad (never crop) to the 3200 x 1800 canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    # Other data can widen the legend or the tick labels: shrink the whole image to fit, never crop
    fit = min(TARGET_W / img.width, TARGET_H / img.height)
    img = img.resize((int(img.width * fit), int(img.height * fit)), Image.Resampling.LANCZOS)
if img.size != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
