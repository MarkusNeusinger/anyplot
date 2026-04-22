""" pyplots.ai
box-horizontal: Horizontal Box Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Response times (ms) by service type
np.random.seed(42)

services = ["Database Query", "API Gateway", "Authentication", "File Storage", "Cache Lookup", "Message Queue"]

# Generate data with different distributions for each service
data = []
distributions = [
    (120, 40, 15),  # Database Query - higher, more spread
    (85, 25, 8),  # API Gateway - medium
    (45, 15, 5),  # Authentication - fast, tight
    (200, 80, 20),  # File Storage - slow, very spread, many outliers
    (15, 5, 3),  # Cache Lookup - very fast
    (65, 30, 10),  # Message Queue - medium with spread
]

for service, (mean, std, n_outliers) in zip(services, distributions):
    n = 100
    values = np.random.normal(mean, std, n)
    # Add some outliers
    outliers = np.random.normal(mean + 3 * std, std / 2, n_outliers)
    all_values = np.concatenate([values, outliers])
    # Ensure positive values (response times can't be negative)
    all_values = np.maximum(all_values, 5)
    for v in all_values:
        data.append({"Service": service, "Response Time (ms)": v})

df = pd.DataFrame(data)

# Sort services by median response time for easier comparison
median_order = df.groupby("Service")["Response Time (ms)"].median().sort_values()
services_sorted = median_order.index.tolist()

# Create figure with horizontal box plots
fig = go.Figure()

# Python colors
colors = ["#306998", "#FFD43B", "#306998", "#FFD43B", "#306998", "#FFD43B"]

for i, service in enumerate(services_sorted):
    service_data = df[df["Service"] == service]["Response Time (ms)"]
    fig.add_trace(
        go.Box(
            x=service_data,
            name=service,
            orientation="h",
            marker=dict(color=colors[i % len(colors)], size=8, outliercolor=colors[i % len(colors)]),
            line=dict(color=colors[i % len(colors)], width=2),
            fillcolor=colors[i % len(colors)],
            opacity=0.7,
            boxmean=False,
        )
    )

# Layout
fig.update_layout(
    title=dict(text="box-horizontal · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Response Time (ms)", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    yaxis=dict(title=dict(text="Service Type", font=dict(size=22)), tickfont=dict(size=18)),
    template="plotly_white",
    showlegend=False,
    margin=dict(l=180, r=50, t=80, b=80),
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
