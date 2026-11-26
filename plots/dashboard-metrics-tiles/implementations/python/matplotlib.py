"""anyplot.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Status colors: Imprint green, the amber warning anchor, Imprint red
STATUS_COLORS = {"good": "#009E73", "warning": "#DDCC77", "critical": "#AE3030"}
STATUS_LABELS = {"good": "GOOD", "warning": "WARNING", "critical": "CRITICAL"}
STATUS_TEXT = {"good": "white", "warning": "#1A1A17", "critical": "white"}
LOWER_IS_BETTER = {"CPU Usage", "Memory", "Response Time", "Error Rate"}  # a rise in these is unfavorable
GRID_COLUMNS = 3

# Columns: set these to your table's column names
METRIC = "Metric"  # role: metric_name
VALUE = "Current value"  # role: current_value
UNIT = "Unit"  # role: extra
STEP = "Period"  # role: extra
READING = "Reading"  # role: history
CHANGE = "Change (%)"  # role: change_percent
STATUS = "Status"  # role: status

# Data: replace this block with your own table, for example df = pd.read_csv("metrics.csv")
np.random.seed(42)
samples = [
    # name, current value, unit, step scale, change %, status
    ("CPU Usage", 45, "%", 1.0, -5.2, "good"),
    ("Memory", 72, "%", 0.8, 8.1, "warning"),
    ("Response Time", 120, "ms", 5, -15.3, "good"),
    ("Requests/s", 2450, "", 25, 12.7, "good"),
    ("Error Rate", 2.3, "%", 0.08, 45.0, "critical"),
    ("Disk I/O", 156, "MB/s", 4, -3.8, "good"),
]
rows = []
for name, value, unit, scale, change, status in samples:
    # The history ends at the current value; the last period's move matches the change percent
    previous = value / (1 + change / 100)
    walk = np.cumsum(np.random.randn(29) * scale)
    history = np.append(previous + walk - walk[-1], value)
    for step, reading in enumerate(history):
        rows.append((name, value, unit, step, reading, change, status))
df = pd.DataFrame(rows, columns=[METRIC, VALUE, UNIT, STEP, READING, CHANGE, STATUS])

# Plot: 3-column grid of dashboard tiles, one per metric
tiles = df.groupby(METRIC, sort=False)
n_rows = -(-len(tiles) // GRID_COLUMNS)
fig, axes = plt.subplots(n_rows, GRID_COLUMNS, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG, squeeze=False)
fig.subplots_adjust(left=0.04, right=0.96, top=0.88, bottom=0.04, wspace=0.18, hspace=0.25)

fig.suptitle(
    "dashboard-metrics-tiles · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.96
)

for ax in axes.flat[len(tiles) :]:
    ax.axis("off")

for i, (ax, (name, rows_m)) in enumerate(zip(axes.flat, tiles, strict=False)):
    first = rows_m.iloc[0]
    status = first[STATUS]
    status_color = STATUS_COLORS.get(status, IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)])

    ax.set_facecolor(ELEVATED_BG)
    for spine in ax.spines.values():
        spine.set_color(INK_SOFT)
        spine.set_linewidth(0.8)
    ax.set_xticks([])
    ax.set_yticks([])

    # Status bar at top with accessibility text label
    status_ax = ax.inset_axes([0, 0.91, 1, 0.09])
    status_ax.set_facecolor(status_color)
    status_ax.set_xticks([])
    status_ax.set_yticks([])
    for spine in status_ax.spines.values():
        spine.set_visible(False)
    status_ax.text(
        0.5,
        0.5,
        STATUS_LABELS.get(status, str(status).upper()),
        ha="center",
        va="center",
        fontsize=8,
        fontweight="bold",
        color=STATUS_TEXT.get(status, "white"),
        transform=status_ax.transAxes,
    )

    # Metric name
    ax.text(0.5, 0.83, name, ha="center", va="top", fontsize=10, fontweight="bold", color=INK, transform=ax.transAxes)

    # Main value: the most prominent element
    ax.text(
        0.5,
        0.64,
        f"{first[VALUE]:g}{first[UNIT]}",
        ha="center",
        va="top",
        fontsize=16,
        fontweight="bold",
        color=INK,
        transform=ax.transAxes,
    )

    # Change indicator: arrow follows the sign, color follows whether the change is favorable
    change = first[CHANGE]
    favorable = (change < 0) == (name in LOWER_IS_BETTER)
    ax.text(
        0.5,
        0.44,
        f"{'▲' if change >= 0 else '▼'} {abs(change):.1f}%",
        ha="center",
        va="top",
        fontsize=12,
        fontweight="bold",
        color=STATUS_COLORS["good"] if favorable else STATUS_COLORS["critical"],
        transform=ax.transAxes,
    )

    # Sparkline scaled to its own range
    sparkline_ax = ax.inset_axes([0.08, 0.05, 0.84, 0.26])
    sparkline_ax.set_facecolor("none")
    x_vals = rows_m[STEP].to_numpy(dtype=float)
    history = rows_m[READING].to_numpy()
    sparkline_ax.fill_between(x_vals, history, alpha=0.3, color=status_color)
    sparkline_ax.plot(x_vals, history, linewidth=2.0, color=status_color)
    sparkline_ax.set_xlim(np.nanmin(x_vals), np.nanmax(x_vals))
    y_range = np.nanmax(history) - np.nanmin(history)
    sparkline_ax.set_ylim(np.nanmin(history) - 0.1 * y_range, np.nanmax(history) + 0.1 * y_range)
    sparkline_ax.axis("off")

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
