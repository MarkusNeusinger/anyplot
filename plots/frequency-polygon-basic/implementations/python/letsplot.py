""" pyplots.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_freqpoly,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Response times (ms) across three experimental conditions
np.random.seed(42)

# Control group: normal distribution centered at 350ms
control = np.random.normal(loc=350, scale=60, size=200)

# Treatment A: slightly faster responses, centered at 300ms
treatment_a = np.random.normal(loc=300, scale=50, size=200)

# Treatment B: bimodal - mix of fast and slow responders
treatment_b = np.concatenate(
    [np.random.normal(loc=280, scale=40, size=120), np.random.normal(loc=420, scale=45, size=80)]
)

# Combine into DataFrame
df = pd.DataFrame(
    {
        "response_time": np.concatenate([control, treatment_a, treatment_b]),
        "condition": (["Control"] * 200 + ["Treatment A"] * 200 + ["Treatment B"] * 200),
    }
)

# Create frequency polygon
plot = (
    ggplot(df, aes(x="response_time", color="condition"))
    + geom_freqpoly(bins=25, size=2.5, alpha=0.9)
    + scale_color_manual(values=["#306998", "#FFD43B", "#DC2626"])
    + labs(
        x="Response Time (ms)",
        y="Frequency",
        title="frequency-polygon-basic · letsplot · pyplots.ai",
        color="Condition",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28),
        axis_title=element_text(size=22),
        axis_text=element_text(size=18),
        legend_title=element_text(size=20),
        legend_text=element_text(size=18),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x for 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, "plot.html", path=".")
