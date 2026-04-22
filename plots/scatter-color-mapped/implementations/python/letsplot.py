""" pyplots.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Simulating temperature readings across a spatial grid
np.random.seed(42)
n_points = 150

# Create spatial coordinates with some clustering
x = np.concatenate(
    [
        np.random.normal(20, 8, n_points // 3),
        np.random.normal(50, 10, n_points // 3),
        np.random.normal(75, 6, n_points - 2 * (n_points // 3)),
    ]
)
y = np.concatenate(
    [
        np.random.normal(30, 10, n_points // 3),
        np.random.normal(60, 12, n_points // 3),
        np.random.normal(40, 8, n_points - 2 * (n_points // 3)),
    ]
)

# Temperature as third variable - correlated with position
temperature = 15 + 0.2 * x + 0.15 * y + np.random.normal(0, 3, n_points)

df = pd.DataFrame({"x": x, "y": y, "temperature": temperature})

# Create the color-mapped scatter plot
plot = (
    ggplot(df, aes(x="x", y="y", color="temperature"))  # noqa: F405
    + geom_point(  # noqa: F405
        size=5,
        alpha=0.8,
        tooltips=layer_tooltips()  # noqa: F405
        .line("X Coord|@x")
        .line("Y Coord|@y")
        .line("Temperature|@temperature"),
    )
    + scale_color_viridis(name="Temperature (°C)")  # noqa: F405
    + labs(  # noqa: F405
        x="X Coordinate (m)", y="Y Coordinate (m)", title="scatter-color-mapped · lets-plot · pyplots.ai"
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        legend_title=element_text(size=18),  # noqa: F405
        legend_text=element_text(size=14),  # noqa: F405
        panel_grid=element_line(color="#CCCCCC", size=0.5, linetype="dashed"),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG (scale 3x to get 4800 × 2700 px)
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, filename="plot.html", path=".")
