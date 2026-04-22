""" pyplots.ai
parallel-basic: Basic Parallel Coordinates Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Iris-like dataset with 4 dimensions and 3 species
np.random.seed(42)

# Generate realistic Iris-like measurements for 3 species
n_per_species = 50
species = ["Setosa", "Versicolor", "Virginica"]

data = []
for i, sp in enumerate(species):
    # Each species has distinct measurement patterns
    sepal_length = np.random.normal([5.0, 5.9, 6.6][i], 0.35, n_per_species)
    sepal_width = np.random.normal([3.4, 2.8, 3.0][i], 0.38, n_per_species)
    petal_length = np.random.normal([1.5, 4.3, 5.5][i], 0.17 + i * 0.25, n_per_species)
    petal_width = np.random.normal([0.2, 1.3, 2.0][i], 0.1 + i * 0.15, n_per_species)

    for j in range(n_per_species):
        data.append(
            {
                "Species": sp,
                "Sepal Length (cm)": sepal_length[j],
                "Sepal Width (cm)": sepal_width[j],
                "Petal Length (cm)": petal_length[j],
                "Petal Width (cm)": petal_width[j],
                "id": i * n_per_species + j,
            }
        )

df = pd.DataFrame(data)

# Normalize values to 0-1 range for parallel coordinates
dimensions = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]
for dim in dimensions:
    min_val = df[dim].min()
    max_val = df[dim].max()
    df[f"{dim}_norm"] = (df[dim] - min_val) / (max_val - min_val)

# Transform to long format for Altair parallel coordinates
df_long = df.melt(
    id_vars=["id", "Species"], value_vars=[f"{d}_norm" for d in dimensions], var_name="Dimension", value_name="Value"
)

# Clean dimension names for display
df_long["Dimension"] = df_long["Dimension"].str.replace("_norm", "")

# Define dimension order
dimension_order = dimensions

# Define colors (Python Blue, Python Yellow, and a third colorblind-safe color)
species_colors = ["#306998", "#FFD43B", "#E85D75"]

# Create the parallel coordinates chart
lines = (
    alt.Chart(df_long)
    .mark_line(strokeWidth=2.5, opacity=0.6)
    .encode(
        x=alt.X(
            "Dimension:N",
            sort=dimension_order,
            axis=alt.Axis(labelAngle=0, labelFontSize=20, titleFontSize=24, title=None, labelPadding=12),
        ),
        y=alt.Y(
            "Value:Q",
            scale=alt.Scale(domain=[0, 1]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, title="Normalized Value", tickCount=5),
        ),
        detail="id:N",
        color=alt.Color(
            "Species:N",
            scale=alt.Scale(domain=species, range=species_colors),
            legend=alt.Legend(
                title="Species", titleFontSize=22, labelFontSize=20, symbolSize=300, symbolStrokeWidth=4, orient="right"
            ),
        ),
    )
    .properties(
        width=1500, height=850, title=alt.Title("parallel-basic · altair · pyplots.ai", fontSize=30, anchor="middle")
    )
    .configure_view(strokeWidth=0)
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[4, 4])
)

# Save as PNG and HTML
lines.save("plot.png", scale_factor=3.0)
lines.save("plot.html")
