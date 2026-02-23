"""pyplots.ai
density-basic: Basic Density Plot
Library: plotly 6.5.2 | Python 3.14.3
"""

import numpy as np
import plotly.graph_objects as go
from scipy.stats import gaussian_kde


# Data - SAT Math scores with bimodal distribution
np.random.seed(42)
sat_scores = np.concatenate(
    [
        np.random.normal(540, 60, 350),  # Main group around 540
        np.random.normal(680, 35, 150),  # High achievers around 680
    ]
)
sat_scores = np.clip(sat_scores, 200, 800)  # SAT range

# KDE using scipy
kde = gaussian_kde(sat_scores)
x_grid = np.linspace(350, 800, 500)
density = kde(x_grid)

# Identify peaks for annotations (split at valley ~620 pts)
split = int(500 * (620 - 350) / (800 - 350))
peak1_idx = np.argmax(density[:split])
peak2_idx = split + np.argmax(density[split:])
peak1_x, peak1_y = x_grid[peak1_idx], density[peak1_idx]
peak2_x, peak2_y = x_grid[peak2_idx], density[peak2_idx]

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=x_grid,
        y=density,
        mode="lines",
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.25)",
        line={"color": "#306998", "width": 3.5},
        name="Density",
        hovertemplate="Score: %{x:.0f}<br>Density: %{y:.4f}<extra></extra>",
    )
)

# Rug plot
fig.add_trace(
    go.Scatter(
        x=sat_scores,
        y=np.zeros(len(sat_scores)),
        mode="markers",
        marker={"symbol": "line-ns", "size": 14, "color": "#306998", "opacity": 0.5, "line": {"width": 1.5}},
        name="Observations",
        hovertemplate="Score: %{x:.0f}<extra></extra>",
    )
)

# Peak annotations to highlight bimodal structure
fig.add_annotation(
    x=peak1_x,
    y=peak1_y,
    text=f"<b>Primary Peak</b><br>~{peak1_x:.0f} pts",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.2,
    arrowwidth=2,
    arrowcolor="#306998",
    font={"size": 18, "color": "#306998"},
    ax=-80,
    ay=-50,
    bgcolor="rgba(255, 255, 255, 0.9)",
    borderpad=6,
)
fig.add_annotation(
    x=peak2_x,
    y=peak2_y,
    text=f"<b>High Achievers</b><br>~{peak2_x:.0f} pts",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.2,
    arrowwidth=2,
    arrowcolor="#306998",
    font={"size": 18, "color": "#306998"},
    ax=80,
    ay=-40,
    bgcolor="rgba(255, 255, 255, 0.9)",
    borderpad=6,
)

# Layout
fig.update_layout(
    title={"text": "density-basic · plotly · pyplots.ai", "font": {"size": 36}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "SAT Math Score (points)", "font": {"size": 28}},
        "tickfont": {"size": 22},
        "showgrid": False,
        "zeroline": False,
        "showspikes": True,
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": "rgba(48, 105, 152, 0.3)",
        "spikedash": "dot",
    },
    yaxis={
        "title": {"text": "Density", "font": {"size": 28}},
        "tickfont": {"size": 22},
        "gridcolor": "rgba(128, 128, 128, 0.15)",
        "gridwidth": 1,
        "zeroline": False,
        "rangemode": "tozero",
    },
    template="plotly_white",
    showlegend=True,
    legend={
        "font": {"size": 20},
        "x": 0.97,
        "y": 0.95,
        "xanchor": "right",
        "yanchor": "top",
        "bgcolor": "rgba(255, 255, 255, 0.8)",
        "borderwidth": 0,
    },
    hovermode="x",
    margin={"l": 90, "r": 40, "t": 90, "b": 90},
    plot_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn", config={"displayModeBar": True, "scrollZoom": True})
