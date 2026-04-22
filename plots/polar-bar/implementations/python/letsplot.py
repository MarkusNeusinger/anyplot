""" pyplots.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_polar,
    element_line,
    element_text,
    geom_bar,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Wind direction frequency data (8 compass directions)
np.random.seed(42)
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Generate realistic wind frequency data
frequencies = np.array([15, 8, 12, 5, 10, 18, 22, 14])

# Create DataFrame - direction as categorical factor
df = pd.DataFrame(
    {"direction": pd.Categorical(directions, categories=directions, ordered=True), "frequency": frequencies}
)

# Create polar bar chart (wind rose)
# Use coord_polar to wrap bars in a circle
plot = (
    ggplot(df, aes(x="direction", y="frequency", fill="direction"))
    + geom_bar(stat="identity", color="white", size=0.8, alpha=0.85, width=0.95)
    + coord_polar(start=-np.pi / 8)  # Rotate so N is at top
    + scale_fill_manual(values=["#306998", "#4A90C2", "#FFD43B", "#F5A623", "#7B68EE", "#9B59B6", "#2ECC71", "#27AE60"])
    + scale_y_continuous(limits=[0, None], expand=[0, 0.5])
    + labs(title="polar-bar · letsplot · pyplots.ai", x="", y="Frequency (%)")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title_y=element_text(size=18),
        axis_text=element_text(size=14),
        legend_position="none",  # Hide legend (labels shown around chart)
        panel_grid_major=element_line(color="#CCCCCC", size=0.3),
    )
    + ggsize(1200, 1200)  # Square for polar chart
)

# Save as PNG (scale 3x for high resolution: 3600x3600 for square polar)
ggsave(plot, "plot.png", scale=3, path=".")

# Save interactive HTML
ggsave(plot, "plot.html", path=".")
