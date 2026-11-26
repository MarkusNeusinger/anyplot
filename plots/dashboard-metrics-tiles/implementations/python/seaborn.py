"""anyplot.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 88/100 | Updated: 2026-11-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Rectangle


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
TILE_BORDER = "#D5D4CD" if THEME == "light" else "#3A3936"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
# Status colors: Imprint green (good), amber anchor (warning), Imprint red (critical)
STATUS_COLORS = {"good": IMPRINT_PALETTE[0], "warning": "#DDCC77", "critical": IMPRINT_PALETTE[4]}
UNFAVORABLE = IMPRINT_PALETTE[4]  # a change that moves the wrong way
N_COLS = 3  # tiles per row

# Columns: set these to your table's column names
METRIC = "Metric"  # role: metric_name
CURRENT = "Current value"  # role: current_value
PERIOD = "Period"  # role: extra
HISTORY = "History"  # role: history
CHANGE = "Change (%)"  # role: change_percent
STATUS = "Status"  # role: status
UNIT = "Unit"  # role: extra
LOWER_IS_BETTER = "Lower is better"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("metrics.csv")
# Energy-grid control room snapshot: one row per metric and history point
rng = np.random.default_rng(7)
# (name, current value, unit, change %, status, lower is better, relative volatility)
grid_metrics = [
    ("Grid Load", 41.2, " GW", 9.1, "warning", True, 0.015),
    ("Renewable Share", 46.5, "%", 6.8, "good", False, 0.03),
    ("Reserve Margin", 4.1, "%", -18.5, "critical", False, 0.06),
    ("Battery Storage", 78.0, "%", 3.2, "good", False, 0.02),
    ("Spot Price", 87.4, " €/MWh", 14.2, "warning", True, 0.04),
    ("CO₂ Intensity", 212.0, " g/kWh", -6.3, "good", True, 0.025),
]
rows = []
for name, current, unit, change, status, lower_better, volatility in grid_metrics:
    walk = np.cumsum(rng.standard_normal(30))
    history = current * (1 + volatility * (walk - walk[-1]) / walk.std())  # ends at the current value
    for period, reading in enumerate(history):
        rows.append(
            {
                METRIC: name,
                CURRENT: current,
                PERIOD: period,
                HISTORY: reading,
                CHANGE: change,
                STATUS: status,
                UNIT: unit,
                LOWER_IS_BETTER: lower_better,
            }
        )
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
tiles = list(df.groupby(METRIC, sort=False))
n_rows = -(-len(tiles) // N_COLS)

fig, axes = plt.subplots(n_rows, N_COLS, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG, squeeze=False)

for i, (ax, (name, tile)) in enumerate(zip(axes.flat, tiles, strict=False)):
    first = tile.iloc[0]
    status_color = STATUS_COLORS.get(first[STATUS], IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)])
    change = first[CHANGE]
    favorable = (change < 0) == bool(first[LOWER_IS_BETTER])
    change_color = IMPRINT_PALETTE[0] if favorable else UNFAVORABLE

    ax.set_facecolor(ELEVATED_BG)
    for spine in ax.spines.values():
        spine.set_color(TILE_BORDER)
        spine.set_linewidth(1.5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)

    # Status stripe along the top edge of every tile
    ax.add_patch(Rectangle((0, 0.93), 1, 0.07, transform=ax.transAxes, color=status_color, clip_on=True, zorder=2))

    # Metric label (left) and status word (right)
    ax.text(
        0.07, 0.84, name, fontsize=10, fontweight="bold", color=INK_SOFT, ha="left", va="center", transform=ax.transAxes
    )
    ax.text(
        0.93,
        0.84,
        first[STATUS].upper(),
        fontsize=6.5,
        fontweight="bold",
        color=INK_SOFT,
        ha="right",
        va="center",
        transform=ax.transAxes,
    )

    # Main KPI value
    ax.text(
        0.07,
        0.62,
        f"{first[CURRENT]:,g}{first[UNIT]}",
        fontsize=19,
        fontweight="bold",
        color=INK,
        ha="left",
        va="center",
        transform=ax.transAxes,
    )

    # Change indicator: arrow follows the sign, color follows favorable / unfavorable
    arrow = "▲" if change >= 0 else "▼"
    ax.text(
        0.07,
        0.43,
        f"{arrow} {abs(change):.1f}%",
        fontsize=10,
        fontweight="bold",
        color=change_color,
        ha="left",
        va="center",
        transform=ax.transAxes,
    )

    # Sparkline inset: seaborn lineplot on the tile's own history, scaled to its own range
    inset_ax = ax.inset_axes([0.07, 0.07, 0.86, 0.26])
    inset_ax.set_facecolor(ELEVATED_BG)
    sns.lineplot(data=tile, x=PERIOD, y=HISTORY, ax=inset_ax, color=status_color, linewidth=1.8)
    inset_ax.fill_between(tile[PERIOD], tile[HISTORY].min(), tile[HISTORY], color=status_color, alpha=0.4)
    inset_ax.set_xlim(tile[PERIOD].min(), tile[PERIOD].max())
    inset_ax.set_xticks([])
    inset_ax.set_yticks([])
    inset_ax.set_xlabel("")
    inset_ax.set_ylabel("")
    sns.despine(ax=inset_ax, left=True, bottom=True, top=True, right=True)

# Style
fig.suptitle(
    "dashboard-metrics-tiles · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.985
)

plt.tight_layout(rect=[0, 0, 1, 0.985])
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
