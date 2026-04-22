""" pyplots.ai
rose-basic: Basic Rose Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_polar,
    element_blank,
    element_text,
    geom_bar,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Monthly rainfall (mm) showing seasonal patterns
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
rainfall = [78, 65, 82, 95, 120, 145, 168, 155, 130, 105, 85, 70]

df = pd.DataFrame({"month": months, "rainfall": rainfall})
# Maintain natural month ordering
df["month"] = pd.Categorical(df["month"], categories=months, ordered=True)

# Colors - gradient from Python Blue to Python Yellow based on value
colors = [
    "#306998",
    "#3A7199",
    "#44799A",
    "#4E819B",
    "#588A9C",
    "#72A39D",
    "#8CBA8E",
    "#A6D17F",
    "#C0E870",
    "#D4E85C",
    "#E8E848",
    "#FFD43B",
]

# Plot - Rose chart using polar coordinates
plot = (
    ggplot(df, aes(x="month", y="rainfall", fill="month"))
    + geom_bar(stat="identity", width=0.9, alpha=0.85)
    + coord_polar()
    + scale_fill_manual(values=colors)
    + labs(title="Monthly Rainfall Distribution · rose-basic · letsplot · pyplots.ai", x="", y="Rainfall (mm)")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title_y=element_text(size=18),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=14),
        legend_position="none",
        panel_grid_major_x=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
