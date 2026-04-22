""" pyplots.ai
ridgeline-basic: Basic Ridgeline Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_ribbon,
    ggplot,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy import stats


# Data - Monthly temperature distributions
np.random.seed(42)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Temperature parameters for each month (mean, std)
temp_params = {
    "Jan": (2, 4),
    "Feb": (4, 4),
    "Mar": (8, 5),
    "Apr": (13, 4),
    "May": (18, 4),
    "Jun": (22, 3),
    "Jul": (25, 3),
    "Aug": (24, 3),
    "Sep": (20, 4),
    "Oct": (14, 4),
    "Nov": (8, 4),
    "Dec": (4, 4),
}

# Generate data points for KDE
data = []
for month in months:
    mean, std = temp_params[month]
    values = np.random.normal(mean, std, 200)
    for v in values:
        data.append({"month": month, "temp": v})

df = pd.DataFrame(data)

# Compute density curves for ridgeline effect
x_range = np.linspace(-10, 40, 300)
ridge_scale = 2.5  # Height scale for ridges

density_data = []
for i, month in enumerate(months):
    month_data = df[df["month"] == month]["temp"]
    kde = stats.gaussian_kde(month_data)
    density = kde(x_range)
    # Scale density for visibility
    density_scaled = density / density.max() * ridge_scale

    for x, d in zip(x_range, density_scaled, strict=True):
        density_data.append(
            {
                "x": x,
                "ymin": i,  # Baseline for each ridge
                "ymax": i + d,  # Top of the density curve
                "group": month,
            }
        )

ridge_df = pd.DataFrame(density_data)
ridge_df["group"] = pd.Categorical(ridge_df["group"], categories=months, ordered=True)

# Color palette - cool to warm gradient for seasons
colors = [
    "#306998",  # Jan - Python Blue (winter)
    "#3B7CA8",  # Feb
    "#5899B8",  # Mar (spring transition)
    "#75B5C0",  # Apr
    "#95CEC0",  # May
    "#B5D4A0",  # Jun (summer transition)
    "#D4C878",  # Jul
    "#FFD43B",  # Aug - Python Yellow (summer peak)
    "#E8B94C",  # Sep (fall transition)
    "#C99C5D",  # Oct
    "#8C7F8C",  # Nov
    "#4B6B98",  # Dec (winter)
]

# Plot using geom_ribbon to create ridges
plot = (
    ggplot(ridge_df, aes(x="x", ymin="ymin", ymax="ymax", fill="group", group="group"))
    + geom_ribbon(alpha=0.85, color="#333333", size=0.5)
    + scale_fill_manual(values=colors)
    + scale_y_continuous(breaks=list(range(12)), labels=months, limits=(-0.5, 14))
    + labs(x="Temperature (°C)", y="Month", title="ridgeline-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major_y=element_line(alpha=0),
        panel_grid_minor=element_line(alpha=0),
        panel_grid_major_x=element_line(color="#cccccc", alpha=0.3),
        legend_position="none",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
