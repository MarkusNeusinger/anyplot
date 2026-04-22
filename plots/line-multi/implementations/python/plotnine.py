""" pyplots.ai
line-multi: Multi-Line Comparison Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-24
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Data - Monthly sales for 4 product lines over 12 months
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Generate realistic sales data with different trends
base_sales = 100
electronics = base_sales + np.cumsum(np.random.randn(12) * 8) + months * 5
clothing = base_sales + 20 + np.cumsum(np.random.randn(12) * 6) + np.sin(months * 0.5) * 15
furniture = base_sales - 10 + np.cumsum(np.random.randn(12) * 5) + months * 2
accessories = base_sales + 10 + np.cumsum(np.random.randn(12) * 7)

# Create long-format DataFrame for plotnine
df = pd.DataFrame(
    {
        "Month": np.tile(months, 4),
        "Sales": np.concatenate([electronics, clothing, furniture, accessories]),
        "Product": np.repeat(["Electronics", "Clothing", "Furniture", "Accessories"], 12),
    }
)

# Make Product a categorical with specific order to control legend and color mapping
df["Product"] = pd.Categorical(
    df["Product"], categories=["Electronics", "Clothing", "Furniture", "Accessories"], ordered=True
)

# Colors mapped to category order: Python Blue, Yellow, then colorblind-safe
colors = {"Electronics": "#306998", "Clothing": "#FFD43B", "Furniture": "#81C784", "Accessories": "#E57373"}

# Create plot
plot = (
    ggplot(df, aes(x="Month", y="Sales", color="Product", group="Product"))
    + geom_line(size=2.5)
    + geom_point(size=5)
    + scale_color_manual(values=colors)
    + scale_x_continuous(breaks=months, labels=month_labels)
    + labs(x="Month", y="Sales (thousands USD)", title="line-multi · plotnine · pyplots.ai", color="Product Line")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, ha="center"),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_position="right",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
