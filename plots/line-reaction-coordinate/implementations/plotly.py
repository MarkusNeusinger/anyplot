"""pyplots.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: plotly | Python 3.13
Quality: pending | Created: 2026-03-21
"""

import numpy as np
import plotly.graph_objects as go


# Data
reactant_energy = 50.0
transition_energy = 120.0
product_energy = 20.0
peak_pos = 0.4

reaction_coord = np.linspace(0, 1, 500)

baseline = reactant_energy + (product_energy - reactant_energy) * (3 * reaction_coord**2 - 2 * reaction_coord**3)

barrier_height = transition_energy - (
    reactant_energy + (product_energy - reactant_energy) * (3 * peak_pos**2 - 2 * peak_pos**3)
)
gaussian_bump = barrier_height * np.exp(-((reaction_coord - peak_pos) ** 2) / (2 * 0.018))

energy = baseline + gaussian_bump

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=reaction_coord,
        y=energy,
        mode="lines",
        line={"color": "#306998", "width": 4},
        showlegend=False,
        hovertemplate="Reaction Coordinate: %{x:.2f}<br>Energy: %{y:.1f} kJ/mol<extra></extra>",
    )
)

# Horizontal dashed lines at reactant and product energy levels
fig.add_shape(
    type="line",
    x0=-0.05,
    x1=0.3,
    y0=reactant_energy,
    y1=reactant_energy,
    line={"color": "#AAAAAA", "width": 1.5, "dash": "dash"},
)
fig.add_shape(
    type="line",
    x0=0.7,
    x1=1.05,
    y0=product_energy,
    y1=product_energy,
    line={"color": "#AAAAAA", "width": 1.5, "dash": "dash"},
)

# Activation energy (Ea) double-headed arrow
ea_x = 0.12
fig.add_shape(
    type="line", x0=ea_x, y0=reactant_energy, x1=ea_x, y1=transition_energy, line={"color": "#D9534F", "width": 2.5}
)
fig.add_annotation(
    x=ea_x,
    y=transition_energy,
    ax=0,
    ay=-14,
    text="",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2.5,
    arrowcolor="#D9534F",
)
fig.add_annotation(
    x=ea_x,
    y=reactant_energy,
    ax=0,
    ay=14,
    text="",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2.5,
    arrowcolor="#D9534F",
)
fig.add_annotation(
    x=ea_x,
    y=(reactant_energy + transition_energy) / 2,
    text="E<sub>a</sub> = 70 kJ/mol",
    showarrow=False,
    xanchor="right",
    xshift=-14,
    font={"size": 18, "color": "#D9534F"},
)

# Horizontal dashed line at transition state level (for Ea reference)
fig.add_shape(
    type="line",
    x0=ea_x - 0.02,
    x1=peak_pos + 0.08,
    y0=transition_energy,
    y1=transition_energy,
    line={"color": "#AAAAAA", "width": 1, "dash": "dot"},
)

# Enthalpy change (ΔH) double-headed arrow
dh_x = 0.88
fig.add_shape(
    type="line", x0=dh_x, y0=product_energy, x1=dh_x, y1=reactant_energy, line={"color": "#5CB85C", "width": 2.5}
)
fig.add_annotation(
    x=dh_x,
    y=reactant_energy,
    ax=0,
    ay=-14,
    text="",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2.5,
    arrowcolor="#5CB85C",
)
fig.add_annotation(
    x=dh_x,
    y=product_energy,
    ax=0,
    ay=14,
    text="",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2.5,
    arrowcolor="#5CB85C",
)
fig.add_annotation(
    x=dh_x,
    y=(reactant_energy + product_energy) / 2,
    text="ΔH = −30 kJ/mol",
    showarrow=False,
    xanchor="left",
    xshift=14,
    font={"size": 18, "color": "#5CB85C"},
)

# Labels
fig.add_annotation(
    x=0.0,
    y=reactant_energy,
    text="Reactants<br>(50 kJ/mol)",
    showarrow=False,
    yshift=28,
    font={"size": 19, "color": "#333333"},
)

peak_idx = int(np.argmax(energy))
fig.add_annotation(
    x=reaction_coord[peak_idx],
    y=energy[peak_idx],
    text="Transition State<br>(120 kJ/mol)",
    showarrow=True,
    ay=-50,
    ax=30,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=2,
    arrowcolor="#555555",
    font={"size": 19, "color": "#333333"},
)

fig.add_annotation(
    x=1.0,
    y=product_energy,
    text="Products<br>(20 kJ/mol)",
    showarrow=False,
    yshift=-28,
    font={"size": 19, "color": "#333333"},
)

# Style
fig.update_layout(
    title={"text": "line-reaction-coordinate · plotly · pyplots.ai", "font": {"size": 28}},
    xaxis={
        "title": {"text": "Reaction Coordinate", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": False,
        "showticklabels": False,
        "zeroline": False,
        "range": [-0.08, 1.08],
    },
    yaxis={
        "title": {"text": "Potential Energy (kJ/mol)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(0,0,0,0.08)",
        "gridwidth": 1,
        "zeroline": False,
        "range": [0, 140],
    },
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 80, "r": 80, "t": 80, "b": 60},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
