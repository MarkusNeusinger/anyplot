""" pyplots.ai
circos-basic: Circos Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-31
"""

import numpy as np
import plotly.graph_objects as go


# Data: Trade flows between regions (as example for circos visualization)
np.random.seed(42)

# Define 8 segments (regions) for the circular layout
segments = ["North America", "Europe", "East Asia", "South America", "Africa", "Middle East", "South Asia", "Oceania"]
n_segments = len(segments)

# Segment sizes (proportional to economic importance)
segment_sizes = np.array([25, 30, 28, 10, 8, 12, 15, 6])
segment_sizes = segment_sizes / segment_sizes.sum() * 360  # Normalize to 360 degrees

# Connection matrix (trade flow values)
# Random but symmetric-ish values for bilateral trade
connections = np.array(
    [
        [0, 45, 60, 15, 5, 10, 8, 12],  # North America
        [40, 0, 35, 12, 18, 25, 15, 8],  # Europe
        [55, 38, 0, 10, 12, 20, 30, 18],  # East Asia
        [12, 10, 8, 0, 8, 3, 4, 5],  # South America
        [6, 20, 10, 10, 0, 15, 6, 2],  # Africa
        [12, 28, 22, 4, 12, 0, 18, 5],  # Middle East
        [10, 18, 35, 5, 8, 22, 0, 8],  # South Asia
        [15, 10, 22, 6, 3, 6, 10, 0],  # Oceania
    ]
)

# Colors for each segment
colors = ["#306998", "#FFD43B", "#E34234", "#2ECC71", "#9B59B6", "#E67E22", "#1ABC9C", "#3498DB"]


# Helper to blend two hex colors
def blend_colors(c1, c2, ratio=0.5):
    """Blend two hex colors. ratio=0 gives c1, ratio=1 gives c2."""
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 * (1 - ratio) + r2 * ratio)
    g = int(g1 * (1 - ratio) + g2 * ratio)
    b = int(b1 * (1 - ratio) + b2 * ratio)
    return f"#{r:02x}{g:02x}{b:02x}"


# Calculate segment positions on the circle
gap = 2  # Gap between segments in degrees
total_gap = gap * n_segments
available = 360 - total_gap
segment_angles = segment_sizes / segment_sizes.sum() * available

# Starting angles for each segment
start_angles = np.zeros(n_segments)
for i in range(1, n_segments):
    start_angles[i] = start_angles[i - 1] + segment_angles[i - 1] + gap

# Create figure
fig = go.Figure()

# Outer ring radius
outer_r = 1.0
inner_r = 0.85
ribbon_inner = 0.80

# Draw outer segments (arcs)
for i in range(n_segments):
    theta_start = start_angles[i]
    theta_end = theta_start + segment_angles[i]

    # Create arc points
    theta = np.linspace(np.radians(theta_start), np.radians(theta_end), 50)
    theta_rev = theta[::-1]

    # Outer arc
    x_outer = outer_r * np.cos(theta)
    y_outer = outer_r * np.sin(theta)

    # Inner arc (for the segment)
    x_inner = inner_r * np.cos(theta_rev)
    y_inner = inner_r * np.sin(theta_rev)

    # Combine to make a filled arc
    x_arc = np.concatenate([x_outer, x_inner, [x_outer[0]]])
    y_arc = np.concatenate([y_outer, y_inner, [y_outer[0]]])

    fig.add_trace(
        go.Scatter(
            x=x_arc,
            y=y_arc,
            fill="toself",
            fillcolor=colors[i],
            line=dict(color="white", width=1),
            name=segments[i],
            hoverinfo="name",
            showlegend=True,
        )
    )

    # Add label for segment
    mid_angle = np.radians((theta_start + theta_end) / 2)
    label_r = outer_r + 0.12
    label_x = label_r * np.cos(mid_angle)
    label_y = label_r * np.sin(mid_angle)

    # Rotate text based on position for better readability
    text_angle = (theta_start + theta_end) / 2
    if 90 < text_angle < 270:
        text_angle = text_angle - 180

    # Adjust text anchor based on position for less cramping
    mid_deg = (theta_start + theta_end) / 2
    if 45 < mid_deg < 135:
        xanchor = "center"
        yanchor = "bottom"
    elif 225 < mid_deg < 315:
        xanchor = "center"
        yanchor = "top"
    elif mid_deg <= 45 or mid_deg >= 315:
        xanchor = "left"
        yanchor = "middle"
    else:
        xanchor = "right"
        yanchor = "middle"

    fig.add_annotation(
        x=label_x,
        y=label_y,
        text=segments[i],
        showarrow=False,
        font=dict(size=16, color="#333333"),
        textangle=-text_angle,
        xanchor=xanchor,
        yanchor=yanchor,
    )

# Draw ribbons (connections between segments)
# Get midpoint angles for each segment
mid_angles = start_angles + segment_angles / 2

# Track positions within each segment for ribbon placement
segment_positions = np.zeros(n_segments)

