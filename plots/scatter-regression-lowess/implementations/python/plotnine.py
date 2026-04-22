""" pyplots.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_point, geom_smooth, ggplot, labs, theme, theme_minimal


# Data - create complex non-linear relationship (crop yield vs temperature)
np.random.seed(42)
n_points = 150

# Temperature range (x) - realistic agricultural context
x = np.linspace(5, 35, n_points)

# Yield (y) - peaks around 20-25°C, drops at extremes (realistic crop response)
# Complex non-linear pattern: quadratic-like with some local variation
y_base = -0.5 * (x - 22) ** 2 + 80  # Peak around 22°C
y_noise = np.random.normal(0, 8, n_points)  # Natural variation
y = y_base + y_noise + 3 * np.sin(x / 3)  # Add subtle local pattern

# Ensure positive yields
y = np.clip(y, 5, None)

# Create DataFrame
df = pd.DataFrame({"temperature": x, "yield": y})

# Create plot with scatter points and LOWESS smooth
plot = (
    ggplot(df, aes(x="temperature", y="yield"))
    + geom_point(color="#306998", alpha=0.6, size=3)
    + geom_smooth(method="lowess", span=0.4, color="#FFD43B", size=2.5, se=False)
    + labs(
        x="Temperature (°C)", y="Crop Yield (tons/hectare)", title="scatter-regression-lowess · plotnine · pyplots.ai"
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
    )
)

# Save
plot.save("plot.png", dpi=300)
