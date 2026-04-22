""" pyplots.ai
ecdf-basic: Basic ECDF Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 96/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Response times (ms) from a web service
np.random.seed(42)
response_times = np.concatenate(
    [
        np.random.exponential(scale=50, size=150),  # Fast responses
        np.random.normal(loc=200, scale=30, size=50),  # Slower responses
    ]
)

# Sort data and calculate ECDF values
sorted_values = np.sort(response_times)
ecdf_values = np.arange(1, len(sorted_values) + 1) / len(sorted_values)

df = pd.DataFrame({"response_time": sorted_values, "ecdf": ecdf_values})

# Plot - ECDF as step function
plot = (
    ggplot(df, aes(x="response_time", y="ecdf"))  # noqa: F405
    + geom_step(color="#306998", size=2)  # noqa: F405
    + labs(  # noqa: F405
        x="Response Time (ms)", y="Cumulative Proportion", title="ecdf-basic · letsplot · pyplots.ai"
    )
    + scale_y_continuous(limits=[0, 1], breaks=[0, 0.25, 0.5, 0.75, 1.0])  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        panel_grid_major=element_line(color="#CCCCCC", size=0.5, linetype="dashed"),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
    )
)

# Save PNG (scale 3x to get 4800 x 2700 px)
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, filename="plot.html", path=".")
