""" pyplots.ai
bar-grouped: Grouped Bar Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Quarterly sales by product category
categories = ["Q1", "Q2", "Q3", "Q4"]
products = ["Electronics", "Clothing", "Home & Garden"]

data = {
    "Quarter": categories * 3,
    "Product": ["Electronics"] * 4 + ["Clothing"] * 4 + ["Home & Garden"] * 4,
    "Revenue": [
        # Electronics - strong growth
        145,
        168,
        192,
        235,
        # Clothing - seasonal pattern
        98,
        112,
        87,
        142,
        # Home & Garden - spring/summer peak
        67,
        95,
        108,
        72,
    ],
}

df = pd.DataFrame(data)

# Plot - Grouped bar chart
plot = (
    ggplot(df, aes(x="Quarter", y="Revenue", fill="Product"))
    + geom_bar(stat="identity", position="dodge", width=0.7, alpha=0.9)
    + scale_fill_manual(values=["#306998", "#FFD43B", "#DC2626"])
    + labs(x="Quarter", y="Revenue ($ thousands)", title="bar-grouped · letsplot · pyplots.ai", fill="Product Category")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG and HTML
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
