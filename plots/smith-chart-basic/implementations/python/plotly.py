""" anyplot.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: plotly 7.1.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
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

# Imprint palette: position 1 for the locus, position 2 for the matched-condition marker
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = [[0.0, IMPRINT_PALETTE[0]], [1.0, IMPRINT_PALETTE[2]]]

# Smith chart grid color (slightly stronger than a plain rule, thin so the locus dominates)
SMITH_GRID = "rgba(74,74,68,0.30)" if THEME == "light" else "rgba(184,183,176,0.30)"

# Constants
Z0 = 50  # reference impedance in ohms
R_VALUES = [0, 0.2, 0.5, 1, 2, 5]  # normalized resistance circles
X_VALUES = [0.2, 0.5, 1, 2, 5]  # normalized reactance arcs (drawn for + and -)
N_LABELS = 4  # frequency callouts along the locus

# Columns: set these to your table's column names
FREQUENCY = "Frequency (Hz)"  # role: frequency
Z_REAL = "Resistance (ohm)"  # role: z_real
Z_IMAG = "Reactance (ohm)"  # role: z_imag

# Data: replace this block with your own table, for example df = pd.read_csv("s11.csv")
np.random.seed(42)
_t = np.linspace(0, 2 * np.pi, 50)
df = pd.DataFrame(
    {
        FREQUENCY: np.linspace(1e9, 6e9, 50),
        Z_REAL: 25 + 40 * np.sin(_t / 2) ** 2 + 5 * np.random.randn(50),
        Z_IMAG: 60 * np.cos(_t) + 10 * np.sin(2 * _t),
    }
)

# Plot: reads only df and the constants above
z_norm = (df[Z_REAL].to_numpy() + 1j * df[Z_IMAG].to_numpy()) / Z0
gamma = (z_norm - 1) / (z_norm + 1)
freq_ghz = df[FREQUENCY].to_numpy() / 1e9
n_points = len(df)

fig = go.Figure()

# Constant resistance circles
theta_grid = np.linspace(0, 2 * np.pi, 200)
for r in R_VALUES:
    circle_x = r / (r + 1) + np.cos(theta_grid) / (r + 1)
    circle_y = np.sin(theta_grid) / (r + 1)
    mask = circle_x**2 + circle_y**2 <= 1.01
    fig.add_trace(
        go.Scatter(
            x=np.where(mask, circle_x, np.nan),
            y=np.where(mask, circle_y, np.nan),
            mode="lines",
            line=dict(color=SMITH_GRID, width=0.8),
            hoverinfo="skip",
            showlegend=False,
        )
    )

# Constant reactance arcs (positive and negative)
arc_theta = np.linspace(-np.pi, np.pi, 400)
for x in X_VALUES:
    arc_x = 1 + np.cos(arc_theta) / x
    arc_y = 1 / x + np.sin(arc_theta) / x
    mask = (arc_x**2 + arc_y**2 <= 1.01) & (arc_x >= -1)
    for sign in (1, -1):
        fig.add_trace(
            go.Scatter(
                x=np.where(mask, arc_x, np.nan),
                y=sign * np.where(mask, arc_y, np.nan),
                mode="lines",
                line=dict(color=SMITH_GRID, width=0.8),
                hoverinfo="skip",
                showlegend=False,
            )
        )

# Real axis
fig.add_trace(
    go.Scatter(
        x=[-1, 1], y=[0, 0], mode="lines", line=dict(color=SMITH_GRID, width=0.8), hoverinfo="skip", showlegend=False
    )
)

# Unit circle boundary (|Γ| = 1)
fig.add_trace(
    go.Scatter(
        x=np.cos(theta_grid),
        y=np.sin(theta_grid),
        mode="lines",
        line=dict(color=INK_SOFT, width=2),
        hoverinfo="skip",
        showlegend=False,
    )
)

# Impedance locus, markers colored by frequency
hover_text = [
    f"{f:.2f} GHz<br>Z = {zr:.1f} + j{zi:.1f} Ω" for f, zr, zi in zip(freq_ghz, df[Z_REAL], df[Z_IMAG], strict=True)
]
fig.add_trace(
    go.Scatter(
        x=gamma.real,
        y=gamma.imag,
        mode="lines+markers",
        line=dict(color=IMPRINT_PALETTE[0], width=4.0),
        marker=dict(
            size=7,
            color=freq_ghz,
            colorscale=imprint_seq,
            showscale=True,
            colorbar=dict(
                title=dict(text="GHz", font=dict(size=10, color=INK), side="top"),
                tickvals=[freq_ghz.min(), freq_ghz.mean(), freq_ghz.max()],
                ticktext=[f"{v:g}" for v in (freq_ghz.min(), freq_ghz.mean(), freq_ghz.max())],
                len=0.4,
                thickness=12,
                x=1.02,
                tickfont=dict(size=9, color=INK_SOFT),
                bgcolor=ELEVATED_BG,
                bordercolor=INK_SOFT,
                borderwidth=1,
            ),
            line=dict(color=PAGE_BG, width=1.5),
        ),
        name="Impedance Locus",
        text=hover_text,
        hoverinfo="text",
    )
)

# Frequency labels at evenly spaced points along the locus, offset away from the chart center
for k, idx in enumerate(np.linspace(0, n_points - 1, N_LABELS).astype(int)):
    # alternate right/left and up/down by label order so neighbouring boxes never stack
    side = 1 if k % 2 == 0 else -1
    up = 1 if gamma[idx].imag >= 0 else -1
    fig.add_annotation(
        x=gamma[idx].real,
        y=gamma[idx].imag,
        text=f"{freq_ghz[idx]:.1f} GHz",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=1.5,
        arrowcolor=IMPRINT_PALETTE[0],
        ax=70 * side,
        ay=-40 * up if k else 0,
        font=dict(size=11, color=INK),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        borderpad=3,
    )

# Matched condition marker (Z = Z₀, Γ = 0)
fig.add_trace(
    go.Scatter(
        x=[0],
        y=[0],
        mode="markers",
        marker=dict(size=14, color=IMPRINT_PALETTE[1], symbol="x", line=dict(color=IMPRINT_PALETTE[1], width=3)),
        name="Matched (Z = Z₀)",
        hoverinfo="name",
    )
)

# Resistance labels below the real axis, at the crossing of each circle with the axis
for r in R_VALUES:
    fig.add_annotation(
        x=r / (r + 1), y=0, text=f"{r:g}", showarrow=False, font=dict(size=10, color=INK_SOFT), yshift=-18
    )

# Reactance labels just outside the boundary, where each arc meets the unit circle
for x in X_VALUES:
    edge = complex((x**2 - 1) / (x**2 + 1), 2 * x / (x**2 + 1))
    for sign, prefix in ((1, "+"), (-1, "−")):
        fig.add_annotation(
            x=1.1 * edge.real,
            y=sign * 1.1 * edge.imag,
            text=f"{prefix}j{x:g}",
            showarrow=False,
            font=dict(size=10, color=INK_SOFT),
        )

# Style
fig.update_layout(
    autosize=False,
    width=600,
    height=600,
    title=dict(
        text="smith-chart-basic · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5, xanchor="center"
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    xaxis=dict(
        title=dict(text="Re(Γ)", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        range=[-1.2, 1.2],
        scaleanchor="y",
        scaleratio=1,
        showgrid=False,
        zeroline=False,
        linecolor=INK_SOFT,
        tickcolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Im(Γ)", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        range=[-1.2, 1.2],
        showgrid=False,
        zeroline=False,
        linecolor=INK_SOFT,
        tickcolor=INK_SOFT,
    ),
    legend=dict(
        x=0.02, y=0.02, font=dict(size=10, color=INK_SOFT), bgcolor=ELEVATED_BG, bordercolor=INK_SOFT, borderwidth=1
    ),
    margin=dict(l=70, r=120, t=80, b=70),
)

fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
