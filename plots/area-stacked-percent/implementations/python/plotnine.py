""" pyplots.ai
area-stacked-percent: 100% Stacked Area Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_area,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Market share evolution of tech product categories
np.random.seed(42)

years = list(range(2015, 2025))

# Generate category data with realistic trends
smartphones = [45, 43, 40, 38, 36, 35, 34, 33, 32, 31]
tablets = [25, 23, 20, 18, 16, 14, 12, 11, 10, 9]
wearables = [5, 8, 12, 15, 18, 20, 22, 24, 26, 28]
laptops = [25, 26, 28, 29, 30, 31, 32, 32, 32, 32]

# Create DataFrame in long format for plotnine
df_list = []
for i, year in enumerate(years):
    total = smartphones[i] + tablets[i] + wearables[i] + laptops[i]
    df_list.append(
        {"Year": year, "Category": "Smartphones", "Value": smartphones[i], "Percent": smartphones[i] / total * 100}
    )
    df_list.append({"Year": year, "Category": "Tablets", "Value": tablets[i], "Percent": tablets[i] / total * 100})
    df_list.append(
        {"Year": year, "Category": "Wearables", "Value": wearables[i], "Percent": wearables[i] / total * 100}
    )
    df_list.append({"Year": year, "Category": "Laptops", "Value": laptops[i], "Percent": laptops[i] / total * 100})

df = pd.DataFrame(df_list)

# Set category order for stacking
df["Category"] = pd.Categorical(
    df["Category"], categories=["Smartphones", "Tablets", "Wearables", "Laptops"], ordered=True
)

# Create plot
plot = (
    ggplot(df, aes(x="Year", y="Percent", fill="Category"))
    + geom_area(position="stack", alpha=0.85)
    + scale_fill_manual(values=["#306998", "#FFD43B", "#4ECDC4", "#E76F51"])
    + scale_x_continuous(breaks=range(2015, 2025, 2))
    + scale_y_continuous(breaks=[0, 25, 50, 75, 100], labels=["0%", "25%", "50%", "75%", "100%"])
    + labs(
        title="area-stacked-percent · plotnine · pyplots.ai", x="Year", y="Market Share (%)", fill="Product Category"
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major=element_line(color="#CCCCCC", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(alpha=0),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
