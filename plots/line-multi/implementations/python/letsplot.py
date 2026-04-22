""" pyplots.ai
line-multi: Multi-Line Comparison Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-24
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data: Monthly sales for 3 product lines over 12 months
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Generate realistic sales data with distinct trends
electronics = 150 + np.cumsum(np.random.randn(12) * 8) + np.linspace(0, 40, 12)
clothing = 120 + np.cumsum(np.random.randn(12) * 6) + np.sin(np.linspace(0, 2 * np.pi, 12)) * 20
home_goods = 90 + np.cumsum(np.random.randn(12) * 5) + np.linspace(0, 25, 12)

# Create long-format DataFrame for ggplot
df = pd.DataFrame(
    {
        "Month": np.tile(months, 3),
        "MonthLabel": np.tile(month_labels, 3),
        "Sales": np.concatenate([electronics, clothing, home_goods]),
        "Product": np.repeat(["Electronics", "Clothing", "Home Goods"], 12),
    }
)

# Plot
plot = (
    ggplot(df, aes(x="Month", y="Sales", color="Product"))
    + geom_line(size=2.5)
    + geom_point(size=5, alpha=0.9)
    + scale_color_manual(values=["#306998", "#FFD43B", "#DC2626"])
    + scale_x_continuous(breaks=months.tolist(), labels=month_labels)
    + labs(title="line-multi · letsplot · pyplots.ai", x="Month", y="Sales (thousands USD)")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, hjust=0.5),
        axis_title=element_text(size=22),
        axis_text=element_text(size=18),
        legend_title=element_text(size=20),
        legend_text=element_text(size=18),
        legend_position="right",
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, "plot.html", path=".")
