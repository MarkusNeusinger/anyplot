""" pyplots.ai
stem-basic: Basic Stem Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""
# ruff: noqa: F405

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Data - Discrete signal samples (damped oscillation with noise)
np.random.seed(42)
x = np.arange(0, 30)
y = np.exp(-x / 10) * np.cos(x * 0.8) + np.random.randn(30) * 0.05

# Create DataFrame for lets-plot
df = pd.DataFrame({"x": x, "y": y, "y_base": 0})

# Create stem plot using segments (stems) and points (markers)
plot = (
    ggplot(df)
    + geom_segment(aes(x="x", y="y_base", xend="x", yend="y"), color="#306998", size=1.5, alpha=0.8)
    + geom_point(aes(x="x", y="y"), color="#306998", size=5, fill="#306998", stroke=1.5, shape=21)
    + geom_hline(yintercept=0, color="#333333", size=1.5)
    + labs(x="Sample Index", y="Amplitude", title="stem-basic · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid=element_line(color="#cccccc", size=0.5, linetype="dashed"),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive viewing
ggsave(plot, "plot.html", path=".")
