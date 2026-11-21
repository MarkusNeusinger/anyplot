"""anyplot.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.20)" if THEME == "light" else "rgba(240,239,232,0.20)"

# Imprint palette: all eight positions, one per trajectory in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
EQUILIBRIUM = (0.0, 0.0)  # a damped oscillator comes to rest at zero position and zero velocity
ARROW_SPACING = 30  # samples between an arrow's tail and its head
ARROW_POSITIONS = (0.13, 0.33, 0.6)  # arrow heads, as fractions of each trajectory's length

# Columns: set these to your table's column names
TRAJECTORY = "Trajectory"  # role: extra
TIME = "Time (s)"  # role: t
POSITION = "Position x"  # role: x
VELOCITY = "Velocity dx/dt"  # role: dx_dt

# Data: replace this block with your own table, for example df = pd.read_csv("trajectories.csv")
# Damped pendulum, d²x/dt² + 2ζω₀(dx/dt) + ω₀²x = 0, started from two initial conditions
omega_0 = 2.0
zeta = 0.15
omega_d = omega_0 * np.sqrt(1 - zeta**2)
t = np.linspace(0, 15, 1500)
frames = []
for x0, v0 in [(2.0, 0.0), (-1.5, 3.0)]:
    b = (v0 + zeta * omega_0 * x0) / omega_d
    amp = np.hypot(x0, b)
    phase = np.arctan2(b, x0)
    decay = amp * np.exp(-zeta * omega_0 * t)
    angle = omega_d * t - phase
    frames.append(
        pd.DataFrame(
            {
                TRAJECTORY: f"Start x₀={x0:.1f}, v₀={v0:.1f}",
                TIME: t,
                POSITION: decay * np.cos(angle),
                VELOCITY: -zeta * omega_0 * decay * np.cos(angle) - omega_d * decay * np.sin(angle),
            }
        )
    )
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
fig = go.Figure()
groups = list(df.groupby(TRAJECTORY, sort=False))

for i, (name, rows) in enumerate(groups):
    fig.add_trace(
        go.Scatter(
            x=rows[POSITION],
            y=rows[VELOCITY],
            mode="lines+markers",
            name=str(name),
            line=dict(color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)], width=2),
            marker=dict(size=3.5, color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)], opacity=0.8),
            hovertemplate="x: %{x:.2f}<br>dx/dt: %{y:.2f}<extra></extra>",
        )
    )

# Fixed point (equilibrium)
fig.add_trace(
    go.Scatter(
        x=[EQUILIBRIUM[0]],
        y=[EQUILIBRIUM[1]],
        mode="markers",
        name="Fixed point (stable)",
        marker=dict(size=10, color=INK, symbol="x", line=dict(width=2, color=INK)),
        hovertemplate="Equilibrium<br>x=%{x}, dx/dt=%{y}<extra></extra>",
    )
)

# Initial conditions: first row of every trajectory
starts = df.groupby(TRAJECTORY, sort=False).first()
fig.add_trace(
    go.Scatter(
        x=starts[POSITION],
        y=starts[VELOCITY],
        mode="markers",
        name="Initial conditions",
        marker=dict(size=8, color=INK_SOFT, symbol="circle"),
        hovertemplate="Initial: x=%{x:.2f}, dx/dt=%{y:.2f}<extra></extra>",
    )
)

# Direction arrows, pointing along time
for i, (_, rows) in enumerate(groups):
    for frac in ARROW_POSITIONS:
        head = int(frac * len(rows))
        fig.add_annotation(
            x=rows[POSITION].iloc[head],
            y=rows[VELOCITY].iloc[head],
            ax=rows[POSITION].iloc[head - ARROW_SPACING],
            ay=rows[VELOCITY].iloc[head - ARROW_SPACING],
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=2,
            arrowwidth=1.5,
            arrowcolor=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        )

# Style
fig.update_layout(
    autosize=False,
    title=dict(
        text="phase-diagram · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text=POSITION, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        zeroline=True,
        zerolinecolor=INK_SOFT,
        zerolinewidth=1.5,
        linecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text=VELOCITY, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        zeroline=True,
        zerolinecolor=INK_SOFT,
        zerolinewidth=1.5,
        linecolor=INK_SOFT,
    ),
    legend=dict(
        font=dict(size=10, color=INK_SOFT), x=0.02, y=0.98, bgcolor=ELEVATED_BG, bordercolor=INK_SOFT, borderwidth=1
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    margin=dict(l=70, r=30, t=60, b=60),
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
