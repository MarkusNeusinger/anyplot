"""anyplot.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
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
    geom_ribbon,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
YEAR = "Year"  # role: x
AGE_GROUP = "Age group"  # role: category
POPULATION = ["Under 15", "15 to 64", "65 and over"]  # role: y
LOWER = ["Under 15 (lower)", "15 to 64 (lower)", "65 and over (lower)"]  # role: y_lower
UPPER = ["Under 15 (upper)", "15 to 64 (upper)", "65 and over (upper)"]  # role: y_upper
UNIT = "Population (millions)"

# Data: replace this block with your own table, for example df = pd.read_csv("projection.csv")
# Population projection by age group with a 90% prediction interval that widens with the horizon
rng = np.random.default_rng(7)
years = np.arange(2025, 2051)
steps = years - years[0]
trends = [11.8 - 0.07 * steps, 41.0 - 0.03 * steps - 0.0035 * steps**2, 15.2 + 0.42 * steps]
table = {YEAR: years}
for i, trend in enumerate(trends):
    central = trend + rng.normal(0, 0.12, len(years))
    half_width = (0.35 + 0.075 * steps) * (central / central.mean()) ** 0.5
    table[POPULATION[i]] = central.round(2)
    table[LOWER[i]] = (central - half_width).round(2)
    table[UPPER[i]] = (central + half_width).round(2)
df = pd.DataFrame(table)

# Plot: reads only df and the constants above
# Long form, one row per year and age group, in the data's group order
long = pd.concat(
    [
        pd.DataFrame({YEAR: df[YEAR], AGE_GROUP: name, "value": df[name], "low": df[lo], "high": df[hi], "rank": i})
        for i, (name, lo, hi) in enumerate(zip(POPULATION, LOWER, UPPER, strict=True))
    ],
    ignore_index=True,
)
long[AGE_GROUP] = pd.Categorical(long[AGE_GROUP], categories=POPULATION, ordered=True)
long = long.sort_values([YEAR, "rank"], ignore_index=True)

# Stack the layers in group order; each band sits on its own series' stacked edge
long["edge"] = long.groupby(YEAR, sort=False)["value"].cumsum()
long["base"] = long["edge"] - long["value"]
long["band_low"] = long["edge"] - (long["value"] - long["low"])
long["band_high"] = long["edge"] + (long["high"] - long["value"])

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=12),
    legend_background=element_rect(fill=ELEVATED_BG, color="none"),
    legend_key=element_rect(fill=ELEVATED_BG, color="none"),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=9),
    figure_size=(8, 4.5),
)

plot = (
    ggplot(long, aes(x=YEAR))
    # Interval bands around each stacked edge, drawn first and semi-transparent
    + geom_ribbon(aes(ymin="band_low", ymax="band_high", fill=AGE_GROUP), alpha=0.28)
    # Stacked layers
    + geom_ribbon(aes(ymin="base", ymax="edge", fill=AGE_GROUP), alpha=0.7)
    # Stacked central value of each series
    + geom_line(aes(y="edge", color=AGE_GROUP), size=0.8)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=POPULATION, name="Age group\n(lighter band:\n90% interval)")
    + scale_color_manual(values=IMPRINT_PALETTE, limits=POPULATION, guide=None)
    + scale_x_continuous(breaks=range(int(long[YEAR].min()), int(long[YEAR].max()) + 1, 5))
    + labs(x=YEAR, y=POPULATION, title="area-stacked-confidence · python · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
