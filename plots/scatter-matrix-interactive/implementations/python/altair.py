""" anyplot.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os
import sys


# Remove current directory from path to avoid shadowing altair module
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != script_dir]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Synthetic Iris-like multivariate data
np.random.seed(42)

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

variables = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]

# Static PNG version
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
                        axis=alt.Axis(
                            labelFontSize=18,
                            titleFontSize=22,
                            labelAngle=-45,
                            labelColor=INK_SOFT,
                            titleColor=INK,
                            domainColor=INK_SOFT,
                            tickColor=INK_SOFT,
                            gridColor=INK,
                            gridOpacity=0.10,
                        ),
                    ),
                    y=alt.Y(
                        "density:Q",
                        title="Density" if col_idx == 0 else "",
                        axis=alt.Axis(
                            labelFontSize=18,
                            titleFontSize=22,
                            labelColor=INK_SOFT,
                            titleColor=INK,
                            domainColor=INK_SOFT,
                            tickColor=INK_SOFT,
                            gridColor=INK,
                            gridOpacity=0.10,
                        ),
                    ),
                    color=alt.Color(
                        "Species:N",
                        scale=alt.Scale(domain=["setosa", "versicolor", "virginica"], range=IMPRINT),
                        legend=None,
                    ),
                )
                .properties(width=220, height=220)
            )
        else:
            # Off-diagonal: scatter plot
            chart = (
                alt.Chart(df)
                .mark_point(size=80, filled=True, opacity=0.7)
                .encode(
                    x=alt.X(
                        f"{x_var}:Q",
                        title=x_var if row_idx == len(variables) - 1 else "",
                        axis=alt.Axis(
                            labelFontSize=18,
                            titleFontSize=22,
                            labelAngle=-45,
                            labelColor=INK_SOFT,
                            titleColor=INK,
                            domainColor=INK_SOFT,
                            tickColor=INK_SOFT,
                            gridColor=INK,
                            gridOpacity=0.10,
                        ),
                    ),
                    y=alt.Y(
                        f"{y_var}:Q",
                        title=y_var if col_idx == 0 else "",
                        axis=alt.Axis(
                            labelFontSize=18,
                            titleFontSize=22,
                            labelColor=INK_SOFT,
                            titleColor=INK,
                            domainColor=INK_SOFT,
                            tickColor=INK_SOFT,
                            gridColor=INK,
                            gridOpacity=0.10,
                        ),
                    ),
                    color=alt.Color(
                        "Species:N",
                        scale=alt.Scale(domain=["setosa", "versicolor", "virginica"], range=IMPRINT),
                        legend=None,
                    ),
                    tooltip=["Species:N"] + [alt.Tooltip(v, format=".2f") for v in variables],
                )
                .properties(width=220, height=220)
            )
        row_charts.append(chart)
    rows.append(alt.hconcat(*row_charts, spacing=10))

# Create legend as a separate chart
legend_chart = (
    alt.Chart(df)
    .mark_point(size=150, filled=True)
    .encode(
        y=alt.Y("Species:N", title="", axis=alt.Axis(labelFontSize=18, orient="right")),
        color=alt.Color(
            "Species:N", scale=alt.Scale(domain=["setosa", "versicolor", "virginica"], range=IMPRINT), legend=None
        ),
    )
    .properties(width=50, height=150, title=alt.Title("Species", fontSize=22))
)

# Combine all rows vertically
matrix = alt.vconcat(*rows, spacing=10).properties(
    title=alt.Title(
        "scatter-matrix-interactive · python · altair · anyplot.ai",
        fontSize=28,
        anchor="middle",
        color=INK,
        subtitle="Interactive Scatter Plot Matrix",
        subtitleFontSize=18,
    )
)

# Final static chart with legend and styling
static_chart = (
    alt.hconcat(matrix, legend_chart, spacing=40)
    .properties(background=PAGE_BG)
    .configure_axis(grid=True, gridOpacity=0.10)
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT)
)

# Save PNG version (static)
static_chart.save(f"plot-{THEME}.png", scale_factor=3.0)

# Interactive HTML version with brush selection
brush = alt.selection_interval(name="brush", resolve="global")

interactive_chart = (
    alt.Chart(df)
    .mark_point(size=80, filled=True)
    .encode(
        alt.X(
            alt.repeat("column"),
            type="quantitative",
            axis=alt.Axis(
                labelFontSize=18,
                titleFontSize=22,
                labelAngle=-45,
                labelColor=INK_SOFT,
                titleColor=INK,
                domainColor=INK_SOFT,
                tickColor=INK_SOFT,
                gridColor=INK,
                gridOpacity=0.10,
            ),
        ),
        alt.Y(
            alt.repeat("row"),
            type="quantitative",
            axis=alt.Axis(
                labelFontSize=18,
                titleFontSize=22,
                labelColor=INK_SOFT,
                titleColor=INK,
                domainColor=INK_SOFT,
                tickColor=INK_SOFT,
                gridColor=INK,
                gridOpacity=0.10,
            ),
        ),
        color=alt.condition(
            brush,
            alt.Color(
                "Species:N",
                scale=alt.Scale(domain=["setosa", "versicolor", "virginica"], range=IMPRINT),
                legend=alt.Legend(titleFontSize=18, labelFontSize=16, orient="right", title="Species"),
            ),
            alt.value(INK_SOFT),
        ),
        opacity=alt.condition(brush, alt.value(0.8), alt.value(0.15)),
        tooltip=["Species:N"] + [alt.Tooltip(v, format=".2f") for v in variables],
    )
    .properties(width=180, height=180)
    .add_params(brush)
    .repeat(row=variables, column=variables)
    .properties(
        background=PAGE_BG,
        title=alt.Title(
            "scatter-matrix-interactive · python · altair · anyplot.ai",
            fontSize=28,
            anchor="middle",
            color=INK,
            subtitle="Brush any subplot to select points across all panels",
            subtitleFontSize=18,
        ),
    )
    .configure_axis(grid=True, gridOpacity=0.10)
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
    .configure_title(color=INK)
)

# Save HTML version (interactive)
interactive_chart.save(f"plot-{THEME}.html")
