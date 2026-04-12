""" pyplots.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-04-12
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Synthetic AR(1) process with phi=0.85 (strong positive autocorrelation)
np.random.seed(42)
n = 400
lag = 1
phi = 0.85
innovations = np.random.randn(n) * 2.0

temperature = np.zeros(n)
temperature[0] = 20.0
for i in range(1, n):
    temperature[i] = phi * temperature[i - 1] + (1 - phi) * 20.0 + innovations[i]

# Build lag plot data: y(t) vs y(t+lag)
value_t = temperature[:-lag]
value_t_lag = temperature[lag:]
time_index = np.arange(len(value_t))

df = pd.DataFrame({"value_t": value_t, "value_t_lag": value_t_lag, "day": time_index})

# Compute autocorrelation at this lag
r = np.corrcoef(value_t, value_t_lag)[0, 1]

# Reference line data (y = x diagonal)
ref_min = min(value_t.min(), value_t_lag.min()) - 1
ref_max = max(value_t.max(), value_t_lag.max()) + 1
ref_df = pd.DataFrame({"x": [ref_min, ref_max], "y": [ref_min, ref_max]})

# Annotation data
anno_df = pd.DataFrame({"x": [ref_max - 1.5], "y": [ref_min + 1.5], "label": [f"r = {r:.2f}"]})

# Plot
plot = (
    ggplot(df, aes(x="value_t", y="value_t_lag", color="day"))  # noqa: F405
    + geom_line(  # noqa: F405
        aes(x="x", y="y"),  # noqa: F405
        data=ref_df,
        color="#CCCCCC",
        size=1.0,
        linetype="dashed",
        inherit_aes=False,
    )
    + geom_point(  # noqa: F405
        size=4,
        alpha=0.6,
        shape=16,
        tooltips=layer_tooltips()  # noqa: F405
        .line("Day|@day")
        .line("y(t)|@{value_t}{.2f}")
        .line("y(t+1)|@{value_t_lag}{.2f}"),
    )
    + geom_text(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=anno_df,
        size=14,
        color="#444444",
        family="monospace",
        hjust=1.0,
        inherit_aes=False,
    )
    + scale_color_gradient(  # noqa: F405
        low="#306998", high="#E3882D", name="Day"
    )
    + labs(  # noqa: F405
        x="y(t)",
        y=f"y(t + {lag})",
        title="scatter-lag · letsplot · pyplots.ai",
        caption="AR(1) simulated daily temperature · dashed line = y(t+1) = y(t)",
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16, color="#555555"),  # noqa: F405
        axis_title=element_text(size=20, color="#333333"),  # noqa: F405
        plot_title=element_text(size=24, color="#222222", face="bold"),  # noqa: F405
        plot_caption=element_text(size=13, color="#999999", face="italic"),  # noqa: F405
        panel_grid_major=element_line(color="#E8E8E8", size=0.35),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        legend_title=element_text(size=16, color="#444444"),  # noqa: F405
        legend_text=element_text(size=14, color="#555555"),  # noqa: F405
        axis_ticks=element_line(color="#CCCCCC", size=0.3),  # noqa: F405
        plot_margin=[30, 40, 20, 20],
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
