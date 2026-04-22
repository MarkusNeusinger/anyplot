""" pyplots.ai
histogram-density: Density Histogram
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_density, geom_histogram, ggplot, labs, theme, theme_minimal


# Data - generate sample data from a mixture of two normal distributions
np.random.seed(42)
n_samples = 500

# Create a bimodal distribution for interesting visualization
group1 = np.random.normal(loc=65, scale=8, size=n_samples // 2)  # First peak
group2 = np.random.normal(loc=85, scale=6, size=n_samples // 2)  # Second peak
values = np.concatenate([group1, group2])

df = pd.DataFrame({"values": values})

# Create plot - density histogram with overlaid density curve
plot = (
    ggplot(df, aes(x="values"))
    + geom_histogram(aes(y="..density.."), bins=30, fill="#306998", color="white", alpha=0.7)
    + geom_density(color="#FFD43B", size=2, alpha=0.8)
    + labs(x="Test Score", y="Density", title="histogram-density · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major_y=element_text(alpha=0.3),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
