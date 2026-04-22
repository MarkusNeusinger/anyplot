""" pyplots.ai
band-basic: Basic Band Plot
Library: plotnine 0.15.3 | Python 3.14
Quality: 94/100 | Updated: 2026-02-23
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_ribbon,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
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
    + geom_line(aes(y="temperature"), color="#1a3a5c", size=2.5)
    + annotate(
        "text", x=7, y=temp_lower.min() - 0.8, label="Calibration Phase", size=12, color="#555555", fontstyle="italic"
    )
    + annotate(
        "text", x=25, y=temp_lower.min() - 0.8, label="Extrapolation", size=12, color="#555555", fontstyle="italic"
    )
    + annotate(
        "segment",
        x=15,
        xend=15,
        y=temp_lower.min() - 1.6,
        yend=temp_upper.max() + 0.5,
        color="#999999",
        size=0.5,
        linetype="dashed",
    )
    + labs(
        x="Time (days)",
        y="Temperature (\u00b0C)",
        title="Sensor Calibration Forecast \u00b7 band-basic \u00b7 plotnine \u00b7 pyplots.ai",
        subtitle="Shaded region shows 95% confidence interval \u2014 narrowing during calibration, widening for extrapolation",
    )
    + scale_x_continuous(breaks=range(0, 31, 5))
    + scale_y_continuous(labels=lambda lst: [f"{v:.0f}\u00b0C" for v in lst])
    + coord_cartesian(expand=True)
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        plot_subtitle=element_text(size=16, color="#555555"),
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
