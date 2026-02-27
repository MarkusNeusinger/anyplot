""" pyplots.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: plotly 6.5.2 | Python 3.14.3
Quality: 86/100 | Created: 2026-02-27
"""

import numpy as np
import plotly.graph_objects as go


# Data - stress state (MPa)
sigma_x = 80
sigma_y = -40
tau_xy = 30

# Mohr's circle parameters
center = (sigma_x + sigma_y) / 2
radius = np.sqrt(((sigma_x - sigma_y) / 2) ** 2 + tau_xy**2)
sigma_1 = center + radius
sigma_2 = center - radius
tau_max = radius

# Circle points
theta = np.linspace(0, 2 * np.pi, 360)
sigma_circle = center + radius * np.cos(theta)
tau_circle = radius * np.sin(theta)

# Stress points
point_a = (sigma_x, tau_xy)
point_b = (sigma_y, -tau_xy)

# Principal plane angle (2θp)
theta_2p = np.degrees(np.arctan2(tau_xy, (sigma_x - sigma_y) / 2))

# Plot
fig = go.Figure()

# Reference lines through center
axis_pad = radius * 0.3
fig.add_trace(
    go.Scatter(
        x=[sigma_2 - axis_pad, sigma_1 + axis_pad],
        y=[0, 0],
        mode="lines",
        line=dict(color="rgba(0,0,0,0.15)", width=1.5),
        showlegend=False,
        hoverinfo="skip",
    )
)
fig.add_trace(
    go.Scatter(
        x=[center, center],
        y=[-radius - axis_pad, radius + axis_pad],
        mode="lines",
        line=dict(color="rgba(0,0,0,0.15)", width=1.5),
        showlegend=False,
        hoverinfo="skip",
    )
)

# Mohr's circle
fig.add_trace(
    go.Scatter(
        x=sigma_circle,
        y=tau_circle,
        mode="lines",
        line=dict(color="#306998", width=3.5),
        name="Mohr's Circle",
        showlegend=False,
        fill="toself",
        fillcolor="rgba(48,105,152,0.06)",
    )
)

# Diameter line connecting A and B
fig.add_trace(
    go.Scatter(
        x=[point_a[0], point_b[0]],
        y=[point_a[1], point_b[1]],
        mode="lines",
        line=dict(color="#306998", width=2, dash="dash"),
        showlegend=False,
        hoverinfo="skip",
    )
)

# Stress points A and B
fig.add_trace(
    go.Scatter(
        x=[point_a[0]],
        y=[point_a[1]],
        mode="markers",
        marker=dict(size=14, color="#D94E41", line=dict(color="white", width=2)),
        showlegend=False,
        hovertext=f"A (σx={sigma_x}, τxy={tau_xy})",
        hoverinfo="text",
    )
)
fig.add_trace(
    go.Scatter(
        x=[point_b[0]],
        y=[point_b[1]],
        mode="markers",
        marker=dict(size=14, color="#D94E41", line=dict(color="white", width=2)),
        showlegend=False,
        hovertext=f"B (σy={sigma_y}, τxy={-tau_xy})",
        hoverinfo="text",
    )
)

# Principal stresses (σ1, σ2)
fig.add_trace(
    go.Scatter(
        x=[sigma_1, sigma_2],
        y=[0, 0],
        mode="markers",
        marker=dict(size=14, color="#2D8E6F", symbol="diamond", line=dict(color="white", width=2)),
        showlegend=False,
        hovertext=[f"σ₁ = {sigma_1:.1f} MPa", f"σ₂ = {sigma_2:.1f} MPa"],
        hoverinfo="text",
    )
)

# Maximum shear stress (top and bottom)
fig.add_trace(
    go.Scatter(
        x=[center, center],
        y=[tau_max, -tau_max],
        mode="markers",
        marker=dict(size=14, color="#E8910B", symbol="triangle-up", line=dict(color="white", width=2)),
        showlegend=False,
        hovertext=[f"τmax = {tau_max:.1f} MPa", f"−τmax = {-tau_max:.1f} MPa"],
        hoverinfo="text",
    )
)

