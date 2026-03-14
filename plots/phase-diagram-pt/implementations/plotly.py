"""pyplots.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: plotly 6.6.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-14
"""

import numpy as np
import plotly.graph_objects as go


# Data - Water phase diagram (realistic boundaries)
# Triple point: 273.16 K, 611.73 Pa
# Critical point: 647.096 K, 22.064e6 Pa
triple_T = 273.16
triple_P = 611.73
critical_T = 647.096
critical_P = 22.064e6

# Solid-gas boundary (sublimation curve) - Clausius-Clapeyron approximation
T_solid_gas = np.linspace(200, triple_T, 80)
L_sub = 51059  # J/mol (sublimation enthalpy of water)
R = 8.314
P_solid_gas = triple_P * np.exp((L_sub / R) * (1 / triple_T - 1 / T_solid_gas))

# Liquid-gas boundary (vaporization curve) - from triple point to critical point
T_liquid_gas = np.linspace(triple_T, critical_T, 100)
L_vap = 40670  # J/mol (vaporization enthalpy of water)
P_liquid_gas = triple_P * np.exp((L_vap / R) * (1 / triple_T - 1 / T_liquid_gas))

# Solid-liquid boundary (melting curve) - nearly vertical, negative slope for water
P_solid_liquid = np.logspace(np.log10(triple_P), np.log10(1e9), 80)
dT_dP = -7.4e-8  # K/Pa (negative slope for water, Clausius-Clapeyron)
T_solid_liquid = triple_T + dT_dP * (P_solid_liquid - triple_P)

# Color palette - distinct colors for each curve
color_sublimation = "#306998"  # Python blue
color_vaporization = "#8B5CF6"  # Purple
color_melting = "#059669"  # Teal green

# Phase region fill colors
fill_solid = "rgba(48, 105, 152, 0.08)"
fill_liquid = "rgba(139, 92, 246, 0.08)"
fill_gas = "rgba(249, 115, 22, 0.06)"
fill_supercritical = "rgba(234, 179, 8, 0.06)"

# Plot
fig = go.Figure()

# Filled phase regions using shapes
fig.add_shape(
    type="rect", x0=180, x1=280, y0=0, y1=10, xref="x", yref="y", fillcolor=fill_solid, line={"width": 0}, layer="below"
)
fig.add_shape(
    type="rect",
    x0=280,
    x1=647,
    y0=np.log10(triple_P),
    y1=10,
    xref="x",
    yref="y",
    fillcolor=fill_liquid,
    line={"width": 0},
    layer="below",
)
fig.add_shape(
    type="rect",
    x0=200,
    x1=647,
    y0=0,
    y1=np.log10(triple_P),
    xref="x",
    yref="y",
    fillcolor=fill_gas,
    line={"width": 0},
    layer="below",
)
fig.add_shape(
    type="rect",
    x0=647,
    x1=750,
    y0=np.log10(critical_P),
    y1=10,
    xref="x",
    yref="y",
    fillcolor=fill_supercritical,
    line={"width": 0},
    layer="below",
)

# Phase boundary curves with distinct colors
fig.add_trace(
    go.Scatter(
        x=T_solid_gas,
        y=P_solid_gas,
        mode="lines",
        line={"color": color_sublimation, "width": 3.5},
        name="Sublimation curve",
        hovertemplate="<b>Sublimation</b><br>T: %{x:.1f} K<br>P: %{y:.2e} Pa<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=T_liquid_gas,
        y=P_liquid_gas,
        mode="lines",
        line={"color": color_vaporization, "width": 3.5},
        name="Vaporization curve",
        hovertemplate="<b>Vaporization</b><br>T: %{x:.1f} K<br>P: %{y:.2e} Pa<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=T_solid_liquid,
        y=P_solid_liquid,
        mode="lines",
        line={"color": color_melting, "width": 3.5},
        name="Melting curve",
        hovertemplate="<b>Melting</b><br>T: %{x:.1f} K<br>P: %{y:.2e} Pa<extra></extra>",
    )
)

# Triple point marker
fig.add_trace(
    go.Scatter(
        x=[triple_T],
        y=[triple_P],
        mode="markers",
        marker={"size": 16, "color": "#E74C3C", "symbol": "diamond", "line": {"color": "white", "width": 2}},
        name="Triple point",
        hovertemplate="Triple Point<br>T: 273.16 K<br>P: 611.73 Pa<extra></extra>",
    )
)

# Critical point marker
fig.add_trace(
    go.Scatter(
        x=[critical_T],
        y=[critical_P],
        mode="markers",
        marker={"size": 16, "color": "#E67E22", "symbol": "star", "line": {"color": "white", "width": 2}},
        name="Critical point",
        hovertemplate="Critical Point<br>T: 647.1 K<br>P: 2.206×10⁷ Pa<extra></extra>",
    )
)

# Phase region labels
label_font = {"size": 32, "color": "rgba(80, 80, 80, 0.55)", "family": "Arial Black"}

fig.add_annotation(x=225, y=np.log10(1e7), text="SOLID", font=label_font, showarrow=False, yref="y")
fig.add_annotation(x=430, y=np.log10(5e6), text="LIQUID", font=label_font, showarrow=False, yref="y")
fig.add_annotation(x=450, y=np.log10(30), text="GAS", font=label_font, showarrow=False, yref="y")
fig.add_annotation(
    x=685,
    y=np.log10(5e8),
    text="Supercritical<br>Fluid",
    font={"size": 20, "color": "rgba(120, 120, 120, 0.6)", "family": "Arial"},
    showarrow=False,
    yref="y",
)

# Triple point annotation
fig.add_annotation(
    x=triple_T,
    y=np.log10(triple_P),
    yref="y",
    text="Triple Point<br>(273.16 K, 611.73 Pa)",
    font={"size": 16},
    ax=-140,
    ay=50,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2,
    arrowcolor="#E74C3C",
)

# Critical point annotation
fig.add_annotation(
    x=critical_T,
    y=np.log10(critical_P),
    yref="y",
    text="Critical Point<br>(647.1 K, 2.206×10⁷ Pa)",
    font={"size": 16},
    ax=-140,
    ay=-50,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2,
    arrowcolor="#E67E22",
)

# Layout
fig.update_layout(
    title={
        "text": "Water P-T Phase Diagram · phase-diagram-pt · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Temperature (K)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [180, 760],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(200, 200, 200, 0.2)",
    },
    yaxis={
        "title": {"text": "Pressure (Pa)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "type": "log",
        "range": [0, 10],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(200, 200, 200, 0.2)",
    },
    template="plotly_white",
    legend={"font": {"size": 16}, "x": 0.02, "y": 0.98, "bgcolor": "rgba(255, 255, 255, 0.8)"},
    margin={"l": 100, "r": 120, "t": 100, "b": 100},
    showlegend=True,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
