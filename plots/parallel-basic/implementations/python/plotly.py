""" anyplot.ai
parallel-basic: Basic Parallel Coordinates Plot
Library: plotly 6.7.0 | Python 3.14.4
Quality: 78/100 | Updated: 2026-04-27
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

# Okabe-Ito discrete colorscale: Setosa=#009E73, Versicolor=#D55E00, Virginica=#0072B2
OI_COLORSCALE = [
    [0.0, "#009E73"],
    [0.33, "#009E73"],
    [0.33, "#D55E00"],
    [0.67, "#D55E00"],
    [0.67, "#0072B2"],
    [1.0, "#0072B2"],
]

# Data - Iris-like dataset for multivariate demonstration
np.random.seed(42)
n_per_species = 50

setosa = pd.DataFrame(
    {
        "sepal_length": np.random.normal(5.0, 0.35, n_per_species),
        "sepal_width": np.random.normal(3.4, 0.38, n_per_species),
        "petal_length": np.random.normal(1.5, 0.17, n_per_species),
        "petal_width": np.random.normal(0.25, 0.11, n_per_species),
        "species": "setosa",
    }
)

versicolor = pd.DataFrame(
    {
        "sepal_length": np.random.normal(5.9, 0.52, n_per_species),
        "sepal_width": np.random.normal(2.8, 0.31, n_per_species),
        "petal_length": np.random.normal(4.3, 0.47, n_per_species),
        "petal_width": np.random.normal(1.3, 0.20, n_per_species),
        "species": "versicolor",
    }
)

virginica = pd.DataFrame(
    {
        "sepal_length": np.random.normal(6.6, 0.64, n_per_species),
        "sepal_width": np.random.normal(3.0, 0.32, n_per_species),
        "petal_length": np.random.normal(5.6, 0.55, n_per_species),
        "petal_width": np.random.normal(2.0, 0.27, n_per_species),
        "species": "virginica",
    }
)

df = pd.concat([setosa, versicolor, virginica], ignore_index=True)
species_map = {"setosa": 0, "versicolor": 1, "virginica": 2}
df["species_code"] = df["species"].map(species_map)

# Plot
fig = go.Figure(
    data=go.Parcoords(
        line={
            "color": df["species_code"],
            "colorscale": OI_COLORSCALE,
            "showscale": True,
            "cmin": 0,
            "cmax": 2,
            "colorbar": {
                "title": {"text": "Species", "font": {"size": 20, "color": INK}},
                "tickvals": [0, 1, 2],
                "ticktext": ["Setosa", "Versicolor", "Virginica"],
                "tickfont": {"size": 18, "color": INK_SOFT},
                "len": 0.6,
                "y": 0.5,
                "bgcolor": ELEVATED_BG,
                "bordercolor": INK_SOFT,
                "borderwidth": 1,
            },
        },
        dimensions=[
            {"label": "Sepal Length (cm)", "values": df["sepal_length"], "range": [4, 8]},
            {"label": "Sepal Width (cm)", "values": df["sepal_width"], "range": [2, 4.5]},
            {"label": "Petal Length (cm)", "values": df["petal_length"], "range": [0.5, 7]},
            {"label": "Petal Width (cm)", "values": df["petal_width"], "range": [0, 2.8]},
        ],
        labelfont={"size": 22, "color": INK},
        tickfont={"size": 16, "color": INK_SOFT},
        rangefont={"size": 14, "color": INK_SOFT},
    )
)

fig.update_layout(
    title={
        "text": "Iris Flower Measurements · parallel-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.95,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 80, "r": 180, "t": 120, "b": 80},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
