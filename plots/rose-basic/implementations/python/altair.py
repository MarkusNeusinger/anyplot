"""anyplot.ai
rose-basic: Basic Rose Chart
Library: altair | Python 3.13
Quality: pending | Created: 2026-04-30
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Monthly rainfall in mm (12-month cyclical pattern)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
rainfall = [78, 52, 68, 45, 35, 28, 22, 30, 55, 85, 92, 88]

n = len(months)
angle_step = 360 / n
start_angles = [-90 + i * angle_step for i in range(n)]
end_angles = [-90 + (i + 1) * angle_step for i in range(n)]

df = pd.DataFrame(
    {"month": months, "value": rainfall, "startAngle": np.radians(start_angles), "endAngle": np.radians(end_angles)}
)

max_val = 100
chart_radius = 460

# Radial gridlines at 25, 50, 75, 100 mm
grid_values = [25, 50, 75, 100]
grid_data = pd.DataFrame({"value": grid_values})

gridlines = (
    alt.Chart(grid_data)
    .mark_arc(filled=False, stroke=INK_SOFT, strokeWidth=1.0, strokeOpacity=0.35, strokeDash=[6, 4])
    .encode(
        theta=alt.value(2 * np.pi),
        radius=alt.Radius("value:Q", scale=alt.Scale(type="linear", domain=[0, max_val], range=[0, chart_radius])),
    )
)

# Grid labels at 3 o'clock position
grid_label_data = pd.DataFrame(
    {"value": grid_values, "label": [f"{v} mm" for v in grid_values], "theta": [0.0] * len(grid_values)}
)

grid_labels = (
    alt.Chart(grid_label_data)
    .mark_text(fontSize=18, dx=10, align="left", baseline="middle")
    .encode(
        theta=alt.Theta("theta:Q"),
        radius=alt.Radius("value:Q", scale=alt.Scale(type="linear", domain=[0, max_val], range=[0, chart_radius])),
        text="label:N",
        color=alt.value(INK_SOFT),
    )
)

# Rose chart segments — viridis colormap for value-based color encoding (12 categories)
rose = (
    alt.Chart(df)
    .mark_arc(stroke=PAGE_BG, strokeWidth=2, innerRadius=0)
    .encode(
        theta=alt.Theta("startAngle:Q", stack=None),
        theta2=alt.Theta2("endAngle:Q"),
        radius=alt.Radius("value:Q", scale=alt.Scale(type="linear", domain=[0, max_val], range=[0, chart_radius])),
        color=alt.Color("value:Q", scale=alt.Scale(scheme="viridis"), legend=None),
        tooltip=[alt.Tooltip("month:N", title="Month"), alt.Tooltip("value:Q", title="Rainfall (mm)")],
    )
)

# Value labels near segment tips
mid_angles = [-90 + (i + 0.5) * angle_step for i in range(n)]
mid_angles_rad = np.radians(mid_angles)

label_radii = [max(v * 1.35, 45) if v < 35 else v * 1.15 for v in rainfall]

label_data = pd.DataFrame({"month": months, "value": rainfall, "theta": mid_angles_rad, "labelRadius": label_radii})

value_labels = (
    alt.Chart(label_data)
    .mark_text(fontSize=20, fontWeight="bold")
    .encode(
        theta=alt.Theta("theta:Q"),
        radius=alt.Radius(
            "labelRadius:Q", scale=alt.Scale(type="linear", domain=[0, max_val], range=[0, chart_radius])
        ),
        text=alt.Text("value:Q"),
        color=alt.value(INK),
    )
)

# Month labels at outer edge — just beyond the 100 mm gridline
month_label_data = pd.DataFrame({"month": months, "theta": mid_angles_rad, "labelRadius": [115.0] * n})

month_labels = (
    alt.Chart(month_label_data)
    .mark_text(fontSize=22, fontWeight="bold")
    .encode(
        theta=alt.Theta("theta:Q"),
        radius=alt.Radius(
            "labelRadius:Q", scale=alt.Scale(type="linear", domain=[0, max_val], range=[0, chart_radius])
        ),
        text=alt.Text("month:N"),
        color=alt.value(INK),
    )
)

# Combine all layers
chart = (
    alt.layer(gridlines, grid_labels, rose, value_labels, month_labels)
    .properties(
        width=1200,
        height=1200,
        background=PAGE_BG,
        title=alt.Title(text="rose-basic · altair · anyplot.ai", fontSize=32, anchor="middle", offset=20, color=INK),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(grid=False, domain=False, ticks=False, labels=False, title=None)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
