""" pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: plotly 6.6.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-07
"""

import numpy as np
import plotly.graph_objects as go


# Data - Gluon fusion Higgs production with diphoton decay: gg → H → γγ (via top loop)
# Showcases all 4 particle types: fermion (straight), photon (wavy), gluon (curly), boson (dashed)
vertices = {
    "v1": (0.20, 0.72),  # top of top-quark triangle
    "v2": (0.20, 0.28),  # bottom of top-quark triangle
    "v3": (0.44, 0.50),  # right of triangle (Higgs emission)
    "v4": (0.72, 0.50),  # Higgs decay vertex
}

propagators = [
    {"from": (0.02, 0.84), "to": "v1", "type": "gluon", "label": "g"},
    {"from": (0.02, 0.16), "to": "v2", "type": "gluon", "label": "g"},
    {"from": "v1", "to": "v2", "type": "fermion", "label": "t"},
    {"from": "v2", "to": "v3", "type": "fermion", "label": "t"},
    {"from": "v3", "to": "v1", "type": "fermion", "label": "t̄"},
    {"from": "v3", "to": "v4", "type": "boson", "label": "H"},
    {"from": "v4", "to": (0.96, 0.82), "type": "photon", "label": "γ"},
    {"from": "v4", "to": (0.96, 0.18), "type": "photon", "label": "γ"},
]

# Label offsets per propagator (dx, dy from midpoint)
label_offsets = [
    (-0.05, 0.05),  # g (top)
    (-0.05, -0.06),  # g (bottom)
    (-0.06, 0.0),  # t (left side, vertical)
    (0.0, -0.06),  # t (bottom-right diagonal)
    (0.0, 0.06),  # t̄ (top-right diagonal)
    (0.0, 0.06),  # H (above)
    (-0.03, 0.045),  # γ (upper-right)
    (-0.03, -0.055),  # γ (lower-right)
]

# Colors per particle type
COLORS = {"fermion": "#306998", "gluon": "#2E7D32", "photon": "#C62828", "boson": "#7B1FA2"}
LINE_W = 4

fig = go.Figure()

for i, prop in enumerate(propagators):
    p0 = vertices[prop["from"]] if isinstance(prop["from"], str) else prop["from"]
    p1 = vertices[prop["to"]] if isinstance(prop["to"], str) else prop["to"]
    color = COLORS[prop["type"]]
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = np.sqrt(dx**2 + dy**2)

    if prop["type"] == "fermion":
        fig.add_trace(
            go.Scatter(
                x=[p0[0], p1[0]],
                y=[p0[1], p1[1]],
                mode="lines",
                line={"color": color, "width": LINE_W},
                showlegend=False,
                hovertemplate=f"<b>{prop['label']}</b><br>Top quark (fermion)<extra></extra>",
            )
        )
        # Prominent flow arrow at midpoint
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        ndx, ndy = dx / length, dy / length
        fig.add_annotation(
            x=mx + 0.018 * ndx,
            y=my + 0.018 * ndy,
            ax=mx - 0.05 * ndx,
            ay=my - 0.05 * ndy,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=3,
            arrowsize=2.5,
            arrowwidth=3.5,
            arrowcolor=color,
            text="",
        )

    elif prop["type"] == "photon":
        t = np.linspace(0, 1, 400)
        perp_x, perp_y = -dy / length, dx / length
        amp = 0.032
        taper = np.minimum(t / 0.07, 1.0) * np.minimum((1 - t) / 0.07, 1.0)
        wave = amp * np.sin(2 * np.pi * 10 * t) * taper
        fig.add_trace(
            go.Scatter(
                x=p0[0] + t * dx + wave * perp_x,
                y=p0[1] + t * dy + wave * perp_y,
                mode="lines",
                line={"color": color, "width": LINE_W},
                showlegend=False,
                hovertemplate=f"<b>{prop['label']}</b><br>Photon<extra></extra>",
            )
        )

    elif prop["type"] == "gluon":
        t = np.linspace(0, 1, 800)
        dir_x, dir_y = dx / length, dy / length
        perp_x, perp_y = -dy / length, dx / length
        amp = 0.032
        n_loops = 7
        theta = 2 * np.pi * n_loops * t
        taper = np.minimum(t / 0.07, 1.0) * np.minimum((1 - t) / 0.07, 1.0)
        # Perpendicular + parallel displacement creates curly loops
        perp_disp = amp * np.sin(theta) * taper
        para_disp = amp * 0.45 * (1 - np.cos(theta)) * taper
        fig.add_trace(
            go.Scatter(
                x=p0[0] + t * dx + perp_disp * perp_x - para_disp * dir_x,
                y=p0[1] + t * dy + perp_disp * perp_y - para_disp * dir_y,
                mode="lines",
                line={"color": color, "width": LINE_W},
                showlegend=False,
                hovertemplate=f"<b>{prop['label']}</b><br>Gluon<extra></extra>",
            )
        )

    elif prop["type"] == "boson":
        fig.add_trace(
            go.Scatter(
                x=[p0[0], p1[0]],
                y=[p0[1], p1[1]],
                mode="lines",
                line={"color": color, "width": LINE_W, "dash": "10px,6px"},
                showlegend=False,
                hovertemplate=f"<b>{prop['label']}</b><br>Higgs boson (scalar)<extra></extra>",
            )
        )

    # Particle label
    mx = (p0[0] + p1[0]) / 2 + label_offsets[i][0]
    my = (p0[1] + p1[1]) / 2 + label_offsets[i][1]
    fig.add_annotation(
        x=mx,
        y=my,
        text=f"<b>{prop['label']}</b>",
        showarrow=False,
        font={"size": 24, "color": color, "family": "serif"},
        xanchor="center",
        yanchor="middle",
    )

