""" pyplots.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: plotly 6.6.0 | Python 3.14.3
Quality: 93/100 | Created: 2026-03-20
"""

import numpy as np
import plotly.graph_objects as go


# Data: Transfer function G(s) = 2 / (s+1)^3
# Three identical poles at s = -1, no zeros
# DC gain = 2, phase crossover at ω = √3 ≈ 1.73 rad/s
# Gain margin ≈ 12 dB, phase margin ≈ 67.5°
omega = np.logspace(-2, 2, 800)
s = 1j * omega
G = 2.0 / (s + 1) ** 3

real_part = G.real
imag_part = G.imag
magnitude = np.abs(G)
phase_deg = np.degrees(np.angle(G))

# Phase crossover: where imag(G) crosses zero and real(G) < 0
sign_changes = np.where(np.diff(np.sign(imag_part)) != 0)[0]
phase_crossover_idx = None
for idx in sign_changes:
    if real_part[idx] < 0:
        phase_crossover_idx = idx
        break

# Gain crossover: where |G| = 1
gain_crossover_idx = np.argmin(np.abs(magnitude - 1.0))

# Color palette — colorblind-safe (no red-green distinction)
PYTHON_BLUE = "#306998"
CRITICAL_RED = "#C44E52"
GAIN_CROSS_COLOR = "#4C72B0"
PHASE_CROSS_COLOR = "#DD8452"
ANNOTATION_GRAY = "#555770"

# Plot
fig = go.Figure()

