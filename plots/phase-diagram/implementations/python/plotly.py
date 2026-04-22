""" pyplots.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-31
"""

import numpy as np
import plotly.graph_objects as go


# Data - Damped pendulum showing spiral convergence to equilibrium
np.random.seed(42)

# Parameters for damped harmonic oscillator: d²x/dt² + 2ζω₀(dx/dt) + ω₀²x = 0
omega_0 = 2.0  # Natural frequency
zeta = 0.15  # Damping ratio (underdamped: 0 < zeta < 1)

# Time array
t = np.linspace(0, 15, 1500)
dt = t[1] - t[0]

# Analytical solution for underdamped oscillator
omega_d = omega_0 * np.sqrt(1 - zeta**2)  # Damped frequency

# Initial conditions: x(0) = 2.0, dx/dt(0) = 0
x0 = 2.0
v0 = 0.0

# Solution: x(t) = A * exp(-ζω₀t) * cos(ωd*t - φ)
A = np.sqrt(x0**2 + ((v0 + zeta * omega_0 * x0) / omega_d) ** 2)
phi = np.arctan2((v0 + zeta * omega_0 * x0) / omega_d, x0)

x = A * np.exp(-zeta * omega_0 * t) * np.cos(omega_d * t - phi)
dx_dt = -zeta * omega_0 * A * np.exp(-zeta * omega_0 * t) * np.cos(omega_d * t - phi) - omega_d * A * np.exp(
    -zeta * omega_0 * t
) * np.sin(omega_d * t - phi)

# Second trajectory with different initial condition (for basin structure)
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

# Main trajectory with color gradient for time evolution
fig.add_trace(
    go.Scatter(
        x=x,
        y=dx_dt,
        mode="lines+markers",
        name="Trajectory 1 (x₀=2.0, v₀=0)",
        line=dict(color="#306998", width=3),
        marker=dict(size=4, color=t, colorscale="Blues", showscale=False),
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
        line=dict(color="#FFD43B", width=3),
        marker=dict(size=4, color=t, colorscale="YlOrBr", showscale=False),
        hovertemplate="x: %{x:.2f}<br>dx/dt: %{y:.2f}<extra></extra>",
    )
)

# Mark the fixed point (equilibrium at origin)
fig.add_trace(
    go.Scatter(
        x=[0],
        y=[0],
        mode="markers",
        name="Fixed Point (Stable)",
        marker=dict(size=18, color="#E53935", symbol="x", line=dict(width=3)),
        hovertemplate="Equilibrium<br>x=0, dx/dt=0<extra></extra>",
    )
)

# Mark initial conditions
fig.add_trace(
    go.Scatter(
        x=[x[0], x2[0]],
        y=[dx_dt[0], dx_dt_2[0]],
        mode="markers",
        name="Initial Conditions",
        marker=dict(size=14, color="#4CAF50", symbol="circle"),
        hovertemplate="Initial: x=%{x:.2f}, dx/dt=%{y:.2f}<extra></extra>",
    )
)

# Add direction arrows using annotations
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
        arrowcolor="#306998",
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
        arrowcolor="#FFD43B",
    )

# Update layout
fig.update_layout(
    title=dict(
        text="Damped Harmonic Oscillator · phase-diagram · plotly · pyplots.ai",
        font=dict(size=28),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text="Position x", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        zeroline=True,
        zerolinecolor="rgba(0,0,0,0.3)",
        zerolinewidth=2,
    ),
    yaxis=dict(
        title=dict(text="Velocity dx/dt", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        zeroline=True,
        zerolinecolor="rgba(0,0,0,0.3)",
        zerolinewidth=2,
    ),
    legend=dict(
        font=dict(size=16),
        x=0.02,
        y=0.98,
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="rgba(0,0,0,0.2)",
        borderwidth=1,
    ),
    template="plotly_white",
    plot_bgcolor="white",
    margin=dict(l=80, r=40, t=100, b=80),
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
