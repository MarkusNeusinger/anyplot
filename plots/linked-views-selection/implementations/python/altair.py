""" pyplots.ai
linked-views-selection: Multiple Linked Views with Selection Sync
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Iris-like flower measurements with categories
np.random.seed(42)

# Generate multivariate data with 3 categories
n_per_category = 50
categories = ["Setosa", "Versicolor", "Virginica"]

data = []
for i, cat in enumerate(categories):
    # Different distributions for each category
    base_sepal_length = [5.0, 5.9, 6.6][i]
    base_sepal_width = [3.4, 2.8, 3.0][i]
    base_petal_length = [1.5, 4.3, 5.5][i]

    sepal_length = np.random.normal(base_sepal_length, 0.35, n_per_category)
    sepal_width = np.random.normal(base_sepal_width, 0.35, n_per_category)
    petal_length = np.random.normal(base_petal_length, 0.45, n_per_category)

    for j in range(n_per_category):
        data.append(
            {
                "Sepal Length (cm)": sepal_length[j],
                "Sepal Width (cm)": sepal_width[j],
                "Petal Length (cm)": petal_length[j],
                "Species": cat,
            }
        )

df = pd.DataFrame(data)

# Color scheme - colorblind-safe
color_scale = alt.Scale(
    domain=categories,
    range=["#306998", "#FFD43B", "#E24A33"],  # Python Blue, Yellow, accent
)

# Selection - interval selection that syncs across views
brush = alt.selection_interval()

# Base point properties
point_size = 150
opacity_selected = 1.0
opacity_unselected = 0.15

# Scatter plot: Sepal Length vs Sepal Width
scatter = (
    alt.Chart(df)
    .mark_circle(size=point_size)
    .encode(
        x=alt.X("Sepal Length (cm):Q", scale=alt.Scale(zero=False)),
        y=alt.Y("Sepal Width (cm):Q", scale=alt.Scale(zero=False)),
        color=alt.condition(
            brush,
            alt.Color(
                "Species:N", scale=color_scale, legend=alt.Legend(titleFontSize=18, labelFontSize=16, symbolSize=200)
            ),
            alt.value("lightgray"),
        ),
        opacity=alt.condition(brush, alt.value(opacity_selected), alt.value(opacity_unselected)),
        tooltip=["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Species"],
    )
    .properties(width=500, height=400, title=alt.Title("Sepal Dimensions", fontSize=20))
    .add_params(brush)
)

# Histogram: Petal Length distribution
histogram = (
    alt.Chart(df)
    .mark_bar(opacity=0.8)
    .encode(
        x=alt.X("Petal Length (cm):Q", bin=alt.Bin(maxbins=20)),
        y=alt.Y("count():Q", title="Count"),
        color=alt.condition(brush, alt.Color("Species:N", scale=color_scale, legend=None), alt.value("lightgray")),
        opacity=alt.condition(brush, alt.value(0.9), alt.value(opacity_unselected)),
    )
    .properties(width=500, height=400, title=alt.Title("Petal Length Distribution", fontSize=20))
)

# Bar chart: Species count
bar_chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("Species:N", title="Species", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("count():Q", title="Count"),
        color=alt.condition(brush, alt.Color("Species:N", scale=color_scale, legend=None), alt.value("lightgray")),
        opacity=alt.condition(brush, alt.value(0.9), alt.value(opacity_unselected)),
    )
    .properties(width=500, height=400, title=alt.Title("Species Distribution", fontSize=20))
)

# Combine charts: scatter on left, histogram and bar stacked on right
right_column = alt.vconcat(histogram, bar_chart).resolve_scale(color="shared")
combined = alt.hconcat(scatter, right_column).resolve_scale(color="shared")

# Final chart with title and configuration
chart = (
    combined.properties(
        title=alt.Title(
            "linked-views-selection · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            subtitle="Brush on scatter plot to filter all views | Click and drag to select",
            subtitleFontSize=16,
            subtitleColor="gray",
        )
    )
    .configure_axis(labelFontSize=14, titleFontSize=16, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
