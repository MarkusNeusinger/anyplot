"""anyplot.ai
pyramid-basic: Basic Pyramid Chart
Library: plotnine 0.15.3 | Python 3.13.13
Quality: 83/100 | Updated: 2026-04-29
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
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data
age_groups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
male_pop = [4200, 4500, 5100, 5800, 6200, 5500, 4100, 2800, 1200]
female_pop = [4000, 4300, 5000, 5600, 6000, 5700, 4500, 3200, 1800]

df = pd.DataFrame(
    {
        "age_group": age_groups * 2,
        "population": [-m for m in male_pop] + female_pop,
        "gender": ["Male"] * len(age_groups) + ["Female"] * len(age_groups),
    }
)

df["age_group"] = pd.Categorical(df["age_group"], categories=age_groups, ordered=True)
# Male first in legend — matches left-side visual position
df["gender"] = pd.Categorical(df["gender"], categories=["Male", "Female"], ordered=True)

anyplot_theme = theme(
    figure_size=(16, 9),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_blank(),
    panel_border=element_blank(),
    axis_line=element_line(color=INK_SOFT),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_text_x=element_text(color=INK_SOFT, size=16),
    axis_text_y=element_text(color=INK_SOFT, size=14),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
    legend_position="bottom",
)

# Labels for the peak 40-49 row to emphasise the working-age bulge
df_peak = df[df["age_group"] == "40-49"].copy()
df_peak["label"] = df_peak["population"].apply(lambda v: f"{abs(v):,}")
# Position labels just outside each bar end (negative side left, positive side right)
df_peak["label_y"] = df_peak["population"].apply(lambda v: v * 1.08)

# Plot
plot = (
    ggplot(df, aes(x="age_group", y="population", fill="gender"))
    + geom_col(width=0.85)
    + geom_text(
        data=df_peak, mapping=aes(x="age_group", y="label_y", label="label"), color=INK_SOFT, size=13, inherit_aes=False
    )
    + scale_fill_manual(values={"Male": OKABE_ITO[0], "Female": OKABE_ITO[1]})
    + scale_y_continuous(labels=lambda breaks: [f"{abs(int(b)):,}" for b in breaks])
    + labs(
        x="Age Group",
        y="Population (thousands)",
        title="Population by Age & Gender · pyramid-basic · plotnine · anyplot.ai",
        fill="Gender",
    )
    + theme_minimal()
    + anyplot_theme
    + coord_flip()
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
