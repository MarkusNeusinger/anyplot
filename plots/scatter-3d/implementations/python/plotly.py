"""anyplot.ai
scatter-3d: 3D Scatter Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-08
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential scale (single polarity) for the continuous color variable
imprint_seq = [[0.0, IMPRINT_PALETTE[0]], [1.0, IMPRINT_PALETTE[2]]]

# Columns: set these to your table's column names
WEIGHT = "Molecular weight (g/mol)"  # role: x
LOGP = "LogP (lipophilicity)"  # role: y
TPSA = "Polar surface area (Ų)"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("compounds.csv")
# Three compound families in molecular property space
np.random.seed(42)
families = [(320, 40, 3.5, 0.8, 60, 15), (180, 30, 1.2, 0.6, 40, 10), (250, 35, 2.8, 0.7, 80, 12)]
frames = []
for w_mu, w_sd, p_mu, p_sd, t_mu, t_sd in families:
    frames.append(
        pd.DataFrame(
            {
                WEIGHT: np.random.normal(w_mu, w_sd, 50),
                LOGP: np.random.normal(p_mu, p_sd, 50),
                TPSA: np.random.normal(t_mu, t_sd, 50),
            }
        )
    )
df = pd.concat(frames, ignore_index=True)

# Plot
axis_style = dict(
    tickfont=dict(size=10, color=INK_SOFT),
    gridcolor=GRID,
    linecolor=INK_SOFT,
    zerolinecolor=INK_SOFT,
    showbackground=True,
    backgroundcolor=PAGE_BG,
)

fig = go.Figure(
    data=[
        go.Scatter3d(
            x=df[WEIGHT],
            y=df[LOGP],
            z=df[TPSA],
            mode="markers",
            marker=dict(
                size=5,
                color=df[WEIGHT],
                colorscale=imprint_seq,
                opacity=0.8,
                line=dict(width=0.5, color=PAGE_BG),
                colorbar=dict(
                    title=dict(text=WEIGHT, font=dict(size=12, color=INK)),
                    tickfont=dict(size=10, color=INK_SOFT),
                    outlinewidth=0,
                    x=0.93,
                    thickness=14,
                    len=0.7,
                ),
            ),
            hovertemplate=f"<b>Compound</b><br>{WEIGHT}: %{{x:.1f}}<br>{LOGP}: %{{y:.2f}}<br>{TPSA}: %{{z:.1f}}<extra></extra>",
        )
    ]
)

fig.update_layout(
    autosize=False,
    title=dict(
        text="scatter-3d · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5, xanchor="center"
    ),
    scene=dict(
        xaxis=dict(title=dict(text=WEIGHT, font=dict(size=12, color=INK)), **axis_style),
        yaxis=dict(title=dict(text=LOGP, font=dict(size=12, color=INK)), **axis_style),
        zaxis=dict(title=dict(text=TPSA, font=dict(size=12, color=INK)), **axis_style),
        camera=dict(eye=dict(x=1.9, y=1.9, z=1.2), center=dict(x=0, y=0, z=-0.12)),
        domain=dict(x=[0.0, 0.88], y=[0.0, 1.0]),
        bgcolor=PAGE_BG,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    margin=dict(l=10, r=10, t=50, b=10),
)

# Save outputs (theme-suffixed filenames)
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
