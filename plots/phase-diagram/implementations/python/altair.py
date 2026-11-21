"""anyplot.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: altair 6.1.0 | Python 3.13.13
Quality: 97/100 | Updated: 2026-05-14
"""

import os
import sys


sys.path = [p for p in sys.path if not p.endswith("python")]
import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (first series is #009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
EQUILIBRIUM = (0.0, 0.0)  # the damped pendulum rests at x = 0 with dx/dt = 0

# Column constants
X = "Position (x)"  # role: x
DX_DT = "Velocity (dx/dt)"  # role: dx_dt
CONDITION = "Start (x0, v0)"  # role: extra
STEP = "Time step"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("trajectories.csv")
np.random.seed(42)
dt = 0.02
gamma = 0.15
initial_conditions = [(2.5, 0.0), (-2.0, 1.5), (0.5, 2.0), (1.5, -1.5)]

rows = []
for x0, v0 in initial_conditions:
    x, v = x0, v0
    label = f"({x0:.1f}, {v0:.1f})"
    rows.append({X: x, DX_DT: v, CONDITION: label, STEP: 0})
    for step in range(1, 501):
        a = -np.sin(x) - gamma * v
        v = v + a * dt
        x = x + v * dt
        rows.append({X: x, DX_DT: v, CONDITION: label, STEP: step})
df = pd.DataFrame(rows)

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
x_f, y_f, cond_f, step_f = (c.translate(ESCAPE) for c in (X, DX_DT, CONDITION, STEP))
color_scale = alt.Scale(range=IMPRINT_PALETTE)
title = "phase-diagram · python · altair · anyplot.ai"

trajectories = (
    alt.Chart(df)
    .mark_line(strokeWidth=2.2, opacity=0.85)
    .encode(
        x=alt.X(x_f, type="quantitative", title=X, axis=alt.Axis(titleFontSize=15, labelFontSize=13)),
        y=alt.Y(y_f, type="quantitative", title=DX_DT, axis=alt.Axis(titleFontSize=15, labelFontSize=13)),
        color=alt.Color(
            cond_f,
            type="nominal",
            title=CONDITION,
            sort=None,
            scale=color_scale,
            legend=alt.Legend(
                columns=-(-df[CONDITION].nunique() // 14), titleFontSize=13, labelFontSize=12, symbolStrokeWidth=3
            ),
        ),
        order=alt.Order(step_f, type="quantitative"),
    )
    .properties(width=540, height=360, title=alt.Title(text=title, fontSize=18, anchor="middle"))
)

# Starting point of each trajectory
start_points = df.groupby(CONDITION, sort=False).head(1)
starts = (
    alt.Chart(start_points)
    .mark_point(size=260, filled=True, opacity=1.0)
    .encode(
        x=alt.X(x_f, type="quantitative", title=X),
        y=alt.Y(y_f, type="quantitative", title=DX_DT),
        color=alt.Color(cond_f, type="nominal", sort=None, scale=color_scale, legend=None),
    )
)

# Equilibrium marker
equilibrium = pd.DataFrame({X: [EQUILIBRIUM[0]], DX_DT: [EQUILIBRIUM[1]]})
eq_point = (
    alt.Chart(equilibrium)
    .mark_point(shape="cross", size=360, strokeWidth=3, color=INK)
    .encode(x=alt.X(x_f, type="quantitative", title=X), y=alt.Y(y_f, type="quantitative", title=DX_DT))
)

chart = (
    (trajectories + starts + eq_point)
    .properties(background=PAGE_BG)
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save with theme suffix, padded (never cropped) to the 3200 x 1800 target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}×{h}, exceeds target {TW}×{TH}; shrink width/height.")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
canvas.save(f"plot-{THEME}.png")
chart.interactive().save(f"plot-{THEME}.html")
