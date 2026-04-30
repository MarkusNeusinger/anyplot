""" anyplot.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Created: 2026-04-30
"""

import os
import sys

import pandas as pd


_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

import altair as alt  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito: position 1 = Increase, position 2 = Decrease
COLOR_INCREASE = "#009E73"
COLOR_DECREASE = "#D55E00"

# Data
data = pd.DataFrame(
    {
        "Product": [
            "Laptop",
            "Phone",
            "Tablet",
            "Monitor",
            "Keyboard",
            "Mouse",
            "Headphones",
            "Webcam",
            "Speaker",
            "Charger",
        ],
        "Q1 Sales": [850, 1200, 420, 310, 580, 720, 390, 180, 260, 440],
        "Q4 Sales": [920, 980, 650, 410, 520, 810, 620, 350, 240, 380],
    }
)

df_long = pd.melt(data, id_vars=["Product"], value_vars=["Q1 Sales", "Q4 Sales"], var_name="Period", value_name="Sales")
data["Direction"] = data.apply(lambda row: "Increase" if row["Q4 Sales"] > row["Q1 Sales"] else "Decrease", axis=1)
df_long = df_long.merge(data[["Product", "Direction"]], on="Product")

color_scale = alt.Scale(domain=["Increase", "Decrease"], range=[COLOR_INCREASE, COLOR_DECREASE])

# Plot
lines = (
    alt.Chart(df_long)
    .mark_line(strokeWidth=3, opacity=0.8)
    .encode(
        x=alt.X("Period:N", axis=alt.Axis(labelFontSize=20, title=None, labelAngle=0)),
        y=alt.Y(
            "Sales:Q",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, title="Sales (units)"),
            scale=alt.Scale(zero=False),
        ),
        color=alt.Color(
            "Direction:N", scale=color_scale, legend=alt.Legend(titleFontSize=20, labelFontSize=18, orient="top-right")
        ),
        detail="Product:N",
    )
)

points = (
    alt.Chart(df_long)
    .mark_circle(size=200, opacity=0.9)
    .encode(x="Period:N", y="Sales:Q", color=alt.Color("Direction:N", scale=color_scale, legend=None))
)

labels_left = (
    alt.Chart(df_long[df_long["Period"] == "Q1 Sales"])
    .mark_text(align="right", dx=-15, fontSize=16)
    .encode(x="Period:N", y="Sales:Q", text="Product:N", color=alt.Color("Direction:N", scale=color_scale, legend=None))
)

labels_right = (
    alt.Chart(df_long[df_long["Period"] == "Q4 Sales"])
    .mark_text(align="left", dx=15, fontSize=16)
    .encode(x="Period:N", y="Sales:Q", text="Product:N", color=alt.Color("Direction:N", scale=color_scale, legend=None))
)

# Style
chart = (
    (lines + points + labels_left + labels_right)
    .properties(width=1400, height=850, background=PAGE_BG, title="slope-basic · altair · anyplot.ai")
    .configure_title(color=INK, fontSize=28, anchor="middle")
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        grid=True,
        gridColor=INK,
        gridOpacity=0.10,
        gridDash=[4, 4],
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
