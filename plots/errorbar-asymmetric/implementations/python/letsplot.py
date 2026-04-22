""" pyplots.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""
# ruff: noqa: F405

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Data - Quarterly sales performance with asymmetric confidence intervals
np.random.seed(42)
quarters = ["Q1", "Q2", "Q3", "Q4"]
sales = [85, 92, 78, 105]  # Sales in thousands
# Asymmetric errors: different upside/downside uncertainty
error_lower = [8, 5, 12, 7]  # Lower error (downside risk)
error_upper = [15, 18, 6, 22]  # Upper error (upside potential)

df = pd.DataFrame(
    {
        "quarter": quarters,
        "sales": sales,
        "ymin": [s - el for s, el in zip(sales, error_lower, strict=True)],
        "ymax": [s + eu for s, eu in zip(sales, error_upper, strict=True)],
    }
)

# Plot
plot = (
    ggplot(df, aes(x="quarter", y="sales"))
    + geom_point(size=6, color="#306998", alpha=0.9)
    + geom_errorbar(aes(ymin="ymin", ymax="ymax"), width=0.3, size=1.5, color="#306998")
    + labs(
        x="Quarter",
        y="Sales (thousands USD)",
        title="errorbar-asymmetric · letsplot · pyplots.ai",
        caption="Error bars represent 10th-90th percentile forecast range",
    )
    + scale_y_continuous(limits=[50, 140])
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_caption=element_text(size=14),
        panel_grid_major=element_line(color="#cccccc", size=0.3),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", scale=3, path=".")

# Save HTML for interactive version
ggsave(plot, "plot.html", path=".")
