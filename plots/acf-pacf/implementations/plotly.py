"""pyplots.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: plotly 6.6.0 | Python 3.14.3
Quality: 76/100 | Created: 2026-03-14
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data — simulate monthly retail sales with AR(2) structure
np.random.seed(42)
n_obs = 200
ar1_coeff, ar2_coeff = 0.7, -0.3
series = np.zeros(n_obs)
noise = np.random.normal(0, 1, n_obs)
for t in range(2, n_obs):
    series[t] = ar1_coeff * series[t - 1] + ar2_coeff * series[t - 2] + noise[t]

# Compute ACF
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
pacf_plot = pacf_values[1:]

# Classify significant lags
acf_significant = np.abs(acf_values) > conf_bound
pacf_significant = np.abs(pacf_plot) > conf_bound

# Colors
python_blue = "#306998"
sig_color = "#E8590C"
nonsig_color = "#94A3B8"
band_color = "rgba(148, 163, 184, 0.15)"

# Plot
fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.10,
    subplot_titles=["Autocorrelation (ACF)", "Partial Autocorrelation (PACF)"],
)


def add_stems(fig, lags, values, significant, row):
    """Add stem lines and markers with significance coloring."""
    for i, lag in enumerate(lags):
        color = sig_color if significant[i] else nonsig_color
        fig.add_trace(
            go.Scatter(
                x=[lag, lag],
                y=[0, values[i]],
                mode="lines",
                line={"color": color, "width": 3},
                showlegend=False,
                hoverinfo="skip",
            ),
            row=row,
            col=1,
        )
    # Significant markers
    sig_mask = significant
    nonsig_mask = ~significant
    hover_tpl = "Lag %{x}<br>Correlation: %{y:.3f}<extra></extra>"
    if np.any(sig_mask):
        fig.add_trace(
            go.Scatter(
                x=lags[sig_mask],
                y=values[sig_mask],
                mode="markers",
                marker={"size": 13, "color": sig_color, "line": {"color": "white", "width": 2}},
                name="Significant",
                showlegend=(row == 1),
                hovertemplate=hover_tpl,
            ),
            row=row,
            col=1,
        )
    if np.any(nonsig_mask):
        fig.add_trace(
            go.Scatter(
                x=lags[nonsig_mask],
                y=values[nonsig_mask],
                mode="markers",
                marker={"size": 10, "color": nonsig_color, "line": {"color": "white", "width": 1.5}},
                name="Non-significant",
                showlegend=(row == 1),
                hovertemplate=hover_tpl,
            ),
            row=row,
            col=1,
        )


add_stems(fig, lags_acf, acf_values, acf_significant, row=1)
add_stems(fig, lags_pacf, pacf_plot, pacf_significant, row=2)

# Shaded confidence bands and zero lines for both subplots
for row in [1, 2]:
    x_start, x_end = (0, n_lags) if row == 1 else (1, n_lags)
    # Shaded confidence band
    fig.add_trace(
        go.Scatter(
            x=[x_start, x_end, x_end, x_start],
            y=[conf_bound, conf_bound, -conf_bound, -conf_bound],
            fill="toself",
            fillcolor=band_color,
            line={"color": "rgba(148, 163, 184, 0.4)", "width": 1, "dash": "dash"},
            showlegend=(row == 1),
            name="95% Confidence",
            hoverinfo="skip",
        ),
        row=row,
        col=1,
    )
    # Zero line
    fig.add_trace(
        go.Scatter(
            x=[x_start, x_end],
            y=[0, 0],
            mode="lines",
            line={"color": "#CBD5E1", "width": 1},
            showlegend=False,
            hoverinfo="skip",
        ),
        row=row,
        col=1,
    )

# Layout
fig.update_layout(
    title={
        "text": "acf-pacf · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#1E293B"},
        "x": 0.5,
        "xanchor": "center",
    },
    template="plotly_white",
    plot_bgcolor="#FAFBFC",
    paper_bgcolor="#FFFFFF",
    margin={"l": 90, "r": 50, "t": 100, "b": 70},
    height=900,
    width=1600,
    legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1, "font": {"size": 16}},
    hoverlabel={"font_size": 16},
)

# Style subplot titles
for annotation in fig.layout.annotations:
    annotation.font = {"size": 20, "color": "#475569"}

# Y-axes
for row, label in [(1, "ACF"), (2, "PACF")]:
    fig.update_yaxes(
        title_text=label,
        title_font={"size": 22, "color": "#334155"},
        tickfont={"size": 18, "color": "#64748B"},
        showgrid=True,
        gridcolor="rgba(0,0,0,0.05)",
        gridwidth=1,
        zeroline=False,
        row=row,
        col=1,
    )

# X-axes
fig.update_xaxes(
    title_text="Lag",
    title_font={"size": 22, "color": "#334155"},
    tickfont={"size": 18, "color": "#64748B"},
    showgrid=False,
    row=2,
    col=1,
)
fig.update_xaxes(showgrid=False, tickfont={"size": 18, "color": "#64748B"}, row=1, col=1)

# Spike lines for cross-subplot reference
fig.update_xaxes(showspikes=True, spikecolor="#94A3B8", spikethickness=1, spikedash="dot", spikemode="across")

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
