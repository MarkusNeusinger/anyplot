""" pyplots.ai
density-rug: Density Plot with Rug Marks
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_text,
    geom_density,
    geom_segment,
    ggplot,
    ggsave,
    ggsize,
    labs,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - Simulated response times (ms) showing bimodal distribution
np.random.seed(42)
fast_responses = np.random.normal(loc=250, scale=40, size=80)
slow_responses = np.random.normal(loc=450, scale=60, size=40)
response_times = np.concatenate([fast_responses, slow_responses])
df = pd.DataFrame({"response_time": response_times})

# Create rug data - small vertical segments at each data point
rug_height = 0.0003  # Small height for rug marks
rug_df = pd.DataFrame({"x": response_times, "ymin": 0, "ymax": rug_height})

# Plot
plot = (
    ggplot()
    + geom_density(aes(x="response_time"), data=df, fill="#306998", color="#306998", alpha=0.4, size=1.5)
    + geom_segment(aes(x="x", xend="x", y="ymin", yend="ymax"), data=rug_df, color="#306998", alpha=0.6, size=1.0)
    + labs(x="Response Time (ms)", y="Density", title="density-rug · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, "plot.html", path=".")
