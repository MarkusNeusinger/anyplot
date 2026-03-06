""" pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: altair 6.0.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-06
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - synthetic global temperature anomalies (1850-2024) mimicking HadCRUT pattern
np.random.seed(42)
years = np.arange(1850, 2025)
n = len(years)

# Build a realistic warming trend: slight cooling until ~1910, gradual rise, acceleration after 1980
baseline_trend = np.piecewise(
    years.astype(float),
    [years < 1910, (years >= 1910) & (years < 1980), years >= 1980],
    [lambda y: -0.2 + (y - 1850) * (-0.001), lambda y: -0.3 + (y - 1910) * 0.005, lambda y: 0.05 + (y - 1980) * 0.022],
)
noise = np.random.normal(0, 0.08, n)
anomaly = baseline_trend + noise

# Compute decade labels and running mean for layered composition
df = pd.DataFrame({"year": years, "anomaly": anomaly})
df["decade"] = (df["year"] // 10) * 10
df["decade_label"] = df["year"].apply(lambda y: str(y) if y % 50 == 0 else "")

# Plot - warming stripes with layered Altair composition
max_abs = max(abs(anomaly.min()), abs(anomaly.max()))

# Diverging color scale using cividis-inspired endpoints for better accessibility
color_scale = alt.Scale(
    domain=[-max_abs, 0, max_abs], range=["#08519c", "#f7f7f7", "#a50f15"], type="linear", interpolate="lab"
)

# Interactive selection: hovering highlights individual stripe in HTML export
hover = alt.selection_point(on="pointerover", fields=["year"])

# Base stripes layer
stripes = (
    alt.Chart(df)
    .mark_rect(cursor="crosshair")
    .encode(
        x=alt.X("year:O", axis=None),
        color=alt.Color("anomaly:Q", scale=color_scale, legend=None),
        opacity=alt.condition(hover, alt.value(1.0), alt.value(0.85)),
        tooltip=[alt.Tooltip("year:O", title="Year"), alt.Tooltip("anomaly:Q", title="Anomaly (°C)", format="+.2f")],
    )
    .add_params(hover)
)

# Decade markers at the bottom edge using layered text composition
decade_ticks_df = df[df["decade_label"] != ""].copy()
decade_ticks = (
    alt.Chart(decade_ticks_df)
    .mark_text(align="center", baseline="bottom", fontSize=16, fontWeight="bold", color="#333333", opacity=0.6)
    .encode(x=alt.X("year:O", axis=None), y=alt.value(890), text="decade_label:N")
)

# Layer composition with shared properties
chart = (
    alt.layer(stripes, decade_ticks)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "heatmap-stripes-climate \u00b7 altair \u00b7 pyplots.ai",
            fontSize=28,
            anchor="middle",
            fontWeight="bold",
            offset=10,
        ),
    )
    .configure_view(strokeWidth=0)
    .configure_concat(spacing=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
