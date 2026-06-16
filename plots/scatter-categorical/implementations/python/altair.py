""" anyplot.ai
scatter-categorical: Categorical Scatter Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-12
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Iris-like measurements by species
np.random.seed(42)

n_per_species = 50
species_names = ["Setosa", "Versicolor", "Virginica"]

data = []
for i, species in enumerate(species_names):
    base_petal_length = [1.4, 4.2, 5.5][i]
    base_petal_width = [0.2, 1.3, 2.0][i]
    spread = [0.2, 0.5, 0.6][i]

    petal_length = np.random.normal(base_petal_length, spread, n_per_species)
    petal_width = np.random.normal(base_petal_width, spread * 0.5, n_per_species)

    for pl, pw in zip(petal_length, petal_width, strict=True):
        data.append({"Petal Length (cm)": pl, "Petal Width (cm)": pw, "Species": species})

df = pd.DataFrame(data)

# Plot
chart = (
    alt.Chart(df)
    .mark_point(size=200, opacity=0.7, filled=True)
    .encode(
        x=alt.X("Petal Length (cm):Q", title="Petal Length (cm)", scale=alt.Scale(zero=False)),
        y=alt.Y("Petal Width (cm):Q", title="Petal Width (cm)", scale=alt.Scale(zero=False)),
        color=alt.Color(
            "Species:N",
            scale=alt.Scale(domain=species_names, range=IMPRINT),
            legend=alt.Legend(
                title="Species",
                titleFontSize=20,
                labelFontSize=18,
                symbolSize=200,
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
            ),
        ),
        shape=alt.Shape("Species:N", legend=None),
        tooltip=["Species:N", "Petal Length (cm):Q", "Petal Width (cm):Q"],
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("scatter-categorical · altair · anyplot.ai", fontSize=28),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=18,
        titleColor=INK,
        titleFontSize=22,
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
