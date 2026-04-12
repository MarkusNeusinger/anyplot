"""pyplots.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: plotly | Python 3.13
Quality: pending | Created: 2026-04-12
"""

import numpy as np
import plotly.graph_objects as go


# Data - synthetic AR(1) temperature process with strong autocorrelation
np.random.seed(42)
n_points = 500
phi = 0.85
noise = np.random.normal(0, 1, n_points)
temperature = np.zeros(n_points)
temperature[0] = 20.0
for i in range(1, n_points):
    temperature[i] = phi * temperature[i - 1] + (1 - phi) * 20.0 + noise[i]

lag = 1
y_t = temperature[:-lag]
y_t_lag = temperature[lag:]
time_index = np.arange(len(y_t))

# Correlation coefficient
correlation = np.corrcoef(y_t, y_t_lag)[0, 1]

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=y_t,
        y=y_t_lag,
        mode="markers",
        marker={
            "size": 10,
            "color": time_index,
            "colorscale": "Viridis",
            "colorbar": {
                "title": {"text": "Time Index", "font": {"size": 18}},
                "tickfont": {"size": 16},
                "thickness": 20,
                "len": 0.7,
            },
            "opacity": 0.7,
            "line": {"width": 0.5, "color": "white"},
        },
        hovertemplate="y(t): %{x:.2f}<br>y(t+1): %{y:.2f}<extra></extra>",
    )
)

# Diagonal reference line (y = x)
data_min = min(y_t.min(), y_t_lag.min())
data_max = max(y_t.max(), y_t_lag.max())
padding = (data_max - data_min) * 0.05
line_min = data_min - padding
line_max = data_max + padding

fig.add_trace(
    go.Scatter(
        x=[line_min, line_max],
        y=[line_min, line_max],
        mode="lines",
        line={"color": "#999999", "width": 2, "dash": "dash"},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Layout
fig.update_layout(
    title={"text": "scatter-lag · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "y(t)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.08)",
        "gridwidth": 1,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": f"y(t + {lag})", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.08)",
        "gridwidth": 1,
        "zeroline": False,
    },
    template="plotly_white",
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    showlegend=False,
    margin={"l": 80, "r": 120, "t": 80, "b": 80},
)

# Correlation annotation
fig.add_annotation(
    text=f"r = {correlation:.3f}",
    xref="paper",
    yref="paper",
    x=0.02,
    y=0.98,
    showarrow=False,
    font={"size": 20, "color": "#333333"},
    bgcolor="rgba(255,255,255,0.8)",
    bordercolor="#cccccc",
    borderwidth=1,
    borderpad=6,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
