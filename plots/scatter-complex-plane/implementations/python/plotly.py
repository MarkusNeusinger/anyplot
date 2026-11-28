"""anyplot.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-06-02
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens — Imprint palette chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — positions 1 and 2 of the categorical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
C1, C2 = IMPRINT_PALETTE[0], IMPRINT_PALETTE[1]

# Constants
# Label placement per 45° sector around the unit circle: (xanchor, xshift, yshift)
SECTOR_ANCHORS = [
    ("left", 16, 0),
    ("left", 10, 14),
    ("center", 0, 18),
    ("right", -10, 14),
    ("right", -16, 0),
    ("right", -10, -14),
    ("center", 0, -18),
    ("left", 10, -14),
]

# Column constants
REAL = "Re(z)"  # role: real
IMAGINARY = "Im(z)"  # role: imaginary
LABEL = "Point"  # role: label
SERIES = "Series"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("points.csv")
# 8th roots of unity ω = e^(2πi/8), and a geometric spiral: repeated multiplication by
# z₀ = 0.88·e^(iπ/6), a 30° turn and a contraction by 0.88 per step
roots = np.exp(2j * np.pi * np.arange(8) / 8)
z0 = 0.88 * np.exp(1j * np.pi / 6)
spiral = z0 ** np.arange(12)
df = pd.DataFrame(
    {
        REAL: np.concatenate([roots.real, spiral.real]),
        IMAGINARY: np.concatenate([roots.imag, spiral.imag]),
        LABEL: ["1", "ω", "i", "ω³", "−1", "ω⁵", "−i", "ω⁷"] + [f"z₀^{k}" for k in range(12)],
        SERIES: ["8th roots of unity"] * 8 + ["z₀ᵏ, z₀ = 0.88·e^(iπ/6)"] * 12,
    }
)

# Plot
df["modulus"] = np.hypot(df[REAL], df[IMAGINARY])
df["angle"] = np.degrees(np.arctan2(df[IMAGINARY], df[REAL]))
series_names = list(df[SERIES].unique())
ROOTS_NAME = series_names[0]
SPIRAL_NAME = ", ".join(series_names[1:])
roots_df = df[df[SERIES] == ROOTS_NAME].reset_index(drop=True)
spiral_df = df[df[SERIES].isin(series_names[1:])].reset_index(drop=True)
axis_limit = max(1.0, df["modulus"].max()) * 1.45

fig = go.Figure()

# Unit circle reference (dashed)
theta_c = np.linspace(0, 2 * np.pi, 300)
fig.add_trace(
    go.Scatter(
        x=np.cos(theta_c),
        y=np.sin(theta_c),
        mode="lines",
        line={"color": INK_MUTED, "width": 2, "dash": "dash"},
        name="Unit circle |z| = 1",
        hoverinfo="skip",
        showlegend=True,
    )
)

# Spiral connecting path (dotted)
fig.add_trace(
    go.Scatter(
        x=spiral_df[REAL],
        y=spiral_df[IMAGINARY],
        mode="lines",
        line={"color": C2, "width": 1.5, "dash": "dot"},
        hoverinfo="skip",
        showlegend=False,
    )
)

# Vector arrows from origin to each 8th root
for x_end, y_end in zip(roots_df[REAL], roots_df[IMAGINARY], strict=True):
    fig.add_annotation(
        x=x_end,
        y=y_end,
        ax=0,
        ay=0,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=3,
        arrowsize=1.2,
        arrowwidth=2.2,
        arrowcolor=C1,
        opacity=0.65,
    )

# Root label annotations
for _, row in roots_df.iterrows():
    sector = int(((row["angle"] % 360) + 22.5) // 45) % len(SECTOR_ANCHORS)
    xa, xs, ys = SECTOR_ANCHORS[sector]
    ya = "middle"
    if ys > 0:
        ya = "bottom"
    elif ys < 0:
        ya = "top"
    fig.add_annotation(
        x=row[REAL],
        y=row[IMAGINARY],
        text=f"<b>{row[LABEL]}</b>",
        showarrow=False,
        font={"size": 14, "color": C1},
        xanchor=xa,
        yanchor=ya,
        xshift=xs,
        yshift=ys,
    )

# Scatter trace: 8th roots of unity
fig.add_trace(
    go.Scatter(
        x=roots_df[REAL],
        y=roots_df[IMAGINARY],
        mode="markers",
        marker={"size": 16, "color": C1, "line": {"color": PAGE_BG, "width": 2.5}, "symbol": "circle"},
        name=ROOTS_NAME,
        customdata=np.column_stack([[f"ω^{k}" for k in roots_df.index], roots_df["modulus"], roots_df["angle"]]),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Re: %{x:.4f}<br>Im: %{y:.4f}<br>"
            "|z| = %{customdata[1]:.4f}<br>"
            "arg(z) = %{customdata[2]:.1f}°"
            "<extra>8th roots of unity</extra>"
        ),
    )
)

# Scatter trace: geometric spiral (marker size decreases to show convergence)
spiral_sizes = [max(7, round(16 - k * 0.75)) for k in spiral_df.index]
fig.add_trace(
    go.Scatter(
        x=spiral_df[REAL],
        y=spiral_df[IMAGINARY],
        mode="markers",
        marker={"size": spiral_sizes, "color": C2, "line": {"color": PAGE_BG, "width": 2}, "symbol": "diamond"},
        name=SPIRAL_NAME,
        customdata=np.column_stack([spiral_df.index, spiral_df["modulus"], spiral_df["angle"]]),
        hovertemplate=(
            "<b>z₀^%{customdata[0]}</b><br>"
            "Re: %{x:.4f}<br>Im: %{y:.4f}<br>"
            "|z₀ᵏ| = %{customdata[1]:.4f}<br>"
            "arg = %{customdata[2]:.1f}°"
            "<extra>Geometric spiral</extra>"
        ),
    )
)

# "r = 1" label at 120° on unit circle — clear of all data
fig.add_annotation(
    x=np.cos(np.radians(120)),
    y=np.sin(np.radians(120)),
    text="<i>r</i> = 1",
    showarrow=False,
    font={"size": 12, "color": INK_MUTED},
    xshift=-16,
    yshift=12,
)

# Title — 52 characters fit at the 16 px base size
title_str = "scatter-complex-plane · python · plotly · anyplot.ai"
title_fs = 16

fig.update_layout(
    autosize=False,
    title={
        "text": (
            f"{title_str}<br>"
            f"<sup style='color:{INK_MUTED}; font-weight:normal'>"
            "Argand diagram — 8th roots of unity &amp; inward geometric spiral"
            "</sup>"
        ),
        "font": {"size": title_fs, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": REAL, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "zeroline": True,
        "zerolinewidth": 2,
        "zerolinecolor": INK_SOFT,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "showgrid": True,
        "dtick": 0.5,
        "range": [-axis_limit, axis_limit],
    },
    yaxis={
        "title": {"text": IMAGINARY, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "zeroline": True,
        "zerolinewidth": 2,
        "zerolinecolor": INK_SOFT,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "showgrid": True,
        "scaleanchor": "x",
        "scaleratio": 1,
        "dtick": 0.5,
        "range": [-axis_limit, axis_limit],
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "x": 0.01,
        "y": 0.99,
        "xanchor": "left",
        "yanchor": "top",
    },
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
)

# Save — square canvas: 600×600 × scale=4 → 2400×2400 px
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
