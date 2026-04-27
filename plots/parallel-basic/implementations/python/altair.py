""" anyplot.ai
parallel-basic: Basic Parallel Coordinates Plot
Library: altair 6.1.0 | Python 3.14.4
Quality: 88/100 | Updated: 2026-04-27
"""

import importlib
import os
import sys


# This file is named 'altair.py'. Remove the script directory (and '') from sys.path
# before loading the altair library to prevent this file from being imported as altair.
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p not in ("", _script_dir)]

alt = importlib.import_module("altair")
np = importlib.import_module("numpy")
pd = importlib.import_module("pandas")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2"]

# Data - Iris-like dataset with 4 dimensions and 3 species
np.random.seed(42)

n_per_species = 50
species_names = ["Setosa", "Versicolor", "Virginica"]
dimensions = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]

data = []
for i, sp in enumerate(species_names):
    sepal_length = np.random.normal([5.0, 5.9, 6.6][i], 0.35, n_per_species)
    sepal_width = np.random.normal([3.4, 2.8, 3.0][i], 0.38, n_per_species)
    petal_length = np.random.normal([1.5, 4.3, 5.5][i], 0.17 + i * 0.25, n_per_species)
    petal_width = np.random.normal([0.2, 1.3, 2.0][i], 0.1 + i * 0.15, n_per_species)
    for j in range(n_per_species):
        data.append(
            {
                "Species": sp,
                "Sepal Length (cm)": round(sepal_length[j], 2),
                "Sepal Width (cm)": round(sepal_width[j], 2),
                "Petal Length (cm)": round(petal_length[j], 2),
                "Petal Width (cm)": round(petal_width[j], 2),
                "id": i * n_per_species + j,
            }
        )

df = pd.DataFrame(data)

# Normalize values to 0-1 range for fair comparison across axes
for dim in dimensions:
    min_val = df[dim].min()
    max_val = df[dim].max()
    df[f"{dim}_norm"] = (df[dim] - min_val) / (max_val - min_val)

# Long format retaining original values for tooltips
df_long = df.melt(
    id_vars=["id", "Species"] + dimensions,
    value_vars=[f"{d}_norm" for d in dimensions],
    var_name="Dimension",
    value_name="Normalized Value",
)
df_long["Dimension"] = df_long["Dimension"].str.replace("_norm", "")

# Interactive selection: click a species in the legend to highlight/dim
species_select = alt.selection_point(fields=["Species"], bind="legend", empty=True)

# Plot
spec = (
    alt.Chart(df_long)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X(
            "Dimension:N",
            sort=dimensions,
            axis=alt.Axis(labelAngle=0, labelFontSize=20, titleFontSize=24, title=None, labelPadding=12),
        ),
        y=alt.Y(
            "Normalized Value:Q",
            scale=alt.Scale(domain=[0, 1]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, title="Normalized Value", tickCount=5),
        ),
        detail="id:N",
        color=alt.Color(
            "Species:N",
            scale=alt.Scale(domain=species_names, range=OKABE_ITO),
            legend=alt.Legend(
                title="Species", titleFontSize=22, labelFontSize=20, symbolSize=300, symbolStrokeWidth=4, orient="right"
            ),
        ),
        opacity=alt.condition(species_select, alt.value(0.70), alt.value(0.08)),
        tooltip=[
            alt.Tooltip("Species:N"),
            alt.Tooltip("Sepal Length (cm):Q", format=".2f"),
            alt.Tooltip("Sepal Width (cm):Q", format=".2f"),
            alt.Tooltip("Petal Length (cm):Q", format=".2f"),
            alt.Tooltip("Petal Width (cm):Q", format=".2f"),
        ],
    )
    .properties(
        width=1500,
        height=850,
        background=PAGE_BG,
        title=alt.Title("parallel-basic · altair · anyplot.ai", fontSize=30, anchor="middle"),
    )
    .add_params(species_select)
)

chart = (
    spec.configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
