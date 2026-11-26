"""anyplot.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-21
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
AMBER = "#DDCC77"  # Imprint semantic anchor for warning

# Constants: semantic status maps, color plus a shape cue so status never rests on color alone
STATUS_COLORS = {"good": IMPRINT_PALETTE[0], "warning": AMBER, "critical": IMPRINT_PALETTE[4]}
STATUS_SYMBOLS = {"good": "✓", "warning": "⚠", "critical": "✕"}
STATUS_BORDER_WIDTHS = {"good": 1, "warning": 2, "critical": 3}
FAVORABLE = IMPRINT_PALETTE[0]
UNFAVORABLE = IMPRINT_PALETTE[4]

# Columns: set these to your table's column names
METRIC = "Metric"  # role: metric_name
CURRENT = "Current value"  # role: current_value
HISTORY = "History value"  # role: history
CHANGE = "Change (%)"  # role: change_percent
STATUS = "Status"  # role: status
PERIOD = "Day"  # role: extra
UNIT = "Unit"  # role: extra
LOWER_IS_BETTER = "Lower is better"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("metrics.csv")
# One row per history point; the tile-level columns repeat on every row of a metric.
rng = np.random.default_rng(42)
n_points = 30
df = pd.concat(
    [
        pd.DataFrame(
            {
                METRIC: name,
                PERIOD: np.arange(n_points),
                HISTORY: history,
                CURRENT: current,
                UNIT: unit,
                CHANGE: change,
                STATUS: status,
                LOWER_IS_BETTER: lower_is_better,
            }
        )
        for name, current, unit, change, status, lower_is_better, history in [
            ("CPU Usage", 45, "%", -5.2, "good", True, 30 + np.cumsum(rng.normal(0, 2, n_points))),
            ("Memory", 72, "%", 8.3, "warning", True, 60 + np.cumsum(rng.normal(0, 1.5, n_points))),
            ("Response Time", 120, "ms", -15.4, "good", True, 100 + np.cumsum(rng.normal(0, 5, n_points))),
            ("Requests/sec", 1250, "", 12.7, "good", False, 1000 + np.cumsum(rng.normal(0, 50, n_points))),
            ("Error Rate", 2.3, "%", 45.0, "critical", True, 1 + np.abs(np.cumsum(rng.normal(0, 0.3, n_points)))),
            ("Disk I/O", 85, "MB/s", -2.1, "good", False, 70 + np.cumsum(rng.normal(0, 3, n_points))),
        ]
    ],
    ignore_index=True,
)

# Plot: reads only df and the constants above
tiles = list(df.groupby(METRIC, sort=False))
n_tiles = len(tiles)
n_cols = 2 if n_tiles <= 4 else 3 if n_tiles <= 9 else 4
n_rows = int(np.ceil(n_tiles / n_cols))
gap_x, gap_y = 0.035, 0.07
tile_w = (1 - gap_x * (n_cols - 1)) / n_cols
tile_h = (1 - gap_y * (n_rows - 1)) / n_rows

fig = go.Figure()
shapes = []
layout_axes = {}

for idx, (name, rows) in enumerate(tiles):
    first = rows.iloc[0]
    status = first[STATUS]
    status_color = STATUS_COLORS.get(status, IMPRINT_PALETTE[2])
    symbol = STATUS_SYMBOLS.get(status, "•")
    border = STATUS_BORDER_WIDTHS.get(status, 1)

    col, row = idx % n_cols, idx // n_cols
    x0 = col * (tile_w + gap_x)
    x1 = x0 + tile_w
    y1 = 1 - row * (tile_h + gap_y)
    y0 = y1 - tile_h

    # Tile card with a status-colored frame and a status accent bar along its top edge
    shapes.append(
        {
            "type": "rect",
            "xref": "paper",
            "yref": "paper",
            "x0": x0,
            "x1": x1,
            "y0": y0,
            "y1": y1,
            "fillcolor": ELEVATED_BG,
            "line": {"color": status_color, "width": border},
            "layer": "below",
        }
    )
    shapes.append(
        {
            "type": "rect",
            "xref": "paper",
            "yref": "paper",
            "x0": x0,
            "x1": x1,
            "y0": y1 - 0.06 * tile_h,
            "y1": y1,
            "fillcolor": status_color,
            "line": {"width": 0},
            "layer": "below",
        }
    )

    # Value, label and change indicator: a go.Indicator in the upper part of the tile
    change = first[CHANGE]
    rising_is_good = not first[LOWER_IS_BETTER]
    up_color = FAVORABLE if rising_is_good else UNFAVORABLE
    down_color = UNFAVORABLE if rising_is_good else FAVORABLE
    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=first[CURRENT],
            number={"font": {"size": 48, "color": INK}, "suffix": first[UNIT]},
            delta={
                "reference": first[CURRENT] / (1 + change / 100),
                "relative": True,
                "valueformat": ".1%",
                "font": {"size": 22},
                "increasing": {"color": up_color, "symbol": "▲"},
                "decreasing": {"color": down_color, "symbol": "▼"},
            },
            title={"text": f"{symbol}  {name}", "font": {"size": 24, "color": INK}},
            domain={"x": [x0, x1], "y": [y0 + 0.34 * tile_h, y1 - 0.27 * tile_h]},
        )
    )

    # Sparkline: its own pair of axes, scaled to the metric's own range
    history = rows[HISTORY].to_numpy(dtype=float)
    span = np.nanmax(history) - np.nanmin(history)
    scaled = (history - np.nanmin(history)) / (span if span > 0 else 1.0)
    axis_id = idx + 1
    fig.add_trace(
        go.Scatter(
            x=rows[PERIOD],
            y=scaled,
            mode="lines",
            line={"color": INK_SOFT, "width": 4},
            fill="tozeroy",
            fillcolor="rgba(74,74,68,0.16)" if THEME == "light" else "rgba(184,183,176,0.22)",
            showlegend=False,
            hoverinfo="skip",
            xaxis=f"x{axis_id}",
            yaxis=f"y{axis_id}",
        )
    )
    hidden = {"showticklabels": False, "showgrid": False, "zeroline": False, "showline": False}
    layout_axes[f"xaxis{axis_id}"] = dict(
        domain=[x0 + 0.08 * tile_w, x1 - 0.08 * tile_w],
        range=[rows[PERIOD].min(), rows[PERIOD].max()],
        anchor=f"y{axis_id}",
        **hidden,
    )
    layout_axes[f"yaxis{axis_id}"] = dict(
        domain=[y0 + 0.07 * tile_h, y0 + 0.33 * tile_h], range=[-0.1, 1.1], anchor=f"x{axis_id}", **hidden
    )

# Style
fig.update_layout(
    shapes=shapes,
    **layout_axes,
    title={
        "text": "dashboard-metrics-tiles · python · plotly · anyplot.ai",
        "x": 0.5,
        "xanchor": "center",
        "font": {"size": 24, "color": INK},
    },
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 30, "r": 30, "t": 60, "b": 25},
    showlegend=False,
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
