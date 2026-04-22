""" pyplots.ai
errorbar-basic: Basic Error Bar Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_errorbar,
    geom_point,
    ggplot,
    ggsave,
    ggsize,
    labs,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - experimental measurements with uncertainty
data = pd.DataFrame(
    {
        "experiment": ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D"],
        "mean_value": [45.2, 52.8, 61.3, 48.7, 55.1],
        "error": [4.5, 6.2, 5.8, 3.9, 7.1],
    }
)

# Calculate error bar positions
data["ymin"] = data["mean_value"] - data["error"]
data["ymax"] = data["mean_value"] + data["error"]

# Plot
plot = (
    ggplot(data, aes(x="experiment", y="mean_value"))
    + geom_errorbar(aes(ymin="ymin", ymax="ymax"), width=0.3, size=1.5, color="#306998")
    + geom_point(size=6, color="#306998")
    + labs(x="Experimental Group", y="Measured Value", title="errorbar-basic · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(axis_title=element_text(size=20), axis_text=element_text(size=16), plot_title=element_text(size=24))
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 x 2700 px)
ggsave(plot, "plot.png", scale=3, path=".")

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
