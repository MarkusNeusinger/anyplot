""" pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-13
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    labs,
    scale_fill_cmap,
    scale_size_identity,
    theme,
)


# Data: European countries with population (millions) and GDP per capita (USD thousands)
np.random.seed(42)

countries_polygons = {
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
    "Romania": [(11, 0), (14, -1), (15, 1), (14, 3), (12, 3), (11, 2)],
}

# Population in millions (2024 estimates) - this drives the area distortion
population = {
    "France": 68.0,
    "Germany": 84.5,
    "Spain": 48.0,
    "Italy": 59.0,
    "Poland": 37.8,
    "UK": 67.7,
    "Sweden": 10.5,
    "Norway": 5.5,
    "Finland": 5.6,
    "Austria": 9.1,
    "Netherlands": 17.8,
    "Belgium": 11.7,
    "Switzerland": 8.8,
    "Portugal": 10.3,
    "Denmark": 5.9,
    "Romania": 19.0,
}

# GDP per capita in thousands USD (secondary color variable)
gdp_per_capita = {
    "France": 44.4,
    "Germany": 51.4,
    "Spain": 30.1,
    "Italy": 34.8,
    "Poland": 18.3,
    "UK": 46.1,
    "Sweden": 55.2,
    "Norway": 82.8,
    "Finland": 50.6,
    "Austria": 53.6,
    "Netherlands": 57.1,
    "Belgium": 49.5,
    "Switzerland": 93.3,
    "Portugal": 24.5,
    "Denmark": 67.8,
    "Romania": 15.8,
}

# Non-contiguous cartogram: shrink all polygons, then scale by population
# Cap the scale factor to prevent large countries from overlapping
median_pop = np.median(list(population.values()))
base_shrink = 0.38

# Build reference outline data (original boundaries, shown faintly for comparison)
ref_rows = []
for country, coords in countries_polygons.items():
    closed_coords = coords + [coords[0]]
    for i, (x, y) in enumerate(closed_coords):
        ref_rows.append({"country": country, "x": x, "y": y, "order": i})

df_reference = pd.DataFrame(ref_rows)

# Build scaled polygon data and centroid data
polygon_rows = []
centroid_rows = []

for country, coords in countries_polygons.items():
    pop = population[country]
    gdp = gdp_per_capita[country]

    cx = np.mean([c[0] for c in coords])
    cy = np.mean([c[1] for c in coords])

    # Scale factor: base_shrink * sqrt(population / median), capped to prevent overlap
    raw_scale = base_shrink * np.sqrt(pop / median_pop)
    scale = min(raw_scale, 0.72)

    closed_coords = coords + [coords[0]]
    for i, (x, y) in enumerate(closed_coords):
        sx = cx + (x - cx) * scale
        sy = cy + (y - cy) * scale
        polygon_rows.append({"country": country, "x": sx, "y": sy, "order": i, "gdp_pc": gdp, "population": pop})

    # Label size scales with polygon size for readability
    label_sz = max(7, min(11, 6 + pop / 20))
    centroid_rows.append({"country": country, "x": cx, "y": cy, "gdp_pc": gdp, "population": pop, "label_sz": label_sz})

df_polygons = pd.DataFrame(polygon_rows)
df_centroids = pd.DataFrame(centroid_rows)

# Abbreviation labels
abbrevs = {
    "France": "FR",
    "Germany": "DE",
    "Spain": "ES",
    "Italy": "IT",
    "Poland": "PL",
    "UK": "UK",
    "Sweden": "SE",
    "Norway": "NO",
    "Finland": "FI",
    "Austria": "AT",
    "Netherlands": "NL",
    "Belgium": "BE",
    "Switzerland": "CH",
    "Portugal": "PT",
    "Denmark": "DK",
    "Romania": "RO",
}
df_centroids["abbrev"] = df_centroids["country"].map(abbrevs)

# Population label for subtitle context
pop_fmt = f"{sum(population.values()):.0f}M total across {len(population)} countries"

# Plot: reference outlines (faint) + distorted polygons + labels
plot = (
    ggplot()
    # Layer 1: Reference outlines showing original geographic boundaries
    + geom_polygon(
        df_reference,
        aes(x="x", y="y", group="country"),
        fill="none",
        color="#b0b8c4",
        size=0.3,
        linetype="dashed",
        alpha=0.6,
    )
    # Layer 2: Distorted cartogram polygons colored by GDP per capita
    + geom_polygon(
        df_polygons, aes(x="x", y="y", group="country", fill="gdp_pc"), color="#2c3e50", size=0.7, alpha=0.92
    )
    # Layer 3: Country abbreviation labels
    + geom_text(df_centroids, aes(x="x", y="y", label="abbrev", size="label_sz"), color="#1a1a2e", fontweight="bold")
    + scale_size_identity()
    + scale_fill_cmap(cmap_name="viridis", name="GDP per Capita\n(thousand USD)")
    + coord_fixed(ratio=1.0)
    + labs(
        title="cartogram-area-distortion \u00b7 plotnine \u00b7 pyplots.ai",
        subtitle=f"Area \u221d Population \u2014 {pop_fmt}  |  Dashed outlines = original borders",
    )
    # Annotation for area-legend context (bottom-left)
    + annotate(
        "text",
        x=-3.5,
        y=-4.2,
        label="Larger polygon = larger population",
        size=9,
        color="#555555",
        fontstyle="italic",
        ha="left",
    )
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold", margin={"b": 6}),
        plot_subtitle=element_text(size=16, ha="center", color="#444444", margin={"b": 16}),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position="right",
        legend_background=element_rect(fill="white", alpha=0.9),
        panel_background=element_rect(fill="#f0f3f7"),
        plot_background=element_rect(fill="white"),
        axis_text=element_blank(),
        axis_title=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
