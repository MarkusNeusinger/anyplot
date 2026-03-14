"""pyplots.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-14
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave
from statsmodels.tsa.stattools import acf, pacf


LetsPlot.setup_html()  # noqa: F405

# Data - Simulate monthly airline-style passenger data with trend and seasonality
np.random.seed(42)
n = 200
time = np.arange(n)
trend = 0.05 * time
seasonal = 10 * np.sin(2 * np.pi * time / 12)
noise = np.random.normal(0, 2, n)
passengers = 100 + trend + seasonal + noise

# Compute ACF and PACF
n_lags = 36
acf_values = acf(passengers, nlags=n_lags)
pacf_values = pacf(passengers, nlags=n_lags)

# 95% confidence interval
ci_bound = 1.96 / np.sqrt(n)

# Prepare ACF data (include lag 0)
acf_lags = list(range(0, n_lags + 1))
acf_df = pd.DataFrame(
    {
        "lag": acf_lags,
        "value": acf_values.tolist(),
        "zero": 0.0,
        "significant": [abs(v) > ci_bound and i > 0 for i, v in enumerate(acf_values)],
    }
)
acf_df["color"] = acf_df["significant"].map({True: "Significant", False: "Non-significant"})

# Prepare PACF data (start from lag 1)
pacf_vals = pacf_values[1:].tolist()
pacf_lags = list(range(1, n_lags + 1))
pacf_df = pd.DataFrame(
    {"lag": pacf_lags, "value": pacf_vals, "zero": 0.0, "significant": [abs(v) > ci_bound for v in pacf_vals]}
)
pacf_df["color"] = pacf_df["significant"].map({True: "Significant", False: "Non-significant"})

# Color palette
sig_colors = ["#306998", "#C0392B"]  # Non-significant (blue), Significant (red)
sig_labels = ["Non-significant", "Significant"]

# Common theme
x_breaks = list(range(0, n_lags + 1, 6))
common_theme = (
    flavor_high_contrast_light()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.4),  # noqa: F405
        legend_text=element_text(size=16),  # noqa: F405
        legend_title=element_blank(),  # noqa: F405
        legend_position=[0.85, 0.85],  # noqa: F405
        legend_background=element_rect(fill="white", color="#CCCCCC", size=0.5),  # noqa: F405
    )
)

# ACF plot
acf_plot = (
    ggplot(acf_df, aes(x="lag", y="value", color="color"))  # noqa: F405
    + geom_segment(  # noqa: F405
        aes(x="lag", y="zero", xend="lag", yend="value", color="color"),  # noqa: F405
        size=2.5,
    )
    + geom_point(aes(x="lag", y="value", color="color"), size=4.5)  # noqa: F405
    + geom_hline(yintercept=0, color="#333333", size=0.5)  # noqa: F405
    + geom_hline(yintercept=ci_bound, color="#999999", size=0.7, linetype="dashed")  # noqa: F405
    + geom_hline(yintercept=-ci_bound, color="#999999", size=0.7, linetype="dashed")  # noqa: F405
    + scale_color_manual(values=sig_colors, limits=sig_labels)  # noqa: F405
    + scale_x_continuous(breaks=x_breaks)  # noqa: F405
    + labs(x="", y="ACF", title="acf-pacf · letsplot · pyplots.ai")  # noqa: F405
    + theme(plot_title=element_text(size=24, hjust=0.5, face="bold"))  # noqa: F405
    + common_theme
    + ggsize(1600, 500)  # noqa: F405
)

# PACF plot (no legend - shared with ACF)
pacf_plot = (
    ggplot(pacf_df, aes(x="lag", y="value", color="color"))  # noqa: F405
    + geom_segment(  # noqa: F405
        aes(x="lag", y="zero", xend="lag", yend="value", color="color"),  # noqa: F405
        size=2.5,
    )
    + geom_point(aes(x="lag", y="value", color="color"), size=4.5)  # noqa: F405
    + geom_hline(yintercept=0, color="#333333", size=0.5)  # noqa: F405
    + geom_hline(yintercept=ci_bound, color="#999999", size=0.7, linetype="dashed")  # noqa: F405
    + geom_hline(yintercept=-ci_bound, color="#999999", size=0.7, linetype="dashed")  # noqa: F405
    + scale_color_manual(values=sig_colors, limits=sig_labels)  # noqa: F405
    + scale_x_continuous(breaks=x_breaks)  # noqa: F405
    + labs(x="Lag", y="PACF")  # noqa: F405
    + common_theme
    + theme(legend_position="none")  # noqa: F405
    + ggsize(1600, 470)  # noqa: F405
)

# Combine vertically
combined = ggbunch(  # noqa: F405
    plots=[acf_plot, pacf_plot], regions=[(0, 0, 1, 0.54, 0, 0), (0, 0.48, 1, 0.54, 0, 0)]
)

# Save
export_ggsave(combined, filename="plot.png", path=".", scale=3)
export_ggsave(combined, filename="plot.html", path=".")
