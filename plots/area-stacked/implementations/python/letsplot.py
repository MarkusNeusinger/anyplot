""" pyplots.ai
area-stacked: Stacked Area Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_text,
    geom_area,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data: Monthly revenue by product category over 2 years
np.random.seed(42)
months = pd.date_range("2023-01", periods=24, freq="ME")

# Generate revenue data for each product category (in thousands)
# Largest categories at the bottom for easier reading
base_electronics = 80 + np.cumsum(np.random.randn(24) * 3)
base_clothing = 50 + np.cumsum(np.random.randn(24) * 2)
base_home = 35 + np.cumsum(np.random.randn(24) * 2)
base_sports = 25 + np.cumsum(np.random.randn(24) * 1.5)

# Add seasonality
seasonality = 10 * np.sin(np.linspace(0, 4 * np.pi, 24))
electronics = np.maximum(base_electronics + seasonality, 20)
clothing = np.maximum(base_clothing + seasonality * 0.7, 15)
home = np.maximum(base_home + seasonality * 0.5, 10)
sports = np.maximum(base_sports + seasonality * 0.3, 8)

# Create long-format dataframe for lets-plot
df = pd.DataFrame(
    {
        "Month": list(months) * 4,
        "Revenue": np.concatenate([electronics, clothing, home, sports]),
        "Category": ["Electronics"] * 24 + ["Clothing"] * 24 + ["Home & Garden"] * 24 + ["Sports"] * 24,
    }
)

# Convert to numeric for x-axis (months since start)
df["MonthNum"] = df.groupby("Category").cumcount()

# Reorder categories for stacking (largest at bottom)
category_order = ["Electronics", "Clothing", "Home & Garden", "Sports"]
df["Category"] = pd.Categorical(df["Category"], categories=category_order, ordered=True)

# Create stacked area chart
plot = (
    ggplot(df, aes(x="MonthNum", y="Revenue", fill="Category"))
    + geom_area(alpha=0.85, position="stack", size=0.5, color="white")
    + scale_fill_manual(values=["#306998", "#FFD43B", "#2E8B57", "#DC143C"])
    + scale_x_continuous(
        name="Month", breaks=[0, 6, 12, 18, 23], labels=["Jan 2023", "Jul 2023", "Jan 2024", "Jul 2024", "Dec 2024"]
    )
    + scale_y_continuous(name="Revenue (Thousands USD)")
    + labs(title="area-stacked · letsplot · pyplots.ai", fill="Product Category")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major=element_line(color="#CCCCCC", size=0.3),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML version
ggsave(plot, "plot.html", path=".")
