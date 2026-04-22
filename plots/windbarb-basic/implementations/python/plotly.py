""" pyplots.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: plotly 6.5.1 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-11
"""

import numpy as np
import plotly.graph_objects as go


# Data - Surface wind observations from a grid of weather stations
np.random.seed(42)

# Create a grid of observation points (simulating weather station network)
x_grid = np.arange(0, 10, 1)
y_grid = np.arange(0, 6, 1)
X, Y = np.meshgrid(x_grid, y_grid)
X = X.flatten()
Y = Y.flatten()

# Generate wind components (u: east-west, v: north-south) in knots
# Create a realistic wind pattern with some spatial coherence
base_u = 15 + 10 * np.sin(X * 0.5)
base_v = 5 + 8 * np.cos(Y * 0.8)
U = base_u + np.random.uniform(-5, 5, size=X.shape)
V = base_v + np.random.uniform(-5, 5, size=Y.shape)

# Include some calm winds (< 2.5 knots) for demonstration
calm_indices = [0, 25, 45]
U[calm_indices] = np.random.uniform(-1, 1, size=len(calm_indices))
V[calm_indices] = np.random.uniform(-1, 1, size=len(calm_indices))

# Include strong winds with pennants (50+ knots) for variety
strong_indices = [12, 38, 55]
U[strong_indices] = 40 + np.random.uniform(0, 15, size=len(strong_indices))
V[strong_indices] = 30 + np.random.uniform(0, 10, size=len(strong_indices))


# Wind barb parameters
barb_length = 0.35
barb_width = 0.14

# Collect all wind barb line segments
all_barb_x = []
all_barb_y = []

# Draw each wind barb inline
for i in range(len(X)):
    x0, y0 = X[i], Y[i]
    u, v = U[i], V[i]
    speed = np.sqrt(u**2 + v**2)

    # Calm wind (< 2.5 knots) - draw open circle
    if speed < 2.5:
        theta = np.linspace(0, 2 * np.pi, 20)
        circle_r = barb_length * 0.25
        cx = x0 + circle_r * np.cos(theta)
        cy = y0 + circle_r * np.sin(theta)
        all_barb_x.extend(list(cx) + [None])
        all_barb_y.extend(list(cy) + [None])
        continue

    # Calculate direction (wind comes FROM this direction)
    wind_dir = np.arctan2(-v, -u)

    # Staff endpoint (pointing into the wind direction)
    x_end = x0 + barb_length * np.cos(wind_dir)
    y_end = y0 + barb_length * np.sin(wind_dir)

    # Staff line
    all_barb_x.extend([x0, x_end, None])
    all_barb_y.extend([y0, y_end, None])

    # Perpendicular direction for barbs (to the left of staff)
    perp_dir = wind_dir + np.pi / 2

    # Calculate number of pennants, full barbs, and half barbs
    speed_knots = speed
    pennants = int(speed_knots // 50)
    remaining = speed_knots % 50
    full_barbs = int(remaining // 10)
    half_barbs = 1 if (remaining % 10) >= 5 else 0

    # Position along the staff (from tip towards base)
    spacing = barb_length * 0.12
    current_pos = 0.95

    # Draw pennants (triangular flags for 50 knots)
    for _ in range(pennants):
        px1 = x0 + current_pos * barb_length * np.cos(wind_dir)
        py1 = y0 + current_pos * barb_length * np.sin(wind_dir)
        current_pos -= 0.15
        px2 = x0 + current_pos * barb_length * np.cos(wind_dir)
        py2 = y0 + current_pos * barb_length * np.sin(wind_dir)
        px_tip = px1 + barb_width * 1.2 * np.cos(perp_dir)
        py_tip = py1 + barb_width * 1.2 * np.sin(perp_dir)
        all_barb_x.extend([px1, px_tip, px2, px1, None])
        all_barb_y.extend([py1, py_tip, py2, py1, None])
        current_pos -= 0.05

    # Draw full barbs (10 knots each)
    for _ in range(full_barbs):
        bx1 = x0 + current_pos * barb_length * np.cos(wind_dir)
        by1 = y0 + current_pos * barb_length * np.sin(wind_dir)
        bx2 = bx1 + barb_width * np.cos(perp_dir)
        by2 = by1 + barb_width * np.sin(perp_dir)
        all_barb_x.extend([bx1, bx2, None])
        all_barb_y.extend([by1, by2, None])
        current_pos -= spacing / barb_length

    # Draw half barb (5 knots)
    if half_barbs:
        bx1 = x0 + current_pos * barb_length * np.cos(wind_dir)
        by1 = y0 + current_pos * barb_length * np.sin(wind_dir)
        bx2 = bx1 + barb_width * 0.5 * np.cos(perp_dir)
        by2 = by1 + barb_width * 0.5 * np.sin(perp_dir)
        all_barb_x.extend([bx1, bx2, None])
        all_barb_y.extend([by1, by2, None])


# Create figure
fig = go.Figure()

# Add wind barbs as a single scatter trace with lines (thicker for visibility)
fig.add_trace(
    go.Scatter(
        x=all_barb_x,
        y=all_barb_y,
        mode="lines",
        line={"color": "#306998", "width": 5},
        name="Wind Barbs",
        hoverinfo="skip",
        showlegend=False,
    )
)

# Add station markers at observation points
fig.add_trace(
    go.Scatter(
        x=X,
        y=Y,
        mode="markers",
        marker={"size": 10, "color": "#306998", "symbol": "circle"},
        name="Weather Stations",
        hovertemplate="Station (%{x}, %{y})<br>U: %{customdata[0]:.1f} kt<br>V: %{customdata[1]:.1f} kt<br>Speed: %{customdata[2]:.1f} kt<extra></extra>",
        customdata=np.column_stack([U, V, np.sqrt(U**2 + V**2)]),
    )
)

# Layout with tighter axis range and improved legend positioning
fig.update_layout(
    title={"text": "windbarb-basic · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Longitude (°E)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [-0.5, 9.8],
        "dtick": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    yaxis={
        "title": {"text": "Latitude (°N)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [-0.5, 5.8],
        "dtick": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
        "scaleanchor": "x",
        "scaleratio": 1,
    },
    template="plotly_white",
    showlegend=True,
    legend={
        "font": {"size": 18},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "#306998",
        "borderwidth": 1,
    },
    margin={"l": 100, "r": 80, "t": 100, "b": 100},
    annotations=[
        {
            "x": 0.02,
            "y": 0.02,
            "xref": "paper",
            "yref": "paper",
            "text": "<b>Wind Barb Key</b><br>○ Calm (&lt;2.5 kt)<br>╲ Half barb = 5 kt<br>╲╲ Full barb = 10 kt<br>▲ Pennant = 50 kt",
            "showarrow": False,
            "font": {"size": 16, "family": "monospace"},
            "align": "left",
            "bgcolor": "rgba(255,255,255,0.95)",
            "bordercolor": "#306998",
            "borderwidth": 2,
            "borderpad": 10,
            "xanchor": "left",
            "yanchor": "bottom",
        }
    ],
)

# Save as PNG (4800x2700)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
