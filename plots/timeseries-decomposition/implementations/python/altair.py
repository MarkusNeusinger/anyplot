""" pyplots.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose


# Data - Monthly airline passengers (classic time series example)
np.random.seed(42)
dates = pd.date_range("2018-01-01", periods=96, freq="MS")  # 8 years monthly data
# Create realistic airline passenger data with trend + seasonality
trend = np.linspace(100, 180, 96)  # Increasing trend
seasonal = 30 * np.sin(2 * np.pi * np.arange(96) / 12)  # Annual cycle
noise = np.random.normal(0, 8, 96)
values = trend + seasonal + noise

df = pd.DataFrame({"date": dates, "value": values})

# Decompose the time series
series = pd.Series(values, index=dates)
decomposition = seasonal_decompose(series, model="additive", period=12)

# Create dataframe with all components
df_decomp = pd.DataFrame(
    {
        "date": dates,
        "Original": values,
        "Trend": decomposition.trend,
        "Seasonal": decomposition.seasonal,
        "Residual": decomposition.resid,
    }
)

# Melt for faceted plotting
df_long = df_decomp.melt(id_vars=["date"], var_name="component", value_name="value")

# Define component order
component_order = ["Original", "Trend", "Seasonal", "Residual"]

# Color mapping for each component
color_map = {
    "Original": "#306998",  # Python Blue
    "Trend": "#E63946",  # Red
    "Seasonal": "#2A9D8F",  # Teal
    "Residual": "#9B59B6",  # Purple
}

# Create the chart
chart = (
    alt.Chart(df_long)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X(
            "date:T", title="Date", axis=alt.Axis(labelFontSize=16, titleFontSize=20, labelAngle=-45, tickCount=12)
        ),
        y=alt.Y("value:Q", title="Value", axis=alt.Axis(labelFontSize=16, titleFontSize=20)),
        color=alt.Color(
            "component:N", scale=alt.Scale(domain=component_order, range=list(color_map.values())), legend=None
        ),
    )
    .properties(width=1500, height=180)
    .facet(
        row=alt.Row(
            "component:N",
            sort=component_order,
            title=None,
            header=alt.Header(
                labelFontSize=22, labelFontWeight="bold", labelOrient="left", labelAlign="left", labelPadding=10
            ),
        )
    )
    .properties(title=alt.Title("timeseries-decomposition · altair · pyplots.ai", fontSize=28, anchor="middle", dy=-10))
    .configure_view(strokeWidth=0)
    .configure_facet(spacing=25)
    .resolve_scale(y="independent")
)

# Save as PNG (1600 × 900 base → 4800 × 2700 with scale_factor=3)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save("plot.html")
