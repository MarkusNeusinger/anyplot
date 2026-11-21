""" anyplot.ai
cat-box-strip: Box Plot with Strip Overlay
Library: plotly 7.1.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
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

# Imprint palette: single series uses position 1
BRAND = "#009E73"
BRAND_FILL = "rgba(0, 158, 115, 0.15)"

# Columns: set these to your table's column names
METHOD = "Study Method"  # role: category
SCORE = "Exam Score (%)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
scores_c = np.concatenate([rng.normal(58, 10, 27), [25, 28, 95]])
scores_d = np.concatenate([rng.normal(65, 6, 22), rng.normal(80, 6, 23)])
groups = {
    "Method A": rng.normal(72, 8, 35),
    "Method B": rng.normal(85, 5, 40),
    "Method C": scores_c,
    "Method D": scores_d,
}
df = pd.DataFrame(
    {METHOD: [name for name, values in groups.items() for _ in values], SCORE: np.concatenate(list(groups.values()))}
)

# Plot: reads only df and the constants above
fig = go.Figure(
    go.Box(
        x=df[METHOD],
        y=df[SCORE],
        boxpoints="all",
        jitter=0.5,
        pointpos=0,
        boxmean=False,
        width=0.55,
        line={"color": BRAND, "width": 1.5},
        fillcolor=BRAND_FILL,
        marker={"size": 6, "color": BRAND, "opacity": 0.75, "line": {"color": PAGE_BG, "width": 0.5}},
        showlegend=False,
    )
)

# Style
fig.update_layout(
    autosize=False,
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    title={"text": "cat-box-strip · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}},
    xaxis={
        "title": {"text": METHOD, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "linecolor": INK_SOFT,
        "showgrid": False,
    },
    yaxis={
        "title": {"text": SCORE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    hovermode="closest",
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
