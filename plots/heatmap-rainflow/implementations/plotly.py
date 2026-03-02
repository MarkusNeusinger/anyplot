""" pyplots.ai
heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
Library: plotly 6.5.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-02
"""

import numpy as np
import plotly.graph_objects as go


# Data — simulate rainflow counting results from a variable-amplitude load signal
np.random.seed(42)

n_amplitude_bins = 20
n_mean_bins = 20

amplitude_edges = np.linspace(10, 200, n_amplitude_bins + 1)
mean_edges = np.linspace(-50, 250, n_mean_bins + 1)

amplitude_centers = (amplitude_edges[:-1] + amplitude_edges[1:]) / 2
mean_centers = (mean_edges[:-1] + mean_edges[1:]) / 2

# Build a realistic rainflow matrix: cycles cluster around moderate amplitude / moderate mean
amp_grid, mean_grid = np.meshgrid(amplitude_centers, mean_centers, indexing="ij")

# Primary cluster: moderate amplitude (~60 MPa), moderate mean (~100 MPa)
counts = 800 * np.exp(-((amp_grid - 60) ** 2) / (2 * 35**2) - (mean_grid - 100) ** 2 / (2 * 50**2))
# Secondary cluster: low amplitude (~25 MPa), higher mean (~160 MPa) — vibration fatigue
counts += 400 * np.exp(-((amp_grid - 25) ** 2) / (2 * 15**2) - (mean_grid - 160) ** 2 / (2 * 30**2))
# Scatter: sparse high-amplitude events
counts += 20 * np.exp(-((amp_grid - 140) ** 2) / (2 * 40**2) - (mean_grid - 80) ** 2 / (2 * 60**2))

# Add noise and round to integer counts
counts += np.random.exponential(2, counts.shape)
counts = np.round(counts).astype(int)
counts = np.clip(counts, 0, None)

# Replace very low counts with zero for realism (many bins have no cycles)
counts[counts < 3] = 0

# Use NaN for zero-count bins so they appear as white/transparent
z_display = counts.astype(float)
z_display[z_display == 0] = np.nan

font_family = "Palatino, Georgia, serif"

# Custom sequential colorscale: light cream → orange → deep red
# Starts light so low-count bins blend with the white zero-count background
colorscale = [
    [0.0, "#fff7ec"],
    [0.15, "#fee8c8"],
    [0.3, "#fdb863"],
    [0.5, "#e08214"],
    [0.7, "#d94801"],
    [0.85, "#b13507"],
    [1.0, "#7f2704"],
]

# Plot
fig = go.Figure(
    data=go.Heatmap(
        z=z_display,
        x=np.round(mean_centers, 1),
        y=np.round(amplitude_centers, 1),
        colorscale=colorscale,
        colorbar={
            "title": {"text": "Cycle Count", "font": {"size": 20, "family": font_family}},
            "tickfont": {"size": 16, "family": font_family},
            "thickness": 20,
            "len": 0.75,
            "outlinewidth": 0,
        },
        hovertemplate=("Mean: %{x} MPa<br>Amplitude: %{y} MPa<br>Cycles: %{z:.0f}<extra></extra>"),
        xgap=1,
        ygap=1,
        connectgaps=False,
    )
)

# Layout
fig.update_layout(
    title={
        "text": (
            "heatmap-rainflow · plotly · pyplots.ai"
            "<br><sup style='color:#555; font-size:17px; letter-spacing:0.3px'>"
            "Rainflow cycle counting matrix from a simulated variable-amplitude load history"
            "</sup>"
        ),
        "font": {"size": 28, "family": font_family, "color": "#1a1a1a"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
        "yanchor": "top",
    },
    xaxis={
        "title": {"text": "Cycle Mean Stress (MPa)", "font": {"size": 22, "family": font_family, "color": "#333"}},
        "tickfont": {"size": 18, "family": font_family, "color": "#444"},
    },
    yaxis={
        "title": {"text": "Cycle Amplitude (MPa)", "font": {"size": 22, "family": font_family, "color": "#333"}},
        "tickfont": {"size": 18, "family": font_family, "color": "#444"},
    },
    template="plotly_white",
    margin={"l": 100, "r": 60, "t": 120, "b": 80},
    width=1200,
    height=1200,
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff",
)

# Save
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html")
