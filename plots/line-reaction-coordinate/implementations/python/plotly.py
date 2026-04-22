""" pyplots.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: plotly 6.6.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-21
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

# Colorblind-safe colors: blue for Ea, orange for ΔH
ea_color = "#0077BB"
dh_color = "#EE7733"

# Plot
fig = go.Figure()

# Shaded region under curve for visual polish
fig.add_trace(
    go.Scatter(
        x=reaction_coord,
        y=energy,
        mode="lines",
        line={"color": "rgba(0,0,0,0)", "width": 0},
        fill="tozeroy",
        fillcolor="rgba(48,105,152,0.06)",
        showlegend=False,
        hoverinfo="skip",
    )
)

fig.add_trace(
    go.Scatter(
        x=reaction_coord,
        y=energy,
        mode="lines",
        line={"color": "#306998", "width": 4, "shape": "spline"},
        showlegend=False,
        hovertemplate=("Reaction Coordinate: %{x:.2f}<br>Energy: %{y:.1f} kJ/mol<extra></extra>"),
    )
)

# Horizontal dashed lines at reactant and product energy levels
for x0, x1, y_level in [(-0.05, 0.28, reactant_energy), (0.72, 1.05, product_energy)]:
    fig.add_shape(
        type="line", x0=x0, x1=x1, y0=y_level, y1=y_level, line={"color": "#BBBBBB", "width": 1.5, "dash": "dash"}
    )

# Extended dashed line at reactant level on ΔH side for reference
fig.add_shape(
    type="line",
    x0=0.82,
    x1=0.94,
    y0=reactant_energy,
    y1=reactant_energy,
    line={"color": "#BBBBBB", "width": 1, "dash": "dot"},
)

# Activation energy (Ea) double-headed arrow
ea_x = 0.14
fig.add_shape(
    type="line", x0=ea_x, y0=reactant_energy, x1=ea_x, y1=transition_energy, line={"color": ea_color, "width": 2.5}
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
    arrowcolor=ea_color,
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
    arrowcolor=ea_color,
)
fig.add_annotation(
    x=ea_x,
    y=(reactant_energy + transition_energy) / 2,
    text="E<sub>a</sub> = 70 kJ/mol",
    showarrow=False,
    xanchor="right",
    xshift=-14,
    font={"size": 19, "color": ea_color, "family": "Arial Black, sans-serif"},
)

# Horizontal dashed line at transition state level (for Ea reference)
fig.add_shape(
    type="line",
    x0=ea_x - 0.02,
    x1=peak_pos + 0.08,
    y0=transition_energy,
    y1=transition_energy,
    line={"color": "#BBBBBB", "width": 1, "dash": "dot"},
)

# Enthalpy change (ΔH) double-headed arrow
dh_x = 0.88
fig.add_shape(
    type="line", x0=dh_x, y0=product_energy, x1=dh_x, y1=reactant_energy, line={"color": dh_color, "width": 2.5}
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
    arrowcolor=dh_color,
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
    arrowcolor=dh_color,
)
fig.add_annotation(
    x=dh_x,
    y=(reactant_energy + product_energy) / 2,
    text="ΔH = −30 kJ/mol",
    showarrow=False,
    xanchor="left",
    xshift=14,
    font={"size": 19, "color": dh_color, "family": "Arial Black, sans-serif"},
)

# Labels — positioned to avoid crowding with arrows
fig.add_annotation(
    x=0.02,
    y=reactant_energy,
    text="<b>Reactants</b><br>50 kJ/mol",
    showarrow=False,
    yshift=34,
    xanchor="left",
    font={"size": 18, "color": "#2D2D2D", "family": "Arial, sans-serif"},
)

peak_idx = int(np.argmax(energy))
fig.add_annotation(
    x=reaction_coord[peak_idx],
    y=energy[peak_idx],
    text="<b>Transition State</b><br>120 kJ/mol",
    showarrow=True,
    ay=-55,
    ax=40,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=2,
    arrowcolor="#555555",
    font={"size": 18, "color": "#2D2D2D", "family": "Arial, sans-serif"},
)

fig.add_annotation(
    x=0.98,
    y=product_energy,
    text="<b>Products</b><br>20 kJ/mol",
    showarrow=False,
    yshift=-32,
    xanchor="right",
    font={"size": 18, "color": "#2D2D2D", "family": "Arial, sans-serif"},
)

# Style
fig.update_layout(
    title={
        "text": "line-reaction-coordinate · plotly · pyplots.ai",
        "font": {"size": 28, "family": "Arial, sans-serif", "color": "#2D2D2D"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Reaction Coordinate", "font": {"size": 22, "family": "Arial, sans-serif"}, "standoff": 15},
        "tickfont": {"size": 18},
        "showgrid": False,
        "showticklabels": False,
        "zeroline": False,
        "range": [-0.08, 1.08],
        "showline": True,
        "linecolor": "#CCCCCC",
        "linewidth": 1,
    },
    yaxis={
        "title": {
            "text": "Potential Energy (kJ/mol)",
            "font": {"size": 22, "family": "Arial, sans-serif"},
            "standoff": 10,
        },
        "tickfont": {"size": 18},
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "zeroline": False,
        "range": [0, 140],
        "showline": True,
        "linecolor": "#CCCCCC",
        "linewidth": 1,
        "dtick": 20,
    },
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 85, "r": 60, "t": 80, "b": 65},
    font={"family": "Arial, sans-serif"},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
