""" pyplots.ai
line-basic: Basic Line Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_line, element_text, geom_line, geom_point, ggplot, labs, theme, theme_minimal


# Data - Monthly average temperature readings for a typical year
np.random.seed(42)
months = np.arange(1, 13)
base_temp = np.array([5, 7, 11, 15, 19, 23, 26, 25, 21, 15, 10, 6])
temperature = base_temp + np.random.randn(12) * 1.5

df = pd.DataFrame({"Month": months, "Temperature": temperature})

# Plot
plot = (
    ggplot(df, aes(x="Month", y="Temperature"))
    + geom_line(size=2.5, color="#306998")
    + geom_point(size=6, color="#306998")
    + labs(x="Month", y="Temperature (°C)", title="line-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#eeeeee", size=0.3, alpha=0.2),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
