"""anyplot.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-15
"""

import os

import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    labs,
    scale_fill_gradient,
    theme,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
MISSING_DATA_COLOR = "#A9A9A9" if THEME == "light" else "#696969"
LABEL_ON_FILL = "#F0EFE8"  # light ink: both Imprint ramp ends are mid-dark in either theme

# Imprint sequential ramp (single polarity)
IMPRINT_SEQ = ("#009E73", "#4467A3")

# Columns
COUNTRY = "Country"  # role: region_id
VALUE = "Life expectancy (years)"  # role: value
VERTEX = "Vertex order"  # role: extra
X = "x"  # role: extra
Y = "y"  # role: extra

# Data: simplified European country outlines (approximate polygon coordinates) with
# life expectancy at birth (years, 2023-2024). Czechia has no value to show missing data.
countries = {
    "France": [(0, 0), (3, 0), (4, 2), (3, 4), (1, 4), (0, 2)],
    "Germany": [(4, 2), (7, 1), (8, 3), (7, 5), (4, 5), (3, 4)],
    "Spain": [(-3, -3), (1, -3), (2, -1), (0, 0), (-2, 0), (-3, -1)],
    "Italy": [(5, -2), (7, -3), (9, -1), (8, 2), (6, 1), (5, 0)],
    "Poland": [(8, 3), (12, 2), (13, 5), (11, 6), (8, 5), (7, 5)],
    "UK": [(-2, 4), (1, 4), (2, 6), (1, 8), (-1, 8), (-2, 6)],
    "Sweden": [(7, 7), (10, 6), (11, 9), (10, 12), (8, 11), (7, 9)],
    "Norway": [(5, 9), (7, 7), (8, 11), (7, 14), (5, 13), (4, 11)],
    "Finland": [(11, 9), (14, 8), (15, 12), (13, 14), (11, 12), (10, 12)],
    "Austria": [(6, 1), (8, 0), (10, 1), (9, 3), (7, 3), (6, 2)],
    "Netherlands": [(2, 5), (4, 5), (5, 6), (4, 7), (2, 7), (1, 6)],
    "Belgium": [(1, 4), (3, 4), (4, 5), (2, 5), (1, 5)],
    "Switzerland": [(3, 1), (5, 0), (6, 1), (5, 2), (4, 2), (3, 2)],
    "Portugal": [(-4, -2), (-3, -3), (-2, -1), (-3, 0), (-4, 0)],
    "Denmark": [(5, 6), (7, 5), (8, 6), (7, 7), (5, 7)],
    "Czechia": [(7, 3), (9, 3), (10, 4), (9, 5), (7, 5), (6, 4)],
}
life_expectancy = {
    "France": 82.4,
    "Germany": 81.8,
    "Spain": 83.1,
    "Italy": 83.5,
    "Poland": 78.0,
    "UK": 81.3,
    "Sweden": 84.2,
    "Norway": 84.6,
    "Finland": 82.5,
    "Austria": 81.9,
    "Netherlands": 82.1,
    "Belgium": 81.8,
    "Switzerland": 84.0,
    "Portugal": 82.2,
    "Denmark": 81.5,
    "Czechia": None,
}
df = pd.DataFrame(
    [
        {COUNTRY: name, VERTEX: i, X: x, Y: y, VALUE: life_expectancy[name]}
        for name, coords in countries.items()
        for i, (x, y) in enumerate(coords + coords[:1])
    ]
)

# Plot
# Label anchors: polygon centre, nudged for a few narrow countries (labels only, never the shapes)
label_offsets = {"Netherlands": (0.5, 1.0), "Belgium": (-0.8, -0.5), "Germany": (0.5, -0.5), "Denmark": (0.5, 0.5)}
labels = df.groupby(COUNTRY, sort=False).agg({X: "mean", Y: "mean", VALUE: "first"}).reset_index()
for name, (dx, dy) in label_offsets.items():
    labels.loc[labels[COUNTRY] == name, X] += dx
    labels.loc[labels[COUNTRY] == name, Y] += dy
has_value = labels[VALUE].notna()

shaded = df[df[VALUE].notna()]
missing = df[df[VALUE].isna()]

plot = (
    ggplot()
    + geom_polygon(shaded, aes(x=X, y=Y, group=COUNTRY, fill=VALUE), color=INK_SOFT, size=0.3)
    + geom_polygon(missing, aes(x=X, y=Y, group=COUNTRY), fill=MISSING_DATA_COLOR, color=INK_SOFT, size=0.3)
    + geom_text(labels[has_value], aes(x=X, y=Y, label=COUNTRY), size=4, color=LABEL_ON_FILL)
    + geom_text(labels[~has_value], aes(x=X, y=Y, label=COUNTRY), size=4, color=INK)
    + scale_fill_gradient(low=IMPRINT_SEQ[0], high=IMPRINT_SEQ[1], name="Life expectancy\n(years)")
    + coord_fixed(ratio=1.0)
    + labs(title="choropleth-basic · python · plotnine · anyplot.ai")
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, ha="center", color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid=element_blank(),
        panel_border=element_blank(),
        axis_text=element_blank(),
        axis_title=element_blank(),
        axis_ticks=element_blank(),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