# Draw connections as curved ribbons
for i in range(n_segments):
    for j in range(i + 1, n_segments):
        if connections[i, j] > 5:  # Only show significant connections
            # Normalize ribbon width
            max_conn = connections.max()
            width_i = (connections[i, j] / max_conn) * segment_angles[i] * 0.3
            width_j = (connections[i, j] / max_conn) * segment_angles[j] * 0.3

            # Source positions
            theta_i_start = start_angles[i] + segment_positions[i]
            theta_i_end = theta_i_start + width_i
            segment_positions[i] += width_i + 1

            # Target positions
            theta_j_start = start_angles[j] + segment_positions[j]
            theta_j_end = theta_j_start + width_j
            segment_positions[j] += width_j + 1

            # Create bezier-like ribbon using multiple points
            n_points = 30

            # Source arc points
            theta_src = np.linspace(np.radians(theta_i_start), np.radians(theta_i_end), 10)
            x_src = ribbon_inner * np.cos(theta_src)
            y_src = ribbon_inner * np.sin(theta_src)

            # Target arc points
            theta_tgt = np.linspace(np.radians(theta_j_start), np.radians(theta_j_end), 10)
            x_tgt = ribbon_inner * np.cos(theta_tgt)
            y_tgt = ribbon_inner * np.sin(theta_tgt)

            # Create curved path through center
            # Bezier-like curve from source to target
            t = np.linspace(0, 1, n_points)

            # Control points - curve through center with some offset
            cp1_x, cp1_y = 0.2 * x_src[-1], 0.2 * y_src[-1]
            cp2_x, cp2_y = 0.2 * x_tgt[0], 0.2 * y_tgt[0]

            # Quadratic bezier for top edge
            curve1_x = (1 - t) ** 2 * x_src[-1] + 2 * (1 - t) * t * cp1_x + t**2 * x_tgt[0]
            curve1_y = (1 - t) ** 2 * y_src[-1] + 2 * (1 - t) * t * cp1_y + t**2 * y_tgt[0]

            # Control points for bottom edge
            cp3_x, cp3_y = 0.2 * x_tgt[-1], 0.2 * y_tgt[-1]
            cp4_x, cp4_y = 0.2 * x_src[0], 0.2 * y_src[0]

            # Quadratic bezier for bottom edge (reversed)
            curve2_x = (1 - t) ** 2 * x_tgt[-1] + 2 * (1 - t) * t * cp3_x + t**2 * x_src[0]
            curve2_y = (1 - t) ** 2 * y_tgt[-1] + 2 * (1 - t) * t * cp3_y + t**2 * y_src[0]

            # Combine all points to form ribbon shape
            x_ribbon = np.concatenate([x_src, curve1_x, x_tgt, curve2_x, [x_src[0]]])
            y_ribbon = np.concatenate([y_src, curve1_y, y_tgt, curve2_y, [y_src[0]]])

            # Blend colors from source and target segments for better visual connection
            ribbon_color = blend_colors(colors[i], colors[j], 0.5)
            fig.add_trace(
                go.Scatter(
                    x=x_ribbon,
                    y=y_ribbon,
                    fill="toself",
                    fillcolor=ribbon_color,
                    opacity=0.5,
                    line=dict(color="white", width=0.5),
                    hoverinfo="text",
                    hovertext=f"{segments[i]} ↔ {segments[j]}: {connections[i, j]}",
                    showlegend=False,
                )
            )

# Add inner track (simulated data - e.g., GDP values as bar heights)
track_r_outer = 0.78
track_r_inner = 0.60
track_values = np.array([0.8, 0.95, 0.9, 0.4, 0.25, 0.5, 0.55, 0.3])

for i in range(n_segments):
    theta_start = start_angles[i]
    theta_end = theta_start + segment_angles[i]

    theta = np.linspace(np.radians(theta_start), np.radians(theta_end), 30)
    theta_rev = theta[::-1]

    # Height based on track value
    height = track_r_inner + (track_r_outer - track_r_inner) * track_values[i]

    x_outer = height * np.cos(theta)
    y_outer = height * np.sin(theta)
    x_inner = track_r_inner * np.cos(theta_rev)
    y_inner = track_r_inner * np.sin(theta_rev)

    x_bar = np.concatenate([x_outer, x_inner, [x_outer[0]]])
    y_bar = np.concatenate([y_outer, y_inner, [y_outer[0]]])

    fig.add_trace(
        go.Scatter(
            x=x_bar,
            y=y_bar,
            fill="toself",
            fillcolor=colors[i],
            opacity=0.6,
            line=dict(color="white", width=0.5),
            hoverinfo="text",
            hovertext=f"{segments[i]} GDP Index: {track_values[i]:.2f}",
            showlegend=False,
        )
    )

# Update layout
fig.update_layout(
    title=dict(text="circos-basic · plotly · pyplots.ai", font=dict(size=28, color="#333333"), x=0.5, xanchor="center"),
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=14)),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.5, 1.5], scaleanchor="y", scaleratio=1),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.5, 1.5]),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=50, r=50, t=100, b=120),
)

# Save as PNG (4800x2700 equivalent via scale)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML version
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
