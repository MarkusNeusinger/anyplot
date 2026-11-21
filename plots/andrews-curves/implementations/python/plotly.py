"""anyplot.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: plotly 6.7.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.datasets import load_iris


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
VARIABLES = ["sepal length (cm)", "sepal width (cm)", "petal length (cm)", "petal width (cm)"]  # role: variable_
SPECIES = "species"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("flowers.csv")
iris = load_iris()
df = pd.DataFrame(iris.data, columns=VARIABLES)
df[SPECIES] = pd.Categorical.from_codes(iris.target, iris.target_names)

# Plot: reads only df and the constants above
Z = ((df[VARIABLES] - df[VARIABLES].mean()) / df[VARIABLES].std(ddof=0)).to_numpy()
t = np.linspace(-np.pi, np.pi, 200)

# Andrews basis: 1/sqrt(2), sin t, cos t, sin 2t, cos 2t, ...
basis = [np.full_like(t, 1 / np.sqrt(2))]
for j in range(1, len(VARIABLES)):
    freq = (j + 1) // 2
    basis.append(np.sin(freq * t) if j % 2 == 1 else np.cos(freq * t))
curves = Z @ np.array(basis)

fig = go.Figure()
for g, (species, rows) in enumerate(df.groupby(SPECIES, sort=False, observed=True)):
    for k, idx in enumerate(rows.index):
        fig.add_trace(
            go.Scatter(
                x=t,
                y=curves[df.index.get_loc(idx)],
                mode="lines",
                line=dict(color=IMPRINT_PALETTE[g], width=2),
                opacity=0.4,
                name=str(species),
                legendgroup=str(species),
                showlegend=(k == 0),
                hovertemplate=f"{species}<br>t: %{{x:.2f}}<br>f(t): %{{y:.2f}}<extra></extra>",
            )
        )

# Style
axis_style = dict(
    tickfont=dict(size=12, color=INK_SOFT),
    gridcolor=GRID,
    gridwidth=0.5,
    zeroline=True,
    zerolinecolor=GRID,
    zerolinewidth=1,
    linecolor=INK_SOFT,
)
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title=dict(
        text="andrews-curves · python · plotly · anyplot.ai", font=dict(size=18, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Parameter t (radians)", font=dict(size=14, color=INK)),
        range=[-np.pi, np.pi],
        tickvals=[-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi],
        ticktext=["-π", "-π/2", "0", "π/2", "π"],
        **axis_style,
    ),
    yaxis=dict(title=dict(text="f(t) (normalized units)", font=dict(size=14, color=INK)), **axis_style),
    legend=dict(
        title=dict(text=SPECIES, font=dict(size=12, color=INK)),
        font=dict(size=12, color=INK_SOFT),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=80, r=40, t=70, b=60),
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    font=dict(color=INK),
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
