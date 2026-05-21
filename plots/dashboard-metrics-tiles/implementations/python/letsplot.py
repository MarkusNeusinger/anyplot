""" anyplot.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-21
"""

import os

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

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Status colors: good uses brand green (Okabe-Ito #1), warning amber, critical red
STATUS_COLORS = {"good": "#009E73", "warning": "#F59E0B", "critical": "#EF4444", "bad": "#EF4444"}

np.random.seed(42)

# Data
metrics = [
    {"name": "CPU Usage", "value": 45, "unit": "%", "change": -5.2, "status": "good"},
    {"name": "Memory", "value": 72, "unit": "%", "change": 8.3, "status": "warning"},
    {"name": "Response Time", "value": 120, "unit": "ms", "change": -15.1, "status": "good"},
    {"name": "Active Users", "value": 1284, "unit": "", "change": 12.5, "status": "good"},
    {"name": "Error Rate", "value": 0.8, "unit": "%", "change": -22.0, "status": "good"},
    {"name": "Throughput", "value": 847, "unit": "req/s", "change": 3.7, "status": "good"},
]

all_data = []
for m in metrics:
    base = m["value"]
    trend = np.cumsum(np.random.randn(20) * (base * 0.08)) + base * 0.85
    trend = trend - trend[-1] + base

    value_str = f"{m['value']:,}" if m["value"] >= 1000 else str(m["value"])
    value_display = f"{value_str}{m['unit']}"

    change = m["change"]
    if change >= 0:
        arrow = "▲"
        change_color = "bad" if m["name"] in ["CPU Usage", "Memory", "Error Rate", "Response Time"] else "good"
    else:
        arrow = "▼"
        change_color = "good" if m["name"] in ["CPU Usage", "Memory", "Error Rate", "Response Time"] else "bad"

    change_str = f"{arrow} {abs(change):.1f}%"

    # Prepend warning badge to facet strip label for prominent visual distinction
    facet_label = f"⚠  {m['name']}" if m["status"] == "warning" else m["name"]

    for i, val in enumerate(trend):
        all_data.append(
            {
                "metric": facet_label,
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
last_points = df[df["is_last"]].copy()
label_data = df[df["value_label"] != ""].copy()

y_stats = df.groupby("metric").agg({"y": ["min", "max"]}).reset_index()
y_stats.columns = ["metric", "y_min", "y_max"]

label_data = label_data.merge(y_stats, on="metric")
label_data["y_value"] = label_data["y_max"] + (label_data["y_max"] - label_data["y_min"]) * 0.45
label_data["y_change"] = label_data["y_min"] - (label_data["y_max"] - label_data["y_min"]) * 0.25

# Plot
plot = (
    ggplot(df, aes("x", "y"))
    + geom_area(aes(fill="status"), alpha=0.25, show_legend=False)
    + geom_line(aes(color="status"), size=2, show_legend=False)
    + geom_point(data=last_points, mapping=aes(color="status"), size=5, show_legend=False)
    + geom_text(
        data=label_data, mapping=aes(x="x", y="y_value", label="value_label"), size=22, fontface="bold", color=INK
    )
    + geom_text(
        data=label_data,
        mapping=aes(x="x", y="y_change", label="change_label", color="change_color"),
        size=14,
        show_legend=False,
    )
    + scale_fill_manual(values=STATUS_COLORS)
    + scale_color_manual(values=STATUS_COLORS)
    + scale_x_continuous(expand=[0.05, 0.05])
    + scale_y_continuous(expand=[0.45, 0.45])
    + facet_wrap("metric", ncol=3, scales="free_y")
    + labs(title="dashboard-metrics-tiles · python · letsplot · anyplot.ai")
    + theme(
        plot_title=element_text(size=16, face="bold", color=INK, hjust=0.5),
        strip_text=element_text(size=14, face="bold", color=INK_SOFT),
        strip_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_title=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        panel_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=1),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_spacing_x=30,
        panel_spacing_y=30,
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
