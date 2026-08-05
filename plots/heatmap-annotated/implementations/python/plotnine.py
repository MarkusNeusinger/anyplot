""" anyplot.ai
heatmap-annotated: Annotated Heatmap
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 91/100 | Updated: 2026-08-05
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_gradient2,
    theme,
    theme_minimal,
)


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
TEXT_ON_SATURATED = "#F0EFE8"  # readable text over saturated red/blue cells in either theme

# Data: Correlation matrix of economic indicators
np.random.seed(42)
variables = [
    "GDP Growth",
    "Inflation",
    "Unemployment",
    "Interest Rate",
    "Consumer Conf",
    "Mfg Index",
    "Export Vol",
    "Housing",
]

n_vars = len(variables)

# Generate a realistic correlation matrix
base = np.random.randn(n_vars, n_vars)
corr_matrix = np.dot(base, base.T)
d = np.sqrt(np.diag(corr_matrix))
corr_matrix = corr_matrix / d[:, None] / d[None, :]
np.fill_diagonal(corr_matrix, 1.0)
corr_matrix = (corr_matrix + corr_matrix.T) / 2  # Ensure symmetry

# Create DataFrame in long format for plotnine
rows = []
for i, row_var in enumerate(variables):
    for j, col_var in enumerate(variables):
        rows.append({"x": col_var, "y": row_var, "value": corr_matrix[i, j]})

df = pd.DataFrame(rows)

# Convert to categorical to preserve order
df["x"] = pd.Categorical(df["x"], categories=variables, ordered=True)
df["y"] = pd.Categorical(df["y"], categories=variables[::-1], ordered=True)

# Text color must contrast with its own cell: saturated cells get light text,
# near-neutral (midpoint) cells get the theme's own ink color.
df["text_color"] = np.where(df["value"].abs() > 0.5, TEXT_ON_SATURATED, INK)

# Title — length-scaled per prompts/plot-generator.md "Title fontsize must scale with title length"
title = "heatmap-annotated · python · plotnine · anyplot.ai"
title_fontsize = round(12 * min(1.0, 67 / len(title)))

# Create the annotated heatmap using the Imprint diverging colormap (imprint_div)
plot = (
    ggplot(df, aes(x="x", y="y", fill="value"))
    + geom_tile(color=PAGE_BG, size=0.6)
    + geom_text(aes(label="value", color="text_color"), format_string="{:.2f}", size=3.5)
    + scale_fill_gradient2(low="#AE3030", mid=PAGE_BG, high="#4467A3", midpoint=0, limits=(-1, 1), name="Correlation")
    + scale_color_identity()
    + labs(x="Economic Indicator", y="Economic Indicator", title=title)
    + coord_fixed(ratio=1)
    + theme_minimal()
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        plot_title=element_text(size=title_fontsize, color=INK, ha="center"),
        axis_title=element_text(size=10, color=INK),
        axis_text_x=element_text(size=8, color=INK_SOFT, rotation=45, ha="right"),
        axis_text_y=element_text(size=8, color=INK_SOFT),
        axis_ticks=element_blank(),
        legend_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
