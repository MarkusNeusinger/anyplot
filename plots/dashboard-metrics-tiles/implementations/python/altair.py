""" anyplot.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: altair 6.3.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-26
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: status roles (good = position 1, warning = amber, critical = red)
GOOD_COLOR = "#009E73"
WARN_COLOR = "#DDCC77"
CRIT_COLOR = "#AE3030"
EXTRA_COLORS = ["#C475FD", "#4467A3", "#BD8233", "#2ABCCD", "#954477", "#99B314"]  # any other status label
STATUS_COLORS = {"good": GOOD_COLOR, "warning": WARN_COLOR, "critical": CRIT_COLOR}

# Constants
GRID_COLUMNS = 3  # tiles per row
HISTORY_POINTS = 20  # sparkline length
TILE_WIDTH, SPARK_HEIGHT = 190, 55  # view sizes of one tile, in chart units

# Columns: set these to your table's column names
METRIC_NAME = "metric_name"  # role: metric_name
CURRENT_VALUE = "current_value"  # role: current_value
HISTORY = "history"  # role: history
CHANGE_PERCENT = "change_percent"  # role: change_percent
STATUS = "status"  # role: status
UNIT = "unit"  # optional display unit, not a spec role
LOWER_IS_BETTER = "lower_is_better"  # optional: whether a falling value is favorable

# Data: replace this block with your own table, one row per KPI tile
df = pd.DataFrame(
    {
        METRIC_NAME: ["CPU Usage", "Memory", "Response Time", "Requests/sec", "Error Rate", "Disk I/O"],
        CURRENT_VALUE: [45, 72, 120, 2847, 0.8, 156],
        UNIT: ["%", "%", "ms", "", "%", "MB/s"],
        CHANGE_PERCENT: [-5.2, 8.1, -15.3, 12.4, 0.3, -2.1],
        STATUS: ["good", "warning", "good", "good", "warning", "good"],
        LOWER_IS_BETTER: [True, True, True, False, True, True],
    }
)
histories = []
for idx, change in enumerate(df[CHANGE_PERCENT]):
    np.random.seed(100 + idx * 17)
    walk = 50 + np.cumsum(np.random.randn(HISTORY_POINTS) * 5)
    walk = walk + np.linspace((-15 if change < 0 else 15), 0, HISTORY_POINTS)
    span = walk.max() - walk.min()
    histories.append(tuple(20 + 60 * (walk - walk.min()) / (span + 0.001)))
df[HISTORY] = histories

# Plot: reads only df and the constants above
tiles = []
statuses = list(dict.fromkeys(df[STATUS]))
for _, row in df.iterrows():
    values = row[HISTORY]
    spark_df = pd.DataFrame({"t": range(len(values)), "v": values})

    # Headline value, formatted by magnitude
    value = row[CURRENT_VALUE]
    if value >= 1000:
        val_str = f"{value:,.0f}"
    elif value < 1:
        val_str = f"{value:.1f}"
    else:
        val_str = f"{value:.0f}"
    display_val = f"{val_str}{row.get(UNIT, '')}"

    # Change indicator: arrow follows the sign, color follows favorability
    change = row[CHANGE_PERCENT]
    arrow = "▲" if change > 0 else "▼"
    change_text = f"{arrow} {abs(change):.1f}%"
    lower_better = row.get(LOWER_IS_BETTER, True)
    favorable = (change < 0) == (True if pd.isna(lower_better) else bool(lower_better))
    change_color = GOOD_COLOR if favorable else CRIT_COLOR
    tile_color = STATUS_COLORS.get(row[STATUS]) or EXTRA_COLORS[statuses.index(row[STATUS]) % len(EXTRA_COLORS)]

    # Sparkline area chart
    sparkline = (
        alt.Chart(spark_df)
        .mark_area(
            line={"color": tile_color, "strokeWidth": 2},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color=f"{tile_color}55", offset=0),
                    alt.GradientStop(color=f"{tile_color}0a", offset=1),
                ],
                x1=1,
                x2=1,
                y1=1,
                y2=0,
            ),
        )
        .encode(
            x=alt.X("t:Q", axis=None, scale=alt.Scale(domain=[0, len(values) - 1], nice=False)),
            y=alt.Y("v:Q", axis=None, scale=alt.Scale(domain=[0, 100])),
        )
        .properties(width=TILE_WIDTH, height=SPARK_HEIGHT)
    )

    # Change indicator text row
    change_row = (
        alt.Chart(pd.DataFrame([{"x": 0.5, "label": change_text}]))
        .mark_text(fontSize=16, fontWeight="bold", color=change_color)
        .encode(x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[0, 1])), text="label:N")
        .properties(width=TILE_WIDTH, height=22)
    )

    tile = alt.vconcat(sparkline, change_row, spacing=4).properties(
        title=alt.Title(
            text=display_val,
            subtitle=row[METRIC_NAME],
            fontSize=36,
            subtitleFontSize=16,
            subtitleColor=INK_SOFT,
            color=INK,
            anchor="middle",
            offset=6,
        )
    )
    tiles.append(tile)

# Arrange tiles in rows of GRID_COLUMNS
rows = [alt.hconcat(*tiles[i : i + GRID_COLUMNS], spacing=18) for i in range(0, len(tiles), GRID_COLUMNS)]

chart = (
    alt.vconcat(*rows, spacing=18)
    .properties(
        background=PAGE_BG,
        title=alt.Title(
            text="dashboard-metrics-tiles · python · altair · anyplot.ai",
            fontSize=16,
            color=INK,
            anchor="middle",
            offset=12,
        ),
    )
    .configure_view(stroke=INK_SOFT, strokeWidth=1, cornerRadius=8, fill=ELEVATED_BG)
    .configure_concat(spacing=18)
)

# Save PNG, then fit to exactly 3200×1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    # Scale an overshoot down as a whole (never crop), then centre on the canvas
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
