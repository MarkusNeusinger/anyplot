"""anyplot.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-17
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
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: position 1 is the single series colour
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Constants
N_LEVELS = 7  # letter-value levels: quartiles, eighths, sixteenths, ...
MAX_OUTLIERS = 100  # outlier points drawn per category

# Columns: set these to your table's column names
ENDPOINT = "Server endpoint"  # role: category
RESPONSE = "Response time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("responses.csv")
rng = np.random.default_rng(42)
n_points = 5000
df = pd.DataFrame(
    {
        ENDPOINT: np.repeat(["API Gateway", "Auth Service", "Data Query", "File Upload"], n_points),
        RESPONSE: np.concatenate(
            [
                rng.lognormal(mean=4, sigma=0.5, size=int(n_points * 0.9)),
                rng.uniform(200, 500, size=int(n_points * 0.1)),
                rng.exponential(scale=30, size=n_points) + 10,
                rng.normal(loc=100, scale=20, size=int(n_points * 0.7)),
                rng.normal(loc=250, scale=30, size=int(n_points * 0.3)),
                rng.gamma(shape=2, scale=50, size=int(n_points * 0.85)),
                rng.uniform(400, 800, size=int(n_points * 0.15)),
            ]
        ),
    }
)

# Plot: reads only df and the constants above
groups = list(df.groupby(ENDPOINT, sort=False))
red, green, blue = (int(BRAND[i : i + 2], 16) for i in (1, 3, 5))
alphas = np.linspace(1.0, 0.2, N_LEVELS)
level_colors = [f"rgba({red}, {green}, {blue}, {a:.2f})" for a in alphas]
level_labels = [f"{(1 - 0.5**k) * 100:.4g}%" for k in range(1, N_LEVELS + 1)]
level_labels[0] += " (IQR)"
max_width = 0.7
jitter_rng = np.random.default_rng(7)  # horizontal spread and subsampling of the outlier points only

fig = go.Figure()
for pos, (name, rows) in enumerate(groups):
    values = rows[RESPONSE].to_numpy()
    median = np.median(values)

    # Letter values: level k spans the quantiles 1/2^(k+1) and 1 - 1/2^(k+1)
    bounds = [np.quantile(values, [0.5 ** (k + 1), 1 - 0.5 ** (k + 1)]) for k in range(1, N_LEVELS + 1)]

    # Outermost (widest, lightest) first so the inner boxes sit on top
    for k in range(N_LEVELS, 0, -1):
        lower, upper = bounds[k - 1]
        half = max_width * (1 - (k - 1) * 0.15) / 2
        fig.add_shape(
            type="rect",
            x0=pos - half,
            x1=pos + half,
            y0=lower,
            y1=upper,
            fillcolor=level_colors[k - 1],
            line={"color": INK_SOFT, "width": 0.75},
            layer="below",
        )

    fig.add_shape(
        type="line",
        x0=pos - max_width / 2,
        x1=pos + max_width / 2,
        y0=median,
        y1=median,
        line={"color": INK, "width": 2.5},
    )

    # Observations beyond the deepest letter value
    low, high = bounds[-1]
    outliers = values[(values < low) | (values > high)]
    if len(outliers) > MAX_OUTLIERS:
        outliers = jitter_rng.choice(outliers, MAX_OUTLIERS, replace=False)
    fig.add_trace(
        go.Scatter(
            x=pos + jitter_rng.uniform(-0.08, 0.08, size=len(outliers)),
            y=outliers,
            mode="markers",
            marker={"color": BRAND, "size": 6, "opacity": 0.7},
            showlegend=False,
            hovertemplate=f"{name}: %{{y:.0f}} ms<extra></extra>",
        )
    )

# Legend entries for the quantile levels and the median
for color, label in zip(level_colors, level_labels, strict=True):
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker={"size": 12, "color": color, "symbol": "square", "line": {"color": INK_SOFT, "width": 0.75}},
            name=label,
        )
    )
fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line={"color": INK, "width": 2.5}, name="Median"))

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin={"l": 80, "r": 120, "t": 70, "b": 60},
    title={
        "text": "boxen-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": ENDPOINT, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickvals": list(range(len(groups))),
        "ticktext": [name for name, _ in groups],
        "range": [-0.6, len(groups) - 0.4],
        "showgrid": False,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": RESPONSE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "title": {"text": "Quantile level", "font": {"size": 11, "color": INK}},
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
