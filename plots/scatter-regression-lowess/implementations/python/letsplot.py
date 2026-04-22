""" pyplots.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_point,
    geom_smooth,
    ggplot,
    ggsave,
    ggsize,
    labs,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - Complex non-linear relationship (plant growth vs temperature)
np.random.seed(42)
n = 200
x = np.linspace(5, 40, n)
# Growth peaks at moderate temps, drops at extremes
y = 15 + 8 * np.sin((x - 5) * np.pi / 35) + 3 * np.cos((x - 10) * np.pi / 15) + np.random.randn(n) * 2.5

df = pd.DataFrame({"temperature": x, "growth_rate": y})

# Plot
plot = (
    ggplot(df, aes(x="temperature", y="growth_rate"))
    + geom_point(color="#306998", size=4, alpha=0.6)
    + geom_smooth(method="loess", span=0.4, color="#FFD43B", size=2.5, se=True, fill="#FFD43B", alpha=0.2)
    + labs(x="Temperature (°C)", y="Growth Rate (cm/day)", title="scatter-regression-lowess · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_text=element_text(size=16),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x for 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, "plot.html", path=".")
