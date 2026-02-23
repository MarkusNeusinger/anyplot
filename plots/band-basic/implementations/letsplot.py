""" pyplots.ai
band-basic: Basic Band Plot
Library: letsplot 4.8.2 | Python 3.14
Quality: 91/100 | Updated: 2026-02-23
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    arrow,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_line,
    geom_ribbon,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_x_continuous,
    scale_y_continuous,
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

# Annotation with arrow connector pointing to the widening band region
annot_df = pd.DataFrame({"x": [7.0], "y": [9.2], "label": ["Growing uncertainty"]})
target_idx = np.argmin(np.abs(time_seconds - 9.5))
arrow_df = pd.DataFrame({"x": [8.7], "y": [9.0], "xend": [9.5], "yend": [temp_upper[target_idx] + 0.15]})

# Plot
plot = (
    ggplot(df, aes(x="time"))
    # Baseline reference at 0°C
    + geom_hline(yintercept=0, color="#BBBBBB", size=0.7, linetype="dashed", tooltips="none")
    + geom_ribbon(
        aes(ymin="lower", ymax="upper"),
        fill="#306998",
        size=0,
        alpha=0.2,
        tooltips=layer_tooltips()
        .format("lower", "{.2f}")
        .format("upper", "{.2f}")
        .line("95% CI")
        .line("Upper|@upper")
        .line("Lower|@lower"),
    )
    + geom_line(
        aes(y="mean"),
        color="#C75B2E",
        size=2.0,
        tooltips=layer_tooltips()
        .format("mean", "{.2f}")
        .format("time", "{.1f}")
        .line("Time|@time s")
        .line("Mean|@mean"),
    )
    # Arrow connector from annotation to widening band
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=arrow_df,
        color="#555555",
        size=0.7,
        arrow=arrow(length=8, type="open"),
        tooltips="none",
    )
    + geom_text(aes(x="x", y="y", label="label"), data=annot_df, size=12, color="#444444")
    + labs(x="Time (s)", y="Temperature (\u00b0C)", title="band-basic \u00b7 letsplot \u00b7 pyplots.ai")
    + scale_x_continuous(limits=[-0.3, 10.8])
    + scale_y_continuous(limits=[-2.2, 9.5], expand=[0, 0.02])
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20, color="#333333"),
        axis_text=element_text(size=16, color="#555555"),
        plot_title=element_text(size=24, color="#222222"),
        panel_grid_major=element_line(size=0.3, color="#E8E8E8"),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(color="white", fill="white", size=0),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
plot.to_html("plot.html")
