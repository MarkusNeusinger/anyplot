# ruff: noqa: F405
"""pyplots.ai
line-styled: Styled Line Plot
Library: lets-plot | Python 3.13
Quality: pending | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Data - Monthly temperature readings from different weather stations
np.random.seed(42)
months = np.arange(1, 13)
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Temperature patterns for different climate zones
base_temp = np.array([2, 4, 8, 12, 17, 21, 24, 23, 19, 13, 7, 3])
coastal = base_temp + np.random.randn(12) * 0.5 + 3
continental = base_temp + np.random.randn(12) * 0.8 - 2
mountain = base_temp + np.random.randn(12) * 0.6 - 8
mediterranean = base_temp + np.random.randn(12) * 0.4 + 5

# Create long-format DataFrame for lets-plot
df = pd.DataFrame(
    {
        "Month": np.tile(months, 4),
        "Month_Name": np.tile(month_names, 4),
        "Temperature": np.concatenate([coastal, continental, mountain, mediterranean]),
        "Station": np.repeat(["Coastal", "Continental", "Mountain", "Mediterranean"], 12),
    }
)

# Create plot with different line styles
plot = (
    ggplot(df, aes(x="Month", y="Temperature", color="Station", linetype="Station"))
    + geom_line(size=2.5)
    + geom_point(size=5, alpha=0.8)
    + scale_color_manual(values=["#306998", "#FFD43B", "#DC2626", "#22C55E"])
    + scale_linetype_manual(values=["solid", "dashed", "dotted", "longdash"])
    + scale_x_continuous(breaks=months.tolist(), labels=month_names)
    + labs(
        x="Month",
        y="Temperature (°C)",
        title="line-styled · letsplot · pyplots.ai",
        color="Climate Zone",
        linetype="Climate Zone",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title=element_text(size=22),
        axis_text=element_text(size=18),
        legend_title=element_text(size=20),
        legend_text=element_text(size=18),
        legend_position="right",
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_line(color="#DDDDDD", size=0.3),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x = 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive viewing
ggsave(plot, "plot.html", path=".")
