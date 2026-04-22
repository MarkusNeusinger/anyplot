""" pyplots.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Generate server response times for different endpoints
np.random.seed(42)

endpoints = ["API Gateway", "Database", "Auth Service", "Cache"]
data = []

for endpoint in endpoints:
    if endpoint == "API Gateway":
        # Slightly skewed distribution with outliers
        values = np.concatenate(
            [np.random.lognormal(mean=3.5, sigma=0.6, size=2000), np.random.uniform(150, 300, size=50)]
        )
    elif endpoint == "Database":
        # Heavier tail distribution
        values = np.random.lognormal(mean=4.0, sigma=0.8, size=2050)
    elif endpoint == "Auth Service":
        # Tighter distribution
        values = np.concatenate(
            [np.random.lognormal(mean=3.2, sigma=0.4, size=1900), np.random.uniform(80, 150, size=100)]
        )
    else:  # Cache - fastest
        values = np.concatenate(
            [np.random.lognormal(mean=2.5, sigma=0.5, size=1950), np.random.uniform(50, 100, size=100)]
        )

    for v in values:
        data.append({"Endpoint": endpoint, "Response Time (ms)": v})

df = pd.DataFrame(data)

# Build letter-value quantiles (k=6 levels: median, quartiles, eighths, etc.)
k = 6
quantile_levels = []
for i in range(k + 1):
    if i == 0:
        lower, upper = 0.5, 0.5  # median
    else:
        lower = 0.5 ** (i + 1)
        upper = 1 - lower
    quantile_levels.append((lower, upper, i))

# Calculate letter values for each endpoint
letter_value_data = []
outlier_data = []

for endpoint in endpoints:
    endpoint_data = df[df["Endpoint"] == endpoint]["Response Time (ms)"].values

    for lower_q, upper_q, level in quantile_levels:
        lower_val = np.percentile(endpoint_data, lower_q * 100)
        upper_val = np.percentile(endpoint_data, upper_q * 100)
        median = np.median(endpoint_data)

        letter_value_data.append(
            {"Endpoint": endpoint, "lower": lower_val, "upper": upper_val, "level": level, "median": median}
        )

    # Identify outliers beyond the deepest level
    deepest_lower = np.percentile(endpoint_data, 0.5 ** (k + 1) * 100)
    deepest_upper = np.percentile(endpoint_data, (1 - 0.5 ** (k + 1)) * 100)

    outliers = endpoint_data[(endpoint_data < deepest_lower) | (endpoint_data > deepest_upper)]
    for out_val in outliers[:50]:
        outlier_data.append({"Endpoint": endpoint, "value": out_val})

lv_df = pd.DataFrame(letter_value_data)
outlier_df = pd.DataFrame(outlier_data) if outlier_data else pd.DataFrame({"Endpoint": [], "value": []})

# Create boxen plot using layered bars (width decreases with depth level)
boxes = []
for level in range(k + 1):
    level_df = lv_df[lv_df["level"] == level].copy()
    width = 80 - level * 10

    box = (
        alt.Chart(level_df)
        .mark_bar(opacity=0.7 - level * 0.08, stroke="#306998", strokeWidth=1)
        .encode(
            x=alt.X("Endpoint:N", title="Endpoint", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
            y=alt.Y("lower:Q", title="Response Time (ms)", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
            y2=alt.Y2("upper:Q"),
            color=alt.value("#306998") if level == 0 else alt.value("#4A90C2"),
            size=alt.value(width),
        )
    )
    boxes.append(box)

# Median line
median_df = lv_df[lv_df["level"] == 0][["Endpoint", "median"]].drop_duplicates()

median_line = (
    alt.Chart(median_df)
    .mark_tick(thickness=4, color="#FFD43B", size=60)
    .encode(x=alt.X("Endpoint:N"), y=alt.Y("median:Q"))
)

# Outliers
if len(outlier_df) > 0:
    outliers_chart = (
        alt.Chart(outlier_df)
        .mark_point(size=80, color="#306998", opacity=0.5, filled=True)
        .encode(x=alt.X("Endpoint:N"), y=alt.Y("value:Q"))
    )
else:
    outliers_chart = alt.Chart(pd.DataFrame()).mark_point()

# Combine layers
chart = (
    alt.layer(*boxes, median_line, outliers_chart)
    .properties(
        width=1600, height=900, title=alt.Title("boxen-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
