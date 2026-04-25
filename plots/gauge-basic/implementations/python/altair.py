"""anyplot.ai
gauge-basic: Basic Gauge Chart
Library: altair 6.1.0 | Python 3.13
Quality: 92/100 | Updated: 2026-04-25
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito zone colors (colorblind-safe red/yellow/green)
ZONE_BAD = "#D55E00"  # vermillion
ZONE_WARN = "#E69F00"  # orange
ZONE_GOOD = "#009E73"  # bluish green (brand)

# Data — Sales performance gauge
value = 72
min_value = 0
max_value = 100
thresholds = [30, 70]

# Geometry: semi-circle from -pi/2 (left) to +pi/2 (right)
boundaries = np.array([min_value] + thresholds + [max_value], dtype=float)
boundary_angles = -np.pi / 2 + (boundaries - min_value) / (max_value - min_value) * np.pi
needle_angle = -np.pi / 2 + (value - min_value) / (max_value - min_value) * np.pi

# Zone arcs
zones_df = pd.DataFrame(
    {"startAngle": boundary_angles[:-1], "endAngle": boundary_angles[1:], "color": [ZONE_BAD, ZONE_WARN, ZONE_GOOD]}
)

gauge_arcs = (
    alt.Chart(zones_df)
    .mark_arc(innerRadius=220, outerRadius=360, cornerRadius=6, stroke=PAGE_BG, strokeWidth=4)
    .encode(
        theta=alt.Theta("startAngle:Q", scale=None),
        theta2="endAngle:Q",
        color=alt.Color("color:N", scale=None, legend=None),
    )
)

# Needle
needle_length = 300
needle_df = pd.DataFrame(
    [{"x": 0.0, "y": 0.0, "x2": needle_length * np.sin(needle_angle), "y2": needle_length * np.cos(needle_angle)}]
)
needle = (
    alt.Chart(needle_df)
    .mark_rule(color=INK, strokeWidth=10, strokeCap="round")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-450, 450]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-260, 440]), axis=None),
        x2="x2:Q",
        y2="y2:Q",
    )
)

# Center hub (two-tone for definition)
hub_df = pd.DataFrame([{"x": 0, "y": 0}])
hub_outer = alt.Chart(hub_df).mark_circle(size=2400, color=INK).encode(x="x:Q", y="y:Q")
hub_inner = alt.Chart(hub_df).mark_circle(size=400, color=PAGE_BG).encode(x="x:Q", y="y:Q")

# Prominent value label (centered below hub)
value_label_df = pd.DataFrame([{"x": 0, "y": -140, "text": f"{value}"}])
value_label = (
    alt.Chart(value_label_df)
    .mark_text(fontSize=88, fontWeight="bold", color=ZONE_GOOD, baseline="middle")
    .encode(x="x:Q", y="y:Q", text="text:N")
)

context_label_df = pd.DataFrame([{"x": 0, "y": -220, "text": "Current Sales"}])
context_label = (
    alt.Chart(context_label_df)
    .mark_text(fontSize=22, color=INK_MUTED, baseline="middle")
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Min and max labels just below the arc ends
range_label_radius = 290
range_labels_df = pd.DataFrame(
    [
        {"x": range_label_radius * np.sin(boundary_angles[0]), "y": -50, "text": str(min_value)},
        {"x": range_label_radius * np.sin(boundary_angles[-1]), "y": -50, "text": str(max_value)},
    ]
)
range_labels = (
    alt.Chart(range_labels_df)
    .mark_text(fontSize=26, color=INK_SOFT, fontWeight="bold")
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Threshold labels above the arc
threshold_angles = -np.pi / 2 + (np.array(thresholds, dtype=float) - min_value) / (max_value - min_value) * np.pi
threshold_label_radius = 400
threshold_labels_df = pd.DataFrame(
    {
        "x": threshold_label_radius * np.sin(threshold_angles),
        "y": threshold_label_radius * np.cos(threshold_angles),
        "text": [str(t) for t in thresholds],
    }
)
threshold_labels = (
    alt.Chart(threshold_labels_df)
    .mark_text(fontSize=24, color=INK_SOFT, fontWeight="bold", dy=-10)
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Compose layers
chart = (
    alt.layer(gauge_arcs, needle, hub_outer, hub_inner, threshold_labels, range_labels, value_label, context_label)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(
            "gauge-basic · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK, fontWeight="normal"
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
