""" anyplot.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.20)" if THEME == "light" else "rgba(240,239,232,0.20)"
BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT_1 = "#C475FD"  # Okabe-Ito position 2

# Data - Damped pendulum showing spiral convergence to equilibrium
np.random.seed(42)

# Parameters for damped harmonic oscillator: d²x/dt² + 2ζω₀(dx/dt) + ω₀²x = 0
omega_0 = 2.0
zeta = 0.15

# Time array
t = np.linspace(0, 15, 1500)
dt = t[1] - t[0]

# Damped frequency
omega_d = omega_0 * np.sqrt(1 - zeta**2)

# Trajectory 1: x(0) = 2.0, dx/dt(0) = 0
x0 = 2.0
v0 = 0.0
A = np.sqrt(x0**2 + ((v0 + zeta * omega_0 * x0) / omega_d) ** 2)
phi = np.arctan2((v0 + zeta * omega_0 * x0) / omega_d, x0)

x = A * np.exp(-zeta * omega_0 * t) * np.cos(omega_d * t - phi)
dx_dt = -zeta * omega_0 * A * np.exp(-zeta * omega_0 * t) * np.cos(omega_d * t - phi) - omega_d * A * np.exp(
    -zeta * omega_0 * t
) * np.sin(omega_d * t - phi)

# Trajectory 2: x(0) = -1.5, dx/dt(0) = 3.0
x0_2 = -1.5
v0_2 = 3.0
A2 = np.sqrt(x0_2**2 + ((v0_2 + zeta * omega_0 * x0_2) / omega_d) ** 2)
phi2 = np.arctan2((v0_2 + zeta * omega_0 * x0_2) / omega_d, x0_2)

x2 = A2 * np.exp(-zeta * omega_0 * t) * np.cos(omega_d * t - phi2)
dx_dt_2 = -zeta * omega_0 * A2 * np.exp(-zeta * omega_0 * t) * np.cos(omega_d * t - phi2) - omega_d * A2 * np.exp(
    -zeta * omega_0 * t
) * np.sin(omega_d * t - phi2)

# Create figure
fig = go.Figure()

# Main trajectory
fig.add_trace(
    go.Scatter(
        x=x,
        y=dx_dt,
        mode="lines+markers",
        name="Trajectory 1 (x₀=2.0, v₀=0)",
        line=dict(color=BRAND, width=3),
        marker=dict(size=7, color=BRAND, opacity=0.8),
        hovertemplate="x: %{x:.2f}<br>dx/dt: %{y:.2f}<extra></extra>",
    )
)

# Second trajectory
fig.add_trace(
    go.Scatter(
        x=x2,
        y=dx_dt_2,
        mode="lines+markers",
        name="Trajectory 2 (x₀=-1.5, v₀=3.0)",
        line=dict(color=ACCENT_1, width=3),
        marker=dict(size=7, color=ACCENT_1, opacity=0.8),
        hovertemplate="x: %{x:.2f}<br>dx/dt: %{y:.2f}<extra></extra>",
    )
)

# Fixed point (equilibrium at origin)
fig.add_trace(
    go.Scatter(
        x=[0],
        y=[0],
        mode="markers",
        name="Fixed Point (Stable)",
        marker=dict(size=18, color=INK, symbol="x", line=dict(width=3)),
        hovertemplate="Equilibrium<br>x=0, dx/dt=0<extra></extra>",
    )
)

# Initial conditions
fig.add_trace(
    go.Scatter(
        x=[x[0], x2[0]],
        y=[dx_dt[0], dx_dt_2[0]],
        mode="markers",
        name="Initial Conditions",
        marker=dict(size=14, color=INK_SOFT, symbol="circle"),
        hovertemplate="Initial: x=%{x:.2f}, dx/dt=%{y:.2f}<extra></extra>",
    )
)

# Direction arrows
arrow_indices = [200, 500, 900]
for idx in arrow_indices:
    # Arrow for trajectory 1
    fig.add_annotation(
        x=x[idx],
        y=dx_dt[idx],
        ax=x[idx - 30],
        ay=dx_dt[idx - 30],
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=2,
        arrowwidth=2,
        arrowcolor=BRAND,
    )
    # Arrow for trajectory 2
    fig.add_annotation(
        x=x2[idx],
        y=dx_dt_2[idx],
        ax=x2[idx - 30],
        ay=dx_dt_2[idx - 30],
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=2,
        arrowwidth=2,
        arrowcolor=ACCENT_1,
    )

# Update layout
fig.update_layout(
    title=dict(text="phase-diagram · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Position x", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        zeroline=True,
        zerolinecolor=INK_SOFT,
        zerolinewidth=2,
        linecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Velocity dx/dt", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        zeroline=True,
        zerolinecolor=INK_SOFT,
        zerolinewidth=2,
        linecolor=INK_SOFT,
    ),
    legend=dict(
        font=dict(size=16, color=INK_SOFT), x=0.02, y=0.98, bgcolor=ELEVATED_BG, bordercolor=INK_SOFT, borderwidth=1
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    margin=dict(l=80, r=40, t=100, b=80),
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
