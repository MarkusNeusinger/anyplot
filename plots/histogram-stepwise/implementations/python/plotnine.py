""" pyplots.ai
histogram-stepwise: Step Histogram
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_line, element_text, geom_step, ggplot, labs, scale_color_manual, theme, theme_minimal


# Data - Response times (ms) for two server configurations
np.random.seed(42)

# Configuration A: Standard server setup
config_a = np.random.normal(loc=250, scale=60, size=400)

# Configuration B: Optimized server setup (faster, tighter distribution)
config_b = np.random.normal(loc=180, scale=40, size=400)

# Calculate histograms with shared bins for comparison
n_bins = 30
all_data = np.concatenate([config_a, config_b])
bin_edges = np.linspace(all_data.min() - 10, all_data.max() + 10, n_bins + 1)

# Compute histogram counts for each configuration
counts_a, _ = np.histogram(config_a, bins=bin_edges)
counts_b, _ = np.histogram(config_b, bins=bin_edges)

# Create step data: prepend zero at start, append zero at end for clean closure
# For step histogram: use bin edges (not centers) for x values
step_x_a = np.repeat(bin_edges, 2)[1:-1]
step_y_a = np.repeat(counts_a, 2)

step_x_b = np.repeat(bin_edges, 2)[1:-1]
step_y_b = np.repeat(counts_b, 2)

# Create DataFrames
df_a = pd.DataFrame({"x": step_x_a, "count": step_y_a, "config": "Standard Setup"})
df_b = pd.DataFrame({"x": step_x_b, "count": step_y_b, "config": "Optimized Setup"})
df = pd.concat([df_a, df_b], ignore_index=True)

# Plot
plot = (
    ggplot(df, aes(x="x", y="count", color="config"))
    + geom_step(size=2, alpha=0.9)
    + labs(
        x="Response Time (ms)", y="Frequency", title="histogram-stepwise · plotnine · pyplots.ai", color="Configuration"
    )
    + scale_color_manual(values=["#306998", "#FFD43B"])
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