# Vertex dots
for name, (vx, vy) in vertices.items():
    fig.add_trace(
        go.Scatter(
            x=[vx],
            y=[vy],
            mode="markers",
            marker={"size": 16, "color": "#1a1a1a", "line": {"width": 2.5, "color": "white"}},
            showlegend=False,
            hovertemplate=f"<b>Vertex {name}</b><br>Interaction point<extra></extra>",
        )
    )

# Line style legend (bottom-right)
legend_x0, legend_y = 0.62, 0.08
legend_entries = [
    ("fermion", "Fermion (straight)", COLORS["fermion"]),
    ("photon", "Photon (wavy)", COLORS["photon"]),
    ("gluon", "Gluon (curly)", COLORS["gluon"]),
    ("boson", "Boson (dashed)", COLORS["boson"]),
]
for j, (ptype, desc, col) in enumerate(legend_entries):
    lx = legend_x0
    ly = legend_y - j * 0.055
    dash = "10px,6px" if ptype == "boson" else None
    if ptype in ("fermion", "boson"):
        fig.add_shape(type="line", x0=lx, y0=ly, x1=lx + 0.06, y1=ly, line={"color": col, "width": 3, "dash": dash})
    elif ptype == "photon":
        ts = np.linspace(0, 1, 100)
        w = 0.012 * np.sin(2 * np.pi * 5 * ts)
        fig.add_trace(
            go.Scatter(
                x=lx + ts * 0.06,
                y=ly + w,
                mode="lines",
                line={"color": col, "width": 2.5},
                showlegend=False,
                hoverinfo="skip",
            )
        )
    elif ptype == "gluon":
        ts = np.linspace(0, 1, 200)
        theta_s = 2 * np.pi * 4 * ts
        tp = np.minimum(ts / 0.1, 1.0) * np.minimum((1 - ts) / 0.1, 1.0)
        fig.add_trace(
            go.Scatter(
                x=lx + ts * 0.06 - 0.005 * (1 - np.cos(theta_s)) * tp,
                y=ly + 0.012 * np.sin(theta_s) * tp,
                mode="lines",
                line={"color": col, "width": 2.5},
                showlegend=False,
                hoverinfo="skip",
            )
        )
    fig.add_annotation(
        x=lx + 0.07, y=ly, text=desc, showarrow=False, font={"size": 16, "color": col}, xanchor="left", yanchor="middle"
    )

# Time axis arrow
fig.add_annotation(
    x=0.55,
    y=-0.04,
    ax=0.02,
    ay=-0.04,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=2,
    arrowsize=2,
    arrowwidth=2,
    arrowcolor="#888",
    text="",
)
fig.add_annotation(
    x=0.285, y=-0.075, text="<i>time</i>", showarrow=False, font={"size": 20, "color": "#888"}, xanchor="center"
)

# Layout
fig.update_layout(
    title={
        "text": "gg → H → γγ (Gluon Fusion) · feynman-basic · plotly · pyplots.ai",
        "font": {"size": 30, "family": "serif"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"visible": False, "range": [-0.04, 1.04], "fixedrange": True},
    yaxis={"visible": False, "range": [-0.12, 1.0], "fixedrange": True, "scaleanchor": "x"},
    template="plotly_white",
    plot_bgcolor="white",
    margin={"l": 30, "r": 30, "t": 75, "b": 30},
    showlegend=False,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
