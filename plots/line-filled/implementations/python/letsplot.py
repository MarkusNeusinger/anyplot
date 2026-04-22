""" pyplots.ai
line-filled: Filled Line Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Monthly website traffic over a year
np.random.seed(42)
months = np.arange(1, 13)
base_traffic = 50000 + np.cumsum(np.random.randn(12) * 5000)
seasonal_effect = 10000 * np.sin(np.pi * months / 6)
traffic = base_traffic + seasonal_effect + np.random.randn(12) * 3000
traffic = np.maximum(traffic, 20000)  # Ensure positive values

df = pd.DataFrame({"month": months, "visitors": traffic})

# Create filled line plot
plot = (
    ggplot(df, aes(x="month", y="visitors"))
    + geom_area(fill="#306998", alpha=0.4)
    + geom_line(color="#306998", size=2)
    + geom_point(color="#306998", size=5)
    + labs(x="Month", y="Website Visitors", title="line-filled · letsplot · pyplots.ai")
    + scale_x_continuous(breaks=list(range(1, 13)))
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_blank(),
    )
)

# Save PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, "plot.html", path=".")
