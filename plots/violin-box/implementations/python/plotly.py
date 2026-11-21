""" anyplot.ai
violin-box: Violin Plot with Embedded Box Plot
Library: plotly 7.1.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
COURIER = "Courier"  # role: group
DELIVERY_TIME = "Delivery time (minutes)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("deliveries.csv")
rng = np.random.default_rng(42)
couriers = {
    "SwiftDrop": rng.lognormal(mean=np.log(28), sigma=0.22, size=90),
    "MetroRun": rng.lognormal(mean=np.log(36), sigma=0.38, size=100),
    "ParcelPal": np.concatenate([rng.normal(24, 3.5, 45), rng.normal(48, 5, 45)]),
    "GreenWheel": rng.normal(42, 6, 80),
}
df = pd.DataFrame(
    {
        COURIER: np.repeat(list(couriers), [len(v) for v in couriers.values()]),
        DELIVERY_TIME: np.round(np.concatenate(list(couriers.values())), 1),
    }
)

# Plot: reads only df and the constants above
fig = go.Figure()
for i, (courier, rows) in enumerate(df.groupby(COURIER, sort=False)):
    fig.add_trace(
        go.Violin(
            y=rows[DELIVERY_TIME],
            name=str(courier),
            spanmode="hard",
            fillcolor=IMPRINT_PALETTE[i],
            opacity=0.75,
            line={"color": INK_SOFT, "width": 1.5},
            box={"visible": True, "width": 0.2, "fillcolor": PAGE_BG, "line": {"color": INK, "width": 1.5}},
            points="outliers",
            pointpos=0,
            marker={"size": 5, "color": INK, "opacity": 0.7},
        )
    )

# Style
fig.update_layout(
    autosize=False,
    title={"text": "violin-box · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}, "x": 0.5},
    xaxis={
        "title": {"text": COURIER, "font": {"size": 13, "color": INK}},
        "tickfont": {"size": 11, "color": INK_SOFT},
        "showgrid": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": DELIVERY_TIME, "font": {"size": 13, "color": INK}},
        "tickfont": {"size": 11, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    template="plotly_white",
    showlegend=False,
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 80, "r": 40, "t": 70, "b": 65},
    violingap=0.1,
    violinmode="overlay",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