# Unit circle for reference
theta = np.linspace(0, 2 * np.pi, 200)
fig.add_trace(
    go.Scatter(
        x=np.cos(theta),
        y=np.sin(theta),
        mode="lines",
        line={"width": 1.5, "color": "rgba(140,140,160,0.3)", "dash": "dash"},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Nyquist curve (positive frequencies ω ≥ 0)
fig.add_trace(
    go.Scatter(
        x=real_part,
        y=imag_part,
        mode="lines",
        line={"width": 3.5, "color": PYTHON_BLUE},
        name="G(jω), ω ≥ 0",
        customdata=np.column_stack([omega, magnitude, phase_deg]),
        hovertemplate=(
            "<b>Nyquist Curve</b><br>"
            "Re = %{x:.3f}<br>"
            "Im = %{y:.3f}<br>"
            "ω = %{customdata[0]:.3f} rad/s<br>"
            "|G| = %{customdata[1]:.3f}<br>"
            "∠G = %{customdata[2]:.1f}°"
            "<extra></extra>"
        ),
    )
)

# Mirror curve (negative frequencies)
fig.add_trace(
    go.Scatter(
        x=real_part,
        y=-imag_part,
        mode="lines",
        line={"width": 2.5, "color": PYTHON_BLUE, "dash": "dot"},
        name="G(jω), ω < 0",
        opacity=0.4,
        hoverinfo="skip",
    )
)

# Direction arrows along the curve showing increasing frequency
n = len(real_part)
for frac in [0.12, 0.32, 0.52]:
    idx = int(n * frac)
    if idx < n - 5:
        dx = real_part[idx + 5] - real_part[idx]
        dy = imag_part[idx + 5] - imag_part[idx]
        norm = np.sqrt(dx**2 + dy**2)
        if norm > 1e-8:
            fig.add_annotation(
                x=real_part[idx],
                y=imag_part[idx],
                ax=-dx / norm * 30,
                ay=dy / norm * 30,
                xref="x",
                yref="y",
                axref="pixel",
                ayref="pixel",
                showarrow=True,
                arrowhead=3,
                arrowsize=2.0,
                arrowwidth=2.5,
                arrowcolor=PYTHON_BLUE,
                text="",
            )

# Critical point (-1, 0)
fig.add_trace(
    go.Scatter(
        x=[-1],
        y=[0],
        mode="markers",
        marker={"symbol": "x-thin", "size": 24, "color": CRITICAL_RED, "line": {"width": 4}},
        name="Critical point (−1, 0)",
        hovertemplate="Critical point<br>(−1, 0)<extra></extra>",
    )
)

# Gain crossover frequency marker
gc_re = real_part[gain_crossover_idx]
gc_im = imag_part[gain_crossover_idx]
gc_omega = omega[gain_crossover_idx]
gc_phase = phase_deg[gain_crossover_idx]
phase_margin = 180.0 + gc_phase
fig.add_trace(
    go.Scatter(
        x=[gc_re],
        y=[gc_im],
        mode="markers",
        marker={"symbol": "circle", "size": 15, "color": GAIN_CROSS_COLOR, "line": {"width": 2, "color": "white"}},
        name=f"Gain crossover (ω≈{gc_omega:.2f})",
        hovertemplate=(
            f"Gain crossover<br>ω = {gc_omega:.2f} rad/s<br>|G| = 1<br>PM = {phase_margin:.1f}°<extra></extra>"
        ),
    )
)
fig.add_annotation(
    x=gc_re,
    y=gc_im,
    text=f"<b>ω={gc_omega:.2f}</b>  PM={phase_margin:.0f}°",
    showarrow=True,
    arrowhead=0,
    arrowwidth=1.2,
    arrowcolor=GAIN_CROSS_COLOR,
    ax=80,
    ay=35,
    font={"size": 14, "color": GAIN_CROSS_COLOR, "family": "Arial, sans-serif"},
)

# Phase crossover frequency marker
if phase_crossover_idx is not None:
    pc_re = real_part[phase_crossover_idx]
    pc_im = imag_part[phase_crossover_idx]
    pc_omega = omega[phase_crossover_idx]
    gain_margin_db = -20 * np.log10(abs(pc_re))
    fig.add_trace(
        go.Scatter(
            x=[pc_re],
            y=[pc_im],
            mode="markers",
            marker={
                "symbol": "diamond",
                "size": 17,
                "color": PHASE_CROSS_COLOR,
                "line": {"width": 2, "color": "white"},
            },
            name=f"Phase crossover (ω≈{pc_omega:.2f})",
            hovertemplate=(
                f"Phase crossover<br>ω = {pc_omega:.2f} rad/s<br>GM = {gain_margin_db:.1f} dB<extra></extra>"
            ),
        )
    )
    fig.add_annotation(
        x=pc_re,
        y=pc_im,
        text=f"<b>ω={pc_omega:.2f}</b>  GM={gain_margin_db:.1f} dB",
        showarrow=True,
        arrowhead=0,
        arrowwidth=1.2,
        arrowcolor=PHASE_CROSS_COLOR,
        ax=-90,
        ay=-35,
        font={"size": 14, "color": PHASE_CROSS_COLOR, "family": "Arial, sans-serif"},
    )

# Frequency annotations at selected points — placed to avoid overlap
# ω=0.1 is far right (near DC gain), ω=0.5 is mid-curve
# ω=1.0 replaces ω=2.0 to avoid crowding near origin
# ω=3.0 replaces ω=5.0 to avoid crowding near phase crossover
freq_label_config = [(0.1, 30, -28), (0.5, -35, -30), (1.0, -40, 25), (3.0, 25, 28)]
for f_label, ax_off, ay_off in freq_label_config:
    idx = np.argmin(np.abs(omega - f_label))
    fig.add_annotation(
        x=real_part[idx],
        y=imag_part[idx],
        text=f"ω={f_label}",
        showarrow=True,
        arrowhead=0,
        arrowwidth=0.8,
        arrowcolor="rgba(85,87,112,0.4)",
        ax=ax_off,
        ay=ay_off,
        font={"size": 13, "color": ANNOTATION_GRAY, "family": "Arial, sans-serif"},
    )

# Style — equal axis scaling via scaleanchor
fig.update_layout(
    title={
        "text": "nyquist-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#1A1A2E", "family": "Arial Black, Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Real Axis", "font": {"size": 22, "family": "Arial, sans-serif"}, "standoff": 12},
        "tickfont": {"size": 18},
        "zeroline": True,
        "zerolinewidth": 1.5,
        "zerolinecolor": "rgba(0,0,0,0.18)",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.04)",
        "constrain": "domain",
        "range": [-1.6, 2.4],
    },
    yaxis={
        "title": {"text": "Imaginary Axis", "font": {"size": 22, "family": "Arial, sans-serif"}, "standoff": 12},
        "tickfont": {"size": 18},
        "zeroline": True,
        "zerolinewidth": 1.5,
        "zerolinecolor": "rgba(0,0,0,0.18)",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.04)",
        "scaleanchor": "x",
        "scaleratio": 1,
    },
    template="plotly_white",
    legend={
        "font": {"size": 14, "family": "Arial, sans-serif"},
        "bgcolor": "rgba(255,255,255,0.94)",
        "bordercolor": "rgba(0,0,0,0.06)",
        "borderwidth": 1,
        "x": 0.01,
        "y": 0.99,
        "itemsizing": "constant",
    },
    margin={"l": 80, "r": 40, "t": 100, "b": 70},
    plot_bgcolor="white",
    paper_bgcolor="#F7F8FB",
    hoverlabel={"bgcolor": "white", "font_size": 14, "bordercolor": "#bbb"},
)

# Subtitle with transfer function
fig.add_annotation(
    text="G(s) = 2 / (s+1)³",
    xref="paper",
    yref="paper",
    x=0.5,
    y=1.01,
    showarrow=False,
    font={"size": 17, "color": "#444", "family": "Courier New, monospace"},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
