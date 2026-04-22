""" pyplots.ai
density-rug: Density Plot with Rug Marks
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import altair as alt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


# Data - response times (ms) with realistic distribution
np.random.seed(42)
# Mix of normal response times with some slower outliers
response_times = np.concatenate(
    [
        np.random.normal(150, 30, 80),  # Most responses ~150ms
        np.random.normal(250, 40, 40),  # Slower cluster ~250ms
        np.random.uniform(350, 500, 15),  # Some slow outliers
    ]
)
response_times = np.clip(response_times, 50, 500)  # Realistic bounds

# Compute KDE for smooth density curve
kde = gaussian_kde(response_times, bw_method=0.3)
x_range = np.linspace(response_times.min() - 20, response_times.max() + 20, 300)
density_values = kde(x_range)

# Create DataFrames
density_df = pd.DataFrame({"Response Time (ms)": x_range, "Density": density_values})

rug_df = pd.DataFrame({"Response Time (ms)": response_times})

# Density curve with filled area
density_chart = (
    alt.Chart(density_df)
    .mark_area(opacity=0.5, color="#306998", line={"color": "#306998", "strokeWidth": 3})
    .encode(x=alt.X("Response Time (ms):Q", title="Response Time (ms)"), y=alt.Y("Density:Q", title="Density"))
)

# Rug marks along x-axis using rule marks at y=0
rug_chart = (
    alt.Chart(rug_df)
    .mark_rule(color="#306998", opacity=0.5, strokeWidth=1.5)
    .encode(
        x=alt.X("Response Time (ms):Q"),
        y=alt.value(900),  # Start from bottom of chart area
        y2=alt.value(850),  # Extend up 50 pixels
    )
)

# Combine charts with layering
chart = (
    alt.layer(density_chart, rug_chart)
    .properties(
        width=1600, height=900, title=alt.Title("density-rug · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
