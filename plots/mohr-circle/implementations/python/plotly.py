"""anyplot.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: plotly | Python 3.14
Quality: 90/100 | Updated: 2026-05-30
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens — Imprint palette chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — differentiated roles for Mohr's circle elements
CIRCLE_COLOR = "#009E73"  # brand green — primary structural element
POINT_COLOR = "#AE3030"  # matte red — given stress state (A, B)
SIGMA_COLOR = "#4467A3"  # blue — principal stresses σ1, σ2
TAU_COLOR = "#BD8233"  # ochre — maximum shear stress
ARC_COLOR = "#C475FD"  # lavender — principal plane angle arc

# Data — stress state (MPa)
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
fig.add_shape(
    type="line",
    x0=sigma_2 - axis_pad,
    y0=0,
    x1=sigma_1 + axis_pad,
    y1=0,
    line={"color": GRID, "width": 1.5},
    layer="below",
)
fig.add_shape(
    type="line",
    x0=center,
    y0=-radius - axis_pad,
    x1=center,
    y1=radius + axis_pad,
    line={"color": GRID, "width": 1.5},
    layer="below",
)

# Mohr's circle — brand green with subtle fill
circle_fill = "rgba(0,158,115,0.07)" if THEME == "light" else "rgba(0,158,115,0.13)"
fig.add_trace(
    go.Scatter(
        x=sigma_circle,
        y=tau_circle,
        mode="lines",
        line={"color": CIRCLE_COLOR, "width": 3.5},
        showlegend=False,
        fill="toself",
        fillcolor=circle_fill,
    )
)

# Diameter line connecting A and B
fig.add_trace(
    go.Scatter(
        x=[point_a[0], point_b[0]],
        y=[point_a[1], point_b[1]],
        mode="lines",
        line={"color": CIRCLE_COLOR, "width": 2, "dash": "dash"},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Stress points A and B — given state (red)
fig.add_trace(
    go.Scatter(
        x=[point_a[0]],
        y=[point_a[1]],
        mode="markers",
        marker={"size": 14, "color": POINT_COLOR, "line": {"color": PAGE_BG, "width": 2}},
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
        marker={"size": 14, "color": POINT_COLOR, "line": {"color": PAGE_BG, "width": 2}},
        showlegend=False,
        hovertext=f"B (σy={sigma_y}, τxy={-tau_xy})",
        hoverinfo="text",
    )
)

# Principal stresses σ1, σ2 — derived results (blue diamonds)
fig.add_trace(
    go.Scatter(
        x=[sigma_1, sigma_2],
        y=[0, 0],
        mode="markers",
        marker={"size": 14, "color": SIGMA_COLOR, "symbol": "diamond", "line": {"color": PAGE_BG, "width": 2}},
        showlegend=False,
        hovertext=[f"σ₁ = {sigma_1:.1f} MPa", f"σ₂ = {sigma_2:.1f} MPa"],
        hoverinfo="text",
    )
)

# Maximum shear stress top — ochre triangle-up
fig.add_trace(
    go.Scatter(
        x=[center],
        y=[tau_max],
        mode="markers",
        marker={"size": 14, "color": TAU_COLOR, "symbol": "triangle-up", "line": {"color": PAGE_BG, "width": 2}},
        showlegend=False,
        hovertext=[f"τmax = {tau_max:.1f} MPa"],
        hoverinfo="text",
    )
)

# Maximum shear stress bottom — ochre triangle-down
fig.add_trace(
    go.Scatter(
        x=[center],
        y=[-tau_max],
        mode="markers",
        marker={"size": 14, "color": TAU_COLOR, "symbol": "triangle-down", "line": {"color": PAGE_BG, "width": 2}},
        showlegend=False,
        hovertext=[f"−τmax = {-tau_max:.1f} MPa"],
        hoverinfo="text",
    )
)

# Center point
fig.add_trace(
    go.Scatter(
        x=[center],
        y=[0],
        mode="markers",
        marker={"size": 10, "color": CIRCLE_COLOR, "symbol": "x", "line": {"width": 2}},
        showlegend=False,
        hovertext=f"C ({center:.0f}, 0)",
        hoverinfo="text",
    )
)

# Principal plane angle arc (2θp) — lavender
arc_r = radius * 0.28
arc_angles = np.linspace(0, np.radians(theta_2p), 50)
arc_x = center + arc_r * np.cos(arc_angles)
arc_y = arc_r * np.sin(arc_angles)
fig.add_trace(
    go.Scatter(
        x=arc_x, y=arc_y, mode="lines", line={"color": ARC_COLOR, "width": 2.5}, showlegend=False, hoverinfo="skip"
    )
)

# Annotations
fig.add_annotation(
    x=point_a[0],
    y=point_a[1],
    text=f"A ({sigma_x}, {tau_xy})",
    showarrow=True,
    arrowhead=0,
    arrowcolor=POINT_COLOR,
    ax=40,
    ay=-35,
    font={"size": 12, "color": POINT_COLOR},
)
fig.add_annotation(
    x=point_b[0],
    y=point_b[1],
    text=f"B ({sigma_y}, {-tau_xy})",
    showarrow=True,
    arrowhead=0,
    arrowcolor=POINT_COLOR,
    ax=-40,
    ay=35,
    font={"size": 12, "color": POINT_COLOR},
)
fig.add_annotation(
    x=sigma_1, y=0, text=f"σ₁ = {sigma_1:.1f}", showarrow=False, yshift=-28, font={"size": 12, "color": SIGMA_COLOR}
)
fig.add_annotation(
    x=sigma_2, y=0, text=f"σ₂ = {sigma_2:.1f}", showarrow=False, yshift=-28, font={"size": 12, "color": SIGMA_COLOR}
)
fig.add_annotation(
    x=center, y=tau_max, text=f"τmax = {tau_max:.1f}", showarrow=False, yshift=18, font={"size": 12, "color": TAU_COLOR}
)
fig.add_annotation(
    x=center,
    y=-tau_max,
    text=f"−τmax = {-tau_max:.1f}",
    showarrow=False,
    yshift=-18,
    font={"size": 12, "color": TAU_COLOR},
)
fig.add_annotation(
    x=center,
    y=0,
    text=f"C ({center:.0f}, 0)",
    showarrow=False,
    xshift=35,
    yshift=-18,
    font={"size": 12, "color": INK_SOFT},
)

# 2θp label near arc midpoint
mid_angle = np.radians(theta_2p / 2)
fig.add_annotation(
    x=center + arc_r * 1.4 * np.cos(mid_angle),
    y=arc_r * 1.4 * np.sin(mid_angle),
    text=f"2θp = {theta_2p:.1f}°",
    showarrow=False,
    font={"size": 11, "color": ARC_COLOR},
)

# Layout
title_text = "mohr-circle · python · plotly · anyplot.ai"
n = len(title_text)
title_fontsize = round(16 * 67 / n) if n > 67 else 16

fig.update_layout(
    autosize=False,
    title={"text": title_text, "font": {"size": title_fontsize, "color": INK}, "x": 0.5},
    xaxis={
        "title": {"text": "Normal Stress σ (MPa)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": True,
        "zerolinecolor": INK_SOFT,
        "zerolinewidth": 1.5,
        "linecolor": INK_SOFT,
        "scaleanchor": "y",
        "scaleratio": 1,
    },
    yaxis={
        "title": {"text": "Shear Stress τ (MPa)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": True,
        "zerolinecolor": INK_SOFT,
        "zerolinewidth": 1.5,
        "linecolor": INK_SOFT,
    },
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    margin={"l": 65, "r": 65, "t": 80, "b": 60},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
