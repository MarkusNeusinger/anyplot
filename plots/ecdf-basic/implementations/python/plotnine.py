""" anyplot.ai
ecdf-basic: Basic ECDF Plot
Library: plotnine 0.15.3 | Python 3.14.4
Quality: 74/100 | Updated: 2026-04-24
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_line, element_text, geom_step, ggplot, labs, scale_y_continuous, theme, theme_minimal


# Data
np.random.seed(42)
values = np.random.randn(200) * 15 + 50  # Normal distribution centered at 50

# Compute ECDF
sorted_values = np.sort(values)
ecdf_y = np.arange(1, len(sorted_values) + 1) / len(sorted_values)

df = pd.DataFrame({"values": sorted_values, "ecdf": ecdf_y})

# Plot
plot = (
    ggplot(df, aes(x="values", y="ecdf"))
    + geom_step(color="#306998", size=1.5)
    + labs(x="Values", y="Cumulative Proportion", title="ecdf-basic · plotnine · pyplots.ai")
    + scale_y_continuous(limits=(0, 1), breaks=np.arange(0, 1.1, 0.1))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major=element_line(color="#cccccc", alpha=0.3),
    )
)

plot.save("plot.png", dpi=300)
