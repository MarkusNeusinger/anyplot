""" anyplot.ai
quiver-basic: Basic Quiver Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-04-29
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - 15x15 grid with circular rotation field (u = -y, v = x)
np.random.seed(42)
grid_size = 15
x_range = np.linspace(-2, 2, grid_size)
y_range = np.linspace(-2, 2, grid_size)
X, Y = np.meshgrid(x_range, y_range)
x_flat = X.flatten()
y_flat = Y.flatten()

# Circular rotation field: u = -y, v = x
U = -y_flat
V = x_flat

# Magnitude for color encoding
magnitude = np.sqrt(U**2 + V**2)

# Scale vectors proportionally to magnitude (arrow length encodes magnitude)
scale = 0.12
U_scaled = U * scale
V_scaled = V * scale

# Arrow tip positions
x2 = x_flat + U_scaled
y2 = y_flat + V_scaled

# Arrowhead geometry — size proportional to arrow length for visual coherence
angle = np.arctan2(V_scaled, U_scaled)
arrow_length = magnitude * scale
head_size = np.maximum(arrow_length * 0.30, 0.005)

n = len(x_flat)
ids = np.arange(n)

# Vectorized construction of shaft + two arrowhead lines per arrow
shaft = pd.DataFrame({"x": x_flat, "y": y_flat, "x2": x2, "y2": y2, "magnitude": magnitude, "arrow_id": ids})
left = pd.DataFrame(
    {
        "x": x2,
        "y": y2,
        "x2": x2 - head_size * np.cos(angle - 0.4),
        "y2": y2 - head_size * np.sin(angle - 0.4),
        "magnitude": magnitude,
        "arrow_id": ids,
    }
)
right = pd.DataFrame(
    {
        "x": x2,
        "y": y2,
        "x2": x2 - head_size * np.cos(angle + 0.4),
        "y2": y2 - head_size * np.sin(angle + 0.4),
        "magnitude": magnitude,
        "arrow_id": ids,
    }
)

arrow_df = pd.concat([shaft, left, right], ignore_index=True)

# Chart — rule marks encode vectors; viridis colormap encodes magnitude
chart = (
    alt.Chart(arrow_df)
    .mark_rule(strokeWidth=2.5)
    .encode(
        x=alt.X("x:Q", title="X Position", scale=alt.Scale(domain=[-2.5, 2.5])),
        y=alt.Y("y:Q", title="Y Position", scale=alt.Scale(domain=[-2.5, 2.5])),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color(
            "magnitude:Q",
            scale=alt.Scale(scheme="viridis"),
            title="Magnitude",
            legend=alt.Legend(titleFontSize=18, labelFontSize=16),
        ),
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("quiver-basic · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
