""" pyplots.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: plotly 6.6.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-17
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)

ideal_values = np.array([-3, -1, 1, 3])
ideal_i, ideal_q = np.meshgrid(ideal_values, ideal_values)
ideal_i = ideal_i.flatten()
ideal_q = ideal_q.flatten()

n_symbols = 1000
snr_db = 20
snr_linear = 10 ** (snr_db / 10)
signal_power = np.mean(ideal_i**2 + ideal_q**2)
noise_std = np.sqrt(signal_power / snr_linear / 2)

symbol_indices = np.random.randint(0, 16, n_symbols)
received_i = ideal_i[symbol_indices] + np.random.normal(0, noise_std, n_symbols)
received_q = ideal_q[symbol_indices] + np.random.normal(0, noise_std, n_symbols)

error_vectors = np.sqrt((received_i - ideal_i[symbol_indices]) ** 2 + (received_q - ideal_q[symbol_indices]) ** 2)
evm_rms = np.sqrt(np.mean(error_vectors**2)) / np.sqrt(signal_power) * 100

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=received_i,
        y=received_q,
        mode="markers",
        marker={"size": 6, "color": "#306998", "opacity": 0.35},
        name="Received symbols",
        hovertemplate="I: %{x:.2f}<br>Q: %{y:.2f}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=ideal_i,
        y=ideal_q,
        mode="markers",
        marker={"size": 18, "color": "#D64045", "symbol": "x", "line": {"width": 3, "color": "#D64045"}},
        name="Ideal points",
        hovertemplate="I: %{x}<br>Q: %{y}<extra></extra>",
    )
)

# Decision boundaries
for boundary in [-2, 0, 2]:
    fig.add_shape(
        type="line",
        x0=boundary,
        y0=-4.5,
        x1=boundary,
        y1=4.5,
        line={"color": "rgba(0,0,0,0.2)", "width": 1.5, "dash": "dash"},
    )
    fig.add_shape(
        type="line",
        x0=-4.5,
        y0=boundary,
        x1=4.5,
        y1=boundary,
        line={"color": "rgba(0,0,0,0.2)", "width": 1.5, "dash": "dash"},
    )

# EVM annotation
fig.add_annotation(
    x=0.98,
    y=0.98,
    xref="paper",
    yref="paper",
    text=f"EVM = {evm_rms:.1f}%",
    showarrow=False,
    font={"size": 20, "color": "#333333"},
    bgcolor="rgba(255,255,255,0.85)",
    bordercolor="rgba(0,0,0,0.15)",
    borderwidth=1,
    borderpad=8,
    xanchor="right",
    yanchor="top",
)

# Style
fig.update_layout(
    title={"text": "scatter-constellation-diagram · plotly · pyplots.ai", "font": {"size": 28}},
    xaxis={
        "title": {"text": "In-Phase (I)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [-4.8, 4.8],
        "zeroline": True,
        "zerolinewidth": 1.5,
        "zerolinecolor": "rgba(0,0,0,0.3)",
        "dtick": 1,
        "showgrid": False,
        "constrain": "domain",
    },
    yaxis={
        "title": {"text": "Quadrature (Q)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [-4.8, 4.8],
        "scaleanchor": "x",
        "scaleratio": 1,
        "constrain": "domain",
        "zeroline": True,
        "zerolinewidth": 1.5,
        "zerolinecolor": "rgba(0,0,0,0.3)",
        "dtick": 1,
        "showgrid": False,
    },
    template="plotly_white",
    legend={
        "font": {"size": 18},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": "rgba(255,255,255,0.85)",
        "bordercolor": "rgba(0,0,0,0.15)",
        "borderwidth": 1,
    },
    plot_bgcolor="white",
    width=1200,
    height=1200,
)

# Save
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
