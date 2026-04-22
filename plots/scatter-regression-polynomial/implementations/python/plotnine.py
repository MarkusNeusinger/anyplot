""" pyplots.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_text,
    geom_point,
    geom_smooth,
    ggplot,
    labs,
    theme,
    theme_minimal,
)


# Data - Temperature vs energy consumption (quadratic relationship)
np.random.seed(42)
n_points = 100
temperature = np.random.uniform(0, 40, n_points)
# Energy consumption follows U-shaped curve: high at cold and hot temps, low in middle
optimal_temp = 20
energy = 50 + 0.15 * (temperature - optimal_temp) ** 2 + np.random.normal(0, 3, n_points)

df = pd.DataFrame({"temperature": temperature, "energy": energy})

# Calculate polynomial regression coefficients for annotation
coeffs = np.polyfit(temperature, energy, 2)
poly_func = np.poly1d(coeffs)
y_pred = poly_func(temperature)
ss_res = np.sum((energy - y_pred) ** 2)
ss_tot = np.sum((energy - np.mean(energy)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Create equation and R² text
a, b, c = coeffs
# Format coefficient b with proper sign
b_sign = "+" if b >= 0 else "-"
b_abs = abs(b)
equation_text = f"y = {a:.3f}x² {b_sign} {b_abs:.3f}x + {c:.2f}"
r_squared_text = f"R² = {r_squared:.3f}"
annotation_text = f"{equation_text}\n{r_squared_text}"

# Plot with polynomial regression using formula
plot = (
    ggplot(df, aes(x="temperature", y="energy"))
    + geom_point(size=4, alpha=0.65, color="#306998")
    + geom_smooth(
        method="lm", formula="y ~ I(x) + I(x**2)", se=True, color="#FFD43B", fill="#FFD43B", alpha=0.3, size=2
    )
    + annotate("text", x=38, y=115, label=annotation_text, ha="right", va="top", size=14, color="#333333")
    + labs(
        title="scatter-regression-polynomial · plotnine · pyplots.ai",
        x="Temperature (°C)",
        y="Energy Consumption (kWh)",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major=element_line(color="#cccccc", alpha=0.3),
        panel_grid_minor=element_line(color="#dddddd", alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
