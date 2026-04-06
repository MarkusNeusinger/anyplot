"""pyplots.ai
chord-basic: Basic Chord Diagram
Library: plotly 6.5.2 | Python 3.14
Quality: 88/100 | Updated: 2026-04-06
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

# Colors: Python Blue first, then colorblind-safe palette
# Replaced green (#2E8B57) with teal (#00B4D8) for deuteranopia accessibility
colors = ["#306998", "#FFD43B", "#00B4D8", "#DC143C", "#9370DB", "#FF8C00"]
colors_dim = [
    "rgba(48,105,152,0.4)",
    "rgba(255,212,59,0.4)",
    "rgba(0,180,216,0.4)",
    "rgba(220,20,60,0.4)",
    "rgba(147,112,219,0.4)",
    "rgba(255,140,0,0.4)",
]

# Calculate totals for each continent
totals = flow_matrix.sum(axis=0) + flow_matrix.sum(axis=1)
total_flow = flow_matrix.sum()

# Identify the dominant corridor for storytelling emphasis
max_flow_idx = np.unravel_index(np.argmax(flow_matrix + flow_matrix.T), flow_matrix.shape)
dominant_src, dominant_tgt = max_flow_idx
dominant_flow = flow_matrix[dominant_src, dominant_tgt] + flow_matrix[dominant_tgt, dominant_src]

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

# Draw outer arcs with gradient-like layered effect
for i in range(n):
    angles_outer = np.linspace(2 * np.pi * arc_starts[i] - np.pi / 2, 2 * np.pi * arc_ends[i] - np.pi / 2, 100)
    # Outer ring (thicker, slightly transparent for depth)
    x_o = 1.02 * np.cos(angles_outer)
    y_o = 1.02 * np.sin(angles_outer)
    angles_rev = angles_outer[::-1]
    x_i = 0.98 * np.cos(angles_rev)
    y_i = 0.98 * np.sin(angles_rev)

    fig.add_trace(
        go.Scatter(
            x=np.concatenate([x_o, x_i]),
            y=np.concatenate([y_o, y_i]),
            fill="toself",
            fillcolor=colors_dim[i],
            line={"color": "rgba(255,255,255,0)", "width": 0},
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Inner ring (solid color, main arc)
    x_outer = 1.0 * np.cos(angles_outer)
    y_outer = 1.0 * np.sin(angles_outer)
    x_inner = 0.94 * np.cos(angles_rev)
    y_inner = 0.94 * np.sin(angles_rev)

    fig.add_trace(
        go.Scatter(
            x=np.concatenate([x_outer, x_inner]),
            y=np.concatenate([y_outer, y_inner]),
            fill="toself",
            fillcolor=colors[i],
            line={"color": "white", "width": 0.5},
            hovertemplate=(
                f"<b>{continents[i]}</b><br>"
                f"Outgoing: {int(flow_matrix[i].sum())}M<br>"
                f"Incoming: {int(flow_matrix[:, i].sum())}M<br>"
                f"Total: {int(totals[i])}M people"
                "<extra></extra>"
            ),
            name=continents[i],
            showlegend=True,
            legendgroup=continents[i],
        )
    )

# Draw chords with enhanced visibility and storytelling
min_chord_width = 0.008  # Minimum visual width for thin chords
for i in range(n):
    src_pos = arc_starts[i]
    for j in range(n):
        if i == j or flow_matrix[i, j] == 0:
            continue

        flow = flow_matrix[i, j]
        chord_width = max((flow / total_flow) * (1 - n * gap), min_chord_width)

        # Highlight dominant corridor with higher opacity
        is_dominant = (i == dominant_src and j == dominant_tgt) or (i == dominant_tgt and j == dominant_src)
        opacity = 0.72 if is_dominant else 0.45
        line_width = 1.0 if is_dominant else 0.3

        # Target position offset based on prior incoming flows
        tgt_base = arc_starts[j]
        tgt_offset = sum(
            max((flow_matrix[k, j] / total_flow) * (1 - n * gap), min_chord_width)
            for k in range(i)
            if flow_matrix[k, j] > 0
        )

        # Source arc endpoints
        src_angle1 = 2 * np.pi * src_pos - np.pi / 2
        src_angle2 = 2 * np.pi * (src_pos + chord_width) - np.pi / 2
        sx1, sy1 = 0.94 * np.cos(src_angle1), 0.94 * np.sin(src_angle1)
        sx2, sy2 = 0.94 * np.cos(src_angle2), 0.94 * np.sin(src_angle2)

        # Target arc endpoints
        tgt_start = tgt_base + tgt_offset
        tgt_end = tgt_start + chord_width
        tgt_angle1 = 2 * np.pi * tgt_start - np.pi / 2
        tgt_angle2 = 2 * np.pi * tgt_end - np.pi / 2
        tx1, ty1 = 0.94 * np.cos(tgt_angle1), 0.94 * np.sin(tgt_angle1)
        tx2, ty2 = 0.94 * np.cos(tgt_angle2), 0.94 * np.sin(tgt_angle2)

        # Build chord path with smoother bezier curves
        src_angles = np.linspace(src_angle1, src_angle2, 20)
        src_x = 0.94 * np.cos(src_angles)
        src_y = 0.94 * np.sin(src_angles)

        t = np.linspace(0, 1, 40)
        bez1_x = (1 - t) ** 2 * sx2 + 2 * (1 - t) * t * 0 + t**2 * tx1
        bez1_y = (1 - t) ** 2 * sy2 + 2 * (1 - t) * t * 0 + t**2 * ty1

        tgt_angles = np.linspace(tgt_angle1, tgt_angle2, 20)
        tgt_x = 0.94 * np.cos(tgt_angles)
        tgt_y = 0.94 * np.sin(tgt_angles)

        bez2_x = (1 - t) ** 2 * tx2 + 2 * (1 - t) * t * 0 + t**2 * sx1
        bez2_y = (1 - t) ** 2 * ty2 + 2 * (1 - t) * t * 0 + t**2 * sy1

        chord_x = np.concatenate([src_x, bez1_x, tgt_x, bez2_x])
        chord_y = np.concatenate([src_y, bez1_y, tgt_y, bez2_y])

        fig.add_trace(
            go.Scatter(
                x=chord_x,
                y=chord_y,
                fill="toself",
                fillcolor=colors[i],
                opacity=opacity,
                line={"color": colors[i], "width": line_width},
                hovertemplate=(
                    f"<b>{continents[i]} → {continents[j]}</b><br>"
                    f"Flow: {flow}M people<br>"
                    f"Share: {flow / total_flow * 100:.1f}% of total"
                    "<extra></extra>"
                ),
                showlegend=False,
                hoveron="fills",
            )
        )

        src_pos += chord_width

# Add continent labels around the perimeter (horizontal for clarity)
for i in range(n):
    mid_pos = (arc_starts[i] + arc_ends[i]) / 2
    angle = 2 * np.pi * mid_pos - np.pi / 2
    label_radius = 1.16

    lx = label_radius * np.cos(angle)
    ly = label_radius * np.sin(angle)
    angle_deg = np.degrees(angle) % 360

    # Anchor text toward the circle center for clean alignment
    if 45 < angle_deg < 135:
        xanchor, yanchor = "center", "bottom"
    elif 135 <= angle_deg < 225:
        xanchor, yanchor = "right", "middle"
    elif 225 <= angle_deg < 315:
        xanchor, yanchor = "center", "top"
    else:
        xanchor, yanchor = "left", "middle"

    fig.add_annotation(
        x=lx,
        y=ly,
        text=f"<b>{continents[i]}</b> <span style='font-size:17px;color:#888'>{int(totals[i])}M</span>",
        font={"size": 20, "color": colors[i], "family": "Arial, Helvetica, sans-serif"},
        showarrow=False,
        xanchor=xanchor,
        yanchor=yanchor,
    )

# Subtitle annotation for storytelling
fig.add_annotation(
    text=(
        f"Europe–Asia corridor dominates at <b>{dominant_flow}M</b> combined flow"
        "  ·  Chord width proportional to flow magnitude"
    ),
    xref="paper",
    yref="paper",
    x=0.5,
    y=0.955,
    showarrow=False,
    font={"size": 17, "color": "#666666", "family": "Arial, Helvetica, sans-serif"},
    xanchor="center",
)

# Layout with refined styling
fig.update_layout(
    title={
        "text": "Migration Flows Between Continents · chord-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#222222", "family": "Arial Black, Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.98,
    },
    xaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "showline": False, "range": [-1.5, 1.5]},
    yaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "showline": False,
        "range": [-1.6, 1.4],
        "scaleanchor": "x",
    },
    template="plotly_white",
    showlegend=True,
    legend={
        "font": {"size": 18, "family": "Arial, Helvetica, sans-serif"},
        "title": {"text": "<b>Continents</b>", "font": {"size": 18, "color": "#444"}},
        "x": 0.98,
        "y": 0.02,
        "xanchor": "right",
        "yanchor": "bottom",
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "#ddd",
        "borderwidth": 1,
        "tracegroupgap": 6,
        "itemsizing": "constant",
    },
    margin={"l": 20, "r": 20, "t": 80, "b": 15},
    plot_bgcolor="white",
    paper_bgcolor="#FAFAFA",
    hovermode="closest",
    hoverlabel={
        "bgcolor": "white",
        "bordercolor": "#ccc",
        "font": {"size": 16, "family": "Arial, Helvetica, sans-serif", "color": "#333"},
    },
)

# Save outputs
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
