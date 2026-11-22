"""anyplot.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: plotly 6.7.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SEPAL_LENGTH = "sepal length"  # role: features
SEPAL_WIDTH = "sepal width"  # role: extra
PETAL_LENGTH = "petal length"  # role: extra
PETAL_WIDTH = "petal width"  # role: extra
SPECIES = "Species"  # role: labels

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
iris = load_iris()
df = pd.DataFrame(iris.data, columns=[SEPAL_LENGTH, SEPAL_WIDTH, PETAL_LENGTH, PETAL_WIDTH])
df[SPECIES] = pd.Categorical.from_codes(iris.target, [name.capitalize() for name in iris.target_names])

# Plot: reads only df and the constants above
FEATURES = [SEPAL_LENGTH, SEPAL_WIDTH, PETAL_LENGTH, PETAL_WIDTH]
df = df.dropna(subset=FEATURES).reset_index(drop=True)  # PCA needs complete rows
X = StandardScaler().fit_transform(df[FEATURES])
pca = PCA(n_components=2)
scores = pca.fit_transform(X)
loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
var_explained = pca.explained_variance_ratio_ * 100

# One common factor scales every loading arrow to the spread of the scores
scale_factor = np.abs(scores).max() / np.abs(loadings).max() * 0.9

fig = go.Figure()

for i, (group, rows) in enumerate(df.groupby(SPECIES, sort=False, observed=True)):
    fig.add_trace(
        go.Scatter(
            x=scores[rows.index, 0],
            y=scores[rows.index, 1],
            mode="markers",
            marker={"size": 8, "color": IMPRINT_PALETTE[i], "opacity": 0.8, "line": {"width": 0.5, "color": PAGE_BG}},
            name=str(group),
        )
    )

# Loading arrows from the origin, each labeled at its tip
tips = loadings * scale_factor
lowest = int(np.argmin(tips[:, 1]))  # its label goes below the tip so near-parallel arrows keep apart
for k, ((load_x, load_y), name) in enumerate(zip(tips, FEATURES, strict=False)):
    fig.add_annotation(
        x=load_x,
        y=load_y,
        ax=0,
        ay=0,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.3,
        arrowwidth=2,
        arrowcolor=INK_SOFT,
    )
    fig.add_annotation(
        x=load_x,
        y=load_y,
        text=name,
        showarrow=False,
        font={"size": 12, "color": INK},
        xanchor="left" if load_x > 0 else "right",
        yanchor="top" if k == lowest else "bottom",
        xshift=6 if load_x > 0 else -6,
        yshift=-4 if k == lowest else 4,
    )

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    title={
        "text": "biplot-pca · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis={
        "title": {"text": f"PC1 ({var_explained[0]:.1f}%)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "zeroline": True,
        "zerolinewidth": 1,
        "zerolinecolor": INK_SOFT,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": f"PC2 ({var_explained[1]:.1f}%)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "zeroline": True,
        "zerolinewidth": 1,
        "zerolinecolor": INK_SOFT,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "scaleanchor": "x",
        "scaleratio": 1,
    },
    legend={
        "title": {"text": SPECIES, "font": {"size": 11, "color": INK}},
        "font": {"size": 11, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.98,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
