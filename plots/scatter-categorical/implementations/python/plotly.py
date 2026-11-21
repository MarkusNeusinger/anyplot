"""anyplot.ai
scatter-categorical: Categorical Scatter Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
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
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
MARKETING = "Marketing Investment (%)"  # role: x
SALES_GROWTH = "Sales Growth (%)"  # role: y
REGION = "Region"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("regions.csv")
rng = np.random.default_rng(42)
n_per_group = 40
centers = {"North": (35, 8, 75, 10), "South": (55, 10, 60, 12), "West": (70, 7, 85, 8), "East": (45, 9, 45, 10)}
df = pd.concat(
    [
        pd.DataFrame(
            {MARKETING: rng.normal(mx, sx, n_per_group), SALES_GROWTH: rng.normal(my, sy, n_per_group), REGION: region}
        )
        for region, (mx, sx, my, sy) in centers.items()
    ],
    ignore_index=True,
)

# Plot
fig = go.Figure()
for i, (region, rows) in enumerate(df.groupby(REGION, sort=False)):
    fig.add_trace(
        go.Scatter(
            x=rows[MARKETING],
            y=rows[SALES_GROWTH],
            mode="markers",
            name=str(region),
            marker={
                "size": 10,
                "color": IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
                "opacity": 0.75,
                "line": {"width": 0.8, "color": PAGE_BG},
            },
            hovertemplate=f"{region}<br>{MARKETING}: %{{x:.1f}}<br>{SALES_GROWTH}: %{{y:.1f}}<extra></extra>",
        )
    )

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "scatter-categorical · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": MARKETING, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "showgrid": True,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": SALES_GROWTH, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "showgrid": True,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    legend={
        "title": {"text": REGION, "font": {"size": 11, "color": INK}},
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "x": 1.02,
        "y": 0.5,
        "yanchor": "middle",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 80, "r": 100, "t": 80, "b": 60},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
