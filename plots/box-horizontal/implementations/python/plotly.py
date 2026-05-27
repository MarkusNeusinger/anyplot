""" anyplot.ai
box-horizontal: Horizontal Box Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-12
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

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

for i, service in enumerate(services_sorted):
    service_data = df[df["Service"] == service]["Response Time (ms)"]
    fig.add_trace(
        go.Box(
            x=service_data,
            name=service,
            orientation="h",
            marker=dict(color=IMPRINT[i % len(IMPRINT)], size=8, outliercolor=IMPRINT[i % len(IMPRINT)]),
            line=dict(color=IMPRINT[i % len(IMPRINT)], width=2),
            fillcolor=IMPRINT[i % len(IMPRINT)],
            opacity=0.7,
            boxmean=False,
            hovertemplate="<b>%{name}</b><br>Value: %{x:.1f} ms<extra></extra>",
        )
    )

# Layout
fig.update_layout(
    title=dict(text="box-horizontal · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Response Time (ms)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Service Type", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        linecolor=INK_SOFT,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    showlegend=False,
    margin=dict(l=180, r=50, t=80, b=80),
    font=dict(color=INK),
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
