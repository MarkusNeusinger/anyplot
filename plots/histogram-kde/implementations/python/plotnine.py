""" pyplots.ai
histogram-kde: Histogram with KDE Overlay
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 98/100 | Created: 2025-12-24
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    after_stat,
    element_line,
    element_text,
    geom_density,
    geom_histogram,
    ggplot,
    labs,
    theme,
    theme_minimal,
)


# Data - Stock daily returns (realistic financial data)
np.random.seed(42)
# Simulate stock returns with slight negative skew and fat tails (realistic market behavior)
returns = np.concatenate(
    [
        np.random.normal(0.001, 0.015, 400),  # Normal trading days
        np.random.normal(-0.02, 0.03, 80),  # Volatile periods
        np.random.normal(0.005, 0.008, 120),  # Low volatility periods
    ]
)
returns = returns * 100  # Convert to percentage

df = pd.DataFrame({"returns": returns})

# Plot - Histogram with KDE overlay
plot = (
    ggplot(df, aes(x="returns"))
    + geom_histogram(aes(y=after_stat("density")), bins=35, fill="#306998", color="#1a3d5c", alpha=0.5, size=0.3)
    + geom_density(color="#FFD43B", size=2.5)
    + labs(x="Daily Return (%)", y="Density", title="histogram-kde · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#eeeeee", size=0.3, alpha=0.2),
    )
)

plot.save("plot.png", dpi=300)
