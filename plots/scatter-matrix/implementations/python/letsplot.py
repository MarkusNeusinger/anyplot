"""anyplot.ai
scatter-matrix: Scatter Plot Matrix
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405
from lets_plot.export import ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SEPAL_LENGTH = "Sepal Length (cm)"  # role: variables
SEPAL_WIDTH = "Sepal Width (cm)"  # role: extra
PETAL_LENGTH = "Petal Length (cm)"  # role: extra
PETAL_WIDTH = "Petal Width (cm)"  # role: extra
SPECIES = "Species"  # role: extra
VARIABLES = [SEPAL_LENGTH, SEPAL_WIDTH, PETAL_LENGTH, PETAL_WIDTH]

# Data: replace this block with your own table, for example df = pd.read_csv("iris.csv")
np.random.seed(42)
n_per_species = 50
# (mean, std) per variable, in the order of VARIABLES
profiles = {
    "Setosa": [(5.0, 0.35), (3.4, 0.38), (1.5, 0.17), (0.25, 0.10)],
    "Versicolor": [(5.9, 0.52), (2.8, 0.31), (4.3, 0.47), (1.3, 0.20)],
    "Virginica": [(6.6, 0.64), (3.0, 0.32), (5.5, 0.55), (2.0, 0.27)],
}
frames = []
for name, profile in profiles.items():
    columns = {var: np.random.normal(mean, std, n_per_species) for var, (mean, std) in zip(VARIABLES, profile)}
    frames.append(pd.DataFrame({**columns, SPECIES: name}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
n_vars = len(VARIABLES)

# Shared axis range per variable so a point can be traced across the grid
limits = {}
for var in VARIABLES:
    low, high = df[var].min(), df[var].max()
    pad = (high - low) * 0.06
    limits[var] = [low - pad, high + pad]

# Grid geometry (fractions of the canvas)
margin_top = 0.07
margin_bottom = 0.09
margin_left = 0.01
margin_right = 0.01
cell_width = (1.0 - margin_left - margin_right) / n_vars
cell_height = (1.0 - margin_top - margin_bottom) / n_vars


def cell_theme():
    return theme(
        axis_title=element_blank(),
        axis_text=element_text(size=9, color=INK_SOFT),
        legend_position="none",
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_minor=element_blank(),
        panel_grid_major=element_line(color=INK_SOFT, size=0.2),
    )


# Full-canvas background layer, drawn first so the margins carry the page color
background = ggplot() + geom_blank() + theme_void() + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))
plots = [background]
regions = [(0, 0, 1, 1, 0, 0)]

for i, var_y in enumerate(VARIABLES):
    for j, var_x in enumerate(VARIABLES):
        if i == j:
            # Diagonal: histogram of the variable, one layer per species
            p = (
                ggplot(df, aes(x=var_x, fill=SPECIES))
                + geom_histogram(alpha=0.7, bins=15, position="identity")
                + scale_fill_manual(values=IMPRINT_PALETTE)
                + scale_x_continuous(limits=limits[var_x])
            )
        else:
            # Off-diagonal: scatter of the pair
            p = (
                ggplot(df, aes(x=var_x, y=var_y, color=SPECIES))
                + geom_point(size=2.0, alpha=0.7)
                + scale_color_manual(values=IMPRINT_PALETTE)
                + scale_x_continuous(limits=limits[var_x])
                + scale_y_continuous(limits=limits[var_y])
            )
        p = p + theme_minimal() + cell_theme()

        # Variable names along the bottom edge (last row) and the left edge (first column)
        if i == n_vars - 1:
            p = p + labs(x=var_x) + theme(axis_title_x=element_text(size=11, color=INK))
        if j == 0:
            p = p + labs(y=var_y) + theme(axis_title_y=element_text(size=11, color=INK))

        plots.append(p)
        regions.append((margin_left + j * cell_width, margin_top + i * cell_height, cell_width, cell_height, 0, 0))

# Title
title_plot = (
    ggplot()
    + geom_blank()
    + ggtitle("scatter-matrix · python · letsplot · anyplot.ai")
    + theme_void()
    + theme(plot_title=element_text(size=18, hjust=0.5, face="bold", color=INK), plot_background=element_blank())
)
plots.append(title_plot)
regions.append((0, 0, 1, margin_top, 0, 0))

# One legend for the whole grid: a key per species, drawn as points with text labels
legend_df = df[[SPECIES]].drop_duplicates().reset_index(drop=True)
legend_df["pos"] = legend_df.index.astype(float)
legend_df["row"] = 0.0
legend_plot = (
    ggplot(legend_df, aes(x="pos", y="row", color=SPECIES))
    + geom_point(size=6)
    + geom_text(aes(label=SPECIES), nudge_x=0.1, hjust=0, size=7, color=INK_SOFT)
    + scale_color_manual(values=IMPRINT_PALETTE)
    + scale_x_continuous(limits=[-0.3, len(legend_df) - 0.1])
    + theme_void()
    + theme(legend_position="none", plot_background=element_blank())
)
plots.append(legend_plot)
regions.append((0.2, 1.0 - margin_bottom, 0.6, margin_bottom, 0, 0))

combined = ggbunch(plots, regions) + ggsize(600, 600)

# Save: scale 4 gives 2400 x 2400 px
ggsave(combined, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(combined, filename=f"plot-{THEME}.html", path=".")
