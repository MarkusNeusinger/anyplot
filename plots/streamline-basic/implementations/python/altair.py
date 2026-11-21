""" anyplot.ai
streamline-basic: Basic Streamline Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-21
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

# Imprint palette: continuous speed uses the single-polarity sequential ramp
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]

# Disable data row limit
alt.data_transformers.disable_max_rows()

# Columns: set these to your table's column names
X_POS = "X position (units)"  # role: x
Y_POS = "Y position (units)"  # role: y
U_VEL = "Velocity u (units/s)"  # role: u
V_VEL = "Velocity v (units/s)"  # role: v
SPEED = "Flow speed (units/s)"  # role: extra
LINE_ID = "Streamline"  # role: extra
STEP = "Step"  # role: extra

# Data: replace this block with your own table, one row per streamline point, for example df = pd.read_csv("streamlines.csv")
# Vortex flow field (u = -y, v = x), streamlines traced by Euler integration
np.random.seed(42)
radii = [0.4, 0.7, 1.0, 1.4, 1.8, 2.2, 2.6, 3.0]
n_per_radius = 6
dt = 0.03
bound = 3.2

rows = []
line_id = 0
for r in radii:
    for i in range(n_per_radius):
        angle = 2 * np.pi * i / n_per_radius + (r * 0.1)
        x = r * np.cos(angle)
        y = r * np.sin(angle)
        points = [(x, y)]
        for _ in range(int(2 * np.pi * r / n_per_radius / dt) + 1):  # one arc per line, so lines never overlap
            u = -y
            v = x
            mag = np.sqrt(u**2 + v**2)
            if mag < 1e-6:
                break
            x_new = x + dt * u / mag
            y_new = y + dt * v / mag
            if abs(x_new) > bound or abs(y_new) > bound:
                break
            x, y = x_new, y_new
            points.append((x, y))
        if len(points) > 5:
            for step, (px, py) in enumerate(points):
                # In this vortex the speed equals the distance from the center
                rows.append(
                    {X_POS: px, Y_POS: py, U_VEL: -py, V_VEL: px, SPEED: np.hypot(px, py), LINE_ID: line_id, STEP: step}
                )
            line_id += 1

df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
title = "streamline-basic · python · altair · anyplot.ai"
lim = float(np.ceil(df[[X_POS, Y_POS]].abs().to_numpy().max() * 2) / 2)

# Color each streamline by its mean speed
df["mean_speed"] = df.groupby(LINE_ID)[SPEED].transform("mean")

chart = (
    alt.Chart(df)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X(X_POS.translate(ESCAPE), type="quantitative", title=X_POS, scale=alt.Scale(domain=[-lim, lim])),
        y=alt.Y(Y_POS.translate(ESCAPE), type="quantitative", title=Y_POS, scale=alt.Scale(domain=[-lim, lim])),
        color=alt.Color(
            "mean_speed",
            type="quantitative",
            title=SPEED,
            scale=alt.Scale(range=IMPRINT_SEQ),
            legend=alt.Legend(titleFontSize=11, labelFontSize=10, gradientLength=160, gradientThickness=14),
        ),
        detail=alt.Detail(LINE_ID.translate(ESCAPE), type="nominal"),
        order=alt.Order(STEP.translate(ESCAPE), type="quantitative"),
    )
    .properties(width=370, height=370, title=alt.Title(title, fontSize=16, anchor="middle"), background=PAGE_BG)
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
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
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=8)
)

# Save as PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad (never crop) up to the square target canvas
TARGET = (2400, 2400)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET[0] or img.height > TARGET[1]:
    raise SystemExit(f"altair produced {img.size}, exceeds target {TARGET}; shrink width/height")
canvas = Image.new("RGB", TARGET, PAGE_BG)
canvas.paste(img, ((TARGET[0] - img.width) // 2, (TARGET[1] - img.height) // 2))
canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
