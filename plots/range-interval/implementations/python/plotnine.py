""" pyplots.ai
range-interval: Range Interval Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import pandas as pd
from plotnine import aes, element_blank, element_text, geom_linerange, geom_point, ggplot, labs, theme, theme_minimal


# Data - Monthly temperature ranges (high/low) for a weather station
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
min_temps = [2, 3, 7, 11, 15, 19, 22, 21, 17, 12, 7, 3]
max_temps = [8, 10, 14, 18, 23, 27, 30, 29, 25, 19, 12, 9]

df = pd.DataFrame({"month": months, "min_temp": min_temps, "max_temp": max_temps})
df["month"] = pd.Categorical(df["month"], categories=months, ordered=True)

# Plot - Range interval chart showing temperature ranges
plot = (
    ggplot(df, aes(x="month", ymin="min_temp", ymax="max_temp"))
    + geom_linerange(size=8, color="#306998", alpha=0.8)
    + geom_point(aes(y="max_temp"), size=4, color="#FFD43B", stroke=0.5)
    + geom_point(aes(y="min_temp"), size=4, color="#FFD43B", stroke=0.5)
    + labs(x="Month", y="Temperature (°C)", title="range-interval · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300)
