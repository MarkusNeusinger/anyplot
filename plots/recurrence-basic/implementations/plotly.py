""" pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: plotly 6.6.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-14
"""

import numpy as np
import plotly.graph_objects as go
from scipy.integrate import solve_ivp
from scipy.spatial.distance import cdist


# Data — Lorenz attractor x-component
np.random.seed(42)
sol = solve_ivp(
    lambda t, s: [10 * (s[1] - s[0]), s[0] * (28 - s[2]) - s[1], s[0] * s[1] - 8 / 3 * s[2]],
    [0, 40],
    [1.0, 1.0, 1.0],
    dense_output=True,
    max_step=0.01,
)
t_eval = np.linspace(0, 40, 500)
x_series = sol.sol(t_eval)[0]

# Time-delay embedding (Takens' theorem)
embedding_dim = 3
delay = 5
n_embedded = len(x_series) - (embedding_dim - 1) * delay
embedded = np.column_stack([x_series[i * delay : i * delay + n_embedded] for i in range(embedding_dim)])

# Compute distance matrix and apply threshold for binary recurrence
distance_matrix = cdist(embedded, embedded, metric="euclidean")
threshold = np.percentile(distance_matrix, 15)
recurrence_matrix = (distance_matrix <= threshold).astype(float)

# Time indices
time_indices = np.arange(n_embedded)

# Font
font_family = "Palatino, Georgia, serif"

# Plot
fig = go.Figure(
    data=go.Heatmap(
        z=recurrence_matrix,
        x=time_indices,
        y=time_indices,
        colorscale=[[0, "#FFFFFF"], [1, "#306998"]],
        showscale=False,
        hovertemplate="i: %{x}<br>j: %{y}<br>Recurrent: %{z}<extra></extra>",
        xgap=0,
        ygap=0,
    )
)

# Layout — square format for symmetric matrix
fig.update_layout(
    title={
        "text": (
            "Lorenz Attractor · recurrence-basic · plotly · pyplots.ai"
            "<br><sup style='color:#555; font-size:17px; letter-spacing:0.3px'>"
            "Time-delay embedded recurrence plot reveals deterministic structure "
            "— diagonal lines indicate chaotic but recurrent dynamics"
            "</sup>"
        ),
        "font": {"size": 28, "family": font_family, "color": "#1a1a1a"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
        "yanchor": "top",
    },
    xaxis={
        "title": {"text": "Time Index (i)", "font": {"size": 22, "family": font_family, "color": "#333"}},
        "tickfont": {"size": 18, "family": font_family, "color": "#444"},
        "scaleanchor": "y",
        "scaleratio": 1,
        "constrain": "domain",
        "showgrid": False,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Time Index (j)", "font": {"size": 22, "family": font_family, "color": "#333"}},
        "tickfont": {"size": 18, "family": font_family, "color": "#444"},
        "constrain": "domain",
        "autorange": "reversed",
        "showgrid": False,
        "zeroline": False,
    },
    template="plotly_white",
    margin={"l": 100, "r": 40, "t": 120, "b": 80},
    width=1200,
    height=1200,
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
)

# Save
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html")
