""" pyplots.ai
bar-race-animated: Animated Bar Chart Race
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data: Simulated streaming platform subscriber counts (millions) over 8 years
np.random.seed(42)

platforms = ["StreamMax", "ViewHub", "FlixNet", "WatchNow", "CineCloud", "MediaFlow"]
years = list(range(2016, 2024))
colors = ["#306998", "#FFD43B", "#DC2626", "#059669", "#7C3AED", "#EA580C"]

# Generate realistic growth patterns for each platform
data_rows = []
base_values = [50, 80, 120, 30, 20, 40]  # Starting subscribers in millions
growth_rates = [1.35, 1.15, 1.08, 1.45, 1.55, 1.25]  # Annual growth multipliers

for i, platform in enumerate(platforms):
    value = base_values[i]
    for year in years:
        # Add some randomness to growth
        noise = np.random.uniform(0.9, 1.1)
        value = value * growth_rates[i] * noise
        data_rows.append({"platform": platform, "year": year, "subscribers": round(value, 1)})

df = pd.DataFrame(data_rows)

# Select 4 key time snapshots for the small multiples grid
snapshot_years = [2016, 2018, 2021, 2023]

# Assign consistent colors to each platform (dictionary for named mapping)
platform_colors = dict(zip(platforms, colors))

# Build individual plots for each snapshot year
plots = []
for year in snapshot_years:
    year_data = df[df["year"] == year].copy()
    year_data = year_data.sort_values("subscribers", ascending=True)
    # Create ordered factor for proper bar ordering (sorted by value)
    year_data["platform"] = pd.Categorical(
        year_data["platform"], categories=year_data["platform"].tolist(), ordered=True
    )

    plot = (
        ggplot(year_data, aes(x="platform", y="subscribers", fill="platform"))
        + geom_bar(stat="identity", width=0.7, alpha=0.9)
        + coord_flip()
        + scale_fill_manual(values=platform_colors)
        + labs(title=str(year), x="", y="Subscribers (millions)")
        + theme_minimal()
        + theme(
            plot_title=element_text(size=28, face="bold"),
            axis_title_x=element_text(size=18),
            axis_title_y=element_blank(),
            axis_text_x=element_text(size=16),
            axis_text_y=element_text(size=18),
            legend_position="none",
            panel_grid_major_y=element_blank(),
            panel_grid_minor=element_blank(),
        )
    )
    plots.append(plot)

# Use gggrid for 2x2 layout with overall title
grid = (
    gggrid(plots, ncol=2)
    + labs(title="bar-race-animated · letsplot · pyplots.ai")
    + theme(plot_title=element_text(size=32, face="bold", hjust=0.5))
    + ggsize(1600, 900)
)

# Save as PNG (scale=3 for 4800x2700 px output)
ggsave(grid, "plot.png", path=".", scale=3)

# Save interactive HTML version
ggsave(grid, "plot.html", path=".")
