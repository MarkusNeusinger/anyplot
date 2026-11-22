"""anyplot.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26, 26, 23, 0.15)" if THEME == "light" else "rgba(240, 239, 232, 0.15)"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 20  # bins shared by every group
FILL_ALPHA = 0.2
LINE_DASHES = ["solid", "solid", "dash", "dot"]  # style is the second cue besides color

# Columns: set these to your table's column names
DELIVERY_TIME = "Delivery time (min)"  # role: values
COURIER = "Courier"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("deliveries.csv")
rng = np.random.default_rng(42)
df = pd.DataFrame(
    {
        DELIVERY_TIME: np.concatenate(
            [
                rng.normal(loc=22, scale=5, size=300),
                rng.normal(loc=36, scale=8, size=300),
                rng.lognormal(mean=np.log(52), sigma=0.3, size=300),
            ]
        ),
        COURIER: ["Bike courier"] * 300 + ["Van fleet"] * 300 + ["Postal service"] * 300,
    }
)

# Plot: reads only df and the constants above
# One set of bin edges for all groups, so every polygon has its vertices at the same x positions
edges = np.linspace(df[DELIVERY_TIME].min(), df[DELIVERY_TIME].max(), N_BINS + 1)
width = edges[1] - edges[0]
centers = (edges[:-1] + edges[1:]) / 2
# Close each polygon on the baseline one bin beyond the first and last midpoint
x_closed = np.concatenate([[centers[0] - width], centers, [centers[-1] + width]])

fig = go.Figure()
for i, (group, rows) in enumerate(df.groupby(COURIER, sort=False)):
    counts, _ = np.histogram(rows[DELIVERY_TIME], bins=edges)
    color = IMPRINT_PALETTE[i]
    r, g, b = (int(color[k : k + 2], 16) for k in (1, 3, 5))
    fig.add_trace(
        go.Scatter(
            x=x_closed,
            y=np.concatenate([[0], counts, [0]]),
            mode="lines+markers",
            name=str(group),
            line={"color": color, "width": 3, "dash": LINE_DASHES[i % len(LINE_DASHES)]},
            marker={"size": 7, "color": color},
            fill="tozeroy",
            fillcolor=f"rgba({r}, {g}, {b}, {FILL_ALPHA})",
        )
    )

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={"text": "frequency-polygon-basic · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}},
    xaxis={
        "title": {"text": DELIVERY_TIME, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Frequency (deliveries)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "rangemode": "tozero",
    },
    legend={
        "title": {"text": COURIER, "font": {"size": 10, "color": INK}},
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.98,
        "y": 0.98,
        "xanchor": "right",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 70, "r": 40, "t": 60, "b": 60},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
