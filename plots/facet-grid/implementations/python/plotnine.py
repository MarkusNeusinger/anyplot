""" pyplots.ai
facet-grid: Faceted Grid Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    facet_grid,
    geom_point,
    ggplot,
    labs,
    scale_color_brewer,
    theme,
    theme_minimal,
)


# Data - Plant growth study with soil type and light conditions
np.random.seed(42)

# Create faceting variables
soil_types = ["Sandy", "Loamy", "Clay"]
light_levels = ["Low", "Medium", "High"]
species = ["Basil", "Fern", "Tomato"]  # Alphabetical order for consistent legend

# Generate realistic data with more pronounced differences between conditions
data = []
for soil in soil_types:
    for light in light_levels:
        # Amplified effects to show clearer differences between facets
        soil_effect = {"Sandy": -12, "Loamy": 0, "Clay": 8}[soil]
        light_effect = {"Low": -15, "Medium": 0, "High": 18}[light]

        for sp in species:
            species_effect = {"Basil": 0, "Tomato": 8, "Fern": -5}[sp]
            n_points = 12  # Slightly fewer points per panel for clarity

            # Water amount (x-axis)
            water = np.random.uniform(25, 65, n_points)

            # Growth depends on water, soil, light, and species
            base_growth = 25 + 0.9 * water + soil_effect + light_effect + species_effect
            growth = base_growth + np.random.randn(n_points) * 4

            for i in range(n_points):
                data.append(
                    {"water": water[i], "growth": growth[i], "soil_type": soil, "light_level": light, "species": sp}
                )

df = pd.DataFrame(data)

# Ensure correct ordering of categorical variables for facets
df["soil_type"] = pd.Categorical(df["soil_type"], categories=soil_types, ordered=True)
df["light_level"] = pd.Categorical(df["light_level"], categories=light_levels, ordered=True)
# Match legend order with species order
df["species"] = pd.Categorical(df["species"], categories=species, ordered=True)

# Plot - Faceted grid showing growth patterns across soil and light conditions
plot = (
    ggplot(df, aes(x="water", y="growth", color="species"))
    + geom_point(size=3.5, alpha=0.75)
    + facet_grid("soil_type ~ light_level", labeller="label_both")
    + scale_color_brewer(type="qual", palette="Set2")
    + labs(title="facet-grid · plotnine · pyplots.ai", x="Water (mL/day)", y="Growth (cm)", color="Species")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, face="bold", ha="center"),
        axis_title=element_text(size=18),
        axis_text=element_text(size=14),
        strip_text_x=element_text(size=14, face="bold"),
        strip_text_y=element_text(size=14, face="bold", rotation=0),
        strip_background=element_rect(fill="#f0f0f0", color="#cccccc"),
        legend_title=element_text(size=16, face="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_grid_major=element_line(color="#cccccc", alpha=0.4),
        panel_grid_minor=element_line(color="#eeeeee", alpha=0.2),
        panel_spacing_x=0.06,
        panel_spacing_y=0.06,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