# Center point
fig.add_trace(
    go.Scatter(
        x=[center],
        y=[0],
        mode="markers",
        marker=dict(size=10, color="#306998", symbol="x", line=dict(width=2)),
        showlegend=False,
        hovertext=f"C ({center:.0f}, 0)",
        hoverinfo="text",
    )
)

# Angle arc for 2θp
arc_r = radius * 0.28
arc_angles = np.linspace(0, np.radians(theta_2p), 50)
arc_x = center + arc_r * np.cos(arc_angles)
arc_y = arc_r * np.sin(arc_angles)
fig.add_trace(
    go.Scatter(
        x=arc_x, y=arc_y, mode="lines", line=dict(color="#8B6AAF", width=2.5), showlegend=False, hoverinfo="skip"
    )
)

# Annotations
fig.add_annotation(
    x=point_a[0],
    y=point_a[1],
    text=f"A ({sigma_x}, {tau_xy})",
    showarrow=True,
    arrowhead=0,
    arrowcolor="#D94E41",
    ax=40,
    ay=-35,
    font=dict(size=17, color="#D94E41"),
)
fig.add_annotation(
    x=point_b[0],
    y=point_b[1],
    text=f"B ({sigma_y}, {-tau_xy})",
    showarrow=True,
    arrowhead=0,
    arrowcolor="#D94E41",
    ax=-40,
    ay=35,
    font=dict(size=17, color="#D94E41"),
)
fig.add_annotation(
    x=sigma_1, y=0, text=f"σ₁ = {sigma_1:.1f}", showarrow=False, yshift=-22, font=dict(size=17, color="#2D8E6F")
)
fig.add_annotation(
    x=sigma_2, y=0, text=f"σ₂ = {sigma_2:.1f}", showarrow=False, yshift=-22, font=dict(size=17, color="#2D8E6F")
)
fig.add_annotation(
    x=center, y=tau_max, text=f"τmax = {tau_max:.1f}", showarrow=False, yshift=18, font=dict(size=17, color="#E8910B")
)
fig.add_annotation(
    x=center,
    y=-tau_max,
    text=f"−τmax = {-tau_max:.1f}",
    showarrow=False,
    yshift=-18,
    font=dict(size=17, color="#E8910B"),
)
fig.add_annotation(
    x=center,
    y=0,
    text=f"C ({center:.0f}, 0)",
    showarrow=False,
    xshift=35,
    yshift=-18,
    font=dict(size=15, color="#555555"),
)

# 2θp label
mid_angle = np.radians(theta_2p / 2)
fig.add_annotation(
    x=center + arc_r * 1.4 * np.cos(mid_angle),
    y=arc_r * 1.4 * np.sin(mid_angle),
    text=f"2θp = {theta_2p:.1f}°",
    showarrow=False,
    font=dict(size=16, color="#8B6AAF"),
)

# Style
fig.update_layout(
    title=dict(text="mohr-circle · plotly · pyplots.ai", font=dict(size=28), x=0.5),
    xaxis=dict(
        title=dict(text="Normal Stress σ (MPa)", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(0,0,0,0.08)",
        gridwidth=1,
        zeroline=True,
        zerolinecolor="rgba(0,0,0,0.2)",
        zerolinewidth=1.5,
        scaleanchor="y",
        scaleratio=1,
    ),
    yaxis=dict(
        title=dict(text="Shear Stress τ (MPa)", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(0,0,0,0.08)",
        gridwidth=1,
        zeroline=True,
        zerolinecolor="rgba(0,0,0,0.2)",
        zerolinewidth=1.5,
    ),
    plot_bgcolor="white",
    paper_bgcolor="white",
    showlegend=False,
    width=1200,
    height=1200,
    margin=dict(l=80, r=80, t=100, b=80),
)

# Save
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
