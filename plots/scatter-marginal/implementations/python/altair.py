""" pyplots.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - bivariate distribution with correlation
np.random.seed(42)
n = 150
x = np.random.randn(n) * 15 + 50
y = 0.7 * x + np.random.randn(n) * 10 + 20

df = pd.DataFrame({"X Value": x, "Y Value": y})

# Shared axis domains for proper alignment
x_domain = [df["X Value"].min() - 2, df["X Value"].max() + 2]
y_domain = [df["Y Value"].min() - 2, df["Y Value"].max() + 2]

# Interactive brush selection
brush = alt.param(name="brush", select="interval")

# Base chart
base = alt.Chart(df)

# Main scatter plot with selection
scatter = (
    base.mark_circle(size=120, opacity=0.65)
    .encode(
        x=alt.X("X Value:Q", title="X Value (units)", scale=alt.Scale(domain=x_domain)),
        y=alt.Y("Y Value:Q", title="Y Value (units)", scale=alt.Scale(domain=y_domain)),
        color=alt.condition(brush, alt.value("#306998"), alt.value("lightgray")),
        tooltip=["X Value:Q", "Y Value:Q"],
    )
    .properties(width=1000, height=600)
    .add_params(brush)
)

# Top marginal histogram with matching X scale
top_hist = (
    base.mark_bar(color="#306998", opacity=0.5)
    .encode(
        x=alt.X("X Value:Q", bin=alt.Bin(maxbins=25), title=None, scale=alt.Scale(domain=x_domain), axis=None),
        y=alt.Y("count()", title=None, axis=alt.Axis(labels=False, ticks=False)),
    )
    .properties(width=1000, height=120)
)

# Right marginal histogram with matching Y scale
right_hist = (
    base.mark_bar(color="#306998", opacity=0.5)
    .encode(
        y=alt.Y("Y Value:Q", bin=alt.Bin(maxbins=25), title=None, scale=alt.Scale(domain=y_domain), axis=None),
        x=alt.X("count()", title=None, axis=alt.Axis(labels=False, ticks=False)),
    )
    .properties(width=120, height=600)
)

# Combine: top histogram above, scatter with right histogram below
combined = (
    alt.vconcat(top_hist, alt.hconcat(scatter, right_hist, spacing=5), spacing=5)
    .properties(title=alt.Title(text="scatter-marginal · altair · pyplots.ai", fontSize=28, anchor="middle"))
    .configure_axis(labelFontSize=16, titleFontSize=20)
    .configure_title(fontSize=28)
    .configure_view(strokeWidth=0)
    .configure_concat(spacing=5)
)

# Save outputs
combined.save("plot.png", scale_factor=3.0)
combined.save("plot.html")
