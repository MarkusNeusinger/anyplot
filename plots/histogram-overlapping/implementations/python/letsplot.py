""" pyplots.ai
histogram-overlapping: Overlapping Histograms
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_histogram,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - comparing response times between two experimental conditions
np.random.seed(42)

# Control group - baseline response times (ms)
control = np.random.normal(loc=450, scale=80, size=200)

# Treatment group - faster response times with intervention
treatment = np.random.normal(loc=380, scale=70, size=200)

# Create DataFrame
df = pd.DataFrame(
    {"response_time": np.concatenate([control, treatment]), "group": ["Control"] * 200 + ["Treatment"] * 200}
)

# Create overlapping histograms
plot = (
    ggplot(df, aes(x="response_time", fill="group"))
    + geom_histogram(alpha=0.5, bins=25, position="identity", color="white", size=0.3)
    + scale_fill_manual(values=["#306998", "#FFD43B"])
    + labs(x="Response Time (ms)", y="Count", title="histogram-overlapping · letsplot · pyplots.ai", fill="Condition")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x to get 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
