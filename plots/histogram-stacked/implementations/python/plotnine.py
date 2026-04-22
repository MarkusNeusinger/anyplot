""" pyplots.ai
histogram-stacked: Stacked Histogram
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 97/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_histogram, ggplot, labs, scale_fill_manual, theme, theme_minimal


# Data - Plant growth measurements across different soil types
np.random.seed(42)

# Generate realistic plant height data for three soil types
soil_a = np.random.normal(loc=25, scale=5, size=150)  # Sandy soil
soil_b = np.random.normal(loc=30, scale=6, size=120)  # Loamy soil
soil_c = np.random.normal(loc=22, scale=4, size=100)  # Clay soil

df = pd.DataFrame(
    {
        "height": np.concatenate([soil_a, soil_b, soil_c]),
        "soil_type": (["Sandy Soil"] * 150 + ["Loamy Soil"] * 120 + ["Clay Soil"] * 100),
    }
)

# Create stacked histogram
plot = (
    ggplot(df, aes(x="height", fill="soil_type"))
    + geom_histogram(bins=20, position="stack", alpha=0.85, color="white", size=0.3)
    + labs(x="Plant Height (cm)", y="Frequency", title="histogram-stacked · plotnine · pyplots.ai", fill="Soil Type")
    + scale_fill_manual(values=["#306998", "#FFD43B", "#4ECDC4"])
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_position="right",
    )
)

# Save
plot.save("plot.png", dpi=300)
