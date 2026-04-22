""" pyplots.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - bivariate data with correlation
np.random.seed(42)
n = 200
x = np.random.randn(n) * 2 + 10
y = x * 0.8 + np.random.randn(n) * 1.5 + 2

df = pd.DataFrame({"x": x, "y": y})

# Calculate axis limits for aligned marginal plots
x_min, x_max = df["x"].min() - 0.5, df["x"].max() + 0.5
y_min, y_max = df["y"].min() - 0.5, df["y"].max() + 0.5

# Main scatter plot with integrated title
main_scatter = (
    ggplot(df, aes(x="x", y="y"))  # noqa: F405
    + geom_point(color="#306998", size=4, alpha=0.65)  # noqa: F405
    + labs(  # noqa: F405
        x="X Value", y="Y Value", title="scatter-marginal · letsplot · pyplots.ai"
    )
    + scale_x_continuous(limits=[x_min, x_max])  # noqa: F405
    + scale_y_continuous(limits=[y_min, y_max])  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
    )
)

# Top marginal histogram with KDE overlay
top_hist = (
    ggplot(df, aes(x="x"))  # noqa: F405
    + geom_histogram(  # noqa: F405
        aes(y="..density.."),  # noqa: F405
        fill="#306998",
        color="white",
        alpha=0.6,
        bins=25,
    )
    + geom_density(color="#DC2626", size=1.5, alpha=0.8)  # noqa: F405
    + scale_x_continuous(limits=[x_min, x_max])  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_blank(),  # noqa: F405
        axis_text_x=element_blank(),  # noqa: F405
        axis_ticks_x=element_blank(),  # noqa: F405
        axis_text_y=element_text(size=16),  # noqa: F405
    )
)

# Right marginal histogram with KDE overlay
right_hist = (
    ggplot(df, aes(x="y"))  # noqa: F405
    + geom_histogram(  # noqa: F405
        aes(y="..density.."),  # noqa: F405
        fill="#306998",
        color="white",
        alpha=0.6,
        bins=25,
    )
    + geom_density(color="#DC2626", size=1.5, alpha=0.8)  # noqa: F405
    + coord_flip()  # noqa: F405
    + scale_x_continuous(limits=[y_min, y_max])  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_blank(),  # noqa: F405
        axis_text_y=element_blank(),  # noqa: F405
        axis_ticks_y=element_blank(),  # noqa: F405
        axis_text_x=element_text(size=16),  # noqa: F405
        plot_margin=[0, 15, 0, 0],  # noqa: F405
    )
)

# Combine using ggbunch
# Regions: (x, y, width, height) - relative coordinates
combined = (
    ggbunch(  # noqa: F405
        [top_hist, main_scatter, right_hist],
        [
            (0, 0.08, 0.76, 0.20),  # Top histogram (below title space)
            (0, 0.28, 0.76, 0.72),  # Main scatter plot (with title at top)
            (0.76, 0.28, 0.24, 0.72),  # Right histogram (wider for tick labels)
        ],
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save as PNG (scale 3x to get 4800 x 2700 px)
export_ggsave(combined, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(combined, filename="plot.html", path=".")
