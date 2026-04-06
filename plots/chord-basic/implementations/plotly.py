""" pyplots.ai
chord-basic: Basic Chord Diagram
Library: plotly 6.5.2 | Python 3.14
Quality: 82/100 | Updated: 2026-04-06
"""

import numpy as np
import plotly.graph_objects as go


# Data: Migration flows between 6 continents (bidirectional, millions of people)
continents = ["Africa", "Asia", "Europe", "N. America", "S. America", "Oceania"]
n = len(continents)

# Flow matrix (row = source, col = target) - realistic migration patterns
flow_matrix = np.array(
    [
        [0, 15, 25, 10, 5, 3],  # Africa to others
        [12, 0, 30, 20, 8, 15],  # Asia to others
        [20, 35, 0, 25, 12, 10],  # Europe to others
        [8, 18, 22, 0, 15, 5],  # N. America to others
        [6, 10, 18, 20, 0, 4],  # S. America to others
        [2, 12, 8, 6, 3, 0],  # Oceania to others
    ]
)

# Colors for each continent (Python Blue first, then colorblind-safe palette)
colors = ["#306998", "#FFD43B", "#2E8B57", "#DC143C", "#9370DB", "#FF8C00"]

# Calculate totals for each continent
totals = flow_matrix.sum(axis=0) + flow_matrix.sum(axis=1)
total_flow = flow_matrix.sum()

# Calculate arc positions around the circle
gap = 0.02
arc_starts = []
arc_ends = []
current_pos = 0
for total in totals:
    arc_starts.append(current_pos)
    arc_ends.append(current_pos + (total / total_flow) * (1 - n * gap))
    current_pos = arc_ends[-1] + gap

# Create figure
fig = go.Figure()

# Draw outer arcs for each continent
for i in range(n):
    angles_outer = np.linspace(2 * np.pi * arc_starts[i] - np.pi / 2, 2 * np.pi * arc_ends[i] - np.pi / 2, 100)
    x_outer = 1.0 * np.cos(angles_outer)
    y_outer = 1.0 * np.sin(angles_outer)

    angles_inner = np.linspace(2 * np.pi * arc_ends[i] - np.pi / 2, 2 * np.pi * arc_starts[i] - np.pi / 2, 100)
    x_inner = 0.95 * np.cos(angles_inner)
    y_inner = 0.95 * np.sin(angles_inner)

    fig.add_trace(
        go.Scatter(
            x=np.concatenate([x_outer, x_inner]),
            y=np.concatenate([y_outer, y_inner]),
            fill="toself",
            fillcolor=colors[i],
            line={"color": "white", "width": 1},
            hovertemplate=(f"<b>{continents[i]}</b><br>Total flow: {int(totals[i])}M people<extra></extra>"),
            name=continents[i],
            showlegend=True,
        )
    )

# Draw chords as interactive traces (not shapes) for hover support
for i in range(n):
    src_pos = arc_starts[i]
    for j in range(n):
        if i == j or flow_matrix[i, j] == 0:
            continue

        flow = flow_matrix[i, j]
        chord_width = (flow / total_flow) * (1 - n * gap)

        # Target position offset based on prior incoming flows
        tgt_base = arc_starts[j]
        tgt_offset = sum((flow_matrix[k, j] / total_flow) * (1 - n * gap) for k in range(i) if flow_matrix[k, j] > 0)

        # Source arc endpoints
        src_angle1 = 2 * np.pi * src_pos - np.pi / 2
        src_angle2 = 2 * np.pi * (src_pos + chord_width) - np.pi / 2
        sx1, sy1 = 0.95 * np.cos(src_angle1), 0.95 * np.sin(src_angle1)
        sx2, sy2 = 0.95 * np.cos(src_angle2), 0.95 * np.sin(src_angle2)

        # Target arc endpoints
        tgt_start = tgt_base + tgt_offset
        tgt_end = tgt_start + chord_width
        tgt_angle1 = 2 * np.pi * tgt_start - np.pi / 2
        tgt_angle2 = 2 * np.pi * tgt_end - np.pi / 2
        tx1, ty1 = 0.95 * np.cos(tgt_angle1), 0.95 * np.sin(tgt_angle1)
        tx2, ty2 = 0.95 * np.cos(tgt_angle2), 0.95 * np.sin(tgt_angle2)

        # Build chord path: source arc -> bezier to target -> target arc -> bezier back
        # Source side arc points
        src_angles = np.linspace(src_angle1, src_angle2, 20)
        src_x = 0.95 * np.cos(src_angles)
        src_y = 0.95 * np.sin(src_angles)

        # Bezier from source end to target start (through center)
        t = np.linspace(0, 1, 30)
        bez1_x = (1 - t) ** 2 * sx2 + 2 * (1 - t) * t * 0 + t**2 * tx1
        bez1_y = (1 - t) ** 2 * sy2 + 2 * (1 - t) * t * 0 + t**2 * ty1

        # Target side arc points
        tgt_angles = np.linspace(tgt_angle1, tgt_angle2, 20)
        tgt_x = 0.95 * np.cos(tgt_angles)
        tgt_y = 0.95 * np.sin(tgt_angles)

        # Bezier from target end back to source start (through center)
        bez2_x = (1 - t) ** 2 * tx2 + 2 * (1 - t) * t * 0 + t**2 * sx1
        bez2_y = (1 - t) ** 2 * ty2 + 2 * (1 - t) * t * 0 + t**2 * sy1

        # Combine into closed polygon
        chord_x = np.concatenate([src_x, bez1_x, tgt_x, bez2_x])
        chord_y = np.concatenate([src_y, bez1_y, tgt_y, bez2_y])

        fig.add_trace(
            go.Scatter(
                x=chord_x,
                y=chord_y,
                fill="toself",
                fillcolor=colors[i],
                opacity=0.55,
                line={"color": colors[i], "width": 0.5},
                hovertemplate=(f"<b>{continents[i]} → {continents[j]}</b><br>Flow: {flow}M people<extra></extra>"),
                showlegend=False,
                hoveron="fills",
            )
        )

        src_pos += chord_width

# Add continent labels around the perimeter
for i in range(n):
    mid_pos = (arc_starts[i] + arc_ends[i]) / 2
    angle = 2 * np.pi * mid_pos - np.pi / 2
    label_radius = 1.12

    text_angle_deg = np.degrees(angle)
    if 90 < text_angle_deg < 270 or -270 < text_angle_deg < -90:
        text_angle_deg += 180
    rotation = -text_angle_deg + 90 if -90 < np.degrees(angle) < 90 else -text_angle_deg - 90

    fig.add_annotation(
        x=label_radius * np.cos(angle),
        y=label_radius * np.sin(angle),
        text=f"<b>{continents[i]}</b>",
        font={"size": 22, "color": colors[i]},
        showarrow=False,
        textangle=rotation,
    )

# Layout
fig.update_layout(
    title={
        "text": "Migration Flows Between Continents · chord-basic · plotly · pyplots.ai",
        "font": {"size": 30, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    xaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-1.35, 1.35]},
    yaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-1.35, 1.35], "scaleanchor": "x"},
    template="plotly_white",
    showlegend=True,
    legend={"font": {"size": 18}, "x": 1.01, "y": 0.5, "yanchor": "middle", "tracegroupgap": 5},
    margin={"l": 30, "r": 160, "t": 80, "b": 30},
    plot_bgcolor="white",
    paper_bgcolor="white",
    hovermode="closest",
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
