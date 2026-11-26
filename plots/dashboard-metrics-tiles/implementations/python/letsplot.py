""" anyplot.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-26
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
    geom_blank,
    geom_line,
    geom_point,
    geom_ribbon,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
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

# Imprint palette: good = brand green, critical/unfavorable = matte red, warning = amber anchor
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
ANYPLOT_AMBER = "#DDCC77"

# Constants
STATE_COLORS = {
    "good": IMPRINT_PALETTE[0],
    "warning": ANYPLOT_AMBER,
    "critical": IMPRINT_PALETTE[4],
    "bad": IMPRINT_PALETTE[4],
}
WARNING_BADGE = "⚠  "
BADGE_STATES = ("warning", "critical")
FAVORABLE, UNFAVORABLE = "good", "bad"

METRIC = "Metric"  # role: metric_name
CURRENT = "Current value"  # role: current_value
HISTORY = "History"  # role: history
CHANGE = "Change (%)"  # role: change_percent
STATUS = "Status"  # role: status
STEP = "Step"  # role: extra
UNIT = "Unit"  # role: extra
LOWER_BETTER = "Lower is better"  # role: extra
TILE = "Tile"  # role: extra
EFFECT = "Effect"  # role: extra
VALUE_TEXT = "Value text"  # role: extra
CHANGE_TEXT = "Change text"  # role: extra
VALUE_Y = "Value y"  # role: extra
CHANGE_Y = "Change y"  # role: extra
FLOOR = "Floor"  # role: extra
TOP = "Top"  # role: extra

# Data: replace this block with your own table, one row per metric and step
np.random.seed(42)
metrics = [
    ("CPU Usage", 45, "%", -5.2, "good", True),
    ("Memory", 72, "%", 8.3, "warning", True),
    ("Response Time", 120, "ms", -15.1, "good", True),
    ("Active Users", 1284, "", 12.5, "good", False),
    ("Error Rate", 0.8, "%", -22.0, "good", True),
    ("Throughput", 847, "req/s", 3.7, "good", False),
]
rows = []
for name, value, unit, change, status, lower_is_better in metrics:
    walk = np.cumsum(np.random.randn(20) * (value * 0.08)) + value * 0.85
    walk = walk - walk[-1] + value
    for step, level in enumerate(walk):
        rows.append((name, value, unit, change, status, lower_is_better, step, level))
df = pd.DataFrame(rows, columns=[METRIC, CURRENT, UNIT, CHANGE, STATUS, LOWER_BETTER, STEP, HISTORY])

# Plot
tiles = df.groupby(METRIC, sort=False).agg(
    {CURRENT: "first", UNIT: "first", CHANGE: "first", STATUS: "first", LOWER_BETTER: "first"}
)
low = df.groupby(METRIC, sort=False)[HISTORY].min()
high = df.groupby(METRIC, sort=False)[HISTORY].max()
span = high - low

labels = tiles.reset_index()
labels[STEP] = df[STEP].median()
labels[VALUE_TEXT] = [
    (f"{v:,.0f}" if v >= 1000 else f"{v:g}") + unit for v, unit in zip(labels[CURRENT], labels[UNIT], strict=True)
]
labels[CHANGE_TEXT] = [("▲ " if c >= 0 else "▼ ") + f"{abs(c):.1f}%" for c in labels[CHANGE]]
# favorable when the change goes the way the metric wants: down where lower is better, else up
labels[EFFECT] = [
    FAVORABLE if (c < 0) == lower else UNFAVORABLE
    for c, lower in zip(labels[CHANGE], labels[LOWER_BETTER], strict=True)
]
labels[VALUE_Y] = (high + span * 0.55).to_numpy()
labels[CHANGE_Y] = (low - span * 0.40).to_numpy()
labels[TOP] = (high + span * 0.95).to_numpy()

# Warning tiles carry a badge in the strip, a second cue beyond color
badge = {m: WARNING_BADGE + m if s in BADGE_STATES else m for m, s in zip(tiles.index, tiles[STATUS], strict=True)}
df[TILE] = df[METRIC].map(badge)
labels[TILE] = labels[METRIC].map(badge)
df[FLOOR] = df[METRIC].map(low - span * 0.7)
last_points = df[df[STEP] == df[STEP].max()]

plot = (
    ggplot(df, aes(STEP, HISTORY))
    + geom_ribbon(aes(ymin=FLOOR, ymax=HISTORY, fill=STATUS), alpha=0.25, size=0, show_legend=False, tooltips="none")
    + geom_line(
        aes(color=STATUS),
        size=2,
        show_legend=False,
        tooltips=layer_tooltips().line(f"@{{{METRIC}}}").line(f"value|@{{{HISTORY}}}{{.1f}}"),
    )
    + geom_point(
        data=last_points,
        mapping=aes(color=STATUS),
        size=5,
        show_legend=False,
        tooltips=layer_tooltips().line(f"@{{{METRIC}}}").line(f"current|@{{{HISTORY}}}{{.1f}}"),
    )
    + geom_text(data=labels, mapping=aes(x=STEP, y=VALUE_Y, label=VALUE_TEXT), size=20, fontface="bold", color=INK)
    + geom_text(
        data=labels,
        mapping=aes(x=STEP, y=CHANGE_Y, label=CHANGE_TEXT, color=EFFECT),
        size=17,
        fontface="bold",
        show_legend=False,
    )
    + geom_blank(data=labels, mapping=aes(x=STEP, y=TOP))
    + scale_fill_manual(values=STATE_COLORS)
    + scale_color_manual(values=STATE_COLORS)
    + scale_x_continuous(expand=[0.05, 0.05])
    + scale_y_continuous(expand=[0.03, 0.03])
    + facet_wrap(TILE, ncol=3, scales="free_y")
    + labs(title="dashboard-metrics-tiles · python · letsplot · anyplot.ai")
    + theme(
        plot_title=element_text(size=16, face="bold", color=INK, hjust=0.5),
        strip_text=element_text(size=17, face="bold", color=INK_SOFT),
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
