""" pyplots.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: plotly 6.6.0 | Python 3.14.3
Quality: 93/100 | Created: 2026-03-17
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)

ideal_values = np.array([-3, -1, 1, 3])
ideal_i, ideal_q = np.meshgrid(ideal_values, ideal_values)
ideal_i = ideal_i.flatten()
ideal_q = ideal_q.flatten()

n_symbols = 1200
snr_db = 20
snr_linear = 10 ** (snr_db / 10)
signal_power = np.mean(ideal_i**2 + ideal_q**2)
noise_std = np.sqrt(signal_power / snr_linear / 2)

symbol_indices = np.random.randint(0, 16, n_symbols)

# Additive Gaussian noise
noise_i = np.random.normal(0, noise_std, n_symbols)
noise_q = np.random.normal(0, noise_std, n_symbols)

# Phase offset impairment (small carrier phase error of ~5 degrees)
phase_offset = np.deg2rad(5)
ref_i = ideal_i[symbol_indices]
ref_q = ideal_q[symbol_indices]
rotated_i = ref_i * np.cos(phase_offset) - ref_q * np.sin(phase_offset)
rotated_q = ref_i * np.sin(phase_offset) + ref_q * np.cos(phase_offset)

received_i = rotated_i + noise_i
received_q = rotated_q + noise_q

# Error vector magnitude (relative to ideal, not rotated)
error_vectors = np.sqrt((received_i - ref_i) ** 2 + (received_q - ref_q) ** 2)
evm_rms = np.sqrt(np.mean(error_vectors**2)) / np.sqrt(signal_power) * 100

# Plot
fig = go.Figure()

# Received symbols colored by error magnitude for visual storytelling
fig.add_trace(
    go.Scattergl(
        x=received_i,
        y=received_q,
        mode="markers",
        marker={
            "size": 9,
            "color": error_vectors,
            "colorscale": "Viridis",
            "opacity": 0.6,
            "colorbar": {
                "title": {"text": "Error<br>Magnitude", "font": {"size": 16}},
                "tickfont": {"size": 14},
                "thickness": 16,
                "len": 0.45,
                "y": 0.25,
                "outlinewidth": 0,
            },
            "cmin": 0,
            "cmax": np.percentile(error_vectors, 97),
        },
        name="Received symbols",
        hovertemplate="I: %{x:.3f}<br>Q: %{y:.3f}<br>Error: %{marker.color:.3f}<extra></extra>",
        showlegend=True,
    )
)

# Ideal constellation points
fig.add_trace(
    go.Scatter(
        x=ideal_i,
        y=ideal_q,
        mode="markers",
        marker={"size": 20, "color": "rgba(0,0,0,0)", "symbol": "x", "line": {"width": 3, "color": "#E67E22"}},
        name="Ideal points",
        hovertemplate="I: %{x}<br>Q: %{y}<extra></extra>",
    )
)

# Decision boundaries
for boundary in [-2, 0, 2]:
    fig.add_shape(
        type="line",
        x0=boundary,
        y0=-4.8,
        x1=boundary,
        y1=4.8,
        line={"color": "rgba(0,0,0,0.15)", "width": 1, "dash": "dash"},
    )
    fig.add_shape(
        type="line",
        x0=-4.8,
        y0=boundary,
        x1=4.8,
        y1=boundary,
        line={"color": "rgba(0,0,0,0.15)", "width": 1, "dash": "dash"},
    )

# EVM annotation
fig.add_annotation(
    x=0.98,
    y=0.98,
    xref="paper",
    yref="paper",
    text=f"<b>EVM = {evm_rms:.1f}%</b><br><span style='font-size:14px'>SNR = {snr_db} dB · Phase offset = 5°</span>",
    showarrow=False,
    font={"size": 20, "color": "#2C3E50", "family": "Arial"},
    bgcolor="rgba(255,255,255,0.9)",
    bordercolor="rgba(44,62,80,0.25)",
    borderwidth=1,
    borderpad=10,
    xanchor="right",
    yanchor="top",
    align="right",
)

# Style
fig.update_layout(
    title={
        "text": "scatter-constellation-diagram · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2C3E50", "family": "Arial"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "In-Phase (I)", "font": {"size": 22, "family": "Arial"}},
        "tickfont": {"size": 18},
        "range": [-4.8, 4.8],
        "zeroline": True,
        "zerolinewidth": 1.5,
        "zerolinecolor": "rgba(0,0,0,0.25)",
        "dtick": 1,
        "showgrid": False,
        "constrain": "domain",
    },
    yaxis={
        "title": {"text": "Quadrature (Q)", "font": {"size": 22, "family": "Arial"}},
        "tickfont": {"size": 18},
        "range": [-4.8, 4.8],
        "scaleanchor": "x",
        "scaleratio": 1,
        "constrain": "domain",
        "zeroline": True,
        "zerolinewidth": 1.5,
        "zerolinecolor": "rgba(0,0,0,0.25)",
        "dtick": 1,
        "showgrid": False,
    },
    template="plotly_white",
    legend={
        "font": {"size": 18, "family": "Arial"},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "rgba(44,62,80,0.2)",
        "borderwidth": 1,
    },
    plot_bgcolor="#FAFBFC",
    paper_bgcolor="white",
    width=1200,
    height=1200,
    margin={"l": 80, "r": 100, "t": 70, "b": 70},
)

# Save
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
