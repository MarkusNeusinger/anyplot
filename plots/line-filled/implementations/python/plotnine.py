""" pyplots.ai
line-filled: Filled Line Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_line, element_text, geom_area, geom_line, ggplot, labs, theme, theme_minimal


# Data - Monthly website traffic over a year
np.random.seed(42)
months = np.arange(1, 13)
base_traffic = 50000 + np.cumsum(np.random.randn(12) * 5000)
seasonal = 10000 * np.sin(np.pi * months / 6)
visitors = base_traffic + seasonal + np.random.randn(12) * 3000
visitors = np.maximum(visitors, 20000)

df = pd.DataFrame({"Month": months, "Visitors": visitors})

# Plot
plot = (
    ggplot(df, aes(x="Month", y="Visitors"))
    + geom_area(fill="#306998", alpha=0.4)
    + geom_line(color="#306998", size=2)
    + labs(x="Month", y="Website Visitors", title="line-filled · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(alpha=0),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
