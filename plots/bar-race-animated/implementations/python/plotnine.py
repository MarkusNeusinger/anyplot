""" pyplots.ai
bar-race-animated: Animated Bar Chart Race
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_blank,
    element_rect,
    element_text,
    expand_limits,
    facet_wrap,
    geom_col,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Tech companies revenue over time (billions USD)
np.random.seed(42)

companies = ["TechCorp", "DataFlow", "CloudBase", "NetSys", "CodeLab", "AppStream", "ByteWorks", "DigiCore"]

# Color palette for companies - using Python colors and colorblind-safe additions
colors = {
    "TechCorp": "#306998",  # Python Blue
    "DataFlow": "#FFD43B",  # Python Yellow
    "CloudBase": "#2E86AB",  # Steel Blue
    "NetSys": "#A23B72",  # Mulberry
    "CodeLab": "#F18F01",  # Orange
    "AppStream": "#C73E1D",  # Vermilion
    "ByteWorks": "#3B1F2B",  # Dark Purple
    "DigiCore": "#95C623",  # Yellow Green
}

years = [2018, 2020, 2022, 2024]

# Generate realistic growth data with different trajectories
base_values = {
    "TechCorp": 150,
    "DataFlow": 80,
    "CloudBase": 60,
    "NetSys": 120,
    "CodeLab": 40,
    "AppStream": 90,
    "ByteWorks": 70,
    "DigiCore": 55,
}

growth_rates = {
    "TechCorp": 1.15,
    "DataFlow": 1.35,
    "CloudBase": 1.45,
    "NetSys": 1.08,
    "CodeLab": 1.50,
    "AppStream": 1.12,
    "ByteWorks": 1.25,
    "DigiCore": 1.40,
}

# Build dataframe
data = []
for year in years:
    year_idx = years.index(year)
    for company in companies:
        value = base_values[company] * (growth_rates[company] ** year_idx)
        value += np.random.normal(0, value * 0.05)
        data.append({"company": company, "year": year, "revenue": max(10, value)})

df = pd.DataFrame(data)

# Add rank for each year (for positioning) - rank 1 = highest value
df["rank"] = df.groupby("year")["revenue"].rank(ascending=False, method="first").astype(int)

# Create year labels for faceting
df["year_label"] = df["year"].apply(lambda x: f"Year {x}")

# Create label text
df["label"] = df["revenue"].apply(lambda x: f"${x:.0f}B")

# Sort for consistent ordering within facets
df = df.sort_values(["year", "rank"])

# Create a categorical ordering column for proper per-facet bar sorting
# This creates a unique rank-based key for each year-company pair
df["bar_order"] = df.groupby("year")["revenue"].rank(ascending=True, method="first").astype(int)

# Get max revenue for consistent x-axis scaling
max_revenue = df["revenue"].max()

# Create combined label for display (company name and value)
df["bar_label"] = df.apply(lambda row: f"{row['company']}  {row['label']}", axis=1)

# Create the small multiples plot - bars sorted by revenue within each facet
# Using bar_order ensures proper sorting per-facet (rank-based within each year)
plot = (
    ggplot(df, aes(x="bar_order", y="revenue", fill="company"))
    + geom_col(width=0.8, show_legend=False)
    + geom_text(aes(label="bar_label"), ha="left", nudge_y=5, size=9, color="#333333")
    + coord_flip()
    + facet_wrap("~year_label", ncol=2)
    + scale_fill_manual(values=colors)
    + scale_y_continuous(expand=(0.02, 0, 0.25, 0))
    + expand_limits(y=max_revenue * 1.2)
    + labs(
        title="Tech Company Revenue Race · bar-race-animated · plotnine · pyplots.ai", x="", y="Revenue (Billions USD)"
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 10),
        plot_title=element_text(size=24, weight="bold", ha="center", margin={"b": 15}),
        axis_title_x=element_text(size=18, margin={"t": 10}),
        axis_title_y=element_blank(),
        axis_text_x=element_text(size=14),
        axis_text_y=element_blank(),
        strip_text=element_text(size=20, weight="bold"),
        strip_background=element_rect(fill="#f0f0f0", color="none"),
        panel_spacing=0.05,
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        plot_margin=0.02,
    )
)

# Save
plot.save("plot.png", dpi=300)
