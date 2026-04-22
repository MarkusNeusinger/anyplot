""" pyplots.ai
histogram-cumulative: Cumulative Histogram
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_line, element_text, geom_bar, ggplot, labs, scale_y_continuous, theme, theme_minimal


# Data - Product shelf life measurements (days until expiration)
np.random.seed(42)
shelf_life = np.concatenate(
    [
        np.random.normal(45, 8, 300),  # Standard products
        np.random.normal(65, 5, 150),  # Premium long-life products
    ]
)

# Calculate cumulative histogram
n_bins = 25
hist, bin_edges = np.histogram(shelf_life, bins=n_bins)
cumulative_counts = np.cumsum(hist)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
bin_width = bin_edges[1] - bin_edges[0]

# Create DataFrame with cumulative counts
df_hist = pd.DataFrame({"bin_center": bin_centers, "cumulative_count": cumulative_counts})

total = len(shelf_life)

# Create the cumulative histogram using geom_bar
plot = (
    ggplot(df_hist, aes(x="bin_center", y="cumulative_count"))
    + geom_bar(stat="identity", width=bin_width * 0.95, fill="#306998", color="#1a3d5c", alpha=0.85, size=0.3)
    + labs(x="Shelf Life (days)", y="Cumulative Count", title="histogram-cumulative · plotnine · pyplots.ai")
    + scale_y_continuous(breaks=[0, 100, 200, 300, 400, total], limits=(0, total + 20))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
