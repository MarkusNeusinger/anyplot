""" pyplots.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-16
"""

import altair as alt
import numpy as np
import pandas as pd
from scipy import stats


# Data: Simulated daily stock returns (252 trading days)
np.random.seed(42)
n_days = 252
# Generate returns with slight negative skew and fat tails (more realistic)
returns = np.random.standard_t(df=5, size=n_days) * 0.015 + 0.0003

# Calculate statistics
mean_ret = np.mean(returns) * 100
std_ret = np.std(returns) * 100
skewness = stats.skew(returns)
kurtosis = stats.kurtosis(returns)

# Create DataFrame for histogram
df = pd.DataFrame({"returns": returns * 100})  # Convert to percentage

# Determine bin edges and create histogram data
bin_count = 30
hist_values, bin_edges = np.histogram(df["returns"], bins=bin_count, density=True)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
bin_width = bin_edges[1] - bin_edges[0]

hist_df = pd.DataFrame(
    {"bin_center": bin_centers, "density": hist_values, "bin_start": bin_edges[:-1], "bin_end": bin_edges[1:]}
)

# Mark tail regions (beyond 2 standard deviations)
lower_tail = mean_ret - 2 * std_ret
upper_tail = mean_ret + 2 * std_ret
hist_df["is_tail"] = (hist_df["bin_center"] < lower_tail) | (hist_df["bin_center"] > upper_tail)

# Create normal distribution overlay
x_range = np.linspace(df["returns"].min() - 0.5, df["returns"].max() + 0.5, 200)
normal_pdf = stats.norm.pdf(x_range, mean_ret, std_ret)
normal_df = pd.DataFrame({"x": x_range, "density": normal_pdf})

# Histogram bars with tail highlighting
histogram = (
    alt.Chart(hist_df)
    .mark_bar(opacity=0.8)
    .encode(
        x=alt.X("bin_start:Q", bin="binned", title="Returns (%)"),
        x2="bin_end:Q",
        y=alt.Y("density:Q", title="Density"),
        color=alt.condition(
            alt.datum.is_tail,
            alt.value("#E74C3C"),  # Red for tails
            alt.value("#306998"),  # Python blue for main distribution
        ),
        tooltip=[
            alt.Tooltip("bin_center:Q", title="Return (%)", format=".2f"),
            alt.Tooltip("density:Q", title="Density", format=".4f"),
        ],
    )
)

# Normal distribution curve
normal_curve = (
    alt.Chart(normal_df)
    .mark_line(color="#FFD43B", strokeWidth=4, strokeDash=[8, 4])
    .encode(x=alt.X("x:Q"), y=alt.Y("density:Q"))
)

# Statistics text annotation
stats_text = f"Mean: {mean_ret:.2f}%\nStd Dev: {std_ret:.2f}%\nSkewness: {skewness:.2f}\nKurtosis: {kurtosis:.2f}"

# Create annotation using mark_text
stats_df = pd.DataFrame({"x": [df["returns"].max() - 1], "y": [max(hist_values) * 0.95], "text": [stats_text]})

stats_annotation = (
    alt.Chart(stats_df)
    .mark_text(align="right", baseline="top", fontSize=18, fontWeight="bold", color="#333333", lineBreak="\n")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="text:N")
)

# Combine layers
chart = (
    alt.layer(histogram, normal_curve, stats_annotation)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("histogram-returns-distribution \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save("plot.html")
