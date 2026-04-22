""" pyplots.ai
line-markers: Line Plot with Markers
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Quarterly product performance metrics
np.random.seed(42)
quarters = np.arange(1, 13)  # 12 quarters (3 years)

# Three product lines with different growth patterns
product_a = 45 + np.cumsum(np.random.randn(12) * 3) + np.arange(12) * 2
product_b = 60 + np.cumsum(np.random.randn(12) * 4) + np.arange(12) * 1.5
product_c = 35 + np.cumsum(np.random.randn(12) * 2.5) + np.arange(12) * 2.5

df = pd.DataFrame(
    {
        "Quarter": list(quarters) * 3,
        "Revenue": np.concatenate([product_a, product_b, product_c]),
        "Product": ["Product A"] * 12 + ["Product B"] * 12 + ["Product C"] * 12,
    }
)

# Create plot
plot = (
    ggplot(df, aes(x="Quarter", y="Revenue", color="Product"))
    + geom_line(size=2.5)
    + geom_point(size=6, alpha=0.9)
    + scale_color_manual(values=["#306998", "#FFD43B", "#DC2626"])
    + scale_x_continuous(breaks=list(range(1, 13)))
    + labs(x="Quarter", y="Revenue (Million USD)", title="line-markers · lets-plot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28),
        axis_title=element_text(size=22),
        axis_text=element_text(size=18),
        legend_title=element_text(size=20),
        legend_text=element_text(size=18),
        legend_position="right",
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
    )
    + ggsize(1600, 900)
)

# Save outputs
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
