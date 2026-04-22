""" pyplots.ai
violin-box: Violin Plot with Embedded Box Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Response times (ms) for different server configurations
np.random.seed(42)

n_per_group = 150
groups = ["Standard", "Optimized", "Premium", "Enterprise"]

data = []
# Standard: higher mean, moderate spread
data.extend([(np.random.normal(85, 15), "Standard") for _ in range(n_per_group)])
# Optimized: lower mean, some outliers
vals = np.concatenate([np.random.normal(55, 12, n_per_group - 5), np.random.normal(100, 5, 5)])
data.extend([(v, "Optimized") for v in vals])
# Premium: bimodal distribution
vals = np.concatenate([np.random.normal(40, 8, n_per_group // 2), np.random.normal(60, 8, n_per_group // 2)])
data.extend([(v, "Premium") for v in vals])
# Enterprise: low mean, tight spread, few outliers
vals = np.concatenate([np.random.normal(30, 6, n_per_group - 3), np.random.normal(70, 3, 3)])
data.extend([(v, "Enterprise") for v in vals])

df = pd.DataFrame(data, columns=["response_time", "configuration"])

# Create violin plot with embedded box plot
plot = (
    ggplot(df, aes(x="configuration", y="response_time", fill="configuration"))
    + geom_violin(alpha=0.7, color="#306998", size=1.0, trim=False)
    + geom_boxplot(width=0.15, fill="white", color="#306998", alpha=0.9, outlier_shape=21, outlier_size=3)
    + scale_fill_manual(values=["#306998", "#FFD43B", "#4A90A4", "#7CB342"])
    + labs(x="Server Configuration", y="Response Time (ms)", title="violin-box · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_position="none",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive version
ggsave(plot, "plot.html", path=".")
