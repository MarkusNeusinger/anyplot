""" pyplots.ai
arc-basic: Basic Arc Diagram
Library: plotly 6.5.2 | Python 3.14.3
Quality: 90/100 | Updated: 2026-02-23
"""

import numpy as np
import plotly.graph_objects as go


# Data: Character interactions in a story narrative
nodes = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry", "Iris", "Jack"]
n_nodes = len(nodes)

# Edges: pairs of (source_idx, target_idx, weight)
edges = [
    (0, 1, 3),  # Alice-Bob (neighbors, strong)
    (0, 3, 2),  # Alice-David
    (1, 2, 2),  # Bob-Carol
    (2, 4, 3),  # Carol-Eve (strong)
    (3, 5, 2),  # David-Frank
    (4, 6, 2),  # Eve-Grace
    (5, 7, 3),  # Frank-Henry (strong)
    (0, 8, 1),  # Alice-Iris (long, weak)
    (2, 9, 2),  # Carol-Jack (long)
    (1, 4, 2),  # Bob-Eve
    (3, 7, 1),  # David-Henry (long, weak)
    (6, 9, 2),  # Grace-Jack
]

# Node positions along horizontal axis
x_positions = np.linspace(0, 10, n_nodes)

# Weight-based styling: color intensity, opacity, and width encode connection strength
arc_styles = {
    1: {"color": "rgba(100, 149, 194, 0.50)", "width": 3.0, "label": "Weak (1)"},
    2: {"color": "rgba(48, 105, 152, 0.65)", "width": 3.5, "label": "Medium (2)"},
    3: {"color": "rgba(20, 66, 110, 0.90)", "width": 5.0, "label": "Strong (3)"},
}

# Create figure
fig = go.Figure()

# Track weight per trace for interactive filtering
trace_weights = []

# Draw arcs as smooth parabolic curves
for src, tgt, weight in edges:
    x_src, x_tgt = x_positions[src], x_positions[tgt]
    arc_height = abs(tgt - src) * 0.45

    t = np.linspace(0, 1, 50)
    x_arc = x_src + t * (x_tgt - x_src)
    y_arc = arc_height * 4 * t * (1 - t)

    style = arc_styles[weight]
    distance = abs(tgt - src)
    fig.add_trace(
        go.Scatter(
            x=x_arc,
            y=y_arc,
            mode="lines",
            line={"width": style["width"], "color": style["color"]},
            hovertemplate=(
                f"<b>{nodes[src]} \u2014 {nodes[tgt]}</b><br>"
                f"Weight: <b>{weight}</b> ({style['label'].split(' ')[0].lower()})<br>"
                f"Distance: {distance} positions<extra></extra>"
            ),
            showlegend=False,
        )
    )
    trace_weights.append(weight)

# Weight legend using dummy traces
for w in [3, 2, 1]:
    style = arc_styles[w]
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            line={"width": style["width"], "color": style["color"]},
            name=style["label"],
            showlegend=True,
        )
    )
    trace_weights.append(w)

# Compute per-node connection counts for rich hover
conn_count = [0] * n_nodes
for src, tgt, _ in edges:
    conn_count[src] += 1
    conn_count[tgt] += 1

# Draw nodes on horizontal axis
fig.add_trace(
    go.Scatter(
        x=x_positions,
        y=np.zeros(n_nodes),
        mode="markers+text",
        marker={"size": 26, "color": "#FFD43B", "line": {"width": 2.5, "color": "#306998"}},
        text=nodes,
        textposition="bottom center",
        textfont={"size": 22, "color": "#2a2a2a"},
        customdata=np.array(conn_count),
        hovertemplate="<b>%{text}</b><br>Connections: %{customdata}<extra></extra>",
        showlegend=False,
    )
)
trace_weights.append(0)  # 0 = always visible

# Subtle horizontal baseline
fig.add_shape(
    type="line", x0=x_positions[0] - 0.3, x1=x_positions[-1] + 0.3, y0=0, y1=0, line={"width": 1.5, "color": "#CCCCCC"}
)

# Annotate longest-range arc as focal point
mid_x = (x_positions[0] + x_positions[8]) / 2
peak_y = abs(8 - 0) * 0.45
fig.add_annotation(
    x=mid_x,
    y=peak_y,
    text="longest range",
    showarrow=True,
    arrowhead=2,
    arrowwidth=1.5,
    arrowcolor="#666666",
    ax=55,
    ay=-25,
    font={"size": 20, "color": "#555555", "family": "Arial"},
    bgcolor="rgba(255, 255, 255, 0.7)",
    borderpad=4,
)

# Build interactive filter buttons (Plotly-distinctive updatemenus)
filter_options = [("All", {1, 2, 3}), ("Strong", {3}), ("Medium", {2}), ("Weak", {1})]
buttons = []
for label, keep in filter_options:
    visible = [True if tw == 0 else (tw in keep) for tw in trace_weights]
    buttons.append({"label": label, "method": "update", "args": [{"visible": visible}]})

# Layout
fig.update_layout(
    title={
        "text": (
            "arc-basic \u00b7 plotly \u00b7 pyplots.ai"
            "<br><span style='font-size:18px;color:#777777;font-weight:normal'>"
            "Character interactions in a story narrative</span>"
        ),
        "font": {"size": 30, "color": "#2a2a2a"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    xaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "showline": False, "range": [-0.5, 10.5]},
    yaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "showline": False, "range": [-0.7, 4.1]},
    hovermode="closest",
    hoverlabel={"bgcolor": "white", "font_size": 16, "font_color": "#306998", "bordercolor": "#306998"},
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 30, "r": 30, "t": 90, "b": 30},
    legend={
        "title": {"text": "Connection Strength", "font": {"size": 18, "color": "#2a2a2a"}},
        "font": {"size": 16},
        "x": 0.98,
        "y": 0.98,
        "xanchor": "right",
        "yanchor": "top",
        "bgcolor": "rgba(255, 255, 255, 0.85)",
        "bordercolor": "#CCCCCC",
        "borderwidth": 1,
    },
    updatemenus=[
        {
            "type": "buttons",
            "direction": "right",
            "x": 0.02,
            "y": 0.98,
            "xanchor": "left",
            "yanchor": "top",
            "buttons": buttons,
            "showactive": True,
            "bgcolor": "rgba(255, 255, 255, 0.85)",
            "bordercolor": "#CCCCCC",
            "font": {"size": 14, "color": "#306998"},
            "pad": {"r": 8, "t": 8},
        }
    ],
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html(
    "plot.html",
    include_plotlyjs="cdn",
    config={
        "displaylogo": False,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        "toImageButtonOptions": {"width": 4800, "height": 2700, "scale": 1},
    },
)
