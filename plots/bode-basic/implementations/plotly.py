""" pyplots.ai
bode-basic: Bode Plot for Frequency Response
Library: plotly 6.6.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-21
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data - Third-order open-loop transfer function: H(s) = K / (s/p1 + 1)(s/p2 + 1)(s/p3 + 1)
K = 50
p1 = 2 * np.pi * 1  # pole at 1 Hz
p2 = 2 * np.pi * 10  # pole at 10 Hz
p3 = 2 * np.pi * 100  # pole at 100 Hz

frequency_hz = np.logspace(-1, 4, 500)
omega = 2 * np.pi * frequency_hz
s = 1j * omega

H = K / ((s / p1 + 1) * (s / p2 + 1) * (s / p3 + 1))
magnitude_db = 20 * np.log10(np.abs(H))
phase_deg = np.degrees(np.unwrap(np.angle(H)))

# Gain crossover: where magnitude crosses 0 dB
gain_cross_idx = np.where(np.diff(np.sign(magnitude_db)))[0]
if len(gain_cross_idx) > 0:
    gc_idx = gain_cross_idx[-1]
    gc_freq = frequency_hz[gc_idx]
    gc_phase = phase_deg[gc_idx]
    phase_margin = 180 + gc_phase

# Phase crossover: where phase crosses -180 degrees
phase_cross_idx = np.where(np.diff(np.sign(phase_deg + 180)))[0]
if len(phase_cross_idx) > 0:
    pc_idx = phase_cross_idx[0]
    pc_freq = frequency_hz[pc_idx]
    pc_mag = magnitude_db[pc_idx]
    gain_margin = -pc_mag

# Plot
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, subplot_titles=None)

# Magnitude trace
fig.add_trace(
    go.Scatter(
        x=frequency_hz,
        y=magnitude_db,
        mode="lines",
        line={"color": "#306998", "width": 3},
        name="Magnitude",
        showlegend=False,
    ),
    row=1,
    col=1,
)

# 0 dB reference line
fig.add_hline(y=0, row=1, col=1, line={"color": "#888888", "width": 1.5, "dash": "dash"})

# Phase trace
fig.add_trace(
    go.Scatter(
        x=frequency_hz, y=phase_deg, mode="lines", line={"color": "#306998", "width": 3}, name="Phase", showlegend=False
    ),
    row=2,
    col=1,
)

# -180 degree reference line
fig.add_hline(y=-180, row=2, col=1, line={"color": "#888888", "width": 1.5, "dash": "dash"})

# Gain margin annotation
if len(phase_cross_idx) > 0:
    fig.add_trace(
        go.Scatter(
            x=[pc_freq, pc_freq],
            y=[pc_mag, 0],
            mode="lines+markers",
            line={"color": "#E8590C", "width": 2.5},
            marker={"size": 10, "symbol": "diamond"},
            name=f"Gain Margin: {gain_margin:.1f} dB",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=[pc_freq],
            y=[-180],
            mode="markers",
            marker={"size": 12, "color": "#E8590C", "symbol": "x"},
            showlegend=False,
        ),
        row=2,
        col=1,
    )

# Phase margin annotation
if len(gain_cross_idx) > 0:
    fig.add_trace(
        go.Scatter(
            x=[gc_freq, gc_freq],
            y=[gc_phase, -180],
            mode="lines+markers",
            line={"color": "#2B8A3E", "width": 2.5},
            marker={"size": 10, "symbol": "diamond"},
            name=f"Phase Margin: {phase_margin:.1f}°",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=[gc_freq], y=[0], mode="markers", marker={"size": 12, "color": "#2B8A3E", "symbol": "x"}, showlegend=False
        ),
        row=1,
        col=1,
    )

# Style
fig.update_layout(
    title={"text": "bode-basic · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5},
    template="plotly_white",
    legend={"font": {"size": 18}, "x": 0.72, "y": 0.98, "bgcolor": "rgba(255,255,255,0.8)"},
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
)

fig.update_xaxes(
    type="log",
    row=2,
    col=1,
    title={"text": "Frequency (Hz)", "font": {"size": 22}},
    tickfont={"size": 18},
    showgrid=True,
    gridcolor="rgba(0,0,0,0.08)",
    gridwidth=1,
)
fig.update_xaxes(
    type="log", row=1, col=1, tickfont={"size": 18}, showgrid=True, gridcolor="rgba(0,0,0,0.08)", gridwidth=1
)

fig.update_yaxes(
    row=1,
    col=1,
    title={"text": "Magnitude (dB)", "font": {"size": 22}},
    tickfont={"size": 18},
    showgrid=True,
    gridcolor="rgba(0,0,0,0.08)",
    gridwidth=1,
)
fig.update_yaxes(
    row=2,
    col=1,
    title={"text": "Phase (degrees)", "font": {"size": 22}},
    tickfont={"size": 18},
    showgrid=True,
    gridcolor="rgba(0,0,0,0.08)",
    gridwidth=1,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
