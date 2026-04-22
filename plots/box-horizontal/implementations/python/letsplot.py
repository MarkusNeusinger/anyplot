""" pyplots.ai
box-horizontal: Horizontal Box Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Response times by service type (realistic scenario with varied distributions)
np.random.seed(42)

services = ["API Gateway", "Database Query", "Authentication", "File Storage", "Cache Lookup", "Email Service"]

data = []
# Different distributions to showcase boxplot features (medians, spreads, outliers)
distributions = {
    "API Gateway": (120, 40, 3),  # Medium response, moderate spread, some outliers
    "Database Query": (250, 100, 5),  # Slower, high variability, more outliers
    "Authentication": (80, 25, 2),  # Fast, consistent
    "File Storage": (300, 80, 4),  # Slowest, variable
    "Cache Lookup": (15, 8, 2),  # Very fast, tight distribution
    "Email Service": (180, 60, 6),  # Medium, some outliers
}

for service in services:
    mean, std, n_outliers = distributions[service]
    # Main distribution
    values = np.random.normal(mean, std, 80)
    # Add some outliers
    outliers = np.random.normal(mean + 4 * std, std / 2, n_outliers)
    all_values = np.concatenate([values, outliers])
    all_values = np.maximum(all_values, 5)  # Ensure positive values

    for val in all_values:
        data.append({"Service": service, "Response Time (ms)": val})

df = pd.DataFrame(data)

# Create horizontal box plot
plot = (
    ggplot(df, aes(x="Response Time (ms)", y="Service"))
    + geom_boxplot(
        fill="#306998", color="#1a3a4f", alpha=0.7, outlier_color="#FFD43B", outlier_size=4, outlier_alpha=0.8, size=1.2
    )
    + labs(x="Response Time (ms)", y="Service Type", title="box-horizontal · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_y=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML version
ggsave(plot, "plot.html", path=".")
