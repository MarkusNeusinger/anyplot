""" anyplot.ai
cat-box-strip: Box Plot with Strip Overlay
Library: plotly 6.7.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-13
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
BRAND = "#009E73"  # Okabe-Ito position 1
SERIES2 = "#C475FD"  # Okabe-Ito position 2

# Data - Exam scores across different study methods
np.random.seed(42)

categories = ["Methods A", "Method B", "Method C", "Method D"]
n_per_group = [35, 40, 30, 45]

data = []
# Method A: Normal distribution, moderate spread
data.extend([{"Method": "Method A", "Score": v} for v in np.random.normal(72, 8, n_per_group[0])])
# Method B: Higher scores, tighter spread
data.extend([{"Method": "Method B", "Score": v} for v in np.random.normal(85, 5, n_per_group[1])])
# Method C: Lower scores with some outliers
scores_c = np.concatenate([np.random.normal(58, 10, n_per_group[2] - 3), [25, 28, 95]])
data.extend([{"Method": "Method C", "Score": v} for v in scores_c])
# Method D: Bimodal distribution
scores_d = np.concatenate(
    [np.random.normal(65, 6, n_per_group[3] // 2), np.random.normal(80, 6, n_per_group[3] - n_per_group[3] // 2)]
)
data.extend([{"Method": "Method D", "Score": v} for v in scores_d])

df = pd.DataFrame(data)

# Create figure
fig = go.Figure()

# Add box plots for each category using native boxpoints
for cat in categories:
    cat_data = df[df["Method"] == cat]["Score"]
    fig.add_trace(
        go.Box(
            y=cat_data,
            name=cat,
            boxmean=False,
            marker_color=BRAND,
            line=dict(color=BRAND, width=2),
            fillcolor="rgba(0, 158, 115, 0.15)",
            boxpoints="all",
            jitter=0.3,
            pointpos=-1.5,
            marker=dict(size=10, color=BRAND, opacity=0.7, line=dict(color=PAGE_BG, width=0.5)),
            showlegend=False,
        )
    )

# Update layout with theme-adaptive styling
fig.update_layout(
    title=dict(text="cat-box-strip · plotly · anyplot.ai", font=dict(size=28, color=INK)),
    xaxis=dict(
        title=dict(text="Study Method", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Exam Score (%)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    showlegend=False,
    margin=dict(l=80, r=50, t=100, b=80),
    hovermode="closest",
)

# Save as PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
