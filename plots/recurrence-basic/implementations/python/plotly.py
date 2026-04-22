""" pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-14
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
accent = "#306998"
text_dark = "#1a1a1a"
text_mid = "#444"

# Create figure with marginal time series subplot
fig = make_subplots(rows=2, cols=1, row_heights=[0.15, 0.85], vertical_spacing=0.03, shared_xaxes=True)

# Top panel: original Lorenz x-component time series
fig.add_trace(
    go.Scatter(
        x=time_indices,
        y=x_series[:n_embedded],
        mode="lines",
        line={"color": accent, "width": 1.5},
        fill="tozeroy",
        fillcolor="rgba(48,105,152,0.12)",
        hovertemplate="t: %{x}<br>x(t): %{y:.2f}<extra></extra>",
        showlegend=False,
    ),
    row=1,
    col=1,
)

# Bottom panel: recurrence matrix heatmap
fig.add_trace(
    go.Heatmap(
        z=recurrence_matrix,
        x=time_indices,
        y=time_indices,
        colorscale=[[0, "#F7F9FC"], [0.5, "#C8D8E8"], [1, "#1B4F72"]],
        showscale=False,
        hovertemplate="i: %{x}<br>j: %{y}<br>Recurrent: %{z}<extra></extra>",
        xgap=0,
        ygap=0,
    ),
    row=2,
    col=1,
)

# Layout — square-proportioned recurrence matrix with marginal context
fig.update_layout(
    title={
        "text": (
            "recurrence-basic · plotly · pyplots.ai"
            "<br><sup style='color:#555; font-size:17px; letter-spacing:0.3px'>"
            "Lorenz attractor recurrence plot — diagonal lines reveal"
            " deterministic chaotic dynamics"
            "</sup>"
        ),
        "font": {"size": 28, "family": font_family, "color": text_dark},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.98,
        "yanchor": "top",
    },
    template="plotly_white",
    margin={"l": 80, "r": 60, "t": 120, "b": 70},
    width=1200,
    height=1200,
    paper_bgcolor="#FAFBFD",
    plot_bgcolor="#FFFFFF",
    font={"family": font_family},
)

# Top subplot (time series) axis styling
fig.update_yaxes(
    title={"text": "x(t)", "font": {"size": 18, "family": font_family, "color": text_mid}},
    tickfont={"size": 14, "family": font_family, "color": text_mid},
    showgrid=False,
    zeroline=False,
    row=1,
    col=1,
)
fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False, row=1, col=1)

# Bottom subplot (recurrence matrix) axis styling
fig.update_xaxes(
    title={"text": "Time Index (i)", "font": {"size": 22, "family": font_family, "color": "#333"}},
    tickfont={"size": 18, "family": font_family, "color": text_mid},
    showgrid=False,
    zeroline=False,
    row=2,
    col=1,
)
fig.update_yaxes(
    title={"text": "Time Index (j)", "font": {"size": 22, "family": font_family, "color": "#333"}},
    tickfont={"size": 18, "family": font_family, "color": text_mid},
    scaleanchor="x2",
    scaleratio=1,
    constrain="domain",
    autorange="reversed",
    showgrid=False,
    zeroline=False,
    row=2,
    col=1,
)

# Save
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html")
