"""pyplots.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: plotly | Python 3.14
Quality: pending | Created: 2026-03-14
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data — generate AR(2) process with known structure
np.random.seed(42)
n_obs = 200
ar1_coeff = 0.7
ar2_coeff = -0.3
series = np.zeros(n_obs)
noise = np.random.normal(0, 1, n_obs)
for t in range(2, n_obs):
    series[t] = ar1_coeff * series[t - 1] + ar2_coeff * series[t - 2] + noise[t]

# Compute ACF manually
n_lags = 35
series_centered = series - np.mean(series)
variance = np.sum(series_centered**2)
acf_values = np.array(
    [np.sum(series_centered[: n_obs - k] * series_centered[k:]) / variance for k in range(n_lags + 1)]
)

# Compute PACF via Durbin-Levinson recursion
pacf_values = np.zeros(n_lags + 1)
pacf_values[0] = 1.0
pacf_values[1] = acf_values[1]
phi = np.zeros((n_lags + 1, n_lags + 1))
phi[1, 1] = acf_values[1]
for k in range(2, n_lags + 1):
    num = acf_values[k] - np.sum(phi[k - 1, 1:k] * acf_values[k - 1 : 0 : -1])
    den = 1.0 - np.sum(phi[k - 1, 1:k] * acf_values[1:k])
    phi[k, k] = num / den if abs(den) > 1e-12 else 0.0
    for j in range(1, k):
        phi[k, j] = phi[k - 1, j] - phi[k, k] * phi[k - 1, k - j]
    pacf_values[k] = phi[k, k]

conf_bound = 1.96 / np.sqrt(n_obs)
lags_acf = np.arange(0, n_lags + 1)
lags_pacf = np.arange(1, n_lags + 1)

# Plot
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12, subplot_titles=["", ""])

python_blue = "#306998"
conf_color = "#E74C3C"

# ACF stems
for i, lag in enumerate(lags_acf):
    fig.add_trace(
        go.Scatter(
            x=[lag, lag], y=[0, acf_values[i]], mode="lines", line=dict(color=python_blue, width=3), showlegend=False
        ),
        row=1,
        col=1,
    )

# ACF markers
fig.add_trace(
    go.Scatter(
        x=lags_acf,
        y=acf_values,
        mode="markers",
        marker=dict(size=10, color=python_blue, line=dict(color="white", width=1.5)),
        showlegend=False,
    ),
    row=1,
    col=1,
)

# ACF confidence bounds
for bound in [conf_bound, -conf_bound]:
    fig.add_trace(
        go.Scatter(
            x=[0, n_lags],
            y=[bound, bound],
            mode="lines",
            line=dict(color=conf_color, width=2, dash="dash"),
            showlegend=False,
        ),
        row=1,
        col=1,
    )

# ACF zero line
fig.add_trace(
    go.Scatter(x=[0, n_lags], y=[0, 0], mode="lines", line=dict(color="#999999", width=1), showlegend=False),
    row=1,
    col=1,
)

# PACF stems
pacf_plot_values = pacf_values[1:]
for i, lag in enumerate(lags_pacf):
    fig.add_trace(
        go.Scatter(
            x=[lag, lag],
            y=[0, pacf_plot_values[i]],
            mode="lines",
            line=dict(color=python_blue, width=3),
            showlegend=False,
        ),
        row=2,
        col=1,
    )

# PACF markers
fig.add_trace(
    go.Scatter(
        x=lags_pacf,
        y=pacf_plot_values,
        mode="markers",
        marker=dict(size=10, color=python_blue, line=dict(color="white", width=1.5)),
        showlegend=False,
    ),
    row=2,
    col=1,
)

# PACF confidence bounds
for bound in [conf_bound, -conf_bound]:
    fig.add_trace(
        go.Scatter(
            x=[1, n_lags],
            y=[bound, bound],
            mode="lines",
            line=dict(color=conf_color, width=2, dash="dash"),
            showlegend=False,
        ),
        row=2,
        col=1,
    )

# PACF zero line
fig.add_trace(
    go.Scatter(x=[1, n_lags], y=[0, 0], mode="lines", line=dict(color="#999999", width=1), showlegend=False),
    row=2,
    col=1,
)

# Style
fig.update_layout(
    title=dict(text="acf-pacf · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    template="plotly_white",
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    margin=dict(l=80, r=40, t=80, b=60),
    height=900,
    width=1600,
)

fig.update_yaxes(
    title_text="ACF",
    title_font=dict(size=22),
    tickfont=dict(size=18),
    showgrid=True,
    gridcolor="rgba(0,0,0,0.08)",
    gridwidth=1,
    zeroline=False,
    row=1,
    col=1,
)
fig.update_yaxes(
    title_text="PACF",
    title_font=dict(size=22),
    tickfont=dict(size=18),
    showgrid=True,
    gridcolor="rgba(0,0,0,0.08)",
    gridwidth=1,
    zeroline=False,
    row=2,
    col=1,
)
fig.update_xaxes(title_text="Lag", title_font=dict(size=22), tickfont=dict(size=18), showgrid=False, row=2, col=1)
fig.update_xaxes(showgrid=False, tickfont=dict(size=18), row=1, col=1)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
