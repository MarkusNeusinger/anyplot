""" pyplots.ai
band-basic: Basic Band Plot
Library: plotnine 0.15.3 | Python 3.14
Quality: 88/100 | Updated: 2026-02-23
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_ribbon,
    ggplot,
    labs,
    theme,
    theme_minimal,
)


# Data - sensor readings with 95% confidence interval
np.random.seed(42)
n_points = 60
days = np.linspace(0, 30, n_points)

# Central trend: temperature rising then stabilizing (realistic sensor pattern)
temperature = 18 + 4 * (1 - np.exp(-0.15 * days)) + 1.5 * np.sin(0.4 * days)
noise = np.random.normal(0, 0.3, n_points)
temperature = temperature + noise

# Uncertainty narrows as model calibrates, then widens for extrapolation
uncertainty = 1.8 * np.exp(-0.08 * days) + 0.3 + 0.04 * np.maximum(days - 20, 0)

# Confidence band boundaries (95% CI)
temp_lower = temperature - 1.96 * uncertainty
temp_upper = temperature + 1.96 * uncertainty

df = pd.DataFrame({"days": days, "temperature": temperature, "temp_lower": temp_lower, "temp_upper": temp_upper})

# Plot
plot = (
    ggplot(df, aes(x="days"))
    + geom_ribbon(aes(ymin="temp_lower", ymax="temp_upper"), fill="#306998", alpha=0.25)
    + geom_line(aes(y="temperature"), color="#306998", size=2.5)
    + labs(
        x="Time (days)",
        y="Temperature (\u00b0C)",
        title="Sensor Calibration Forecast \u00b7 band-basic \u00b7 plotnine \u00b7 pyplots.ai",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major_y=element_line(color="#cccccc", size=0.5, alpha=0.2),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_line_x=element_line(color="#333333", size=0.5),
        axis_line_y=element_line(color="#333333", size=0.5),
        plot_background=element_rect(fill="white", color="none"),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
