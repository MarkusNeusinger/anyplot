"""anyplot.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    ggplot,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
VARIABLES = ["Sepal length (cm)", "Sepal width (cm)", "Petal length (cm)", "Petal width (cm)"]  # role: variable_
SPECIES = "Species"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("flowers.csv")
iris = load_iris()
df = pd.DataFrame(iris.data, columns=VARIABLES)
df[SPECIES] = pd.Categorical.from_codes(iris.target, iris.target_names)

# Plot: reads only df and the constants above
# Normalize the variables so no single one dominates the curves
values = StandardScaler().fit_transform(df[VARIABLES].to_numpy())

# One full period of the Fourier parameter, evaluated densely enough for smooth curves
T, VALUE, OBSERVATION = "t (radians)", "Andrews curve value", "observation"
t = np.linspace(-np.pi, np.pi, 200)

# Andrews curve: x1/sqrt(2) + x2*sin(t) + x3*cos(t) + x4*sin(2t) + x5*cos(2t) + ...
basis = [np.full_like(t, 1 / np.sqrt(2))]
for i in range(1, values.shape[1]):
    basis.append(np.sin((i // 2 + 1) * t) if i % 2 == 1 else np.cos((i // 2) * t))
curves = values @ np.vstack(basis)

n_obs = len(df)
curve_df = pd.DataFrame(
    {
        T: np.tile(t, n_obs),
        VALUE: curves.ravel(),
        SPECIES: np.repeat(df[SPECIES].astype(str).to_numpy(), len(t)),
        OBSERVATION: np.repeat(np.arange(n_obs), len(t)),
    }
)
groups = df[SPECIES].astype(str).unique().tolist()

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(size=10, color=INK),
    axis_text=element_text(size=8, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(size=12, color=INK),
    legend_background=element_rect(fill=PAGE_BG, color=INK_SOFT),
    legend_text=element_text(size=8, color=INK_SOFT),
    legend_title=element_text(size=9, color=INK),
)

plot = (
    ggplot(curve_df, aes(x=T, y=VALUE, color=SPECIES, group=OBSERVATION))
    + geom_line(alpha=0.4, size=0.6)
    + labs(title="andrews-curves · python · plotnine · anyplot.ai")
    + scale_color_manual(values=IMPRINT_PALETTE, limits=groups)
    + theme_minimal()
    + anyplot_theme
    + theme(figure_size=(8, 4.5))
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
