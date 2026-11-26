"""anyplot.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-26
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

# Imprint palette: position 1 is green, position 5 is red
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
ANYPLOT_AMBER = "#DDCC77"  # warning anchor, outside the categorical pool

# Constants
STATUS_COLORS = {"good": IMPRINT_PALETTE[0], "warning": ANYPLOT_AMBER, "critical": IMPRINT_PALETTE[4]}
FAVORABLE = IMPRINT_PALETTE[0]
UNFAVORABLE = IMPRINT_PALETTE[4]

# Columns: set these to your table's column names
METRIC = "Metric"  # role: metric_name
CURRENT = "Current value"  # role: current_value
HISTORY = "History"  # role: history
CHANGE = "Change (%)"  # role: change_percent
STATUS = "Status"  # role: status
UNIT = "Unit"  # role: extra
BETTER = "Better direction (1 = higher, -1 = lower)"  # role: extra
STEP = "Step"  # role: extra

# Data: replace this block with your own table, one row per history point, for example df = pd.read_csv("metrics.csv")
np.random.seed(42)
n_points = 20
metrics = [
    ("CPU Usage", 45, "%", -5.2, "good", -1),
    ("Memory", 72, "%", 8.3, "warning", -1),
    ("Response Time", 120, "ms", -15.4, "good", -1),
    ("Active Users", 1284, "", 12.7, "good", 1),
    ("Error Rate", 0.8, "%", 45.2, "critical", -1),
    ("Throughput", 3450, "req/s", -2.1, "good", 1),
]
rows = []
for name, value, unit, change, status, better in metrics:
    history = np.linspace(value / (1 + change / 100), value, n_points) + np.random.randn(n_points) * value * 0.03
    history[-1] = value
    for step, point in enumerate(history):
        rows.append(
            {
                METRIC: name,
                CURRENT: value,
                HISTORY: point,
                CHANGE: change,
                STATUS: status,
                UNIT: unit,
                BETTER: better,
                STEP: step,
            }
        )
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
order = df[METRIC].unique().tolist()
n_steps = df[STEP].max() + 1

spark = pd.DataFrame(
    {
        "tile": pd.Categorical(df[METRIC], categories=order, ordered=True),
        "x": df[STEP] / (n_steps - 1) * 18 + 1,
        "y": df.groupby(METRIC, sort=False)[HISTORY].transform(lambda s: (s - s.min()) / (s.max() - s.min())) * 0.22
        + 0.03,
        "line_color": df[STATUS].map(lambda s: STATUS_COLORS.get(s, INK_SOFT)),
    }
)

head = df.groupby(METRIC, sort=False).first().reset_index()
fmt = head[CURRENT].map(lambda v: f"{v:,.0f}" if v >= 1000 else (f"{v:.1f}" if v < 1 else f"{v:.0f}"))
favorable = (head[CHANGE] > 0) == (head[BETTER] > 0)
tiles = pd.DataFrame(
    {
        "tile": pd.Categorical(head[METRIC], categories=order, ordered=True),
        "name": head[METRIC],
        "value": fmt + head[UNIT],
        "change": np.where(head[CHANGE] >= 0, "▲ ", "▼ ") + head[CHANGE].abs().map(lambda v: f"{v:.1f}%"),
        "status_color": head[STATUS].map(lambda s: STATUS_COLORS.get(s, INK_SOFT)),
        "change_color": np.where(favorable, FAVORABLE, UNFAVORABLE),
        "ink": INK,
        "x": 10,
    }
)

strip = pd.DataFrame({"tile": tiles["tile"], "xmin": 0, "xmax": 20, "ymin": 0, "ymax": 0.28})

plot = (
    ggplot()
    + geom_rect(strip, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill=SPARKLINE_BG)
    + geom_line(spark, aes(x="x", y="y", color="line_color"), size=1.4, alpha=0.9)
    + geom_text(
        tiles, aes(x="x", y=0.88, label="name", color="ink"), size=7, ha="center", va="center", fontweight="bold"
    )
    + geom_text(
        tiles, aes(x="x", y=0.62, label="value", color="ink"), size=13, ha="center", va="center", fontweight="bold"
    )
    + geom_text(
        tiles,
        aes(x="x", y=0.40, label="change", color="change_color"),
        size=8,
        ha="center",
        va="center",
        fontweight="bold",
    )
    + scale_color_identity()
    + facet_wrap("~tile", ncol=3)
    + scale_x_continuous(limits=(0, 20), expand=(0.02, 0.02))
    + scale_y_continuous(limits=(0, 1), expand=(0.02, 0.02))
    + labs(title="dashboard-metrics-tiles · python · plotnine · anyplot.ai")
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=10, ha="center", color=INK, margin={"b": 12}),
        strip_text=element_blank(),
        strip_background=element_blank(),
        plot_margin=0.03,
        panel_spacing_x=0.03,
        panel_spacing_y=0.04,
        panel_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_position="none",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
