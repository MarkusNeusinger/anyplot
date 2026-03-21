"""pyplots.ai
bode-basic: Bode Plot for Frequency Response
Library: plotly 6.6.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-21
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data - Third-order open-loop transfer function: H(s) = K / (s/p1 + 1)(s/p2 + 1)(s/p3 + 1)
# with one lightly-damped complex pair to show a resonance peak
K = 40
p1 = 2 * np.pi * 1  # real pole at 1 Hz
p2 = 2 * np.pi * 10  # real pole at 10 Hz
wn = 2 * np.pi * 100  # resonance frequency 100 Hz
zeta = 0.3  # underdamped for visible peak

frequency_hz = np.logspace(-1, 4, 800)
omega = 2 * np.pi * frequency_hz
s = 1j * omega

H = K / ((s / p1 + 1) * (s / p2 + 1) * (s**2 / wn**2 + 2 * zeta * s / wn + 1))
magnitude_db = 20 * np.log10(np.abs(H))
phase_deg = np.degrees(np.unwrap(np.angle(H)))

# Gain crossover: where magnitude crosses 0 dB
gain_cross_idx = np.where(np.diff(np.sign(magnitude_db)))[0]
gc_found = len(gain_cross_idx) > 0
if gc_found:
    gc_idx = gain_cross_idx[-1]
    gc_freq = frequency_hz[gc_idx]
    gc_phase = phase_deg[gc_idx]
    phase_margin = 180 + gc_phase

# Phase crossover: where phase crosses -180 degrees
phase_cross_idx = np.where(np.diff(np.sign(phase_deg + 180)))[0]
pc_found = len(phase_cross_idx) > 0
if pc_found:
    pc_idx = phase_cross_idx[0]
    pc_freq = frequency_hz[pc_idx]
    pc_mag = magnitude_db[pc_idx]
    gain_margin = -pc_mag

# Colors - colorblind-safe: orange for gain margin, purple for phase margin
# Orange vs purple is clearly distinguishable under all color vision types
clr_main = "#306998"
clr_gain = "#E8590C"
clr_phase = "#7B2D8E"

# Plot
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06, row_heights=[0.55, 0.45])

# Magnitude trace
fig.add_trace(
    go.Scatter(
        x=frequency_hz,
        y=magnitude_db,
        mode="lines",
        line={"color": clr_main, "width": 3},
        name="Magnitude",
        showlegend=False,
    ),
    row=1,
    col=1,
)

# 0 dB reference line
fig.add_hline(y=0, row=1, col=1, line={"color": "#AAAAAA", "width": 1, "dash": "dash"})

# Phase trace
fig.add_trace(
    go.Scatter(
        x=frequency_hz, y=phase_deg, mode="lines", line={"color": clr_main, "width": 3}, name="Phase", showlegend=False
    ),
    row=2,
    col=1,
)

# -180 degree reference line
fig.add_hline(y=-180, row=2, col=1, line={"color": "#AAAAAA", "width": 1, "dash": "dash"})

# Gain margin annotation (orange, solid line, diamond markers)
if pc_found:
    fig.add_shape(
        type="rect",
        x0=pc_freq * 0.8,
        x1=pc_freq * 1.25,
        y0=pc_mag,
        y1=0,
        fillcolor=clr_gain,
        opacity=0.1,
        line={"width": 0},
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=[pc_freq, pc_freq],
            y=[pc_mag, 0],
            mode="lines+markers",
            line={"color": clr_gain, "width": 2.5},
            marker={"size": 10, "symbol": "diamond"},
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    fig.add_annotation(
        x=np.log10(pc_freq),
        y=(pc_mag + 0) / 2,
        text=f"<b>GM = {gain_margin:.1f} dB</b>",
        showarrow=True,
        arrowhead=0,
        arrowwidth=1.5,
        arrowcolor=clr_gain,
        ax=75,
        ay=0,
        font={"size": 17, "color": clr_gain},
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=clr_gain,
        borderwidth=1.5,
        borderpad=5,
        xref="x",
        yref="y",
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=[pc_freq],
            y=[-180],
            mode="markers",
            marker={"size": 12, "color": clr_gain, "symbol": "diamond"},
            showlegend=False,
        ),
        row=2,
        col=1,
    )

# Phase margin annotation (purple, dashed line, square markers)
if gc_found:
    fig.add_shape(
        type="rect",
        x0=gc_freq * 0.8,
        x1=gc_freq * 1.25,
        y0=gc_phase,
        y1=-180,
        fillcolor=clr_phase,
        opacity=0.1,
        line={"width": 0},
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=[gc_freq, gc_freq],
            y=[gc_phase, -180],
            mode="lines+markers",
            line={"color": clr_phase, "width": 2.5, "dash": "dash"},
            marker={"size": 10, "symbol": "square"},
            showlegend=False,
        ),
        row=2,
        col=1,
    )
    fig.add_annotation(
        x=np.log10(gc_freq),
        y=(gc_phase + (-180)) / 2,
        text=f"<b>PM = {phase_margin:.1f}°</b>",
        showarrow=True,
        arrowhead=0,
        arrowwidth=1.5,
        arrowcolor=clr_phase,
        ax=-75,
        ay=0,
        font={"size": 17, "color": clr_phase},
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=clr_phase,
        borderwidth=1.5,
        borderpad=5,
        xref="x2",
        yref="y2",
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=[gc_freq],
            y=[0],
            mode="markers",
            marker={"size": 12, "color": clr_phase, "symbol": "square"},
            showlegend=False,
        ),
        row=1,
        col=1,
    )

# Style
fig.update_layout(
    title={"text": "bode-basic · plotly · pyplots.ai", "font": {"size": 28, "color": "#333333"}, "x": 0.5, "y": 0.97},
    template="plotly_white",
    showlegend=False,
    margin={"l": 90, "r": 50, "t": 70, "b": 65},
    plot_bgcolor="rgba(250,250,252,1)",
)

fig.update_xaxes(
    type="log",
    row=2,
    col=1,
    title={"text": "Frequency (Hz)", "font": {"size": 22}},
    tickfont={"size": 18},
    showgrid=True,
    gridcolor="rgba(0,0,0,0.06)",
    gridwidth=1,
    minor={"showgrid": True, "gridcolor": "rgba(0,0,0,0.03)"},
)
fig.update_xaxes(
    type="log",
    row=1,
    col=1,
    tickfont={"size": 18},
    showgrid=True,
    gridcolor="rgba(0,0,0,0.06)",
    gridwidth=1,
    minor={"showgrid": True, "gridcolor": "rgba(0,0,0,0.03)"},
)

fig.update_yaxes(
    row=1,
    col=1,
    title={"text": "Magnitude (dB)", "font": {"size": 22}},
    tickfont={"size": 18},
    showgrid=True,
    gridcolor="rgba(0,0,0,0.06)",
    gridwidth=1,
)
fig.update_yaxes(
    row=2,
    col=1,
    title={"text": "Phase (degrees)", "font": {"size": 22}},
    tickfont={"size": 18},
    showgrid=True,
    gridcolor="rgba(0,0,0,0.06)",
    gridwidth=1,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
