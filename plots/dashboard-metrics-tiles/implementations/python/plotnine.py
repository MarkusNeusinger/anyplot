""" pyplots.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-19
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    facet_wrap,
    geom_line,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)


# Data
np.random.seed(42)

# Define metrics with their properties
metrics = [
    {"name": "CPU Usage", "value": 45, "unit": "%", "change": -5.2, "status": "good"},
    {"name": "Memory", "value": 72, "unit": "%", "change": 8.3, "status": "warning"},
    {"name": "Response Time", "value": 120, "unit": "ms", "change": -15.4, "status": "good"},
    {"name": "Active Users", "value": 1284, "unit": "", "change": 12.7, "status": "good"},
    {"name": "Error Rate", "value": 0.8, "unit": "%", "change": 45.2, "status": "critical"},
    {"name": "Throughput", "value": 3450, "unit": "req/s", "change": -2.1, "status": "good"},
]

# Generate sparkline history data for each metric
n_points = 20
sparkline_data = []

for i, metric in enumerate(metrics):
    # Generate realistic trending data based on current value
    base_value = metric["value"]
    trend_direction = -1 if metric["change"] < 0 else 1
    noise = np.random.randn(n_points) * (base_value * 0.1)
    trend = np.linspace(0, trend_direction * abs(metric["change"]) / 100 * base_value, n_points)
    history = base_value - trend + noise

    # Normalize to 0-1 range for plotting, scaled to bottom area
    hist_min, hist_max = history.min(), history.max()
    if hist_max > hist_min:
        history_norm = (history - hist_min) / (hist_max - hist_min)
    else:
        history_norm = np.ones(n_points) * 0.5

    # Scale sparkline to occupy bottom 25% of tile (0 to 0.25)
    history_scaled = history_norm * 0.22 + 0.03

    for j, val in enumerate(history_scaled):
        sparkline_data.append(
            {
                "metric_name": metric["name"],
                "x": j / (n_points - 1) * 18 + 1,  # Scale x from 1 to 19
                "y": val,
                "order": i,
            }
        )

df_sparkline = pd.DataFrame(sparkline_data)

# Create text labels data for each tile
label_data = []
for i, metric in enumerate(metrics):
    # Format value display
    if metric["value"] >= 1000:
        value_str = f"{metric['value']:,.0f}"
    elif metric["value"] < 1:
        value_str = f"{metric['value']:.1f}"
    else:
        value_str = f"{metric['value']:.0f}"
    value_display = f"{value_str}{metric['unit']}"

    # Format change indicator
    change = metric["change"]
    arrow = "\u25b2" if change >= 0 else "\u25bc"  # Up/down triangle
    change_str = f"{arrow} {abs(change):.1f}%"

    # Determine colors based on status
    status_colors = {"good": "#27AE60", "warning": "#F39C12", "critical": "#E74C3C"}
    status_color = status_colors[metric["status"]]

    # Change color based on direction and context
    # For Error Rate, up is bad, down is good
    if metric["name"] == "Error Rate":
        change_color = "#E74C3C" if change >= 0 else "#27AE60"
    else:
        change_color = "#27AE60" if change >= 0 else "#E74C3C"

    label_data.append(
        {
            "metric_name": metric["name"],
            "metric_label": metric["name"],
            "value_display": value_display,
            "change_str": change_str,
            "status_color": status_color,
            "change_color": change_color,
            "order": i,
            # Position coordinates
            "label_x": 10,
            "label_y": 0.88,
            "value_x": 10,
            "value_y": 0.62,
            "change_x": 10,
            "change_y": 0.38,
        }
    )

df_labels = pd.DataFrame(label_data)

# Merge order into sparkline data and set factor order
all_metrics = [m["name"] for m in metrics]
df_sparkline["metric_name"] = pd.Categorical(df_sparkline["metric_name"], categories=all_metrics, ordered=True)
df_labels["metric_name"] = pd.Categorical(df_labels["metric_name"], categories=all_metrics, ordered=True)

# Determine sparkline color based on status
status_color_map = {}
for m in metrics:
    status_colors = {"good": "#27AE60", "warning": "#F39C12", "critical": "#E74C3C"}
    status_color_map[m["name"]] = status_colors[m["status"]]

df_sparkline["status_color"] = df_sparkline["metric_name"].map(status_color_map)

# Create background rect data for sparkline area
bg_data = []
for m in metrics:
    bg_data.append({"metric_name": m["name"], "xmin": 0, "xmax": 20, "ymin": 0, "ymax": 0.28})
df_bg = pd.DataFrame(bg_data)
df_bg["metric_name"] = pd.Categorical(df_bg["metric_name"], categories=all_metrics, ordered=True)

# Plot
plot = (
    ggplot()
    # Light background for sparkline area
    + geom_rect(df_bg, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill="#F0F4F8", alpha=0.7)
    # Sparkline
    + geom_line(df_sparkline, aes(x="x", y="y", color="metric_name"), size=2, alpha=0.9)
    # Metric label (title of each tile)
    + geom_text(
        df_labels,
        aes(x="label_x", y="label_y", label="metric_label"),
        size=14,
        ha="center",
        va="center",
        color="#34495E",
        fontweight="bold",
    )
    # Main value display
    + geom_text(
        df_labels,
        aes(x="value_x", y="value_y", label="value_display", color="metric_name"),
        size=26,
        ha="center",
        va="center",
        fontweight="bold",
    )
    # Change indicator
    + geom_text(
        df_labels,
        aes(x="change_x", y="change_y", label="change_str"),
        size=11,
        ha="center",
        va="center",
        color="#7F8C8D",
    )
    # Color scale for sparklines and values based on status
    + scale_color_manual(
        values={
            "CPU Usage": "#27AE60",
            "Memory": "#F39C12",
            "Response Time": "#27AE60",
            "Active Users": "#27AE60",
            "Error Rate": "#E74C3C",
            "Throughput": "#27AE60",
        }
    )
    # Facet wrap to create grid layout (3 columns for 6 tiles)
    + facet_wrap("~metric_name", ncol=3)
    # Coordinate system
    + scale_x_continuous(limits=(0, 20), expand=(0.02, 0.02))
    + scale_y_continuous(limits=(0, 1), expand=(0.02, 0.02))
    # Labels
    + labs(title="dashboard-metrics-tiles \u00b7 plotnine \u00b7 pyplots.ai")
    # Theme - clean dashboard look
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", color="#2C3E50", margin={"b": 25}),
        strip_text=element_blank(),  # Hide facet labels (we use our own)
        strip_background=element_blank(),
        panel_spacing=0.12,
        panel_background=element_rect(fill="#FFFFFF", color="#E0E5E9", size=1),
        plot_background=element_rect(fill="#F8FAFB"),
        legend_position="none",
    )
)

plot.save("plot.png", dpi=300, width=16, height=9, verbose=False)
