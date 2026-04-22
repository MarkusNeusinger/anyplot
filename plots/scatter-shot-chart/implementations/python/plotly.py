""" pyplots.ai
scatter-shot-chart: Basketball Shot Chart
Library: plotly 6.6.0 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-20
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)
n_shots = 350

# Generate shot locations across the half-court
# Court: 50 ft wide (-25 to 25), 47 ft deep (0 to 47) from baseline
x = np.concatenate(
    [
        np.random.normal(0, 4, 80),  # Paint area shots
        np.random.normal(0, 8, 100),  # Mid-range
        np.random.uniform(-22, 22, 50),  # Corner threes and wings
        np.random.normal(0, 10, 70),  # Top of key / three-point
        np.zeros(50),  # Free throws
    ]
)
y = np.concatenate(
    [
        np.random.uniform(0, 8, 80),  # Paint area
        np.random.uniform(6, 18, 100),  # Mid-range
        np.random.uniform(0, 10, 50),  # Corner threes
        np.random.uniform(20, 28, 70),  # Top of key / three-point
        np.full(50, 15.0) + np.random.normal(0, 0.3, 50),  # Free throws
    ]
)

# Clip to court boundaries
x = np.clip(x, -24.5, 24.5)
y = np.clip(y, 0.5, 46)

# Shot outcomes — closer shots have higher make percentage
distance = np.sqrt(x**2 + y**2)
make_prob = np.clip(0.65 - distance * 0.012, 0.25, 0.70)
made = np.random.random(len(x)) < make_prob

# Shot types based on distance from basket
three_pt_distance = np.where(np.abs(x) >= 22, 22.0, 23.75)
shot_type = np.where(y < 1.5, "free-throw", np.where(distance > three_pt_distance, "3-pointer", "2-pointer"))
ft_mask = (np.abs(x) < 1) & (y > 14) & (y < 16)
shot_type = np.where(ft_mask, "free-throw", shot_type)

# Compute zone shooting percentages for storytelling
paint_mask = (np.abs(x) < 8) & (y < 10)
mid_mask = ~paint_mask & (distance <= three_pt_distance) & ~ft_mask
three_mask = distance > three_pt_distance
paint_pct = np.mean(made[paint_mask]) * 100
mid_pct = np.mean(made[mid_mask]) * 100
three_pct = np.mean(made[three_mask]) * 100
overall_pct = np.mean(made) * 100

# Court drawing shapes
court_shapes = []

# Court shadow for subtle depth
court_shapes.append(
    {
        "type": "rect",
        "x0": -24.6,
        "y0": -0.4,
        "x1": 25.4,
        "y1": 47.4,
        "line": {"width": 0},
        "fillcolor": "rgba(80,60,40,0.08)",
        "layer": "below",
    }
)

# Subtle court floor — warm hardwood tone (layer below traces so shots are visible)
court_shapes.append(
    {
        "type": "rect",
        "x0": -25,
        "y0": 0,
        "x1": 25,
        "y1": 47,
        "line": {"color": "#6B5B4F", "width": 2.5},
        "fillcolor": "#FDF6EC",
        "layer": "below",
    }
)

# Paint / key area with subtle highlight
court_shapes.append(
    {
        "type": "rect",
        "x0": -8,
        "y0": 0,
        "x1": 8,
        "y1": 19,
        "line": {"color": "#6B5B4F", "width": 2},
        "fillcolor": "#F5EBD8",
        "layer": "below",
    }
)

# Free-throw circle (6 ft radius at y=19)
theta_ft = np.linspace(0, np.pi, 100)
ft_circle_x = 6 * np.cos(theta_ft)
ft_circle_y = 19 + 6 * np.sin(theta_ft)

# Restricted area arc (4 ft radius)
theta_ra = np.linspace(0, np.pi, 100)
ra_x = 4 * np.cos(theta_ra)
ra_y = 4 * np.sin(theta_ra)

# Three-point arc
theta_3pt = np.linspace(np.arccos(22 / 23.75), np.pi - np.arccos(22 / 23.75), 200)
three_x = 23.75 * np.cos(theta_3pt)
three_y = 23.75 * np.sin(theta_3pt)
corner_3_left_x = [-22, -22]
corner_3_left_y = [0, 23.75 * np.sin(np.arccos(22 / 23.75))]
corner_3_right_x = [22, 22]
corner_3_right_y = [0, 23.75 * np.sin(np.arccos(22 / 23.75))]

# Backboard
court_shapes.append(
    {
        "type": "line",
        "x0": -3,
        "y0": -0.5,
        "x1": 3,
        "y1": -0.5,
        "line": {"color": "#6B5B4F", "width": 3},
        "layer": "below",
    }
)

# Basket (rim)
theta_rim = np.linspace(0, 2 * np.pi, 50)
rim_x = 0.75 * np.cos(theta_rim)
rim_y = 1.25 + 0.75 * np.sin(theta_rim)

# Plot
fig = go.Figure()

# Court line style
line_style = {"color": "#6B5B4F", "width": 2}

# Three-point arc
fig.add_trace(
    go.Scatter(
        x=np.concatenate([[-22], three_x[::-1], [22]]),
        y=np.concatenate([[0], three_y[::-1], [0]]),
        mode="lines",
        line={"color": "#6B5B4F", "width": 2.5},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Corner three lines
fig.add_trace(
    go.Scatter(x=corner_3_left_x, y=corner_3_left_y, mode="lines", line=line_style, showlegend=False, hoverinfo="skip")
)
fig.add_trace(
    go.Scatter(
        x=corner_3_right_x, y=corner_3_right_y, mode="lines", line=line_style, showlegend=False, hoverinfo="skip"
    )
)

# Free-throw circle (top half)
fig.add_trace(
    go.Scatter(x=ft_circle_x, y=ft_circle_y, mode="lines", line=line_style, showlegend=False, hoverinfo="skip")
)

# Free-throw circle (bottom half, dashed)
theta_ft_bottom = np.linspace(np.pi, 2 * np.pi, 100)
fig.add_trace(
    go.Scatter(
        x=6 * np.cos(theta_ft_bottom),
        y=19 + 6 * np.sin(theta_ft_bottom),
        mode="lines",
        line={"color": "#6B5B4F", "width": 2, "dash": "dash"},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Restricted area arc
fig.add_trace(go.Scatter(x=ra_x, y=ra_y, mode="lines", line=line_style, showlegend=False, hoverinfo="skip"))

# Basket rim
fig.add_trace(
    go.Scatter(
        x=rim_x, y=rim_y, mode="lines", line={"color": "#CC5500", "width": 2.5}, showlegend=False, hoverinfo="skip"
    )
)

# Colorblind-safe palette: blue for made, orange for missed
color_made = "#306998"
color_missed = "#E8871E"

# Marker sizes vary slightly by distance for visual depth
marker_sizes = np.clip(14 - distance * 0.15, 8, 14)

# Shot markers — missed shots first (underneath)
missed_mask = ~made
fig.add_trace(
    go.Scatter(
        x=x[missed_mask],
        y=y[missed_mask],
        mode="markers",
        marker={
            "size": marker_sizes[missed_mask],
            "color": color_missed,
            "symbol": "x",
            "line": {"width": 1.5, "color": color_missed},
            "opacity": 0.7,
        },
        name="Missed",
        hovertemplate="x: %{x:.1f} ft<br>y: %{y:.1f} ft<br>Missed<extra></extra>",
    )
)

# Made shots on top
fig.add_trace(
    go.Scatter(
        x=x[made],
        y=y[made],
        mode="markers",
        marker={
            "size": marker_sizes[made],
            "color": color_made,
            "symbol": "circle",
            "line": {"width": 1.2, "color": "white"},
            "opacity": 0.8,
        },
        name="Made",
        hovertemplate="x: %{x:.1f} ft<br>y: %{y:.1f} ft<br>Made<extra></extra>",
    )
)

# Zone shooting percentage annotations for storytelling
fig.add_annotation(
    x=0,
    y=9,
    text=f"Paint<br><b>{paint_pct:.0f}%</b>",
    showarrow=False,
    font={"size": 20, "color": "#3A3A3A", "family": "Arial Black, sans-serif"},
    bgcolor="rgba(255,255,255,0.8)",
    borderpad=6,
    bordercolor="rgba(107,91,79,0.3)",
    borderwidth=1,
)
fig.add_annotation(
    x=18,
    y=16,
    text=f"Mid-range<br><b>{mid_pct:.0f}%</b>",
    showarrow=False,
    font={"size": 18, "color": "#3A3A3A", "family": "Arial Black, sans-serif"},
    bgcolor="rgba(255,255,255,0.8)",
    borderpad=6,
    bordercolor="rgba(107,91,79,0.3)",
    borderwidth=1,
)
fig.add_annotation(
    x=0,
    y=35,
    text=f"3-Point<br><b>{three_pct:.0f}%</b>",
    showarrow=False,
    font={"size": 18, "color": "#3A3A3A", "family": "Arial Black, sans-serif"},
    bgcolor="rgba(255,255,255,0.8)",
    borderpad=6,
    bordercolor="rgba(107,91,79,0.3)",
    borderwidth=1,
)

# Style
subtitle = f"{int(np.sum(made))}/{len(made)} shots made ({overall_pct:.1f}% FG)  ·  Paint {paint_pct:.0f}%  ·  Mid {mid_pct:.0f}%  ·  3PT {three_pct:.0f}%"
fig.update_layout(
    title={
        "text": f"scatter-shot-chart · plotly · pyplots.ai<br><span style='font-size:20px;color:#777777'>{subtitle}</span>",
        "font": {"size": 30, "color": "#2A2A2A", "family": "Arial Black, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
    },
    template="plotly_white",
    width=1200,
    height=1200,
    xaxis={
        "range": [-28, 28],
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "scaleanchor": "y",
        "scaleratio": 1,
        "fixedrange": True,
    },
    yaxis={"range": [-2.5, 40], "showgrid": False, "zeroline": False, "showticklabels": False, "fixedrange": True},
    plot_bgcolor="#FAFAFA",
    shapes=court_shapes,
    legend={
        "font": {"size": 18},
        "x": 0.85,
        "y": 0.98,
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "#CCCCCC",
        "borderwidth": 1,
        "itemsizing": "constant",
    },
    margin={"l": 20, "r": 20, "t": 80, "b": 20},
)

# Save
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
