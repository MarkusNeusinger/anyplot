"""anyplot.ai
pyramid-basic: Basic Pyramid Chart
Library: plotnine 0.15.3 | Python 3.13.13
Quality: pending | Updated: 2026-04-29
"""

import os
import sys


sys.path[0:1] = []  # Prevent script dir from shadowing the plotnine package

import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_col,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_discrete,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
AGE_GROUP = "Age group"  # role: category
MALE = "Male"  # role: value_left
FEMALE = "Female"  # role: value_right

# Data: replace this block with your own table, for example df = pd.read_csv("population.csv")
df = pd.DataFrame(
    {
        AGE_GROUP: ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"],
        MALE: [4200, 4500, 5100, 5800, 6200, 5500, 4100, 2800, 1200],
        FEMALE: [4000, 4300, 5000, 5600, 6000, 5700, 4500, 3200, 1800],
    }
)

# Plot: reads only df and the constants above
sides = [MALE, FEMALE]
long = df.melt(id_vars=AGE_GROUP, value_vars=sides, var_name="Side", value_name="Population (thousands)")
# The left side runs negative so its bars extend left of the shared axis
long["Population (thousands)"] = long["Population (thousands)"].where(
    long["Side"] != MALE, -long["Population (thousands)"]
)

# One symmetric scale: equal distance from the center means equal amounts
reach = df[sides].max().max() * 1.05

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_blank(),
    panel_border=element_blank(),
    axis_line=element_line(color=INK_SOFT),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    plot_title=element_text(color=INK, size=11),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=9),
    legend_position="bottom",
)

plot = (
    ggplot(long, aes(x=AGE_GROUP, y="Population (thousands)", fill="Side"))
    + geom_col(width=0.85)
    + scale_x_discrete(limits=df[AGE_GROUP].tolist())
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=sides)
    + scale_y_continuous(limits=(-reach, reach), labels=lambda breaks: [f"{abs(b):,.0f}" for b in breaks])
    + labs(title="Population by Age & Gender · pyramid-basic · python · plotnine · anyplot.ai", fill="Gender")
    + theme_minimal()
    + anyplot_theme
    + coord_flip()
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
