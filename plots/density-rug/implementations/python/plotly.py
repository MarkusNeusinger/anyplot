"""anyplot.ai
density-rug: Density Plot with Rug Marks
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: position 1 carries the single series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]
BRAND_RGB = ", ".join(str(int(BRAND[i : i + 2], 16)) for i in (1, 3, 5))

# Columns: set these to your table's column names
RESPONSE_TIME = "Response time (ms)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
rng = np.random.default_rng(42)
df = pd.DataFrame(
    {
        RESPONSE_TIME: np.concatenate(
            [
                rng.normal(120, 25, 80),  # fast responses
                rng.normal(250, 40, 40),  # slower responses
            ]
        )
    }
)

# Plot: reads only df and the constants above
values = df[RESPONSE_TIME].dropna().to_numpy()
kde = gaussian_kde(values)
pad = 0.5 * values.std()
x_range = np.linspace(values.min() - pad, values.max() + pad, 500)
density = kde(x_range)
peak = density.max()
rug_height = peak * 0.04

fig = go.Figure()

# Filled KDE curve
fig.add_trace(
    go.Scatter(
        x=x_range,
        y=density,
        mode="lines",
        fill="tozeroy",
        fillcolor=f"rgba({BRAND_RGB}, 0.35)",
        line=dict(color=BRAND, width=2),
        name="Density",
        hovertemplate="Time: %{x:.1f} ms<br>Density: %{y:.4f}<extra></extra>",
    )
)

# Rug marks: one tick per observation at its exact value, just below the baseline
fig.add_trace(
    go.Scatter(
        x=values,
        y=np.full_like(values, -rug_height * 0.5),
        mode="markers",
        marker=dict(
            symbol="line-ns",
            size=9,
            color=f"rgba({BRAND_RGB}, 0.6)",
            line=dict(width=1.5, color=f"rgba({BRAND_RGB}, 0.6)"),
        ),
        name="Observations",
        hovertemplate="Response time: %{x:.1f} ms<extra></extra>",
    )
)

fig.update_layout(
    autosize=False,
    title=dict(
        text="density-rug · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text=RESPONSE_TIME, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        zeroline=False,
        showline=True,
        linewidth=1,
        linecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Density", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        zeroline=False,
        showline=True,
        linewidth=1,
        linecolor=INK_SOFT,
        range=[-rug_height * 1.5, peak * 1.08],
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    showlegend=True,
    legend=dict(
        font=dict(size=10, color=INK_SOFT),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=80, r=40, t=80, b=60),
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
