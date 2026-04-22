""" pyplots.ai
line-confidence: Line Plot with Confidence Interval
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_line,
    geom_ribbon,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data: Simulated monthly sales forecast with 95% confidence interval
np.random.seed(42)
months = np.arange(1, 25)
trend = 50 + 2.5 * months + 5 * np.sin(months * np.pi / 6)  # Trend with seasonality
noise = np.random.randn(24) * 3
y = trend + noise

# Confidence interval widens over time (uncertainty increases for forecasts)
base_ci = 4
ci_growth = 0.3 * months
y_lower = y - (base_ci + ci_growth)
y_upper = y + (base_ci + ci_growth)

df = pd.DataFrame({"Month": months, "Sales": y, "Lower": y_lower, "Upper": y_upper, "series": "Forecast"})

# Plot with legend
plot = (
    ggplot(df, aes(x="Month"))
    + geom_ribbon(aes(ymin="Lower", ymax="Upper", fill="series"), alpha=0.3)
    + geom_line(aes(y="Sales", color="series"), size=1.5)
    + scale_fill_manual(values={"Forecast": "#306998"}, labels={"Forecast": "95% CI"})
    + scale_color_manual(values={"Forecast": "#306998"}, labels={"Forecast": "Forecast"})
    + labs(x="Month", y="Sales (thousands)", title="line-confidence · plotnine · pyplots.ai", fill="", color="")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_blank(),
        legend_position="right",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
