""" pyplots.ai
histogram-cumulative: Cumulative Histogram
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 99/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Response times in milliseconds (realistic API monitoring scenario)
np.random.seed(42)
response_times = np.concatenate(
    [
        np.random.exponential(scale=50, size=400),  # Normal requests
        np.random.exponential(scale=150, size=80),  # Slower requests
        np.random.uniform(300, 500, size=20),  # Occasional slow outliers
    ]
)

# Compute cumulative histogram data
n_bins = 25
counts, bin_edges = np.histogram(response_times, bins=n_bins)
cumulative_counts = np.cumsum(counts)

df = pd.DataFrame({"xmin": bin_edges[:-1], "xmax": bin_edges[1:], "ymin": 0, "ymax": cumulative_counts})

# Plot - Cumulative histogram using geom_rect for precise bin widths
plot = (
    ggplot(df)
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill="#306998", color="#1e4a6e", alpha=0.85, size=0.5
    )
    + labs(x="Response Time (ms)", y="Cumulative Count", title="histogram-cumulative · letsplot · pyplots.ai")
    + scale_x_continuous(expand=[0.02, 0])
    + scale_y_continuous(expand=[0, 0, 0.05, 0])
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#cccccc", size=0.3),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG and HTML
ggsave(plot, "plot.png", scale=3)
ggsave(plot, "plot.html")
