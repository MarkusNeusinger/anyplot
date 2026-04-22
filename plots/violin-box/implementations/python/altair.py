""" pyplots.ai
violin-box: Violin Plot with Embedded Box Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Generate realistic response time data for different server tiers
np.random.seed(42)

groups = ["Basic", "Standard", "Premium", "Enterprise"]
n_per_group = 80

data = []
# Basic tier - higher latency, more variance
data.extend([(np.random.exponential(120) + 80, "Basic") for _ in range(n_per_group)])
# Standard tier - moderate latency
data.extend([(np.random.normal(100, 25), "Standard") for _ in range(n_per_group)])
# Premium tier - lower latency, tighter distribution
data.extend([(np.random.normal(60, 15), "Premium") for _ in range(n_per_group)])
# Enterprise tier - lowest latency, bimodal (some cached, some not)
enterprise_cached = np.random.normal(25, 8, n_per_group // 2)
enterprise_uncached = np.random.normal(55, 12, n_per_group // 2)
data.extend([(v, "Enterprise") for v in np.concatenate([enterprise_cached, enterprise_uncached])])

df = pd.DataFrame(data, columns=["Response Time (ms)", "Server Tier"])
# Ensure positive values for response times
df["Response Time (ms)"] = df["Response Time (ms)"].clip(lower=5)

# Create violin plot layer using transform_density
violin = (
    alt.Chart(df)
    .transform_density("Response Time (ms)", as_=["Response Time (ms)", "density"], groupby=["Server Tier"])
    .mark_area(orient="horizontal", opacity=0.6)
    .encode(
        y=alt.Y("Response Time (ms):Q"),
        x=alt.X(
            "density:Q",
            stack="center",
            impute=None,
            title=None,
            axis=alt.Axis(labels=False, values=[0], grid=False, ticks=False),
        ),
        color=alt.Color(
            "Server Tier:N",
            scale=alt.Scale(
                domain=["Basic", "Standard", "Premium", "Enterprise"],
                range=["#306998", "#FFD43B", "#4B8BBE", "#8BC34A"],
            ),
        ),
    )
)

# Create box plot layer
boxplot = (
    alt.Chart(df)
    .mark_boxplot(
        extent="min-max",
        size=25,
        median={"stroke": "white", "strokeWidth": 2},
        box={"fill": "#333333", "fillOpacity": 0.7},
        outliers={"size": 60, "strokeWidth": 2},
    )
    .encode(y=alt.Y("Response Time (ms):Q", title="Response Time (ms)"), x=alt.value(0), color=alt.value("#333333"))
)

# Layer violin and box plots first, then facet
layered = alt.layer(violin, boxplot).properties(width=280, height=600)

# Apply faceting after layering
chart = (
    layered.facet(
        column=alt.Column(
            "Server Tier:N",
            header=alt.Header(titleFontSize=20, labelFontSize=18, labelOrient="bottom"),
            title=None,
            sort=["Basic", "Standard", "Premium", "Enterprise"],
        )
    )
    .properties(title=alt.Title("violin-box · altair · pyplots.ai", fontSize=28, anchor="middle", offset=20))
    .configure_axis(labelFontSize=16, titleFontSize=20, gridOpacity=0.3)
    .configure_view(stroke=None)
    .configure_legend(titleFontSize=18, labelFontSize=16, symbolSize=200, orient="right")
    .resolve_scale(x="independent")
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
