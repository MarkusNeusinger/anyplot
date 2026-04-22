""" pyplots.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-19
"""

import matplotlib.pyplot as plt
import numpy as np


np.random.seed(42)

# Dashboard metrics data
metrics = [
    {
        "name": "CPU Usage",
        "value": 45,
        "unit": "%",
        "history": np.cumsum(np.random.randn(30) * 2) + 50,
        "change": -5.2,
        "status": "good",
    },
    {
        "name": "Memory",
        "value": 72,
        "unit": "%",
        "history": np.cumsum(np.random.randn(30) * 1.5) + 70,
        "change": 8.1,
        "status": "warning",
    },
    {
        "name": "Response Time",
        "value": 120,
        "unit": "ms",
        "history": np.cumsum(np.random.randn(30) * 10) + 130,
        "change": -15.3,
        "status": "good",
    },
    {
        "name": "Requests/s",
        "value": 2450,
        "unit": "",
        "history": np.cumsum(np.random.randn(30) * 50) + 2400,
        "change": 12.7,
        "status": "good",
    },
    {
        "name": "Error Rate",
        "value": 2.3,
        "unit": "%",
        "history": np.cumsum(np.random.randn(30) * 0.3) + 2,
        "change": 45.0,
        "status": "critical",
    },
    {
        "name": "Disk I/O",
        "value": 156,
        "unit": "MB/s",
        "history": np.cumsum(np.random.randn(30) * 8) + 150,
        "change": -3.8,
        "status": "good",
    },
]

# Color scheme
status_colors = {"good": "#28a745", "warning": "#ffc107", "critical": "#dc3545"}
tile_bg = "#f8f9fa"
text_dark = "#212529"

# Create figure with subplots - 3 columns x 2 rows
fig, axes = plt.subplots(2, 3, figsize=(16, 9), facecolor="white")
fig.subplots_adjust(left=0.05, right=0.95, top=0.88, bottom=0.05, wspace=0.15, hspace=0.2)

# Title
fig.suptitle(
    "dashboard-metrics-tiles · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", color=text_dark, y=0.96
)

for ax, metric in zip(axes.flat, metrics, strict=True):
    # Clear axis and set background
    ax.set_facecolor(tile_bg)
    for spine in ax.spines.values():
        spine.set_color("#dee2e6")
        spine.set_linewidth(2)
    ax.set_xticks([])
    ax.set_yticks([])

    # Status bar at top (using axhspan)
    status_color = status_colors[metric["status"]]

    # Add colored status bar at top using a separate axes
    status_ax = ax.inset_axes([0, 0.93, 1, 0.07])
    status_ax.set_facecolor(status_color)
    status_ax.set_xticks([])
    status_ax.set_yticks([])
    for spine in status_ax.spines.values():
        spine.set_visible(False)

    # Metric name
    ax.text(
        0.5,
        0.82,
        metric["name"],
        ha="center",
        va="top",
        fontsize=16,
        fontweight="bold",
        color=text_dark,
        transform=ax.transAxes,
    )

    # Main value
    value_str = f"{metric['value']}{metric['unit']}"
    ax.text(
        0.5,
        0.62,
        value_str,
        ha="center",
        va="top",
        fontsize=32,
        fontweight="bold",
        color=text_dark,
        transform=ax.transAxes,
    )

    # Change indicator
    change = metric["change"]
    arrow = "▲" if change >= 0 else "▼"
    # For error rate and response time, decrease is good; for others, increase is good
    if metric["name"] in ["Error Rate", "Response Time"]:
        change_color = status_colors["good"] if change < 0 else status_colors["critical"]
    else:
        change_color = status_colors["good"] if change >= 0 else status_colors["critical"]

    change_str = f"{arrow} {abs(change):.1f}%"
    ax.text(
        0.5,
        0.42,
        change_str,
        ha="center",
        va="top",
        fontsize=14,
        fontweight="bold",
        color=change_color,
        transform=ax.transAxes,
    )

    # Sparkline using inset axes
    sparkline_ax = ax.inset_axes([0.1, 0.08, 0.8, 0.22])
    sparkline_ax.set_facecolor("none")
    history = metric["history"]
    x_vals = range(len(history))

    sparkline_ax.fill_between(x_vals, history, alpha=0.3, color=status_color)
    sparkline_ax.plot(x_vals, history, linewidth=2.5, color=status_color)
    sparkline_ax.set_xlim(0, len(history) - 1)
    y_range = max(history) - min(history)
    sparkline_ax.set_ylim(min(history) - 0.1 * y_range, max(history) + 0.1 * y_range)
    sparkline_ax.axis("off")

plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
