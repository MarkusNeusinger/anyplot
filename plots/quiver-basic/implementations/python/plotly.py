""" pyplots.ai
quiver-basic: Basic Quiver Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.figure_factory as ff
import plotly.graph_objects as go


# Data - create a 15x15 grid with circular rotation pattern (u = -y, v = x)
np.random.seed(42)
x_grid = np.linspace(-2, 2, 15)
y_grid = np.linspace(-2, 2, 15)
X, Y = np.meshgrid(x_grid, y_grid)

# Flatten for plotly
x = X.flatten()
y = Y.flatten()

# Circular rotation pattern: u = -y, v = x
u = -Y.flatten()
v = X.flatten()

# Calculate magnitude for coloring
magnitude = np.sqrt(u**2 + v**2)
magnitude[magnitude == 0] = 1  # Avoid division by zero at origin

# Normalize vectors for consistent arrow length display
scale_factor = 0.2
u_norm = u / magnitude * scale_factor
v_norm = v / magnitude * scale_factor

# Create quiver plot using figure_factory
fig = ff.create_quiver(x, y, u_norm, v_norm, scale=1, arrow_scale=0.3, line={"width": 2.5, "color": "#306998"})

# Add scatter points at arrow bases for magnitude coloring
fig.add_trace(
    go.Scatter(
        x=x,
        y=y,
        mode="markers",
        marker={
            "size": 10,
            "color": magnitude,
            "colorscale": "Viridis",
            "colorbar": {
                "title": {"text": "Magnitude", "font": {"size": 22}},
                "tickfont": {"size": 18},
                "thickness": 25,
            },
            "showscale": True,
        },
        hovertemplate="x: %{x:.2f}<br>y: %{y:.2f}<br>magnitude: %{marker.color:.2f}<extra></extra>",
    )
)

# Layout for 4800x2700 px
fig.update_layout(
    title={"text": "Circular Flow Field · quiver-basic · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5},
    xaxis={
        "title": {"text": "X Position", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.1)",
        "zeroline": True,
        "zerolinecolor": "rgba(0,0,0,0.3)",
    },
    yaxis={
        "title": {"text": "Y Position", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.1)",
        "zeroline": True,
        "zerolinecolor": "rgba(0,0,0,0.3)",
        "scaleanchor": "x",
        "scaleratio": 1,
    },
    template="plotly_white",
    showlegend=False,
    margin={"l": 80, "r": 130, "t": 100, "b": 80},
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html")
