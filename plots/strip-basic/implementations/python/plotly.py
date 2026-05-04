""" anyplot.ai
strip-basic: Basic Strip Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-04
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette — first series always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Survey response scores grouped by demographic category
np.random.seed(42)

categories = ["Group A", "Group B", "Group C", "Group D"]
n_per_group = [45, 60, 50, 55]

data = {
    "Group A": np.random.normal(65, 12, n_per_group[0]),
    "Group B": np.random.normal(78, 8, n_per_group[1]),
    "Group C": np.random.normal(55, 15, n_per_group[2]),
    "Group D": np.random.normal(70, 10, n_per_group[3]),
}

# Plot
fig = go.Figure()

for i, (cat, values) in enumerate(data.items()):
    jitter = np.random.uniform(-0.2, 0.2, len(values))
    x_positions = np.full(len(values), i) + jitter

    fig.add_trace(
        go.Scatter(
            x=x_positions,
            y=values,
            mode="markers",
            name=cat,
            marker={"size": 14, "opacity": 0.6, "color": OKABE_ITO[i]},
            hovertemplate=f"{cat}<br>Value: %{{y:.1f}}<extra></extra>",
        )
    )

# Mean reference lines
for i, (_cat, values) in enumerate(data.items()):
    mean_val = np.mean(values)
    fig.add_shape(type="line", x0=i - 0.3, x1=i + 0.3, y0=mean_val, y1=mean_val, line={"color": INK, "width": 3})

# Style
fig.update_layout(
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    title={
        "text": "strip-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Category", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "tickmode": "array",
        "tickvals": list(range(len(categories))),
        "ticktext": categories,
        "showgrid": False,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Response Score", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    showlegend=True,
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 16, "color": INK_SOFT},
        "x": 1.02,
        "y": 0.5,
        "xanchor": "left",
        "yanchor": "middle",
    },
    margin={"l": 80, "r": 160, "t": 100, "b": 80},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
