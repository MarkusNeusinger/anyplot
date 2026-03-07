"""pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: plotly | Python 3.13
Quality: pending | Created: 2026-03-07
"""

import numpy as np
import plotly.graph_objects as go


# Data - Electron-positron annihilation to muon pair: e⁻ e⁺ → γ* → μ⁻ μ⁺
vertices = {"v1": (0.30, 0.50), "v2": (0.70, 0.50)}

propagators = [
    {"from": (0.05, 0.85), "to": "v1", "type": "fermion", "label": "e⁻"},
    {"from": (0.05, 0.15), "to": "v1", "type": "antifermion", "label": "e⁺"},
    {"from": "v1", "to": "v2", "type": "photon", "label": "γ"},
    {"from": "v2", "to": (0.95, 0.85), "type": "fermion", "label": "μ⁻"},
    {"from": "v2", "to": (0.95, 0.15), "type": "antifermion", "label": "μ⁺"},
]

fig = go.Figure()


# Helper: resolve vertex name to coordinate
def _pos(v):
    return vertices[v] if isinstance(v, str) else v


# Draw fermion lines (straight with arrow)
for prop in propagators:
    p0 = _pos(prop["from"])
    p1 = _pos(prop["to"])

    if prop["type"] in ("fermion", "antifermion"):
        # Arrow direction: fermion flows forward, antifermion flows backward
        if prop["type"] == "antifermion":
            arrow_start, arrow_end = p1, p0
        else:
            arrow_start, arrow_end = p0, p1

        # Draw the line
        fig.add_trace(
            go.Scatter(
                x=[p0[0], p1[0]],
                y=[p0[1], p1[1]],
                mode="lines",
                line={"color": "#306998", "width": 3},
                showlegend=False,
                hovertemplate=f"<b>{prop['label']}</b><br>Type: {'Fermion' if prop['type'] == 'fermion' else 'Antifermion'}<extra></extra>",
            )
        )

        # Arrow annotation for particle flow direction
        mid_x = (arrow_start[0] + arrow_end[0]) / 2
        mid_y = (arrow_start[1] + arrow_end[1]) / 2
        dx = arrow_end[0] - arrow_start[0]
        dy = arrow_end[1] - arrow_start[1]
        arrow_tip_x = mid_x + 0.01 * dx
        arrow_tip_y = mid_y + 0.01 * dy
        fig.add_annotation(
            x=arrow_tip_x,
            y=arrow_tip_y,
            ax=mid_x - 0.03 * dx,
            ay=mid_y - 0.03 * dy,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=2,
            arrowwidth=2.5,
            arrowcolor="#306998",
            text="",
        )

    elif prop["type"] == "photon":
        # Wavy line for photon
        n_waves = 8
        t = np.linspace(0, 1, 200)
        x_line = p0[0] + t * (p1[0] - p0[0])
        y_line = p0[1] + t * (p1[1] - p0[1])
        # Perpendicular wave
        amplitude = 0.035
        wave = amplitude * np.sin(2 * np.pi * n_waves * t)
        # Add wave perpendicular to line direction
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        length = np.sqrt(dx**2 + dy**2)
        perp_x = -dy / length
        perp_y = dx / length
        x_wavy = x_line + wave * perp_x
        y_wavy = y_line + wave * perp_y

        fig.add_trace(
            go.Scatter(
                x=x_wavy,
                y=y_wavy,
                mode="lines",
                line={"color": "#C62828", "width": 3},
                showlegend=False,
                hovertemplate=f"<b>{prop['label']}</b><br>Type: Virtual Photon<extra></extra>",
            )
        )

# Vertex dots
for name, (vx, vy) in vertices.items():
    fig.add_trace(
        go.Scatter(
            x=[vx],
            y=[vy],
            mode="markers",
            marker={"size": 14, "color": "#1a1a1a", "line": {"width": 2, "color": "white"}},
            showlegend=False,
            hovertemplate=f"<b>Vertex {name}</b><br>Interaction point<extra></extra>",
        )
    )

# Particle labels
label_offsets = {"e⁻": (-0.03, 0.04), "e⁺": (-0.03, -0.05), "γ": (0.0, 0.06), "μ⁻": (0.03, 0.04), "μ⁺": (0.03, -0.05)}

for prop in propagators:
    p0 = _pos(prop["from"])
    p1 = _pos(prop["to"])
    mid_x = (p0[0] + p1[0]) / 2
    mid_y = (p0[1] + p1[1]) / 2
    offset = label_offsets.get(prop["label"], (0, 0))
    color = "#C62828" if prop["type"] == "photon" else "#306998"
    fig.add_annotation(
        x=mid_x + offset[0],
        y=mid_y + offset[1],
        text=f"<b>{prop['label']}</b>",
        showarrow=False,
        font={"size": 22, "color": color},
        xanchor="center",
        yanchor="middle",
    )

# Time axis arrow
fig.add_annotation(
    x=0.95,
    y=-0.02,
    ax=0.05,
    ay=-0.02,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=1.5,
    arrowcolor="#999",
    text="",
)
fig.add_annotation(
    x=0.50, y=-0.06, text="<i>time</i>", showarrow=False, font={"size": 18, "color": "#999"}, xanchor="center"
)

# Layout
fig.update_layout(
    title={
        "text": "e⁻e⁺ → μ⁻μ⁺ Annihilation · feynman-basic · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"visible": False, "range": [-0.05, 1.05], "fixedrange": True},
    yaxis={"visible": False, "range": [-0.12, 1.05], "fixedrange": True, "scaleanchor": "x"},
    template="plotly_white",
    plot_bgcolor="white",
    margin={"l": 40, "r": 40, "t": 80, "b": 40},
    showlegend=False,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
