""" pyplots.ai
scatter-matrix: Scatter Plot Matrix
Library: altair 6.0.0 | Python 3.13.11
Quality: 85/100 | Created: 2025-12-26
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Iris dataset (classic multivariate data)
np.random.seed(42)

# Generate realistic iris-like data with 4 variables and 3 species
n_per_species = 50

data = []
# Setosa - smaller flowers
for _ in range(n_per_species):
    data.append(
        {
            "Sepal Length (cm)": np.random.normal(5.0, 0.35),
            "Sepal Width (cm)": np.random.normal(3.4, 0.38),
            "Petal Length (cm)": np.random.normal(1.5, 0.17),
            "Petal Width (cm)": np.random.normal(0.25, 0.1),
            "Species": "Setosa",
        }
    )

# Versicolor - medium flowers
for _ in range(n_per_species):
    data.append(
        {
            "Sepal Length (cm)": np.random.normal(5.9, 0.52),
            "Sepal Width (cm)": np.random.normal(2.8, 0.31),
            "Petal Length (cm)": np.random.normal(4.3, 0.47),
            "Petal Width (cm)": np.random.normal(1.3, 0.2),
            "Species": "Versicolor",
        }
    )

# Virginica - larger flowers
for _ in range(n_per_species):
    data.append(
        {
            "Sepal Length (cm)": np.random.normal(6.6, 0.64),
            "Sepal Width (cm)": np.random.normal(3.0, 0.32),
            "Petal Length (cm)": np.random.normal(5.5, 0.55),
            "Petal Width (cm)": np.random.normal(2.0, 0.27),
            "Species": "Virginica",
        }
    )

df = pd.DataFrame(data)

# Variables for the scatter matrix
variables = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]

# Color scheme - Distinct colorblind-safe palette (blue, orange, green)
color_scale = alt.Scale(domain=["Setosa", "Versicolor", "Virginica"], range=["#306998", "#E69F00", "#009E73"])

# Use Altair's native repeat() for declarative scatter matrix construction
# This is the idiomatic Altair approach for creating SPLOM (scatter plot matrix)
scatter_matrix = (
    alt.Chart(df)
    .mark_circle(size=100, opacity=0.7)
    .encode(
        alt.X(alt.repeat("column"), type="quantitative", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        alt.Y(alt.repeat("row"), type="quantitative", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        alt.Color(
            "Species:N",
            scale=color_scale,
            legend=alt.Legend(
                title="Species",
                titleFontSize=28,
                labelFontSize=24,
                symbolSize=400,
                orient="right",
                titlePadding=15,
                labelPadding=10,
            ),
        ),
        tooltip=[
            "Species:N",
            alt.Tooltip(alt.repeat("column"), type="quantitative"),
            alt.Tooltip(alt.repeat("row"), type="quantitative"),
        ],
    )
    .properties(width=320, height=320)
    .repeat(row=variables, column=variables)
)

# Apply configuration and title
chart = (
    scatter_matrix.properties(
        title=alt.Title(text="scatter-matrix · altair · pyplots.ai", fontSize=36, anchor="middle", offset=25)
    )
    .configure_axis(gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG (scale_factor=3 gives us ~3840x3840 for square output close to 3600x3600 target)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart.save("plot.html")
