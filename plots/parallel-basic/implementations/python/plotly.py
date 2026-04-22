""" pyplots.ai
parallel-basic: Basic Parallel Coordinates Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Iris-like dataset for multivariate demonstration
np.random.seed(42)

# Generate data for 3 species with distinct characteristics
n_per_species = 50

# Setosa: small petals, medium sepals
setosa = pd.DataFrame(
    {
        "sepal_length": np.random.normal(5.0, 0.35, n_per_species),
        "sepal_width": np.random.normal(3.4, 0.38, n_per_species),
        "petal_length": np.random.normal(1.5, 0.17, n_per_species),
        "petal_width": np.random.normal(0.25, 0.11, n_per_species),
        "species": "setosa",
    }
)

# Versicolor: medium petals, medium sepals
versicolor = pd.DataFrame(
    {
        "sepal_length": np.random.normal(5.9, 0.52, n_per_species),
        "sepal_width": np.random.normal(2.8, 0.31, n_per_species),
        "petal_length": np.random.normal(4.3, 0.47, n_per_species),
        "petal_width": np.random.normal(1.3, 0.20, n_per_species),
        "species": "versicolor",
    }
)

# Virginica: large petals, large sepals
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

# Map species to numeric for color scale
species_map = {"setosa": 0, "versicolor": 1, "virginica": 2}
df["species_code"] = df["species"].map(species_map)

# Create parallel coordinates plot
fig = go.Figure(
    data=go.Parcoords(
        line={
            "color": df["species_code"],
            "colorscale": [[0, "#306998"], [0.5, "#FFD43B"], [1, "#4CAF50"]],
            "showscale": True,
            "colorbar": {
                "title": {"text": "Species", "font": {"size": 20}},
                "tickvals": [0, 1, 2],
                "ticktext": ["Setosa", "Versicolor", "Virginica"],
                "tickfont": {"size": 18},
                "len": 0.6,
                "y": 0.5,
            },
        },
        dimensions=[
            {"label": "Sepal Length (cm)", "values": df["sepal_length"], "range": [4, 8]},
            {"label": "Sepal Width (cm)", "values": df["sepal_width"], "range": [2, 4.5]},
            {"label": "Petal Length (cm)", "values": df["petal_length"], "range": [0.5, 7]},
            {"label": "Petal Width (cm)", "values": df["petal_width"], "range": [0, 2.8]},
        ],
        labelfont={"size": 22},
        tickfont={"size": 16},
        rangefont={"size": 14},
    )
)

# Layout - sized for 4800x2700 px output
fig.update_layout(
    title={
        "text": "Iris Flower Measurements · parallel-basic · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.95,
    },
    template="plotly_white",
    margin={"l": 80, "r": 180, "t": 120, "b": 80},
    paper_bgcolor="white",
    plot_bgcolor="white",
)

# Save as PNG (4800x2700 px) and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
