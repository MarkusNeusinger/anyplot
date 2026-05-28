""" anyplot.ai
linked-views-selection: Multiple Linked Views with Selection Sync
Library: altair 6.1.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-17
"""

import os
import sys


script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)
sys.path = [p for p in sys.path if p not in ("", ".")]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first three positions)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Iris-like flower measurements with categories
np.random.seed(42)

n_per_category = 50
categories = ["Setosa", "Versicolor", "Virginica"]

data = []
for i, cat in enumerate(categories):
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

# Color scale using Okabe-Ito
color_scale = alt.Scale(domain=categories, range=IMPRINT)

# Selection mechanism
brush = alt.selection_interval()

# Point styling
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
            alt.value(INK_SOFT),
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
        color=alt.condition(brush, alt.Color("Species:N", scale=color_scale, legend=None), alt.value(INK_SOFT)),
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
        color=alt.condition(brush, alt.Color("Species:N", scale=color_scale, legend=None), alt.value(INK_SOFT)),
        opacity=alt.condition(brush, alt.value(0.9), alt.value(opacity_unselected)),
    )
    .properties(width=500, height=400, title=alt.Title("Species Distribution", fontSize=20))
)

# Combine charts
right_column = alt.vconcat(histogram, bar_chart).resolve_scale(color="shared")
combined = alt.hconcat(scatter, right_column).resolve_scale(color="shared")

# Final chart with theme-adaptive styling
chart = (
    combined.properties(
        background=PAGE_BG,
        title=alt.Title(
            "linked-views-selection · altair · anyplot.ai",
            fontSize=28,
            anchor="middle",
            color=INK,
            subtitle="Brush on scatter plot to filter all views | Click and drag to select",
            subtitleFontSize=16,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_axis(
        labelFontSize=14,
        labelColor=INK_SOFT,
        titleFontSize=16,
        titleColor=INK,
        gridOpacity=0.10,
        gridColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=18,
        labelFontSize=16,
    )
    .configure_title(color=INK)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
