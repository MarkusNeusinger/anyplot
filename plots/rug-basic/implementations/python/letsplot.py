""" pyplots.ai
rug-basic: Basic Rug Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Simulated response times with clusters and gaps (realistic scenario)
np.random.seed(42)
cluster1 = np.random.normal(120, 15, 45)  # Fast responses ~120ms
cluster2 = np.random.normal(250, 30, 35)  # Medium responses ~250ms
cluster3 = np.random.normal(400, 40, 15)  # Slow responses ~400ms
outliers = np.array([550, 620, 700, 780])  # Edge outliers
values = np.concatenate([cluster1, cluster2, cluster3, outliers])

df = pd.DataFrame({"response_time": values})

# Rug data - create short segments at bottom of plot
# Height scaled to be visible but small relative to plot (spec requirement)
rug_y_max = 0.0004  # Small tick height, ~10% of density peak
df_rug = pd.DataFrame(
    {"x": values, "xend": values, "y": np.zeros(len(values)), "yend": np.full(len(values), rug_y_max)}
)

# Plot - Density curve with rug marks along x-axis
plot = (
    ggplot(df, aes(x="response_time"))  # noqa: F405
    + geom_density(fill="#306998", alpha=0.3, size=1.5, color="#306998")  # noqa: F405
    + geom_segment(  # noqa: F405
        aes(x="x", xend="xend", y="y", yend="yend"),  # noqa: F405
        data=df_rug,
        color="#306998",
        alpha=0.8,
        size=1.2,
    )
    + labs(x="Response Time (ms)", y="Density", title="rug-basic · letsplot · pyplots.ai")  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        panel_grid=element_line(color="#cccccc", size=0.5),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG (scale 3x to get 4800 x 2700 px)
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, filename="plot.html", path=".")
