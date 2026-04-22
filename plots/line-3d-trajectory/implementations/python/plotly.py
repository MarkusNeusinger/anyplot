""" pyplots.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-07
"""

import numpy as np
import plotly.graph_objects as go


# Data: Lorenz attractor trajectory
np.random.seed(42)

# Lorenz system parameters
sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
dt = 0.01
n_steps = 3000

# Initial conditions
x, y, z = [0.0], [1.0], [1.05]

# Integrate Lorenz equations
for _ in range(n_steps - 1):
    dx = sigma * (y[-1] - x[-1]) * dt
    dy = (x[-1] * (rho - z[-1]) - y[-1]) * dt
    dz = (x[-1] * y[-1] - beta * z[-1]) * dt
    x.append(x[-1] + dx)
    y.append(y[-1] + dy)
    z.append(z[-1] + dz)

x = np.array(x)
y = np.array(y)
z = np.array(z)

# Time array for color gradient (shows trajectory evolution)
t = np.linspace(0, 1, n_steps)

# Create 3D line plot
fig = go.Figure()

fig.add_trace(
    go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode="lines",
        line={
            "width": 5,
            "color": t,
            "colorscale": "Viridis",
            "colorbar": {
                "title": {"text": "Time", "font": {"size": 20}},
                "tickfont": {"size": 16},
                "thickness": 25,
                "len": 0.7,
            },
        },
        name="Lorenz Attractor",
    )
)

# Update layout for 4800x2700 output
fig.update_layout(
    title={
        "text": "Lorenz Attractor · line-3d-trajectory · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    scene={
        "xaxis": {
            "title": {"text": "X Position", "font": {"size": 20}},
            "tickfont": {"size": 14},
            "gridcolor": "rgba(0,0,0,0.1)",
            "showbackground": True,
            "backgroundcolor": "rgba(245,245,245,0.9)",
        },
        "yaxis": {
            "title": {"text": "Y Position", "font": {"size": 20}},
            "tickfont": {"size": 14},
            "gridcolor": "rgba(0,0,0,0.1)",
            "showbackground": True,
            "backgroundcolor": "rgba(245,245,245,0.9)",
        },
        "zaxis": {
            "title": {"text": "Z Position", "font": {"size": 20}},
            "tickfont": {"size": 14},
            "gridcolor": "rgba(0,0,0,0.1)",
            "showbackground": True,
            "backgroundcolor": "rgba(245,245,245,0.9)",
        },
        "camera": {"eye": {"x": 1.5, "y": 1.5, "z": 0.8}},
        "aspectmode": "data",
    },
    template="plotly_white",
    margin={"l": 20, "r": 20, "t": 80, "b": 20},
    showlegend=False,
)

# Save as PNG (4800x2700) and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
