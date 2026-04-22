""" pyplots.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Synthetic Iris-like multivariate data
np.random.seed(42)

# Generate 3 clusters representing different plant species
n_per_species = 50
species_data = []

# Species A: small petals, medium sepals
species_data.append(
    pd.DataFrame(
        {
            "Sepal Length (cm)": np.random.normal(5.0, 0.35, n_per_species),
            "Sepal Width (cm)": np.random.normal(3.4, 0.38, n_per_species),
            "Petal Length (cm)": np.random.normal(1.5, 0.17, n_per_species),
            "Petal Width (cm)": np.random.normal(0.25, 0.1, n_per_species),
            "Species": "setosa",
        }
    )
)

# Species B: medium petals, medium sepals
species_data.append(
    pd.DataFrame(
        {
            "Sepal Length (cm)": np.random.normal(5.9, 0.52, n_per_species),
            "Sepal Width (cm)": np.random.normal(2.8, 0.31, n_per_species),
            "Petal Length (cm)": np.random.normal(4.3, 0.47, n_per_species),
            "Petal Width (cm)": np.random.normal(1.3, 0.2, n_per_species),
            "Species": "versicolor",
        }
    )
)

# Species C: large petals, large sepals
species_data.append(
    pd.DataFrame(
        {
            "Sepal Length (cm)": np.random.normal(6.6, 0.64, n_per_species),
            "Sepal Width (cm)": np.random.normal(3.0, 0.32, n_per_species),
            "Petal Length (cm)": np.random.normal(5.5, 0.55, n_per_species),
            "Petal Width (cm)": np.random.normal(2.0, 0.27, n_per_species),
            "Species": "virginica",
        }
    )
)

df = pd.concat(species_data, ignore_index=True)

# Variables for SPLOM
variables = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]

# Color scale for species
color_scale = alt.Scale(domain=["setosa", "versicolor", "virginica"], range=["#306998", "#FFD43B", "#E35F62"])

# Build SPLOM manually as a grid of charts
# Use simpler encoding without conditional opacity for PNG export
rows = []
for row_idx, y_var in enumerate(variables):
    row_charts = []
    for col_idx, x_var in enumerate(variables):
        if x_var == y_var:
            # Diagonal: KDE/histogram for each variable
            chart = (
                alt.Chart(df)
                .transform_density(x_var, as_=[x_var, "density"], groupby=["Species"])
                .mark_area(opacity=0.6)
                .encode(
                    x=alt.X(
                        f"{x_var}:Q",
                        title=x_var if row_idx == len(variables) - 1 else "",
                        axis=alt.Axis(labelFontSize=14, titleFontSize=14, labelAngle=-45),
                    ),
                    y=alt.Y(
                        "density:Q",
                        title="Density" if col_idx == 0 else "",
                        axis=alt.Axis(labelFontSize=14, titleFontSize=14),
                    ),
                    color=alt.Color("Species:N", scale=color_scale, legend=None),
                )
                .properties(width=230, height=230)
            )
        else:
            # Off-diagonal: scatter plot
            chart = (
                alt.Chart(df)
                .mark_point(size=100, filled=True, opacity=0.7)
                .encode(
                    x=alt.X(
                        f"{x_var}:Q",
                        title=x_var if row_idx == len(variables) - 1 else "",
                        axis=alt.Axis(labelFontSize=14, titleFontSize=14, labelAngle=-45),
                    ),
                    y=alt.Y(
                        f"{y_var}:Q",
                        title=y_var if col_idx == 0 else "",
                        axis=alt.Axis(labelFontSize=14, titleFontSize=14),
                    ),
                    color=alt.Color("Species:N", scale=color_scale, legend=None),
                    tooltip=["Species:N"] + [alt.Tooltip(v, format=".2f") for v in variables],
                )
                .properties(width=230, height=230)
            )
        row_charts.append(chart)
    rows.append(alt.hconcat(*row_charts, spacing=10))

# Create legend as a separate chart
legend_chart = (
    alt.Chart(df)
    .mark_point(size=150, filled=True)
    .encode(
        y=alt.Y("Species:N", title="", axis=alt.Axis(labelFontSize=18, orient="right")),
        color=alt.Color("Species:N", scale=color_scale, legend=None),
    )
    .properties(width=50, height=150, title=alt.Title("Species", fontSize=20))
)

# Combine all rows vertically
matrix = alt.vconcat(*rows, spacing=10).properties(
    title=alt.Title(
        "scatter-matrix-interactive · altair · pyplots.ai",
        fontSize=28,
        anchor="middle",
        subtitle="Interactive Scatter Plot Matrix | Brush to select in HTML version",
        subtitleFontSize=18,
    )
)

# Final chart with legend
final_chart = (
    alt.hconcat(matrix, legend_chart, spacing=40)
    .configure_axis(grid=True, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save PNG version (static) - target 3600x3600 for square format
final_chart.save("plot.png", scale_factor=3.0)

# Create interactive HTML version with brush selection
brush = alt.selection_interval(name="brush", resolve="global")

interactive_chart = (
    alt.Chart(df)
    .mark_point(size=80, filled=True)
    .encode(
        alt.X(
            alt.repeat("column"), type="quantitative", axis=alt.Axis(labelFontSize=14, titleFontSize=14, labelAngle=-45)
        ),
        alt.Y(alt.repeat("row"), type="quantitative", axis=alt.Axis(labelFontSize=14, titleFontSize=14)),
        color=alt.condition(
            brush,
            alt.Color(
                "Species:N",
                scale=color_scale,
                legend=alt.Legend(titleFontSize=18, labelFontSize=16, orient="right", title="Species"),
            ),
            alt.value("lightgray"),
        ),
        opacity=alt.condition(brush, alt.value(0.8), alt.value(0.15)),
        tooltip=["Species:N"] + [alt.Tooltip(v, format=".2f") for v in variables],
    )
    .properties(width=180, height=180)
    .add_params(brush)
    .repeat(row=variables, column=variables)
    .properties(
        title=alt.Title(
            "scatter-matrix-interactive · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            subtitle="Brush any subplot to select points across all panels",
            subtitleFontSize=18,
        )
    )
    .configure_axis(grid=True, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

interactive_chart.save("plot.html")
