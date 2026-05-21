"""pyplots.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: plotnine | Python
"""

import os

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
    scale_color_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
SPARKLINE_BG = "#EDEAE0" if THEME == "light" else "#2A2A26"

# Okabe-Ito status colors
STATUS_COLORS = {
    "good": "#009E73",  # Okabe-Ito 1: bluish green
    "warning": "#E69F00",  # Okabe-Ito 5: orange
    "critical": "#D55E00",  # Okabe-Ito 2: vermillion
}

np.random.seed(42)

metrics = [
    {"name": "CPU Usage", "value": 45, "unit": "%", "change": -5.2, "status": "good"},
    {"name": "Memory", "value": 72, "unit": "%", "change": 8.3, "status": "warning"},
    {"name": "Response Time", "value": 120, "unit": "ms", "change": -15.4, "status": "good"},
    {"name": "Active Users", "value": 1284, "unit": "", "change": 12.7, "status": "good"},
    {"name": "Error Rate", "value": 0.8, "unit": "%", "change": 45.2, "status": "critical"},
    {"name": "Throughput", "value": 3450, "unit": "req/s", "change": -2.1, "status": "good"},
]

# Generate sparkline history for each metric
n_points = 20
sparkline_data = []
for metric in metrics:
    base_value = metric["value"]
    trend_direction = -1 if metric["change"] < 0 else 1
    noise = np.random.randn(n_points) * (base_value * 0.1)
    trend = np.linspace(0, trend_direction * abs(metric["change"]) / 100 * base_value, n_points)
    history = base_value - trend + noise

    hist_min, hist_max = history.min(), history.max()
    history_norm = (history - hist_min) / (hist_max - hist_min) if hist_max > hist_min else np.ones(n_points) * 0.5
    history_scaled = history_norm * 0.22 + 0.03

    for j, val in enumerate(history_scaled):
        sparkline_data.append(
            {
                "metric_name": metric["name"],
                "x": j / (n_points - 1) * 18 + 1,
                "y": val,
                "line_color": STATUS_COLORS[metric["status"]],
            }
        )

df_sparkline = pd.DataFrame(sparkline_data)

# Build label rows with theme-adaptive and status-aware colors
label_data = []
for metric in metrics:
    value = metric["value"]
    value_str = f"{value:,.0f}" if value >= 1000 else (f"{value:.1f}" if value < 1 else f"{value:.0f}")
    value_display = f"{value_str}{metric['unit']}"

    change = metric["change"]
    arrow = "▲" if change >= 0 else "▼"
    change_str = f"{arrow} {abs(change):.1f}%"

    # Context-aware change color: for error rate, up = bad
    if metric["name"] == "Error Rate":
        change_color = "#D55E00" if change >= 0 else "#009E73"
    else:
        change_color = "#009E73" if change >= 0 else "#D55E00"

    label_data.append(
        {
            "metric_name": metric["name"],
            "metric_label": metric["name"],
            "value_display": value_display,
            "change_str": change_str,
            "status_color": STATUS_COLORS[metric["status"]],
            "change_color": change_color,
            "ink_color": INK,
            "label_x": 10,
            "label_y": 0.88,
            "value_x": 10,
            "value_y": 0.62,
            "change_x": 10,
            "change_y": 0.38,
        }
    )

df_labels = pd.DataFrame(label_data)

all_metrics = [m["name"] for m in metrics]
df_sparkline["metric_name"] = pd.Categorical(df_sparkline["metric_name"], categories=all_metrics, ordered=True)
df_labels["metric_name"] = pd.Categorical(df_labels["metric_name"], categories=all_metrics, ordered=True)

bg_data = [{"metric_name": m["name"], "xmin": 0, "xmax": 20, "ymin": 0, "ymax": 0.28} for m in metrics]
df_bg = pd.DataFrame(bg_data)
df_bg["metric_name"] = pd.Categorical(df_bg["metric_name"], categories=all_metrics, ordered=True)

# Plot
plot = (
    ggplot()
    # Sparkline area background
    + geom_rect(df_bg, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill=SPARKLINE_BG)
    # Sparklines — thicker for visibility, colored by status
    + geom_line(df_sparkline, aes(x="x", y="y", color="line_color"), size=1.4, alpha=0.9)
    # Metric label
    + geom_text(
        df_labels,
        aes(x="label_x", y="label_y", label="metric_label", color="ink_color"),
        size=7,
        ha="center",
        va="center",
        fontweight="bold",
    )
    # Main value (colored by status)
    + geom_text(
        df_labels,
        aes(x="value_x", y="value_y", label="value_display", color="status_color"),
        size=13,
        ha="center",
        va="center",
        fontweight="bold",
    )
    # Change indicator (colored green/red by favorable/unfavorable direction)
    + geom_text(
        df_labels,
        aes(x="change_x", y="change_y", label="change_str", color="change_color"),
        size=6,
        ha="center",
        va="center",
    )
    # Use hex values directly from data columns
    + scale_color_identity()
    + facet_wrap("~metric_name", ncol=3)
    + scale_x_continuous(limits=(0, 20), expand=(0.02, 0.02))
    + scale_y_continuous(limits=(0, 1), expand=(0.02, 0.02))
    + labs(title="dashboard-metrics-tiles · plotnine · pyplots.ai")
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=10, ha="center", color=INK, margin={"b": 12}),
        strip_text=element_blank(),
        strip_background=element_blank(),
        panel_spacing=0.12,
        panel_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_position="none",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
