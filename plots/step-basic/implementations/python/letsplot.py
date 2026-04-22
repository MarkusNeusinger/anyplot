""" pyplots.ai
step-basic: Basic Step Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Monthly cumulative sales figures (in thousands)
np.random.seed(42)
months = np.arange(1, 13)
# Monthly sales that accumulate over the year
monthly_sales = np.array([45, 52, 48, 61, 55, 72, 68, 75, 82, 78, 91, 95])
cumulative_sales = np.cumsum(monthly_sales)

df = pd.DataFrame({"month": months, "cumulative_sales": cumulative_sales})

# Plot - Step plot showing cumulative values that remain constant between changes
plot = (
    ggplot(df, aes(x="month", y="cumulative_sales"))  # noqa: F405
    + geom_step(color="#306998", size=2, direction="hv")  # noqa: F405
    + geom_point(color="#FFD43B", size=5, stroke=1)  # noqa: F405
    + labs(  # noqa: F405
        x="Month", y="Cumulative Sales ($K)", title="step-basic · letsplot · pyplots.ai"
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
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, filename="plot.html", path=".")
