""" pyplots.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-19
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    facet_wrap,
    geom_area,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

np.random.seed(42)

# Define metrics data
metrics = [
    {"name": "CPU Usage", "value": 45, "unit": "%", "change": -5.2, "status": "good"},
    {"name": "Memory", "value": 72, "unit": "%", "change": 8.3, "status": "warning"},
    {"name": "Response Time", "value": 120, "unit": "ms", "change": -15.1, "status": "good"},
    {"name": "Active Users", "value": 1284, "unit": "", "change": 12.5, "status": "good"},
    {"name": "Error Rate", "value": 0.8, "unit": "%", "change": -22.0, "status": "good"},
    {"name": "Throughput", "value": 847, "unit": "req/s", "change": 3.7, "status": "good"},
]

# Generate sparkline history for each metric (20 points)
all_data = []
for m in metrics:
    base = m["value"]
    # Generate trend data ending at current value
    trend = np.cumsum(np.random.randn(20) * (base * 0.08)) + base * 0.85
    # Normalize to end near current value
    trend = trend - trend[-1] + base

    # Format value display
    if m["value"] >= 1000:
        value_str = f"{m['value']:,}"
    else:
        value_str = str(m["value"])
    value_display = f"{value_str}{m['unit']}"

    # Determine change indicator
    change = m["change"]
    if change >= 0:
        arrow = "▲"
        # Up is bad for CPU, Memory, Error Rate, Response Time
        change_color = "bad" if m["name"] in ["CPU Usage", "Memory", "Error Rate", "Response Time"] else "good"
    else:
        arrow = "▼"
        # Down is good for CPU, Memory, Error Rate, Response Time
        change_color = "good" if m["name"] in ["CPU Usage", "Memory", "Error Rate", "Response Time"] else "bad"

    change_str = f"{arrow} {abs(change):.1f}%"

    for i, val in enumerate(trend):
        all_data.append(
            {
                "metric": m["name"],
                "x": i,
                "y": val,
                "status": m["status"],
                "value_label": value_display if i == 10 else "",
                "change_label": change_str if i == 10 else "",
                "change_color": change_color,
                "is_last": i == len(trend) - 1,
            }
        )

df = pd.DataFrame(all_data)

# Status colors
status_colors = {"good": "#22C55E", "warning": "#F59E0B", "critical": "#EF4444"}

# Map status to color in dataframe
df["fill_color"] = df["status"].map(status_colors)
df["line_color"] = df["status"].map(status_colors)

# Create the last point markers
last_points = df[df["is_last"]].copy()

# Create label data at midpoint
label_data = df[df["value_label"] != ""].copy()

# Get y ranges for positioning labels
y_stats = df.groupby("metric").agg({"y": ["min", "max"]}).reset_index()
y_stats.columns = ["metric", "y_min", "y_max"]

label_data = label_data.merge(y_stats, on="metric")
label_data["y_value"] = label_data["y_max"] + (label_data["y_max"] - label_data["y_min"]) * 0.45
label_data["y_change"] = label_data["y_min"] - (label_data["y_max"] - label_data["y_min"]) * 0.25

# Build the plot with facets
plot = (
    ggplot(df, aes("x", "y"))
    + geom_area(aes(fill="status"), alpha=0.25, show_legend=False)
    + geom_line(aes(color="status"), size=2, show_legend=False)
    + geom_point(data=last_points, mapping=aes(color="status"), size=5, show_legend=False)
    # Value labels
    + geom_text(
        data=label_data, mapping=aes(x="x", y="y_value", label="value_label"), size=22, fontface="bold", color="#1F2937"
    )
    # Change indicator labels
    + geom_text(
        data=label_data,
        mapping=aes(x="x", y="y_change", label="change_label", color="change_color"),
        size=14,
        show_legend=False,
    )
    + scale_fill_manual(values={"good": "#22C55E", "warning": "#F59E0B", "critical": "#EF4444"})
    + scale_color_manual(values={"good": "#22C55E", "warning": "#F59E0B", "critical": "#EF4444", "bad": "#EF4444"})
    + scale_x_continuous(expand=[0.05, 0.05])
    + scale_y_continuous(expand=[0.4, 0.4])
    + facet_wrap("metric", ncol=3, scales="free_y")
    + labs(title="dashboard-metrics-tiles · letsplot · pyplots.ai")
    + theme(
        plot_title=element_text(size=28, face="bold", color="#1F2937", hjust=0.5),
        strip_text=element_text(size=18, face="bold", color="#4B5563"),
        strip_background=element_rect(fill="#F3F4F6", color="#E5E7EB"),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_title=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        panel_background=element_rect(fill="#FFFFFF", color="#E5E7EB", size=1),
        plot_background=element_rect(fill="#F9FAFB"),
        panel_spacing_x=30,
        panel_spacing_y=30,
    )
    + ggsize(1600, 900)
)

# Save PNG (scale=3 gives 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, "plot.html", path=".")
