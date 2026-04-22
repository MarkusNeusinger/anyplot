""" pyplots.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
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


# Data - Quarterly energy consumption forecast by source with prediction intervals
np.random.seed(42)

quarters = np.arange(1, 21)  # 20 quarters (5 years)

# Base values for three energy sources (in TWh)
solar_base = 50 + quarters * 3 + np.random.randn(20) * 2
wind_base = 80 + quarters * 2.5 + np.random.randn(20) * 3
hydro_base = 120 + quarters * 0.5 + np.random.randn(20) * 2

# Confidence intervals (uncertainty grows over time for forecasts)
uncertainty_factor = 1 + quarters * 0.08

solar_lower = solar_base - 8 * uncertainty_factor
solar_upper = solar_base + 8 * uncertainty_factor

wind_lower = wind_base - 10 * uncertainty_factor
wind_upper = wind_base + 10 * uncertainty_factor

hydro_lower = hydro_base - 6 * uncertainty_factor
hydro_upper = hydro_base + 6 * uncertainty_factor

# Create stacked values (cumulative)
# Layer 1: Solar (bottom)
solar_cum = solar_base
solar_cum_lower = solar_lower
solar_cum_upper = solar_upper

# Layer 2: Wind (stacked on solar)
wind_cum = solar_base + wind_base
wind_cum_lower = solar_base + wind_lower
wind_cum_upper = solar_base + wind_upper

# Layer 3: Hydro (stacked on wind + solar)
hydro_cum = solar_base + wind_base + hydro_base
hydro_cum_lower = solar_base + wind_base + hydro_lower
hydro_cum_upper = solar_base + wind_base + hydro_upper

# Create long-form dataframe for proper legend support
df_areas = pd.concat(
    [
        pd.DataFrame(
            {
                "quarter": quarters,
                "y": solar_cum,
                "ymin": np.zeros(20),
                "ymax": solar_cum,
                "lower": solar_cum_lower,
                "upper": solar_cum_upper,
                "series": "Solar",
            }
        ),
        pd.DataFrame(
            {
                "quarter": quarters,
                "y": wind_cum,
                "ymin": solar_cum,
                "ymax": wind_cum,
                "lower": wind_cum_lower,
                "upper": wind_cum_upper,
                "series": "Wind",
            }
        ),
        pd.DataFrame(
            {
                "quarter": quarters,
                "y": hydro_cum,
                "ymin": wind_cum,
                "ymax": hydro_cum,
                "lower": hydro_cum_lower,
                "upper": hydro_cum_upper,
                "series": "Hydro",
            }
        ),
    ],
    ignore_index=True,
)

# Set order for legend
df_areas["series"] = pd.Categorical(df_areas["series"], categories=["Solar", "Wind", "Hydro"], ordered=True)

# Colors - using Python blue and complementary colors
color_map = {"Solar": "#FFD43B", "Wind": "#306998", "Hydro": "#4ECDC4"}

# Create the plot with stacked areas and confidence bands
plot = (
    ggplot(df_areas, aes(x="quarter"))
    # Confidence bands (lighter, drawn first)
    + geom_ribbon(aes(ymin="lower", ymax="upper", fill="series"), alpha=0.25)
    # Stacked areas (main fill)
    + geom_ribbon(aes(ymin="ymin", ymax="ymax", fill="series"), alpha=0.7)
    # Central lines for each series
    + geom_line(aes(y="y", color="series"), size=1.5)
    # Color scales
    + scale_fill_manual(values=color_map, name="Energy Source\n(with 90% CI)")
    + scale_color_manual(values=color_map, guide=None)
    # Labels and styling
    + labs(x="Quarter", y="Energy Consumption (TWh)", title="area-stacked-confidence · plotnine · pyplots.ai")
    + scale_x_continuous(breaks=range(1, 21, 2))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_minor=element_blank(),
    )
)

# Save the plot
plot.save("plot.png", dpi=300, verbose=False)
