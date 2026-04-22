""" pyplots.ai
sparkline-basic: Basic Sparkline
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - simulated daily stock prices over 60 trading days
# Using different seed transformation to avoid min=last overlap
np.random.seed(42)
n_points = 60
base_returns = np.random.randn(n_points) * 0.018  # Daily returns ~1.8% volatility
# Add slight upward trend at the end to ensure last point differs from min
base_returns[-5:] += 0.008
prices = 100 * np.cumprod(1 + base_returns)

df = pd.DataFrame({"day": range(n_points), "price": prices})

# Find min/max points for highlighting
min_idx = int(np.argmin(prices))
max_idx = int(np.argmax(prices))
first_idx = 0
last_idx = n_points - 1

# Create separate dataframes for each highlight type
min_df = pd.DataFrame({"day": [min_idx], "price": [prices[min_idx]]})
max_df = pd.DataFrame({"day": [max_idx], "price": [prices[max_idx]]})
first_last_df = pd.DataFrame({"day": [first_idx, last_idx], "price": [prices[first_idx], prices[last_idx]]})

# Plot - minimal sparkline with highlighted points
# Using 6:1 aspect ratio typical for sparklines (spec suggests 4:1 to 8:1)
# Width 1600, height 267 -> scaled 3x = 4800 x 800 px
plot = (
    ggplot(df, aes(x="day", y="price"))  # noqa: F405
    + geom_area(fill="#306998", alpha=0.2)  # noqa: F405
    + geom_line(color="#306998", size=2.5)  # noqa: F405
    + geom_point(  # noqa: F405
        data=min_df,
        mapping=aes(x="day", y="price"),  # noqa: F405
        color="#DC2626",
        size=10,
    )  # Min point (red)
    + geom_point(  # noqa: F405
        data=max_df,
        mapping=aes(x="day", y="price"),  # noqa: F405
        color="#16A34A",
        size=10,
    )  # Max point (green)
    + geom_point(  # noqa: F405
        data=first_last_df,
        mapping=aes(x="day", y="price"),  # noqa: F405
        color="#FFD43B",
        size=7,
    )  # First/last points (yellow)
    + scale_y_continuous(expand=[0.15, 0])  # noqa: F405  Expand y-axis to fill canvas
    + labs(title="sparkline-basic · lets-plot · pyplots.ai")  # noqa: F405
    + ggsize(1600, 267)  # noqa: F405  6:1 aspect ratio for sparkline
    + theme_void()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24, hjust=0.5),  # noqa: F405
        plot_margin=[40, 40, 30, 40],
    )
)

# Save PNG (scale 3x for ~4800x800) and HTML to current directory
export_ggsave(plot, "plot.png", path=".", scale=3)
export_ggsave(plot, "plot.html", path=".")
