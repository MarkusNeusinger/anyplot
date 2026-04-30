""" anyplot.ai
polar-basic: Basic Polar Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-04-30
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
BRAND = "#009E73"

# Data - Hourly temperature pattern (24-hour cycle)
np.random.seed(42)
hours = np.arange(24)

base_temp = 15 + 10 * np.sin((hours - 6) * np.pi / 12)
temperatures = base_temp + np.random.randn(24) * 1.5

theta = (90 - hours * 15) * np.pi / 180
radius = temperatures - temperatures.min() + 5

x = radius * np.cos(theta)
y = radius * np.sin(theta)

df = pd.DataFrame({"hour": hours, "temperature": temperatures, "x": x, "y": y})

# Radial gridlines (concentric circles)
max_radius = radius.max() + 2
grid_radii = np.linspace(5, max_radius, 5)
circle_angles = np.linspace(0, 2 * np.pi, 101)

grid_rows = []
for i, r in enumerate(grid_radii):
    for j, angle in enumerate(circle_angles):
        grid_rows.append({"x": r * np.cos(angle), "y": r * np.sin(angle), "circle_id": i, "order": j})

grid_df = pd.DataFrame(grid_rows)

# Angular gridlines (spokes at major hours)
spoke_data = []
major_hours = [0, 3, 6, 9, 12, 15, 18, 21]
for hour in major_hours:
    angle = (90 - hour * 15) * np.pi / 180
    spoke_data.append({"x": 0, "y": 0, "xend": max_radius * np.cos(angle), "yend": max_radius * np.sin(angle)})

spoke_df = pd.DataFrame(spoke_data)

# Hour labels around perimeter
label_data = []
hour_labels_map = {0: "00:00", 3: "03:00", 6: "06:00", 9: "09:00", 12: "12:00", 15: "15:00", 18: "18:00", 21: "21:00"}
for hour, label in hour_labels_map.items():
    angle = (90 - hour * 15) * np.pi / 180
    label_radius = max_radius + 4
    label_data.append({"label": label, "x": label_radius * np.cos(angle), "y": label_radius * np.sin(angle)})

label_df = pd.DataFrame(label_data)

# Closed path for the data line
df_sorted = df.sort_values("hour").copy()
df_sorted["order"] = df_sorted["hour"]
first_row = df_sorted.iloc[[0]].copy()
first_row["order"] = 24
df_path = pd.concat([df_sorted, first_row], ignore_index=True)

# Plot
GRID_OPACITY = 0.25

circles = (
    alt.Chart(grid_df)
    .mark_line(strokeWidth=1.2, opacity=GRID_OPACITY, color=INK_SOFT, strokeDash=[4, 4])
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), detail="circle_id:N", order="order:O")
)

spokes = (
    alt.Chart(spoke_df)
    .mark_rule(strokeWidth=1.2, opacity=GRID_OPACITY, color=INK_SOFT)
    .encode(x="x:Q", y="y:Q", x2="xend:Q", y2="yend:Q")
)

labels = (
    alt.Chart(label_df).mark_text(fontSize=22, fontWeight="bold", color=INK).encode(x="x:Q", y="y:Q", text="label:N")
)

line = (
    alt.Chart(df_path).mark_line(strokeWidth=3.5, color=BRAND, opacity=0.85).encode(x="x:Q", y="y:Q", order="order:O")
)

points = (
    alt.Chart(df)
    .mark_point(filled=True, size=500, opacity=0.95)
    .encode(
        x="x:Q",
        y="y:Q",
        color=alt.Color("temperature:Q", scale=alt.Scale(scheme="viridis"), legend=alt.Legend(title="Temp (°C)")),
        tooltip=[
            alt.Tooltip("hour:O", title="Hour"),
            alt.Tooltip("temperature:Q", title="Temperature (°C)", format=".1f"),
        ],
    )
)

chart = (
    alt.layer(circles, spokes, line, points, labels)
    .properties(
        background=PAGE_BG,
        width=1200,
        height=1200,
        title=alt.Title(text="polar-basic · altair · anyplot.ai", fontSize=30, anchor="middle"),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=16,
        titleFontSize=18,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
