""" pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-13
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
    geom_label,
    geom_path,
    geom_polygon,
    geom_rect,
    ggplot,
    guide_colorbar,
    labs,
    scale_alpha_identity,
    scale_fill_gradientn,
    scale_size_identity,
    theme,
)


# Data: European countries with population (millions) and GDP per capita (USD thousands)
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

# Population in millions (2024 estimates) - drives area distortion
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

# Non-contiguous cartogram: shrink polygons toward centroid, scale by population
median_pop = np.median(list(population.values()))
base_shrink = 0.38

# Build reference outline data (original boundaries for comparison)
ref_rows = []
for country, coords in countries_polygons.items():
    closed = coords + [coords[0]]
    for i, (x, y) in enumerate(closed):
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

    # Scale factor: base_shrink * sqrt(population / median), capped
    raw_scale = base_shrink * np.sqrt(pop / median_pop)
    scale = min(raw_scale, 0.72)

    closed = coords + [coords[0]]
    for i, (x, y) in enumerate(closed):
        sx = cx + (x - cx) * scale
        sy = cy + (y - cy) * scale
        polygon_rows.append({"country": country, "x": sx, "y": sy, "order": i, "gdp_pc": gdp, "population": pop})

    centroid_rows.append(
        {
            "country": country,
            "abbrev": abbrevs[country],
            "x": cx,
            "y": cy,
            "gdp_pc": gdp,
            "population": pop,
            "label_sz": max(10, min(14, 8 + pop / 15)),
            "label_alpha": 1.0 if pop > 30 else 0.85,
        }
    )

df_polygons = pd.DataFrame(polygon_rows)
df_centroids = pd.DataFrame(centroid_rows)

# Nudge labels in crowded central Europe to reduce overlap
label_nudge = {"CH": (0.0, -0.7), "AT": (0.5, -0.5), "BE": (-0.5, 0.5)}
for abbrev, (dx, dy) in label_nudge.items():
    mask = df_centroids["abbrev"] == abbrev
    df_centroids.loc[mask, "x"] += dx
    df_centroids.loc[mask, "y"] += dy

# Compute top-3 largest for storytelling highlight
top3 = df_centroids.nlargest(3, "population")["country"].tolist()
df_polygons["is_top3"] = df_polygons["country"].isin(top3)
df_polygons["edge_width"] = df_polygons["is_top3"].map({True: 1.2, False: 0.6})

pop_fmt = f"{sum(population.values()):.0f}M total across {len(population)} countries"

# Custom color ramp: deep indigo → teal → amber → bright gold
custom_colors = ["#1B0A3C", "#2D1B69", "#1B6B7A", "#2E9E6E", "#85C248", "#E8B828", "#FFD700"]

# Plot with layered grammar of graphics
plot = (
    ggplot()
    # Layer 1: Subtle background rectangle for ocean feel
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=pd.DataFrame({"xmin": [-5.5], "xmax": [16.5], "ymin": [-5], "ymax": [15.5]}),
        fill="#E8EDF3",
        color="none",
        alpha=0.5,
    )
    # Layer 2: Reference outlines via geom_path (idiomatic for non-filled outlines)
    + geom_path(
        df_reference, aes(x="x", y="y", group="country"), color="#C0C8D4", size=0.4, linetype="dashed", alpha=0.5
    )
    # Layer 3: Cartogram polygons with GDP fill and population-driven edge weight
    + geom_polygon(
        df_polygons, aes(x="x", y="y", group="country", fill="gdp_pc", size="edge_width"), color="#1a1a2e", alpha=0.93
    )
    + scale_size_identity()
    # Layer 4: Country labels using geom_label for background contrast (plotnine feature)
    + geom_label(
        df_centroids,
        aes(x="x", y="y", label="abbrev", size="label_sz", alpha="label_alpha"),
        color="#1a1a2e",
        fill="white",
        fontweight="bold",
        label_padding=0.2,
        label_size=0.3,
        boxstyle="round,pad=0.15",
    )
    + scale_alpha_identity()
    # Custom gradient with guide_colorbar for refined legend
    + scale_fill_gradientn(colors=custom_colors, name="GDP per Capita\n(thousand USD)", guide=guide_colorbar(nbin=100))
    + coord_fixed(ratio=1.0, xlim=(-5.5, 16.5), ylim=(-4.8, 15))
    + labs(
        title="cartogram-area-distortion \u00b7 plotnine \u00b7 pyplots.ai",
        subtitle=f"Area \u221d Population \u2014 {pop_fmt}  |  Dashed outlines = original borders",
    )
    # Size-legend annotation: reference square for population context
    + annotate(
        "text",
        x=-4.5,
        y=-3.8,
        label="Larger polygon = larger population",
        size=10,
        color="#555555",
        fontstyle="italic",
        ha="left",
    )
    + annotate(
        "text",
        x=14,
        y=-3.8,
        label="DE, UK, FR = top 3 by population\n(bold outlines)",
        size=9,
        color="#444444",
        ha="right",
    )
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold", color="#1a1a2e", margin={"b": 4}),
        plot_subtitle=element_text(size=16, ha="center", color="#3a3a5a", margin={"b": 12}),
        legend_title=element_text(size=14, weight="bold"),
        legend_text=element_text(size=12),
        legend_position="right",
        legend_background=element_rect(fill="white", alpha=0.95, color="#cccccc", size=0.4),
        legend_key_width=18,
        panel_background=element_rect(fill="#f4f6fa", color="none"),
        plot_background=element_rect(fill="white", color="none"),
        plot_margin=0.02,
        axis_text=element_blank(),
        axis_title=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
