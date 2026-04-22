# ruff: noqa: F405
"""pyplots.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: letsplot | Python 3.13
Quality: pending | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Data - Simulated country-level metrics over 20 years (Gapminder-style)
np.random.seed(42)

countries = [
    "Northland",
    "Eastoria",
    "Westopia",
    "Southaven",
    "Centralia",
    "Alpinia",
    "Deltania",
    "Oceanica",
    "Valleysia",
    "Highlands",
]
years = list(range(2000, 2020))

data_rows = []
for country in countries:
    # Base values with country-specific characteristics
    base_gdp = np.random.uniform(5000, 40000)
    base_life = np.random.uniform(55, 75)
    base_pop = np.random.uniform(5, 200)  # millions

    # Growth trends
    gdp_growth = np.random.uniform(0.02, 0.06)
    life_growth = np.random.uniform(0.002, 0.008)
    pop_growth = np.random.uniform(0.005, 0.02)

    for i, year in enumerate(years):
        # Add some noise and trends
        gdp = base_gdp * (1 + gdp_growth) ** i * (1 + np.random.normal(0, 0.05))
        life_exp = min(85, base_life + life_growth * i * 100 + np.random.normal(0, 0.5))
        pop = base_pop * (1 + pop_growth) ** i

        data_rows.append(
            {"country": country, "year": year, "gdp_per_capita": gdp, "life_expectancy": life_exp, "population": pop}
        )

df = pd.DataFrame(data_rows)

# lets-plot does not have built-in animation like Plotly
# Per spec: "Libraries without animation support should implement a static faceted version"
# Create a faceted view showing key time points

# Select key years for faceted display
key_years = [2000, 2005, 2010, 2015, 2019]
df_key = df[df["year"].isin(key_years)].copy()
df_key["year_label"] = df_key["year"].astype(str)

# Create the faceted plot showing temporal evolution
plot = (
    ggplot(df_key, aes(x="gdp_per_capita", y="life_expectancy"))
    + geom_point(aes(color="country", size="population"), alpha=0.85)
    + scale_size(range=[6, 20], name="Population (M)")
    + scale_color_brewer(palette="Paired", name="Country")
    + scale_x_log10()
    + facet_wrap("year_label", ncol=5)
    + labs(
        title="scatter-animated-controls \u00b7 lets-plot \u00b7 pyplots.ai",
        x="GDP per Capita (log scale, USD)",
        y="Life Expectancy (years)",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title=element_text(size=18),
        axis_text=element_text(size=14),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        strip_text=element_text(size=18, face="bold"),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
