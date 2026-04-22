""" pyplots.ai
scatter-categorical: Categorical Scatter Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 100/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Iris-like measurements by species
np.random.seed(42)

# Generate measurements for 3 plant species
n_per_species = 50
species_names = ["Setosa", "Versicolor", "Virginica"]

data = []
for i, species in enumerate(species_names):
    # Different distributions for each species
    base_petal_length = [1.4, 4.2, 5.5][i]
    base_petal_width = [0.2, 1.3, 2.0][i]
    spread = [0.2, 0.5, 0.6][i]

    petal_length = np.random.normal(base_petal_length, spread, n_per_species)
    petal_width = np.random.normal(base_petal_width, spread * 0.5, n_per_species)

    for pl, pw in zip(petal_length, petal_width, strict=True):
        data.append({"Petal Length (cm)": pl, "Petal Width (cm)": pw, "Species": species})

df = pd.DataFrame(data)

# Create chart
chart = (
    alt.Chart(df)
    .mark_point(size=200, opacity=0.7, filled=True)
    .encode(
        x=alt.X("Petal Length (cm):Q", title="Petal Length (cm)", scale=alt.Scale(zero=False)),
        y=alt.Y("Petal Width (cm):Q", title="Petal Width (cm)", scale=alt.Scale(zero=False)),
        color=alt.Color(
            "Species:N",
            scale=alt.Scale(domain=species_names, range=["#306998", "#FFD43B", "#6B8E23"]),
            legend=alt.Legend(title="Species", titleFontSize=20, labelFontSize=18, symbolSize=200),
        ),
        shape=alt.Shape("Species:N", legend=None),
        tooltip=["Species:N", "Petal Length (cm):Q", "Petal Width (cm):Q"],
    )
    .properties(width=1600, height=900, title=alt.Title("scatter-categorical · altair · pyplots.ai", fontSize=28))
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG (4800 x 2700 with scale_factor=3)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactive version
chart.save("plot.html")
