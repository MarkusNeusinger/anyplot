""" pyplots.ai
box-horizontal: Horizontal Box Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Response times by service type
np.random.seed(42)

data = []
# Create distributions with different characteristics
distributions = {
    "Database Query": (120, 40, 5),  # mean, std, n_outliers
    "API Gateway": (85, 25, 3),
    "Authentication": (45, 15, 2),
    "File Storage": (200, 60, 4),
    "Cache Lookup": (15, 8, 2),
    "Email Service": (150, 50, 3),
}

for service, (mean, std, n_outliers) in distributions.items():
    # Main distribution
    values = np.random.normal(mean, std, 50)
    values = np.clip(values, 5, None)  # No negative response times
    # Add some outliers
    outliers = np.random.uniform(mean + 3 * std, mean + 5 * std, n_outliers)
    all_values = np.concatenate([values, outliers])
    for v in all_values:
        data.append({"Service": service, "Response Time (ms)": v})

df = pd.DataFrame(data)

# Sort by median for easier comparison
medians = df.groupby("Service")["Response Time (ms)"].median().sort_values()
df["Service"] = pd.Categorical(df["Service"], categories=medians.index, ordered=True)

# Create horizontal box plot
chart = (
    alt.Chart(df)
    .mark_boxplot(
        box=alt.MarkConfig(color="#306998"),
        median=alt.MarkConfig(color="#FFD43B", size=3),
        outliers=alt.MarkConfig(color="#306998", size=80),
        ticks=alt.MarkConfig(color="#306998"),
        rule=alt.MarkConfig(color="#306998"),
    )
    .encode(
        x=alt.X("Response Time (ms):Q", title="Response Time (ms)", scale=alt.Scale(zero=False)),
        y=alt.Y("Service:N", title="Service Type", sort=list(medians.index)),
        tooltip=["Service:N", "Response Time (ms):Q"],
    )
    .properties(
        width=1400, height=800, title=alt.Title("box-horizontal · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, labelLimit=300)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
