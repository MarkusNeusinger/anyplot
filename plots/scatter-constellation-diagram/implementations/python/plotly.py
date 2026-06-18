"""anyplot.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: plotly 6.6.0 | Python 3.14.3
Quality: 93/100 | Created: 2026-03-17
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint sequential colormap for continuous error magnitude (single-polarity)
imprint_seq = [[0.0, "#009E73"], [1.0, "#4467A3"]]

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

noise_i = np.random.normal(0, noise_std, n_symbols)
noise_q = np.random.normal(0, noise_std, n_symbols)

# Phase offset impairment (~5 degrees carrier phase error)
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

# Received symbols colored by error magnitude — Imprint sequential colormap
fig.add_trace(
    go.Scattergl(
        x=received_i,
        y=received_q,
        mode="markers",
        marker={
            "size": 9,
            "color": error_vectors,
            "colorscale": imprint_seq,
            "opacity": 0.6,
            "colorbar": {
                "title": {"text": "Error<br>Magnitude", "font": {"size": 12, "color": INK_SOFT}},
                "tickfont": {"size": 10, "color": INK_SOFT},
                "thickness": 16,
                "len": 0.45,
                "y": 0.25,
                "outlinewidth": 0,
                "bgcolor": ELEVATED_BG,
                "bordercolor": INK_SOFT,
                "borderwidth": 1,
            },
            "cmin": 0,
            "cmax": np.percentile(error_vectors, 97),
        },
        name="Received symbols",
        hovertemplate="I: %{x:.3f}<br>Q: %{y:.3f}<br>Error: %{marker.color:.3f}<extra></extra>",
        showlegend=True,
    )
)

# Ideal constellation points — matte red X markers (semantic anchor for reference targets)
fig.add_trace(
    go.Scatter(
        x=ideal_i,
        y=ideal_q,
        mode="markers",
        marker={"size": 20, "color": "rgba(0,0,0,0)", "symbol": "x", "line": {"width": 3, "color": "#AE3030"}},
        name="Ideal points",
        hovertemplate="I: %{x}<br>Q: %{y}<extra></extra>",
    )
)

# Decision boundaries — theme-adaptive grid color
for boundary in [-2, 0, 2]:
    fig.add_shape(
        type="line", x0=boundary, y0=-4.8, x1=boundary, y1=4.8, line={"color": GRID, "width": 1, "dash": "dash"}
    )
    fig.add_shape(
        type="line", x0=-4.8, y0=boundary, x1=4.8, y1=boundary, line={"color": GRID, "width": 1, "dash": "dash"}
    )

# EVM annotation — theme-adaptive colors
fig.add_annotation(
    x=0.98,
    y=0.98,
    xref="paper",
    yref="paper",
    text=f"<b>EVM = {evm_rms:.1f}%</b><br><span style='font-size:10px'>SNR = {snr_db} dB · Phase offset = 5°</span>",
    showarrow=False,
    font={"size": 12, "color": INK, "family": "Arial"},
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=10,
    xanchor="right",
    yanchor="top",
    align="right",
)

TITLE = "scatter-constellation-diagram · python · plotly · anyplot.ai"

fig.update_layout(
    autosize=False,
    title={"text": TITLE, "font": {"size": 16, "color": INK, "family": "Arial"}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "In-Phase (I)", "font": {"size": 12, "color": INK, "family": "Arial"}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [-4.8, 4.8],
        "zeroline": True,
        "zerolinewidth": 1.5,
        "zerolinecolor": INK_SOFT,
        "dtick": 1,
        "showgrid": False,
        "constrain": "domain",
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Quadrature (Q)", "font": {"size": 12, "color": INK, "family": "Arial"}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [-4.8, 4.8],
        "scaleanchor": "x",
        "scaleratio": 1,
        "constrain": "domain",
        "zeroline": True,
        "zerolinewidth": 1.5,
        "zerolinecolor": INK_SOFT,
        "dtick": 1,
        "showgrid": False,
        "linecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "font": {"size": 10, "color": INK_SOFT, "family": "Arial"},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 100, "t": 80, "b": 60},
)

# Save — square 2400×2400 (equal aspect required for constellation geometry)
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
