""" pyplots.ai
line-stress-strain: Engineering Stress-Strain Curve
Library: plotly 6.6.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-20
"""

import numpy as np
import plotly.graph_objects as go


# Data — Mild steel tensile test simulation
np.random.seed(42)

youngs_modulus = 210000  # MPa
yield_stress = 250  # MPa
uts = 400  # MPa
fracture_strain = 0.35
uts_strain = 0.22
yield_strain = yield_stress / youngs_modulus

# Elastic region (steep linear rise)
strain_elastic = np.linspace(0, yield_strain, 50)
stress_elastic = youngs_modulus * strain_elastic

# Yield plateau and early plastic deformation
strain_plateau = np.linspace(yield_strain, 0.02, 20)
stress_plateau = yield_stress + 5000 * (strain_plateau - yield_strain)

# Strain hardening (concave down curve toward UTS)
strain_hardening = np.linspace(0.02, uts_strain, 100)
t = (strain_hardening - 0.02) / (uts_strain - 0.02)
stress_hardening = stress_plateau[-1] + (uts - stress_plateau[-1]) * (1 - (1 - t) ** 2)

# Necking (stress drops from UTS to fracture)
strain_necking = np.linspace(uts_strain, fracture_strain, 50)
t_neck = (strain_necking - uts_strain) / (fracture_strain - uts_strain)
fracture_stress = 310
stress_necking = uts - (uts - fracture_stress) * t_neck**1.5

# Combine all regions
strain = np.concatenate([strain_elastic, strain_plateau, strain_hardening, strain_necking])
stress = np.concatenate([stress_elastic, stress_plateau, stress_hardening, stress_necking])

# Add slight noise for realism (skip elastic region for clean slope)
noise = np.random.normal(0, 1.0, len(strain))
noise[:50] = 0
stress = stress + noise
stress = np.maximum(stress, 0)

# 0.2% offset line for yield determination
offset_line_strain = np.linspace(0.002, 0.002 + yield_strain * 1.3, 50)
offset_line_stress = youngs_modulus * (offset_line_strain - 0.002)

# Key point coordinates
offset_yield_strain = yield_stress / youngs_modulus + 0.002
offset_yield_stress = yield_stress

# UTS at known position (use designed value, not noisy argmax)
uts_plot_strain = uts_strain
uts_plot_stress = uts

fracture_plot_strain = strain[-1]
fracture_plot_stress = stress[-1]

# Plot
fig = go.Figure()

# Main stress-strain curve
fig.add_trace(
    go.Scatter(
        x=strain,
        y=stress,
        mode="lines",
        line={"color": "#306998", "width": 3.5},
        name="Mild Steel",
        hovertemplate="Strain: %{x:.4f}<br>Stress: %{y:.1f} MPa<extra></extra>",
    )
)

# 0.2% offset line
fig.add_trace(
    go.Scatter(
        x=offset_line_strain,
        y=offset_line_stress,
        mode="lines",
        line={"color": "#B85C38", "width": 2.5, "dash": "dash"},
        name="0.2% Offset Line",
        hoverinfo="skip",
    )
)

# Yield point marker
fig.add_trace(
    go.Scatter(
        x=[offset_yield_strain],
        y=[offset_yield_stress],
        mode="markers",
        marker={"size": 14, "color": "#B85C38", "symbol": "diamond", "line": {"color": "white", "width": 1.5}},
        name="Yield Point",
        hovertemplate="Yield Point<br>Strain: %{x:.4f}<br>Stress: %{y:.1f} MPa<extra></extra>",
    )
)

# UTS marker
fig.add_trace(
    go.Scatter(
        x=[uts_plot_strain],
        y=[uts_plot_stress],
        mode="markers",
        marker={"size": 14, "color": "#2E8B57", "symbol": "star", "line": {"color": "white", "width": 1.5}},
        name="Ultimate Tensile Strength",
        hovertemplate="UTS<br>Strain: %{x:.4f}<br>Stress: %{y:.1f} MPa<extra></extra>",
    )
)

# Fracture point marker
fig.add_trace(
    go.Scatter(
        x=[fracture_plot_strain],
        y=[fracture_plot_stress],
        mode="markers",
        marker={"size": 14, "color": "#C62828", "symbol": "x", "line": {"color": "white", "width": 1.5}},
        name="Fracture Point",
        hovertemplate="Fracture<br>Strain: %{x:.4f}<br>Stress: %{y:.1f} MPa<extra></extra>",
    )
)

# Annotations for key points
fig.add_annotation(
    x=offset_yield_strain,
    y=offset_yield_stress,
    text="Yield Point<br>(0.2% offset)",
    showarrow=True,
    arrowhead=2,
    arrowcolor="#B85C38",
    ax=70,
    ay=40,
    font={"size": 15, "color": "#B85C38"},
)

fig.add_annotation(
    x=uts_plot_strain,
    y=uts_plot_stress,
    text=f"UTS = {uts} MPa",
    showarrow=True,
    arrowhead=2,
    arrowcolor="#2E8B57",
    ax=-50,
    ay=-35,
    font={"size": 15, "color": "#2E8B57"},
)

fig.add_annotation(
    x=fracture_plot_strain,
    y=fracture_plot_stress,
    text="Fracture",
    showarrow=True,
    arrowhead=2,
    arrowcolor="#C62828",
    ax=-55,
    ay=30,
    font={"size": 15, "color": "#C62828"},
)

# Region labels
fig.add_annotation(x=0.008, y=100, text="Elastic", showarrow=False, font={"size": 14, "color": "#888888"})

fig.add_annotation(x=0.12, y=320, text="Strain Hardening", showarrow=False, font={"size": 14, "color": "#888888"})

fig.add_annotation(x=0.30, y=375, text="Necking", showarrow=False, font={"size": 14, "color": "#888888"})

# Young's modulus annotation
fig.add_annotation(
    x=yield_strain * 0.5,
    y=youngs_modulus * yield_strain * 0.5,
    text=f"E = {youngs_modulus // 1000} GPa",
    showarrow=True,
    arrowhead=0,
    arrowcolor="#306998",
    ax=60,
    ay=-25,
    font={"size": 14, "color": "#306998"},
)

# Style
fig.update_layout(
    title={"text": "Mild Steel Tensile Test · line-stress-strain · plotly · pyplots.ai", "font": {"size": 28}},
    xaxis={
        "title": {"text": "Engineering Strain", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": False,
        "zeroline": False,
        "range": [-0.01, 0.38],
    },
    yaxis={
        "title": {"text": "Engineering Stress (MPa)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.08)",
        "gridwidth": 1,
        "zeroline": False,
        "range": [-10, 460],
    },
    template="plotly_white",
    legend={
        "font": {"size": 16},
        "x": 0.35,
        "y": 0.20,
        "bgcolor": "rgba(255,255,255,0.85)",
        "bordercolor": "rgba(0,0,0,0.1)",
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    width=1600,
    height=900,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
