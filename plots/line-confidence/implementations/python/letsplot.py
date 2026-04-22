""" pyplots.ai
line-confidence: Line Plot with Confidence Interval
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Monthly sales forecast with 95% confidence interval
np.random.seed(42)
months = np.arange(1, 25)
trend = 50 + months * 2.5 + np.sin(months * np.pi / 6) * 10
noise = np.random.normal(0, 3, len(months))
y = trend + noise

# Calculate confidence interval (simulating forecast uncertainty that grows over time)
std_error = 3 + months * 0.3
y_lower = y - 1.96 * std_error
y_upper = y + 1.96 * std_error

df = pd.DataFrame({"Month": months, "Sales": y, "Lower": y_lower, "Upper": y_upper})

# Create plot
plot = (
    ggplot(df)
    + geom_ribbon(aes(x="Month", ymin="Lower", ymax="Upper"), fill="#306998", alpha=0.3)
    + geom_line(aes(x="Month", y="Sales"), color="#306998", size=2)
    + geom_point(aes(x="Month", y="Sales"), color="#FFD43B", size=4, stroke=1.5)
    + labs(x="Month", y="Sales (thousands)", title="line-confidence · letsplot · pyplots.ai")
    + scale_x_continuous(breaks=list(range(0, 25, 3)))
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_text=element_text(size=16),
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x to get 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive viewing
ggsave(plot, "plot.html", path=".")
