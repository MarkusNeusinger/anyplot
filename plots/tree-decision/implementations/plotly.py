""" pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: plotly 6.6.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-06
"""

import plotly.graph_objects as go


# Data - Two-stage product launch investment decision
nodes = {
    "D1": {
        "type": "decision",
        "parent": None,
        "label": None,
        "prob": None,
        "payoff": None,
        "emv": 280,
        "pruned": False,
    },
    "C1": {
        "type": "chance",
        "parent": "D1",
        "label": "Launch Product",
        "prob": None,
        "payoff": None,
        "emv": 280,
        "pruned": False,
    },
    "T1": {
        "type": "terminal",
        "parent": "C1",
        "label": "High Demand",
        "prob": 0.6,
        "payoff": 500,
        "emv": None,
        "pruned": False,
    },
    "T2": {
        "type": "terminal",
        "parent": "C1",
        "label": "Low Demand",
        "prob": 0.4,
        "payoff": -50,
        "emv": None,
        "pruned": False,
    },
    "C2": {
        "type": "chance",
        "parent": "D1",
        "label": "License Tech",
        "prob": None,
        "payoff": None,
        "emv": 170,
        "pruned": True,
    },
    "T3": {
        "type": "terminal",
        "parent": "C2",
        "label": "Accepted",
        "prob": 0.7,
        "payoff": 200,
        "emv": None,
        "pruned": True,
    },
    "T4": {
        "type": "terminal",
        "parent": "C2",
        "label": "Rejected",
        "prob": 0.3,
        "payoff": 100,
        "emv": None,
        "pruned": True,
    },
    "T5": {
        "type": "terminal",
        "parent": "D1",
        "label": "Do Nothing",
        "prob": None,
        "payoff": 0,
        "emv": None,
        "pruned": True,
    },
}

# Layout positions (x, y) - left-to-right tree
positions = {
    "D1": (0.0, 0.5),
    "C1": (0.35, 0.80),
    "T1": (0.72, 0.95),
    "T2": (0.72, 0.65),
    "C2": (0.35, 0.32),
    "T3": (0.72, 0.44),
    "T4": (0.72, 0.20),
    "T5": (0.35, 0.05),
}

# Colors
decision_color = "#306998"
chance_color = "#E8833A"
terminal_color = "#4CAF50"
pruned_color = "#B0B0B0"

# Plot
fig = go.Figure()

# Draw edges (branches)
for nid, n in nodes.items():
    if n["parent"] is None:
        continue
    px, py = positions[n["parent"]]
    cx, cy = positions[nid]
    line_color = pruned_color if n["pruned"] else "#555555"
    dash = "dash" if n["pruned"] else "solid"
    opacity = 0.4 if n["pruned"] else 1.0

    fig.add_trace(
        go.Scatter(
            x=[px, cx],
            y=[py, cy],
            mode="lines",
            line={"color": line_color, "width": 3, "dash": dash},
            opacity=opacity,
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Branch label
    mid_x = (px + cx) / 2
    mid_y = (py + cy) / 2
    label_text = n["label"] or ""
    if n["prob"] is not None:
        label_text = f"{n['label']} (p={n['prob']})"
    text_color = pruned_color if n["pruned"] else "#333333"

    fig.add_annotation(
        x=mid_x,
        y=mid_y,
        text=f"<b>{label_text}</b>",
        showarrow=False,
        font={"size": 15, "color": text_color},
        yshift=16,
    )

# Draw pruned marks on pruned branches
for nid, n in nodes.items():
    if not n["pruned"] or n["parent"] is None:
        continue
    px, py = positions[n["parent"]]
    cx, cy = positions[nid]
    mark_x = px + (cx - px) * 0.2
    mark_y = py + (cy - py) * 0.2

    fig.add_annotation(
        x=mark_x, y=mark_y, text="//", showarrow=False, font={"size": 22, "color": "#CC0000", "family": "Arial Black"}
    )

# Draw nodes
node_size = 42
for nid, n in nodes.items():
    nx, ny = positions[nid]
    node_color = (
        pruned_color
        if n["pruned"]
        else (decision_color if n["type"] == "decision" else chance_color if n["type"] == "chance" else terminal_color)
    )
    node_opacity = 0.5 if n["pruned"] else 1.0

    if n["type"] == "decision":
        symbol = "square"
    elif n["type"] == "chance":
        symbol = "circle"
    else:
        symbol = "triangle-right"

    fig.add_trace(
        go.Scatter(
            x=[nx],
            y=[ny],
            mode="markers",
            marker={
                "size": node_size,
                "color": node_color,
                "symbol": symbol,
                "line": {"color": "white", "width": 2},
                "opacity": node_opacity,
            },
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # EMV inside decision/chance nodes
    if n["emv"] is not None:
        fig.add_annotation(x=nx, y=ny, text=f"<b>${n['emv']}</b>", showarrow=False, font={"size": 13, "color": "white"})

    # Payoff at terminal nodes
    if n["payoff"] is not None:
        display_color = pruned_color if n["pruned"] else "#333333"
        fig.add_annotation(
            x=nx,
            y=ny,
            text=f"<b>${n['payoff']:+,}</b>",
            showarrow=False,
            font={"size": 16, "color": display_color},
            xshift=52,
        )

# Legend entries for node types
for name, color, symbol in [
    ("Decision Node", decision_color, "square"),
    ("Chance Node", chance_color, "circle"),
    ("Terminal Node", terminal_color, "triangle-right"),
]:
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker={"size": 16, "color": color, "symbol": symbol, "line": {"color": "white", "width": 1}},
            name=name,
            showlegend=True,
        )
    )

fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="lines",
        line={"color": pruned_color, "width": 3, "dash": "dash"},
        name="Pruned Branch",
        showlegend=True,
    )
)

# Style
fig.update_layout(
    title={
        "text": "Product Launch Decision · tree-decision · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    template="plotly_white",
    width=1600,
    height=900,
    xaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-0.08, 0.95]},
    yaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-0.02, 1.08]},
    legend={
        "font": {"size": 16},
        "x": 0.01,
        "y": 0.01,
        "xanchor": "left",
        "yanchor": "bottom",
        "bgcolor": "rgba(255,255,255,0.8)",
        "bordercolor": "#CCCCCC",
        "borderwidth": 1,
    },
    margin={"l": 40, "r": 60, "t": 100, "b": 40},
    plot_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
