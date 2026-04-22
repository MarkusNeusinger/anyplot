""" pyplots.ai
range-interval: Range Interval Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-09
"""

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data: Monthly temperature ranges (°C) for a weather station
data = {
    "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "min_temp": [-2, 0, 4, 8, 13, 17, 19, 18, 14, 9, 4, 0],
    "max_temp": [6, 8, 12, 17, 22, 26, 29, 28, 24, 18, 11, 7],
}

df = pd.DataFrame(data)

# Calculate midpoint for reference markers
df["mid_temp"] = (df["min_temp"] + df["max_temp"]) / 2

# Preserve month order
df["month"] = pd.Categorical(df["month"], categories=data["month"], ordered=True)

# Create range interval chart using geom_segment with endpoints
plot = (
    ggplot(df)
    # Range bars as vertical segments
    + geom_segment(aes(x="month", xend="month", y="min_temp", yend="max_temp"), size=8, color="#306998", alpha=0.8)
    # Min endpoint markers
    + geom_point(aes(x="month", y="min_temp"), size=5, color="#306998", shape=21, fill="white", stroke=2)
    # Max endpoint markers
    + geom_point(aes(x="month", y="max_temp"), size=5, color="#306998", shape=21, fill="#FFD43B", stroke=2)
    # Midpoint markers for context
    + geom_point(aes(x="month", y="mid_temp"), size=3, color="#DC2626", shape=16)
    # Labels and title
    + labs(x="Month", y="Temperature (°C)", title="range-interval · letsplot · pyplots.ai")
    # Theme for large canvas
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#DDDDDD", size=0.5),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", scale=3, path=".")

# Save as HTML for interactive viewing
ggsave(plot, "plot.html", path=".")
