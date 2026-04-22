""" pyplots.ai
scatter-categorical: Categorical Scatter Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_point, ggplot, labs, scale_color_manual, theme, theme_minimal


# Data
np.random.seed(42)

# Create sample data with 3 categories showing different patterns
n_per_group = 40

# Group A: positive correlation
x_a = np.random.normal(25, 8, n_per_group)
y_a = x_a * 0.8 + np.random.normal(10, 4, n_per_group)

# Group B: higher values, positive correlation
x_b = np.random.normal(45, 10, n_per_group)
y_b = x_b * 0.6 + np.random.normal(15, 5, n_per_group)

# Group C: lower values, weaker correlation
x_c = np.random.normal(35, 12, n_per_group)
y_c = np.random.normal(35, 8, n_per_group)

df = pd.DataFrame(
    {
        "Temperature (°C)": np.concatenate([x_a, x_b, x_c]),
        "Growth Rate (cm/week)": np.concatenate([y_a, y_b, y_c]),
        "Plant Species": (["Species A"] * n_per_group + ["Species B"] * n_per_group + ["Species C"] * n_per_group),
    }
)

# Plot
plot = (
    ggplot(df, aes(x="Temperature (°C)", y="Growth Rate (cm/week)", color="Plant Species"))
    + geom_point(size=4, alpha=0.7)
    + scale_color_manual(values=["#306998", "#FFD43B", "#4ECDC4"])
    + labs(
        x="Temperature (°C)",
        y="Growth Rate (cm/week)",
        title="scatter-categorical · plotnine · pyplots.ai",
        color="Plant Species",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
