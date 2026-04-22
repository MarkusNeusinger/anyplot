""" pyplots.ai
sparkline-basic: Basic Sparkline
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    theme,
)


# Data - simulated daily sales trend with realistic patterns
np.random.seed(42)
n_points = 50

# Create trend with some seasonality and noise
trend = np.linspace(0, 3, n_points)
seasonal = 2 * np.sin(np.linspace(0, 4 * np.pi, n_points))
noise = np.random.randn(n_points) * 0.8
values = 100 + trend * 10 + seasonal * 5 + noise * 3

df = pd.DataFrame({"x": range(n_points), "y": values})

# Identify min and max points for highlighting
min_idx = df["y"].idxmin()
max_idx = df["y"].idxmax()
first_idx = 0
last_idx = n_points - 1

# Create highlight points dataframe
highlight_df = pd.DataFrame(
    {
        "x": [min_idx, max_idx, first_idx, last_idx],
        "y": [df.loc[min_idx, "y"], df.loc[max_idx, "y"], df.loc[first_idx, "y"], df.loc[last_idx, "y"]],
        "type": ["min", "max", "first", "last"],
    }
)

# Plot - sparkline with minimal chrome, wide aspect ratio
plot = (
    ggplot(df, aes(x="x", y="y"))
    + geom_line(color="#306998", size=2.5)
    + geom_point(data=highlight_df, mapping=aes(x="x", y="y", color="type"), size=7)
    + scale_color_manual(values={"min": "#E74C3C", "max": "#27AE60", "first": "#306998", "last": "#306998"})
    + labs(title="sparkline-basic · plotnine · pyplots.ai")
    + theme(
        figure_size=(16, 4),  # Wide aspect ratio for sparkline (4:1)
        # Remove all axes and chart chrome for minimal sparkline look
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="white"),
        plot_background=element_rect(fill="white"),
        # Title styling
        plot_title=element_text(size=24, ha="center"),
        # Remove legend
        legend_position="none",
    )
)

plot.save("plot.png", dpi=300, verbose=False)
