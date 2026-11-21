"""anyplot.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    ggplot,
    ggsave,
    ggsize,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
T_MIN, T_MAX = -np.pi, np.pi  # one full period of the Fourier expansion
T_STEPS = 120  # dense enough that no corners show

# Columns: set these to your table's column names
FEATURES = ["Sepal length (cm)", "Sepal width (cm)", "Petal length (cm)", "Petal width (cm)"]  # role: variable_
SPECIES = "Species"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
iris = load_iris()
df = pd.DataFrame(iris.data, columns=FEATURES)
df[SPECIES] = pd.Categorical.from_codes(iris.target, iris.target_names).astype(str)

# Plot: reads only df and the constants above
CURVE = "Andrews function value"
T = "t"
OBSERVATION = "observation"

# Normalize variables to similar scales so no single variable dominates
scaled = StandardScaler().fit_transform(df[FEATURES].to_numpy(dtype=float))

# Andrews basis: 1/sqrt(2), sin(t), cos(t), sin(2t), cos(2t), ...
t = np.linspace(T_MIN, T_MAX, T_STEPS)
basis = [np.full_like(t, 1 / np.sqrt(2))]
for k in range(1, len(FEATURES)):
    harmonic = (k + 1) // 2
    basis.append(np.sin(harmonic * t) if k % 2 == 1 else np.cos(harmonic * t))
values = scaled @ np.vstack(basis)  # one row per observation

curves = pd.DataFrame(
    {
        T: np.tile(t, len(df)),
        CURVE: values.ravel(),
        OBSERVATION: np.repeat(np.arange(len(df)), T_STEPS),
        SPECIES: np.repeat(df[SPECIES].to_numpy(), T_STEPS),
    }
)

plot = (
    ggplot(curves, aes(x=T, y=CURVE, group=OBSERVATION, color=SPECIES))
    + geom_line(alpha=0.4, size=0.8)
    + scale_color_manual(values=IMPRINT_PALETTE)
    + scale_x_continuous(breaks=[-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi], labels=["-π", "-π/2", "0", "π/2", "π"])
    + guides(color=guide_legend(override_aes={"alpha": 1, "size": 2}))
    + labs(
        x="Parameter t (radians)",
        y="Andrews function value (standardized features)",
        title="andrews-curves · python · letsplot · anyplot.ai",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=GRID, size=0.3),
        panel_grid_minor=element_line(color=GRID, size=0.2),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=16, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_position="right",
    )
    + ggsize(800, 450)
)

# Save PNG (scale 4x = 3200 × 1800 px) and interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
