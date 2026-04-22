""" pyplots.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-19
"""

import numpy as np
from bokeh.io import export_png
from bokeh.layouts import column, gridplot
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure


# Data - 6 metric tiles for a 3x2 grid
np.random.seed(42)

metrics = [
    {
        "name": "CPU Usage",
        "value": 45,
        "unit": "%",
        "history": np.clip(40 + np.cumsum(np.random.randn(30) * 2), 20, 80),
        "change": -5.2,
        "status": "good",
    },
    {
        "name": "Memory",
        "value": 72,
        "unit": "%",
        "history": np.clip(65 + np.cumsum(np.random.randn(30) * 1.5), 50, 90),
        "change": 8.1,
        "status": "warning",
    },
    {
        "name": "Response Time",
        "value": 120,
        "unit": "ms",
        "history": np.clip(100 + np.cumsum(np.random.randn(30) * 10), 50, 200),
        "change": -15.3,
        "status": "good",
    },
    {
        "name": "Error Rate",
        "value": 2.4,
        "unit": "%",
        "history": np.clip(2 + np.cumsum(np.random.randn(30) * 0.3), 0.5, 5),
        "change": 12.5,
        "status": "critical",
    },
    {
        "name": "Throughput",
        "value": 1250,
        "unit": "req/s",
        "history": np.clip(1200 + np.cumsum(np.random.randn(30) * 50), 900, 1500),
        "change": 3.7,
        "status": "good",
    },
    {
        "name": "Active Users",
        "value": 8432,
        "unit": "",
        "history": np.clip(8000 + np.cumsum(np.random.randn(30) * 200), 7000, 10000),
        "change": -2.1,
        "status": "warning",
    },
]

# Colors
STATUS_COLORS = {"good": "#28a745", "warning": "#ffc107", "critical": "#dc3545"}
SPARKLINE_COLOR = "#306998"
TILE_BG = "#f8f9fa"

# Metrics where positive change is unfavorable
UNFAVORABLE_WHEN_UP = ["Error Rate", "Response Time"]

# Tile dimensions (total canvas: ~4500x2700, grid: 3x2)
TILE_WIDTH = 1500
TILE_HEIGHT = 1200

# Create all tiles
tiles = []

for metric in metrics:
    # Determine change direction and favorability
    is_positive_change = metric["change"] > 0
    is_favorable = not is_positive_change if metric["name"] in UNFAVORABLE_WHEN_UP else is_positive_change
    change_color = "#28a745" if is_favorable else "#dc3545"
    arrow = "▲" if is_positive_change else "▼"
    status_color = STATUS_COLORS[metric["status"]]

    # Create figure for tile
    p = figure(
        width=TILE_WIDTH, height=TILE_HEIGHT, toolbar_location=None, tools="", x_range=(-0.1, 1.1), y_range=(-0.1, 1.1)
    )

    # Hide axes and grid
    p.xaxis.visible = False
    p.yaxis.visible = False
    p.xgrid.visible = False
    p.ygrid.visible = False
    p.outline_line_color = None
    p.background_fill_color = TILE_BG
    p.border_fill_color = TILE_BG

    # Add status indicator bar at top
    p.quad(left=0, right=1, top=1.05, bottom=1.0, fill_color=status_color, line_color=None)

    # Metric name label
    name_label = Label(
        x=0.5,
        y=0.88,
        text=metric["name"],
        text_font_size="28pt",
        text_font_style="bold",
        text_color="#333333",
        text_align="center",
        text_baseline="middle",
    )
    p.add_layout(name_label)

    # Current value
    value_text = f"{metric['value']}{metric['unit']}"
    value_label = Label(
        x=0.5,
        y=0.65,
        text=value_text,
        text_font_size="56pt",
        text_font_style="bold",
        text_color="#1a1a1a",
        text_align="center",
        text_baseline="middle",
    )
    p.add_layout(value_label)

    # Change indicator
    change_text = f"{arrow} {abs(metric['change']):.1f}%"
    change_label = Label(
        x=0.5,
        y=0.45,
        text=change_text,
        text_font_size="32pt",
        text_font_style="bold",
        text_color=change_color,
        text_align="center",
        text_baseline="middle",
    )
    p.add_layout(change_label)

    # Sparkline - normalize history data
    history = np.array(metric["history"])
    hist_min, hist_max = history.min(), history.max()
    hist_range = hist_max - hist_min if hist_max != hist_min else 1
    y_norm = 0.08 + (history - hist_min) / hist_range * 0.22  # Scale to [0.08, 0.30]
    x_norm = np.linspace(0.1, 0.9, len(history))

    source = ColumnDataSource(data={"x": x_norm, "y": y_norm})

    # Fill area under sparkline
    y_fill = np.concatenate([y_norm, [0.08, 0.08]])
    x_fill = np.concatenate([x_norm, [x_norm[-1], x_norm[0]]])
    p.patch(x_fill, y_fill, fill_color=SPARKLINE_COLOR, fill_alpha=0.2, line_color=None)

    # Sparkline
    p.line("x", "y", source=source, line_width=4, line_color=SPARKLINE_COLOR)

    # Current point on sparkline
    p.scatter(x=[x_norm[-1]], y=[y_norm[-1]], size=12, fill_color=SPARKLINE_COLOR, line_color="white", line_width=2)

    tiles.append(p)

# Arrange in 3x2 grid
grid = gridplot([[tiles[0], tiles[1], tiles[2]], [tiles[3], tiles[4], tiles[5]]], merge_tools=False)

# Create title as a figure with text annotation
title_fig = figure(width=4500, height=120, toolbar_location=None, tools="", x_range=(0, 1), y_range=(0, 1))
title_fig.xaxis.visible = False
title_fig.yaxis.visible = False
title_fig.xgrid.visible = False
title_fig.ygrid.visible = False
title_fig.outline_line_color = None
title_fig.background_fill_color = "white"
title_fig.border_fill_color = "white"

title_label = Label(
    x=0.5,
    y=0.5,
    text="dashboard-metrics-tiles · bokeh · pyplots.ai",
    text_font_size="36pt",
    text_font_style="bold",
    text_color="#333333",
    text_align="center",
    text_baseline="middle",
)
title_fig.add_layout(title_label)

# Create final layout with title
final_layout = column(title_fig, grid)

# Save
export_png(final_layout, filename="plot.png")
