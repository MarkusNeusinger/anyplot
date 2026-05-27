""" anyplot.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-14
"""

import os
import sys


# Fix sys.path to avoid circular import: remove current dir and script location
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir and os.path.abspath(p) != os.getcwd()]
sys.path.insert(0, "/usr/lib/python3.13")
sys.path.insert(0, "/usr/local/lib/python3.13/dist-packages")

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from statsmodels.tsa.seasonal import seasonal_decompose  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (component colors)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Monthly airline passengers
np.random.seed(42)
dates = pd.date_range("2018-01-01", periods=96, freq="MS")
trend = np.linspace(100, 180, 96)
seasonal = 30 * np.sin(2 * np.pi * np.arange(96) / 12)
noise = np.random.normal(0, 8, 96)
values = trend + seasonal + noise

# Decompose time series
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

# Component order
component_order = ["Original", "Trend", "Seasonal", "Residual"]

# Color mapping using Okabe-Ito palette
color_map = {component: IMPRINT[i] for i, component in enumerate(component_order)}

# Base chart with encoding
base_chart = (
    alt.Chart(df_long)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X(
            "date:T", title="Date", axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=-45, tickCount=12)
        ),
        y=alt.Y("value:Q", title="", axis=alt.Axis(labelFontSize=16, titleFontSize=18)),
        color=alt.Color(
            "component:N", scale=alt.Scale(domain=component_order, range=list(color_map.values())), legend=None
        ),
        tooltip=["date:T", "value:Q", "component:N"],
    )
)

# Create faceted chart with grid lines
chart = (
    base_chart.properties(width=1600, height=200)
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
    .properties(title=alt.Title("timeseries-decomposition · altair · anyplot.ai", fontSize=28, anchor="middle", dy=-10))
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_facet(spacing=20)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.12, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK, fontSize=28)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
    .resolve_scale(y="independent")
    .interactive()
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
