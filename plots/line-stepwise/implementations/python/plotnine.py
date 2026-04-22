""" pyplots.ai
line-stepwise: Step Line Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_step, ggplot, labs, theme, theme_minimal


# Data - Server CPU utilization showing discrete state changes
np.random.seed(42)
hours = np.arange(0, 24)
# Simulate CPU utilization that changes in discrete steps
base_utilization = np.array(
    [
        15,
        15,
        12,
        10,
        10,
        20,  # Night/early morning - low usage
        45,
        65,
        75,
        80,
        85,
        80,  # Morning ramp-up - high load
        70,
        75,
        80,
        85,
        90,
        85,  # Afternoon - peak hours
        70,
        55,
        40,
        30,
        25,
        18,  # Evening wind-down
    ]
)

df = pd.DataFrame({"hour": hours, "cpu_utilization": base_utilization})

# Plot
plot = (
    ggplot(df, aes(x="hour", y="cpu_utilization"))
    + geom_step(color="#306998", size=2, direction="hv")
    + labs(x="Hour of Day", y="CPU Utilization (%)", title="line-stepwise · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major=element_text(color="#cccccc"),
        panel_grid_minor=element_text(color="#eeeeee"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
