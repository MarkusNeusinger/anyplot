""" pyplots.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: altair 6.0.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-14
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Water phase diagram (representative values)
# Triple point: 273.16 K, 611.73 Pa
# Critical point: 647.1 K, 2.2064e7 Pa

T_triple = 273.16
P_triple = 611.73
T_critical = 647.1
P_critical = 2.2064e7

# Solid-gas boundary (sublimation curve) - Clausius-Clapeyron approximation
L_sub = 51059  # J/mol sublimation enthalpy (ice)
R = 8.314
T_sg = np.linspace(210, T_triple, 80)
P_sg = P_triple * np.exp((L_sub / R) * (1 / T_triple - 1 / T_sg))
# Clamp to visible pressure range
mask_sg = P_sg >= 1
T_sg = T_sg[mask_sg]
P_sg = P_sg[mask_sg]

# Liquid-gas boundary (vaporization curve) - from triple point to critical point
T_lg = np.linspace(T_triple, T_critical, 100)
L_vap = 40700  # J/mol vaporization enthalpy (water)
P_lg = P_triple * np.exp((L_vap / R) * (1 / T_triple - 1 / T_lg))

# Solid-liquid boundary (melting curve) - nearly vertical, negative slope for water
P_sl = np.linspace(P_triple, 1e9, 80)
# Water has negative slope (dT/dP < 0), use Simon equation approximation
T_sl = T_triple - (P_sl - P_triple) * 7.5e-9

# Combine boundary data into a single DataFrame
df_sg = pd.DataFrame({"temperature": T_sg, "pressure": P_sg, "boundary": "Solid–Gas"})
df_lg = pd.DataFrame({"temperature": T_lg, "pressure": P_lg, "boundary": "Liquid–Gas"})
df_sl = pd.DataFrame({"temperature": T_sl, "pressure": P_sl, "boundary": "Solid–Liquid"})
df_boundaries = pd.concat([df_sg, df_lg, df_sl], ignore_index=True)

# Special points
df_points = pd.DataFrame(
    {
        "temperature": [T_triple, T_critical],
        "pressure": [P_triple, P_critical],
        "label": ["Triple Point (273.16 K, 611.7 Pa)", "Critical Point (647.1 K, 22.06 MPa)"],
        "point_type": ["Triple Point", "Critical Point"],
    }
)

# Phase region labels
df_labels = pd.DataFrame(
    {"temperature": [235, 450, 500], "pressure": [2e5, 5e7, 30], "phase": ["SOLID", "LIQUID", "GAS"]}
)

# Shared scales
x_scale = alt.Scale(domain=[200, 700])
y_scale = alt.Scale(type="log", domain=[1, 2e9])
x_enc = alt.X("temperature:Q", title="Temperature (K)", scale=x_scale)
y_enc = alt.Y("pressure:Q", title="Pressure (Pa)", scale=y_scale)

boundary_colors = alt.Scale(domain=["Solid–Gas", "Liquid–Gas", "Solid–Liquid"], range=["#306998", "#e74c3c", "#2ecc71"])

# Phase boundary lines
lines = (
    alt.Chart(df_boundaries)
    .mark_line(strokeWidth=3, opacity=0.9)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color("boundary:N", scale=boundary_colors, title="Boundary"),
        tooltip=[
            alt.Tooltip("temperature:Q", title="Temperature (K)", format=".1f"),
            alt.Tooltip("pressure:Q", title="Pressure (Pa)", format=".2e"),
            alt.Tooltip("boundary:N", title="Boundary"),
        ],
    )
)

# Special points - markers
points = (
    alt.Chart(df_points)
    .mark_point(size=300, filled=True, stroke="white", strokeWidth=2)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(
            "point_type:N",
            scale=alt.Scale(domain=["Triple Point", "Critical Point"], range=["#f39c12", "#9b59b6"]),
            title="Key Points",
        ),
        tooltip=[alt.Tooltip("label:N", title="Point")],
    )
)

# Special points - text labels (triple point label to right, critical point label to left)
df_tp_label = df_points[df_points["point_type"] == "Triple Point"]
df_cp_label = df_points[df_points["point_type"] == "Critical Point"]

tp_label = (
    alt.Chart(df_tp_label)
    .mark_text(fontSize=15, fontWeight="bold", align="left", dx=14, dy=-12, color="#f39c12")
    .encode(x=x_enc, y=y_enc, text="label:N")
)

cp_label = (
    alt.Chart(df_cp_label)
    .mark_text(fontSize=15, fontWeight="bold", align="right", dx=-14, dy=-12, color="#9b59b6")
    .encode(x=x_enc, y=y_enc, text="label:N")
)

# Phase region labels
phase_labels = (
    alt.Chart(df_labels)
    .mark_text(fontSize=32, fontWeight="bold", opacity=0.18)
    .encode(x=x_enc, y=y_enc, text="phase:N")
)

# Compose chart
chart = (
    alt.layer(phase_labels, lines, points, tp_label, cp_label)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("Water P-T Phase Diagram · phase-diagram-pt · altair · pyplots.ai", fontSize=28),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.15)
    .configure_view(strokeWidth=0)
    .configure_legend(titleFontSize=18, labelFontSize=16, symbolSize=200)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.interactive().save("plot.html")
