"""pyplots.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-14
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_hline,
    geom_point,
    geom_segment,
    ggplot,
    guides,
    labs,
    scale_color_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)
from statsmodels.tsa.stattools import acf, pacf


# Data - Simulated monthly temperature with seasonality and AR(1) component
np.random.seed(42)
n_obs = 240
time = np.arange(n_obs)
seasonal = 12 * np.sin(2 * np.pi * time / 12) + 4 * np.cos(2 * np.pi * time / 6)
ar_component = np.zeros(n_obs)
for t in range(1, n_obs):
    ar_component[t] = 0.4 * ar_component[t - 1] + np.random.normal(0, 2)
temperature = seasonal + ar_component

# Compute ACF and PACF
n_lags = 36
acf_values = acf(temperature, nlags=n_lags, fft=True)
pacf_values = pacf(temperature, nlags=n_lags, method="ywm")
confidence_bound = 1.96 / np.sqrt(n_obs)

# Build long-format DataFrame for faceting
acf_df = pd.DataFrame({"lag": np.arange(len(acf_values)), "correlation": acf_values, "panel": "ACF"})
pacf_df = pd.DataFrame({"lag": np.arange(1, len(pacf_values)), "correlation": pacf_values[1:], "panel": "PACF"})
df = pd.concat([acf_df, pacf_df], ignore_index=True)
df["panel"] = pd.Categorical(df["panel"], categories=["ACF", "PACF"], ordered=True)

# Mark significance: lags outside confidence bounds
df["significant"] = np.where(np.abs(df["correlation"]) > confidence_bound, "Significant", "Non-significant")
# Lag 0 in ACF is always 1.0 by definition - not a meaningful significant lag
df.loc[(df["panel"] == "ACF") & (df["lag"] == 0), "significant"] = "Non-significant"

# Colors
PYTHON_BLUE = "#306998"
MUTED_SILVER = "#B0BEC5"
CONF_RED = "#C0392B"

# Plot with significance coloring for visual storytelling
plot = (
    ggplot(df, aes(x="lag", y="correlation", color="significant"))
    + geom_hline(yintercept=0, color="#9E9E9E", size=0.7)
    + geom_hline(yintercept=confidence_bound, linetype="dashed", color=CONF_RED, size=0.8, alpha=0.5)
    + geom_hline(yintercept=-confidence_bound, linetype="dashed", color=CONF_RED, size=0.8, alpha=0.5)
    + geom_segment(aes(x="lag", xend="lag", y=0, yend="correlation"), size=1.3)
    + geom_point(size=3.2)
    + scale_color_manual(values={"Significant": PYTHON_BLUE, "Non-significant": MUTED_SILVER})
    + guides(color="none")
    + facet_wrap("~panel", ncol=1, scales="free_y")
    + scale_x_continuous(breaks=range(0, n_lags + 1, 6))
    + labs(x="Lag", y="Correlation", title="acf-pacf · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 10),
        text=element_text(size=14, color="#2C3E50"),
        axis_title=element_text(size=20, face="bold"),
        axis_text=element_text(size=16, color="#546E7A"),
        plot_title=element_text(size=24, face="bold", color="#1A237E"),
        strip_text=element_text(size=20, face="bold", color="#263238"),
        strip_background=element_rect(fill="#F5F5F5", color="none"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(color="#ECEFF1", size=0.4),
        panel_grid_minor_y=element_blank(),
        panel_spacing_y=0.15,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
