"""anyplot.ai
streamline-basic: Basic Streamline Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.integrate import solve_ivp


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Imprint palette position 1

# Columns: set these to your table's column names
STREAMLINE = "Streamline"  # role: extra
X = "X position (dimensionless)"  # role: x
Y = "Y position (dimensionless)"  # role: y
U = "Horizontal velocity u"  # role: u
V = "Vertical velocity v"  # role: v

# Data: replace this block with your own table, for example df = pd.read_csv("streamlines.csv")
# Vortex flow u = -y, v = x, integrated from seeds spread over the whole domain.
rows = []
for line_id, radius in enumerate(np.linspace(0.4, 3.6, 10)):
    sol = solve_ivp(
        lambda t, s: [-s[1], s[0]], (0, 2 * np.pi), [radius, 0.0], t_eval=np.linspace(0, 2 * np.pi, 200), rtol=1e-9
    )
    rows.append(pd.DataFrame({STREAMLINE: line_id, X: sol.y[0], Y: sol.y[1], U: -sol.y[1], V: sol.y[0]}))
df = pd.concat(rows, ignore_index=True)

# Plot: reads only df and the constants above
extent = np.ceil(max(df[X].abs().max(), df[Y].abs().max()) * 1.1)
title = "streamline-basic · python · plotly · anyplot.ai"

fig = go.Figure()
for _, line in df.groupby(STREAMLINE, sort=False):
    fig.add_trace(
        go.Scatter(
            x=line[X],
            y=line[Y],
            mode="lines",
            line={"color": BRAND, "width": 2.5, "simplify": False},
            customdata=line[[U, V]],
            hovertemplate="x=%{x:.2f}, y=%{y:.2f}<br>u=%{customdata[0]:.2f}, v=%{customdata[1]:.2f}<extra></extra>",
        )
    )

axis = {
    "tickfont": {"size": 11, "color": INK_SOFT},
    "showgrid": True,
    "gridcolor": GRID,
    "zeroline": False,
    "linecolor": INK_SOFT,
    "range": [-extent, extent],
}
fig.update_layout(
    autosize=False,
    width=600,
    height=600,
    title={"text": title, "font": {"size": 15, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={**axis, "title": {"text": X, "font": {"size": 13, "color": INK}}},
    yaxis={**axis, "title": {"text": Y, "font": {"size": 13, "color": INK}}, "scaleanchor": "x", "scaleratio": 1},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 80, "r": 40, "t": 70, "b": 70},
    showlegend=False,
)

# Output
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
