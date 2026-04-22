""" pyplots.ai
line-basic: Basic Line Plot
Library: letsplot 4.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Monthly temperature readings over a year
np.random.seed(42)
months = np.arange(1, 13)
# Simulate temperature pattern: warmer in summer, cooler in winter
base_temp = 15 + 12 * np.sin((months - 4) * np.pi / 6)
temperature = base_temp + np.random.randn(12) * 1.5

df = pd.DataFrame({"month": months, "temperature": temperature})

# Plot
plot = (
    ggplot(df, aes(x="month", y="temperature"))  # noqa: F405
    + geom_line(color="#306998", size=2)  # noqa: F405
    + geom_point(color="#306998", size=5, alpha=0.8)  # noqa: F405
    + labs(  # noqa: F405
        x="Month", y="Temperature (°C)", title="line-basic · letsplot · pyplots.ai"
    )
    + scale_x_continuous(breaks=list(range(1, 13)))  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        panel_grid=element_line(color="#CCCCCC", size=0.5, linetype="dashed"),  # noqa: F405
    )
)

# Save PNG (scale 3x to get 4800 x 2700 px)
export_ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, "plot.html", path=".")
