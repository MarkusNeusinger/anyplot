""" pyplots.ai
band-basic: Basic Band Plot
Library: letsplot 4.8.2 | Python 3.14
Quality: 82/100 | Updated: 2026-02-23
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_text,
    geom_line,
    geom_ribbon,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - sensor temperature readings with 95% confidence interval
np.random.seed(42)
time_seconds = np.linspace(0, 10, 100)
temp_mean = 2 * np.sin(time_seconds) + 0.5 * time_seconds  # Central trend
uncertainty = 0.3 + 0.15 * time_seconds  # Growing uncertainty over time
temp_lower = temp_mean - 1.96 * uncertainty  # 95% CI lower bound
temp_upper = temp_mean + 1.96 * uncertainty  # 95% CI upper bound

df = pd.DataFrame({"time": time_seconds, "mean": temp_mean, "lower": temp_lower, "upper": temp_upper})

# Plot
plot = (
    ggplot(df, aes(x="time"))
    + geom_ribbon(
        aes(ymin="lower", ymax="upper"),
        fill="#306998",
        alpha=0.25,
        tooltips=layer_tooltips()
        .format("lower", "{.2f}")
        .format("upper", "{.2f}")
        .line("95% CI")
        .line("Upper|@upper")
        .line("Lower|@lower"),
    )
    + geom_line(
        aes(y="mean"),
        color="#306998",
        size=1.5,
        tooltips=layer_tooltips()
        .format("mean", "{.2f}")
        .format("time", "{.1f}")
        .line("Time|@time s")
        .line("Mean|@mean"),
    )
    + labs(x="Time (s)", y="Value (units)", title="band-basic \u00b7 letsplot \u00b7 pyplots.ai")
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major=element_line(size=0.3, color="#E0E0E0"),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
plot.to_html("plot.html")
