""" pyplots.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: altair 6.0.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-14
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Water phase diagram (representative values)
T_triple = 273.16  # K
P_triple = 611.73  # Pa
T_critical = 647.1  # K
P_critical = 2.2064e7  # Pa

# Solid-gas boundary (sublimation curve) - Clausius-Clapeyron approximation
L_sub = 51059  # J/mol sublimation enthalpy (ice)
R = 8.314
T_sg = np.linspace(210, T_triple, 80)
P_sg = P_triple * np.exp((L_sub / R) * (1 / T_triple - 1 / T_sg))
mask_sg = P_sg >= 1
T_sg = T_sg[mask_sg]
P_sg = P_sg[mask_sg]

# Liquid-gas boundary (vaporization curve) - from triple point to critical point
T_lg = np.linspace(T_triple, T_critical, 100)
L_vap = 40700  # J/mol vaporization enthalpy (water)
P_lg = P_triple * np.exp((L_vap / R) * (1 / T_triple - 1 / T_lg))

# Solid-liquid boundary (melting curve) - nearly vertical, negative slope for water
P_sl = np.linspace(P_triple, 1e9, 80)
T_sl = T_triple - (P_sl - P_triple) * 7.5e-9

# Combine boundary data
df_sg = pd.DataFrame({"temperature": T_sg, "pressure": P_sg, "boundary": "Solid–Gas"})
df_lg = pd.DataFrame({"temperature": T_lg, "pressure": P_lg, "boundary": "Liquid–Gas"})
df_sl = pd.DataFrame({"temperature": T_sl, "pressure": P_sl, "boundary": "Solid–Liquid"})
df_boundaries = pd.concat([df_sg, df_lg, df_sl], ignore_index=True)

# Phase region shading (approximate rectangular regions)
df_regions = pd.DataFrame(
    {
        "t1": [200, T_triple, T_triple],
        "t2": [T_triple, 700, 700],
        "p1": [1, 1, P_triple],
        "p2": [2e9, P_critical, 2e9],
        "phase": ["Solid", "Gas", "Liquid"],
    }
)

# Special points
df_points = pd.DataFrame(
    {
        "temperature": [T_triple, T_critical],
        "pressure": [P_triple, P_critical],
        "label": ["Triple Point\n273.16 K, 611.7 Pa", "Critical Point\n647.1 K, 22.06 MPa"],
        "point_type": ["Triple Point", "Critical Point"],
    }
)

# Phase region text labels
df_labels = pd.DataFrame(
    {"temperature": [232, 480, 480], "pressure": [1e6, 1e8, 25], "phase": ["SOLID", "LIQUID", "GAS"]}
)

# Shared scales and encodings
x_scale = alt.Scale(domain=[200, 700])
y_scale = alt.Scale(type="log", domain=[1, 2e9])
x_enc = alt.X("temperature:Q", title="Temperature (K)", scale=x_scale)
y_enc = alt.Y("pressure:Q", title="Pressure (Pa)", scale=y_scale)

boundary_colors = alt.Scale(domain=["Solid–Gas", "Liquid–Gas", "Solid–Liquid"], range=["#306998", "#e68a00", "#8b5cf6"])

# Interactive hover highlight for boundary curves
hover = alt.selection_point(fields=["boundary"], on="pointerover", empty="all")

# Phase region fills
regions = (
    alt.Chart(df_regions)
    .mark_rect(opacity=0.12)
    .encode(
        x=alt.X("t1:Q", scale=x_scale),
        x2="t2:Q",
        y=alt.Y("p1:Q", scale=y_scale),
        y2="p2:Q",
        color=alt.Color(
            "phase:N",
            scale=alt.Scale(domain=["Solid", "Liquid", "Gas"], range=["#a8c4e0", "#f5d4a0", "#a8dbb5"]),
            legend=None,
        ),
    )
)

# Phase region text labels (rendered on top of fills, before lines)
phase_text = (
    alt.Chart(df_labels)
    .mark_text(fontSize=42, fontWeight="bold", opacity=0.4)
    .encode(
        x=alt.X("temperature:Q", scale=x_scale),
        y=alt.Y("pressure:Q", scale=y_scale),
        text="phase:N",
        color=alt.Color(
            "phase:N",
            scale=alt.Scale(domain=["SOLID", "LIQUID", "GAS"], range=["#1a3a5c", "#b06418", "#1d7a3e"]),
            legend=None,
        ),
    )
)

# Phase boundary lines with hover highlight
lines = (
    alt.Chart(df_boundaries)
    .mark_line(strokeWidth=3.5)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color("boundary:N", scale=boundary_colors, legend=alt.Legend(title="Phase Boundary")),
        opacity=alt.condition(hover, alt.value(1.0), alt.value(0.4)),
        strokeWidth=alt.condition(hover, alt.value(5), alt.value(3.5)),
        tooltip=[
            alt.Tooltip("temperature:Q", title="Temperature (K)", format=".1f"),
            alt.Tooltip("pressure:Q", title="Pressure (Pa)", format=".2e"),
            alt.Tooltip("boundary:N", title="Boundary"),
        ],
    )
    .add_params(hover)
)

# Special points - markers with distinct shapes
points = (
    alt.Chart(df_points)
    .mark_point(size=400, filled=True, stroke="white", strokeWidth=2.5)
    .encode(
        x=x_enc,
        y=y_enc,
        shape=alt.Shape(
            "point_type:N",
            scale=alt.Scale(domain=["Triple Point", "Critical Point"], range=["diamond", "square"]),
            legend=None,
        ),
        color=alt.Color(
            "point_type:N",
            scale=alt.Scale(domain=["Triple Point", "Critical Point"], range=["#d4a017", "#7c3aed"]),
            legend=None,
        ),
        tooltip=[alt.Tooltip("label:N", title="Point")],
    )
)

# Special points - text annotations
df_tp = df_points[df_points["point_type"] == "Triple Point"]
df_cp = df_points[df_points["point_type"] == "Critical Point"]

tp_label = (
    alt.Chart(df_tp)
    .mark_text(fontSize=18, fontWeight="bold", align="left", dx=18, dy=-10, lineBreak="\n", color="#b8860b")
    .encode(x=x_enc, y=y_enc, text="label:N")
)

cp_label = (
    alt.Chart(df_cp)
    .mark_text(fontSize=18, fontWeight="bold", align="right", dx=-18, dy=-10, lineBreak="\n", color="#6d28d9")
    .encode(x=x_enc, y=y_enc, text="label:N")
)

# Compose chart
chart = (
    alt.layer(regions, phase_text, lines, points, tp_label, cp_label)
    .resolve_scale(color="independent", shape="independent")
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "phase-diagram-pt · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            subtitle="Water Pressure–Temperature Phase Diagram",
            subtitleFontSize=20,
            subtitleColor="#555",
        ),
    )
    .configure_axis(
        labelFontSize=18, titleFontSize=22, gridOpacity=0.1, gridDash=[3, 3], domainColor="#888", tickColor="#888"
    )
    .configure_view(strokeWidth=0)
    .configure_legend(
        titleFontSize=18,
        labelFontSize=16,
        symbolSize=200,
        titleLimit=300,
        labelLimit=300,
        orient="top-right",
        padding=10,
        cornerRadius=4,
        fillColor="rgba(255,255,255,0.9)",
        strokeColor="#ccc",
    )
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.interactive().save("plot.html")
