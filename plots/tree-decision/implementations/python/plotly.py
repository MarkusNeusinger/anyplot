""" pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: plotly 6.6.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-06
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

# Layout positions (x, y) - left-to-right tree with adjusted spacing
positions = {
    "D1": (0.0, 0.50),
    "C1": (0.35, 0.84),
    "T1": (0.72, 0.96),
    "T2": (0.72, 0.72),
    "C2": (0.35, 0.33),
    "T3": (0.72, 0.46),
    "T4": (0.72, 0.20),
    "T5": (0.35, 0.05),
}

# Colors
decision_color = "#306998"
chance_color = "#E8833A"
terminal_color = "#4CAF50"
pruned_color = "#9E9E9E"
optimal_edge = "#2D5F8A"
bg_color = "#FAFBFC"

# Plot
fig = go.Figure()

# Draw edges (branches) with hover text built inline
for nid, n in nodes.items():
    if n["parent"] is None:
        continue
    px, py = positions[n["parent"]]
    cx, cy = positions[nid]
    line_color = pruned_color if n["pruned"] else optimal_edge
    dash = "dash" if n["pruned"] else "solid"
    line_width = 2.5 if n["pruned"] else 4
    opacity = 0.5 if n["pruned"] else 1.0

    # Build hover text for this edge
    hover_parts = [f"<b>{n['label'] or ''}</b>"]
    if n["prob"] is not None:
        hover_parts.append(f"Probability: {n['prob']:.0%}")
    if n["payoff"] is not None:
        hover_parts.append(f"Payoff: ${n['payoff']:+,}")
    if n["pruned"]:
        hover_parts.append("<i>Pruned (suboptimal)</i>")
    edge_hover = "<br>".join(hover_parts)

    fig.add_trace(
        go.Scatter(
            x=[px, cx],
            y=[py, cy],
            mode="lines",
            line={"color": line_color, "width": line_width, "dash": dash},
            opacity=opacity,
            hoverinfo="text",
            hovertext=[edge_hover, edge_hover],
            showlegend=False,
        )
    )

    # Branch label with adjusted positioning to avoid crowding
    t = 0.42 if n["parent"] == "D1" else 0.5
    mid_x = px + (cx - px) * t
    mid_y = py + (cy - py) * t
    label_text = n["label"] or ""
    if n["prob"] is not None:
        label_text = f"{n['label']} (p={n['prob']})"
    text_color = pruned_color if n["pruned"] else "#2B2B2B"

    # Adjust yshift based on branch direction to prevent crowding
    yshift = 22
    if nid == "T5":
        yshift = -18
    elif nid == "C2":
        yshift = -18

    fig.add_annotation(
        x=mid_x,
        y=mid_y,
        text=f"<b>{label_text}</b>",
        showarrow=False,
        font={"size": 20, "color": text_color, "family": "Arial, sans-serif"},
        yshift=yshift,
    )

# Draw pruned marks on pruned branches
for nid, n in nodes.items():
    if not n["pruned"] or n["parent"] is None:
        continue
    px, py = positions[n["parent"]]
    cx, cy = positions[nid]
    mark_x = px + (cx - px) * 0.18
    mark_y = py + (cy - py) * 0.18

    fig.add_annotation(
        x=mark_x, y=mark_y, text="//", showarrow=False, font={"size": 26, "color": "#CC0000", "family": "Arial Black"}
    )


# Helper to get node color
def _node_color(n):
    if n["pruned"]:
        return pruned_color
    if n["type"] == "decision":
        return decision_color
    if n["type"] == "chance":
        return chance_color
    return terminal_color


# Draw nodes using add_shape for precise geometric rendering + scatter with hovertemplate
shape_size_x = 0.032
shape_size_y = 0.05

for nid, n in nodes.items():
    nx, ny = positions[nid]
    node_color = _node_color(n)
    node_opacity = 0.65 if n["pruned"] else 1.0

    # Build hover text for this node
    hover_parts = [f"<b>{nid}</b> — {n['type'].title()} Node"]
    if n["emv"] is not None:
        hover_parts.append(f"EMV: <b>${n['emv']:,}</b>")
    if n["payoff"] is not None:
        hover_parts.append(f"Payoff: <b>${n['payoff']:+,}</b>")
    if n["prob"] is not None:
        hover_parts.append(f"Probability: {n['prob']:.0%}")
    if n["label"]:
        hover_parts.append(f"Branch: {n['label']}")
    if n["pruned"]:
        hover_parts.append("<i>Pruned (suboptimal path)</i>")
    elif n["type"] != "terminal":
        hover_parts.append("<i>Optimal path</i>")
    node_hover = "<br>".join(hover_parts)

    if n["type"] == "decision":
        fig.add_shape(
            type="rect",
            x0=nx - shape_size_x,
            y0=ny - shape_size_y,
            x1=nx + shape_size_x,
            y1=ny + shape_size_y,
            fillcolor=node_color,
            opacity=node_opacity,
            line={"color": "white", "width": 2.5},
            xref="x",
            yref="y",
        )
    elif n["type"] == "chance":
        fig.add_shape(
            type="circle",
            x0=nx - shape_size_x,
            y0=ny - shape_size_y,
            x1=nx + shape_size_x,
            y1=ny + shape_size_y,
            fillcolor=node_color,
            opacity=node_opacity,
            line={"color": "white", "width": 2.5},
            xref="x",
            yref="y",
        )
    else:
        # Terminal: right-pointing triangle marker
        fig.add_trace(
            go.Scatter(
                x=[nx],
                y=[ny],
                mode="markers",
                marker={
                    "size": 52,
                    "color": node_color,
                    "symbol": "triangle-right",
                    "line": {"color": "white", "width": 2.5},
                    "opacity": node_opacity,
                },
                hoverinfo="text",
                hovertext=[node_hover],
                hoverlabel={"bgcolor": node_color, "font_size": 15, "font_color": "white"},
                showlegend=False,
            )
        )

    # Invisible scatter for hover on decision/chance nodes (shapes don't support hover)
    if n["type"] in ("decision", "chance"):
        fig.add_trace(
            go.Scatter(
                x=[nx],
                y=[ny],
                mode="markers",
                marker={"size": 50, "color": "rgba(0,0,0,0)", "symbol": "square"},
                hoverinfo="text",
                hovertext=[node_hover],
                hoverlabel={"bgcolor": node_color, "font_size": 15, "font_color": "white"},
                showlegend=False,
            )
        )

    # EMV inside decision/chance nodes
    if n["emv"] is not None:
        emv_color = "#333333" if n["pruned"] else "white"
        fig.add_annotation(
            x=nx,
            y=ny,
            text=f"<b>${n['emv']}</b>",
            showarrow=False,
            font={"size": 20, "color": emv_color, "family": "Arial, sans-serif"},
        )

    # Payoff at terminal nodes
    if n["payoff"] is not None:
        display_color = pruned_color if n["pruned"] else "#2B2B2B"
        fig.add_annotation(
            x=nx,
            y=ny,
            text=f"<b>${n['payoff']:+,}</b>",
            showarrow=False,
            font={"size": 20, "color": display_color, "family": "Arial, sans-serif"},
            xshift=58,
        )

# Legend entries using grouped legendgroup for organization
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

# Style using update_layout with plotly_white template
fig.update_layout(
    title={
        "text": (
            "Product Launch Decision · tree-decision · plotly · pyplots.ai"
            "<br><sup style='color:#666; font-size:16px'>"
            "Optimal path maximizes EMV at $280K · Pruned branches marked with //</sup>"
        ),
        "font": {"size": 28, "color": "#2B2B2B", "family": "Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    template="plotly_white",
    width=1600,
    height=900,
    xaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "showline": False, "range": [-0.08, 0.95]},
    yaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "showline": False, "range": [-0.05, 1.08]},
    legend={
        "font": {"size": 17, "family": "Arial, sans-serif"},
        "x": 0.01,
        "y": 0.01,
        "xanchor": "left",
        "yanchor": "bottom",
        "bgcolor": "rgba(255,255,255,0.92)",
        "bordercolor": "#CCCCCC",
        "borderwidth": 1,
        "itemsizing": "constant",
    },
    margin={"l": 40, "r": 60, "t": 100, "b": 30},
    plot_bgcolor=bg_color,
    paper_bgcolor="white",
    hoverlabel={"font_size": 15},
    hovermode="closest",
)

# Save static PNG
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML with all hover already configured
fig.write_html("plot.html", include_plotlyjs="cdn")
