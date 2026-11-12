""" anyplot.ai
horizon-basic: Horizon Chart
Library: plotly 7.1.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-12
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Horizon bands: light to dark steps of the Imprint blue (above baseline) and Imprint red (below)
COLORS_POS = ["#B4C3DC", "#4467A3", "#1F3358"]
COLORS_NEG = ["#E2AEAE", "#AE3030", "#5E1515"]

# Columns: set these to your table's column names
HOUR = "Hour of day"  # role: date
LOAD = "CPU load vs. baseline (%)"  # role: value
SERVER = "Server"  # role: series

# Data: replace this block with your own table, for example df = pd.read_csv("servers.csv")
rng = np.random.default_rng(42)
n_points = 200
hours = np.linspace(0, 24, n_points)
frames = []
for i, name in enumerate(["Server A", "Server B", "Server C", "Server D", "Server E", "Server F"]):
    daily_cycle = np.sin(hours * np.pi / 12 + i * 0.5) * 15
    drift = np.cumsum(rng.standard_normal(n_points) * 0.5)
    spikes = rng.choice([0, 1], n_points, p=[0.95, 0.05]) * rng.standard_normal(n_points) * 20
    frames.append(pd.DataFrame({HOUR: hours, LOAD: daily_cycle + drift + spikes, SERVER: name}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
servers = list(df[SERVER].drop_duplicates())
n_bands = len(COLORS_POS)
band_size = df[LOAD].abs().max() / n_bands  # same band range in every row

fig = make_subplots(rows=len(servers), cols=1, shared_xaxes=True, vertical_spacing=0.015)

for row, server in enumerate(servers, 1):
    rows = df[df[SERVER] == server]
    x = rows[HOUR]
    for sign, colors in ((1, COLORS_POS), (-1, COLORS_NEG)):
        magnitude = np.maximum(sign * rows[LOAD].to_numpy(), 0)  # negative side mirrored upward
        for band, color in enumerate(colors):
            folded = np.clip(magnitude - band * band_size, 0, band_size)
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=folded,
                    fill="tozeroy",
                    fillcolor=color,
                    line=dict(width=0),
                    mode="lines",
                    showlegend=False,
                    hoverinfo="skip",
                ),
                row=row,
                col=1,
            )
    fig.add_annotation(
        x=0.008,
        y=0.5,
        xref="x domain" if row == 1 else f"x{row} domain",
        yref="y domain" if row == 1 else f"y{row} domain",
        text=f"<b>{server}</b>",
        showarrow=False,
        font=dict(size=11, color=INK),
        xanchor="left",
        bgcolor=PAGE_BG,
        opacity=0.85,
        borderpad=2,
    )

# Style
fig.update_layout(
    autosize=False,
    title=dict(text="horizon-basic · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    showlegend=False,
    margin=dict(l=40, r=30, t=70, b=55),
)
fig.update_xaxes(showgrid=False, linecolor=INK_SOFT, tickfont=dict(size=10, color=INK_SOFT))
fig.update_xaxes(title_text=HOUR, title_font=dict(size=12, color=INK), row=len(servers), col=1)
fig.update_yaxes(range=[0, band_size], showticklabels=False, showgrid=False, zeroline=False, linecolor=INK_SOFT)

# Color key for the folded bands
fig.add_annotation(
    x=1,
    y=1.02,
    xref="paper",
    yref="paper",
    text=(
        f"<b>Above baseline:</b> blue | <b>Below baseline:</b> red | "
        f"each shade step = {band_size:.1f} points, darker = larger"
    ),
    showarrow=False,
    font=dict(size=10, color=INK_SOFT),
    xanchor="right",
    yanchor="bottom",
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
