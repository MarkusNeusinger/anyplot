# ruff: noqa: F405
"""anyplot.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: letsplot | Python 3.13
Quality: pending | Created: 2025-12-31
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F401
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

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
for idx, country in enumerate(countries):
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
            {
                "country": country,
                "year": year,
                "gdp_per_capita": gdp,
                "life_expectancy": life_exp,
                "population": pop,
                "color_idx": idx % len(IMPRINT),
            }
        )

df = pd.DataFrame(data_rows)

# lets-plot does not have built-in animation like Plotly
# Per spec: "Libraries without animation support should implement a static faceted version"
# Create a faceted view showing key time points

# Select key years for faceted display
key_years = [2000, 2005, 2010, 2015, 2019]
df_key = df[df["year"].isin(key_years)].copy()
df_key["year_label"] = df_key["year"].astype(str)

# Create color mapping based on Okabe-Ito palette
country_colors = {c: IMPRINT[i % len(IMPRINT)] for i, c in enumerate(countries)}

# Theme configuration
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=24, face="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=16),
    strip_text=element_text(color=INK, size=18, face="bold"),
    legend_position="right",
)

# Create the faceted plot showing temporal evolution
plot = (
    ggplot(df_key, aes(x="gdp_per_capita", y="life_expectancy"))
    + geom_point(aes(color="country", size="population"), alpha=0.85)
    + scale_size(range=[6, 20], name="Population (M)")
    + scale_color_manual(values=country_colors, name="Country")
    + scale_x_log10()
    + facet_wrap("year_label", ncol=5)
    + labs(
        title="scatter-animated-controls · letsplot · anyplot.ai",
        x="GDP per Capita (log scale, USD)",
        y="Life Expectancy (years)",
    )
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, f"plot-{THEME}.html", path=".")
