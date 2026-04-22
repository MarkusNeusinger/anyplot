""" pyplots.ai
histogram-stacked: Stacked Histogram
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Test scores from three different classes
np.random.seed(42)

# Generate scores for three classes with different distributions
class_a = np.random.normal(loc=72, scale=10, size=150)  # Average performers
class_b = np.random.normal(loc=78, scale=8, size=120)  # Above average
class_c = np.random.normal(loc=68, scale=12, size=130)  # More varied

# Combine into DataFrame
df = pd.DataFrame(
    {
        "score": np.concatenate([class_a, class_b, class_c]),
        "class": ["Class A"] * 150 + ["Class B"] * 120 + ["Class C"] * 130,
    }
)

# Clip scores to realistic range [0, 100]
df["score"] = df["score"].clip(0, 100)

# Plot - Stacked histogram
plot = (
    ggplot(df, aes(x="score", fill="class"))
    + geom_histogram(binwidth=5, position="stack", color="white", size=0.3)
    + scale_fill_manual(values=["#306998", "#FFD43B", "#DC2626"])
    + labs(
        x="Test Score (points)",
        y="Number of Students",
        title="histogram-stacked · lets-plot · pyplots.ai",
        fill="Class",
    )
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", scale=3, path=".")

# Save interactive HTML
ggsave(plot, "plot.html", path=".")
