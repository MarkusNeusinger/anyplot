""" pyplots.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_freqpoly, ggplot, labs, scale_color_manual, theme, theme_minimal


# Data - Response times by experimental condition
np.random.seed(42)

# Three experimental conditions with different distributions
control = np.random.normal(loc=450, scale=80, size=200)  # Control group
treatment_a = np.random.normal(loc=380, scale=60, size=200)  # Faster responses
treatment_b = np.random.normal(loc=420, scale=100, size=200)  # More variable

# Combine into DataFrame
df = pd.DataFrame(
    {
        "response_time": np.concatenate([control, treatment_a, treatment_b]),
        "condition": (["Control"] * 200 + ["Treatment A"] * 200 + ["Treatment B"] * 200),
    }
)

# Plot - Frequency polygon comparing distributions
plot = (
    ggplot(df, aes(x="response_time", color="condition"))
    + geom_freqpoly(size=2, bins=25, alpha=0.9)
    + scale_color_manual(values=["#306998", "#FFD43B", "#E74C3C"])
    + labs(
        x="Response Time (ms)",
        y="Frequency",
        title="frequency-polygon-basic · plotnine · pyplots.ai",
        color="Condition",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_position="right",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
