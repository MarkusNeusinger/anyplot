"""anyplot.ai
scatter-matrix: Scatter Plot Matrix
Library: plotly 6.7.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SEED = 42

# Columns
TEMPERATURE = "Temperature (°C)"  # role: variables
HUMIDITY = "Humidity (%)"  # role: variables
PRESSURE = "Pressure (hPa)"  # role: variables
WIND_SPEED = "Wind Speed (m/s)"  # role: variables
REGION = "Region"  # role: category

# Data: weather station measurements from three regions
rng = np.random.RandomState(SEED)
regions = ["Coastal", "Mountain", "Desert"]
n_per_region = 66
# (mean, std) per region for each variable
profile = {
    TEMPERATURE: [(18, 2.5), (12, 3.0), (28, 4.0)],
    HUMIDITY: [(72, 8), (65, 10), (35, 12)],
    PRESSURE: [(1013, 2), (950, 3), (1010, 2)],
    WIND_SPEED: [(4.5, 1.5), (6.0, 2.0), (3.5, 1.2)],
}
columns = {REGION: np.repeat(regions, n_per_region)}
for column, params in profile.items():
    columns[column] = np.concatenate([rng.normal(mean, std, n_per_region) for mean, std in params])
df = pd.DataFrame(columns)

# Plot
dimensions = [TEMPERATURE, HUMIDITY, PRESSURE, WIND_SPEED]
n_dims = len(dimensions)
groups = list(df.groupby(REGION, sort=False))

fig = make_subplots(rows=n_dims, cols=n_dims, horizontal_spacing=0.035, vertical_spacing=0.035)

for i, dim_y in enumerate(dimensions):
    for j, dim_x in enumerate(dimensions):
        row, col = i + 1, j + 1
        for k, (region, rows) in enumerate(groups):
            color = IMPRINT_PALETTE[k % len(IMPRINT_PALETTE)]
            if i == j:
                trace = go.Histogram(
                    x=rows[dim_x],
                    name=str(region),
                    marker=dict(color=color),
                    opacity=0.75,
                    nbinsx=15,
                    showlegend=(i == 0),
                    legendgroup=str(region),
                )
            else:
                trace = go.Scatter(
                    x=rows[dim_x],
                    y=rows[dim_y],
                    mode="markers",
                    name=str(region),
                    marker=dict(color=color, size=4, opacity=0.55),
                    showlegend=False,
                    legendgroup=str(region),
                )
            fig.add_trace(trace, row=row, col=col)

# Shared ranges: one range per variable, used by its column (x) and its row (y)
ranges = {}
for dim in dimensions:
    pad = (df[dim].max() - df[dim].min()) * 0.06
    ranges[dim] = [df[dim].min() - pad, df[dim].max() + pad]

for i, dim_y in enumerate(dimensions):
    for j, dim_x in enumerate(dimensions):
        row, col = i + 1, j + 1
        fig.update_xaxes(
            range=ranges[dim_x],
            nticks=3,
            showticklabels=(i == n_dims - 1),
            title_text=dim_x if i == n_dims - 1 else None,
            title_font=dict(size=12, color=INK),
            title_standoff=4,
            row=row,
            col=col,
        )
        if i == j:
            fig.update_yaxes(showticklabels=False, row=row, col=col)
            if j == 0:
                fig.update_yaxes(
                    title_text=dim_y, title_font=dict(size=12, color=INK), title_standoff=4, row=row, col=col
                )
        else:
            fig.update_yaxes(
                range=ranges[dim_y],
                nticks=3,
                showticklabels=(j == 0),
                title_text=dim_y if j == 0 else None,
                title_font=dict(size=12, color=INK),
                title_standoff=4,
                row=row,
                col=col,
            )

fig.update_layout(
    autosize=False,
    title=dict(text="scatter-matrix · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(size=10, color=INK),
    legend=dict(
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        font=dict(size=11, color=INK_SOFT),
        title=dict(text=REGION, font=dict(size=12, color=INK)),
        orientation="h",
        yanchor="bottom",
        y=1.01,
        xanchor="center",
        x=0.5,
    ),
    showlegend=True,
    barmode="overlay",
    margin=dict(l=60, r=20, t=85, b=50),
)

fig.update_xaxes(
    tickfont=dict(size=10, color=INK_SOFT), showgrid=True, gridcolor=GRID, linecolor=INK_SOFT, zeroline=False
)
fig.update_yaxes(
    tickfont=dict(size=10, color=INK_SOFT), showgrid=True, gridcolor=GRID, linecolor=INK_SOFT, zeroline=False
)

# Save
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
