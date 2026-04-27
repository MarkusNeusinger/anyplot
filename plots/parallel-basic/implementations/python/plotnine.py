""" anyplot.ai
parallel-basic: Basic Parallel Coordinates Plot
Library: plotnine 0.15.3 | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-27
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data — synthetic iris-like measurements, 50 samples per species (balanced)
np.random.seed(42)
n = 50
cov_setosa = np.diag([0.25, 0.09, 0.25, 0.04])
cov_versicol = np.diag([0.25, 0.09, 0.25, 0.04])
cov_virginica = np.diag([0.25, 0.09, 0.25, 0.04])
setosa = np.random.multivariate_normal([5.01, 3.42, 1.46, 0.24], cov_setosa, size=n)
versicol = np.random.multivariate_normal([5.94, 2.77, 4.26, 1.33], cov_versicol, size=n)
virginica = np.random.multivariate_normal([6.59, 2.97, 5.55, 2.03], cov_virginica, size=n)

cols = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
df = pd.DataFrame(np.vstack([setosa, versicol, virginica]), columns=cols)
df["species"] = ["Setosa"] * n + ["Versicolor"] * n + ["Virginica"] * n
df["id"] = range(len(df))

# Clip to realistic ranges
df["sepal_length"] = df["sepal_length"].clip(4.0, 8.5)
df["sepal_width"] = df["sepal_width"].clip(2.0, 4.5)
df["petal_length"] = df["petal_length"].clip(1.0, 7.0)
df["petal_width"] = df["petal_width"].clip(0.1, 2.8)

# Normalize each dimension to 0–1 scale for fair comparison
dimensions = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
df_norm = df.copy()
for col in dimensions:
    df_norm[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())

# Transform to long format for parallel coordinates
df_long = pd.melt(df_norm, id_vars=["id", "species"], value_vars=dimensions, var_name="dimension", value_name="value")
dim_map = {dim: i for i, dim in enumerate(dimensions)}
df_long["dim_num"] = df_long["dimension"].map(dim_map)

# Okabe-Ito colors — first series always #009E73
species_order = ["Setosa", "Versicolor", "Virginica"]
colors = {sp: OKABE_ITO[i] for i, sp in enumerate(species_order)}

# Plot
plot = (
    ggplot(df_long, aes(x="dim_num", y="value", group="id", color="species"))
    + geom_line(alpha=0.35, size=0.8)
    + geom_point(size=2.5, alpha=0.55)
    + scale_color_manual(values=colors, breaks=species_order)
    + scale_x_continuous(
        breaks=list(range(len(dimensions))),
        labels=["Sepal Length\n(cm)", "Sepal Width\n(cm)", "Petal Length\n(cm)", "Petal Width\n(cm)"],
    )
    + labs(
        x="Dimension", y="Normalized Value (0–1)", title="parallel-basic · plotnine · anyplot.ai", color="Iris Species"
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        axis_title=element_text(color=INK, size=20),
        axis_text=element_text(color=INK_SOFT, size=16),
        axis_text_x=element_text(size=14),
        plot_title=element_text(color=INK, size=24),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=16),
        legend_title=element_text(color=INK, size=18),
        text=element_text(size=14),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
