""" pyplots.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
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
    geom_line,
    ggplot,
    labs,
    scale_x_datetime,
    theme,
    theme_minimal,
)
from statsmodels.tsa.seasonal import seasonal_decompose


# Data - Monthly airline passengers with trend and seasonality
np.random.seed(42)
n_months = 144  # 12 years of monthly data

# Create date range
dates = pd.date_range(start="2012-01-01", periods=n_months, freq="MS")

# Generate synthetic airline passenger data with:
# - Upward trend
# - Strong yearly seasonality (peak in summer)
# - Random noise
t = np.arange(n_months)
trend = 200 + t * 2.5  # Growing trend
seasonal = 40 * np.sin(2 * np.pi * t / 12 - np.pi / 2)  # Peak in summer (month 7)
residual = np.random.normal(0, 15, n_months)
value = trend + seasonal + residual

# Create DataFrame
df = pd.DataFrame({"date": dates, "value": value})

# Perform seasonal decomposition using statsmodels
decomposition = seasonal_decompose(df["value"], model="additive", period=12)

# Prepare data for plotnine with all components
df_plot = pd.DataFrame(
    {
        "date": np.tile(dates, 4),
        "value": np.concatenate(
            [df["value"].values, decomposition.trend.values, decomposition.seasonal.values, decomposition.resid.values]
        ),
        "component": np.repeat(["Original", "Trend", "Seasonal", "Residual"], n_months),
    }
)

# Remove NaN values (decomposition creates NaNs at edges)
df_plot = df_plot.dropna()

# Make component a categorical with correct order
df_plot["component"] = pd.Categorical(
    df_plot["component"], categories=["Original", "Trend", "Seasonal", "Residual"], ordered=True
)

# Create faceted plot with four components
plot = (
    ggplot(df_plot, aes(x="date", y="value"))
    + geom_line(color="#306998", size=1.2)
    + facet_wrap("~component", ncol=1, scales="free_y", dir="v")
    + scale_x_datetime(date_labels="%Y", date_breaks="2 years")
    + labs(title="timeseries-decomposition · plotnine · pyplots.ai", x="Date", y="Value")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        axis_title_x=element_text(size=20, margin={"t": 15}),
        axis_title_y=element_text(size=20, margin={"r": 15}),
        axis_text_x=element_text(size=14),
        axis_text_y=element_text(size=12),
        strip_text=element_text(size=16, weight="bold"),
        strip_background=element_rect(fill="#e8e8e8", color=None),
        panel_spacing_y=0.08,
        panel_grid_major=element_line(color="#dddddd", size=0.5, alpha=0.5),
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, width=16, height=9)
