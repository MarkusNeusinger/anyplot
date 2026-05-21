"""anyplot.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-05-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
TILE_BORDER = "#D5D4CD" if THEME == "light" else "#3A3936"

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

# Data
np.random.seed(42)

# Status colors — Okabe-Ito positions 3 (blue), 5 (orange), 4 (reddish-purple)
# Blue/orange/purple avoids red-green distinction issues for colorblind viewers
status_colors = {"good": "#0072B2", "warning": "#E69F00", "critical": "#CC79A7"}

metrics = [
    {
        "name": "CPU Usage",
        "value": 45,
        "unit": "%",
        "history": np.cumsum(np.random.randn(30)) + 50,
        "change": -5.2,
        "status": "good",
    },
    {
        "name": "Memory",
        "value": 72,
        "unit": "%",
        "history": np.cumsum(np.random.randn(30)) + 70,
        "change": 8.1,
        "status": "warning",
    },
    {
        "name": "Response Time",
        "value": 120,
        "unit": "ms",
        "history": np.cumsum(np.random.randn(30)) + 130,
        "change": -15.3,
        "status": "good",
    },
    {
        "name": "Active Users",
        "value": 1847,
        "unit": "",
        "history": np.cumsum(np.random.randn(30)) * 50 + 1800,
        "change": 12.7,
        "status": "good",
    },
    {
        "name": "Error Rate",
        "value": 2.3,
        "unit": "%",
        "history": np.cumsum(np.random.randn(30)) * 0.5 + 2,
        "change": 45.0,
        "status": "critical",
    },
    {
        "name": "Throughput",
        "value": 892,
        "unit": "req/s",
        "history": np.cumsum(np.random.randn(30)) * 30 + 850,
        "change": -3.4,
        "status": "good",
    },
]

# Plot — canonical landscape canvas: figsize=(8, 4.5) @ dpi=400 → 3200×1800 px
fig, axes = plt.subplots(2, 3, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
axes = axes.flatten()

for ax, metric in zip(axes, metrics, strict=True):
    ax.set_facecolor(ELEVATED_BG)
    for spine in ax.spines.values():
        spine.set_color(TILE_BORDER)
        spine.set_linewidth(1.5)

    # Sparkline inset — seaborn lineplot in bottom quarter of tile
    inset_ax = ax.inset_axes([0.1, 0.08, 0.8, 0.25])
    inset_ax.set_facecolor(ELEVATED_BG)

    history = metric["history"]
    spark_df = pd.DataFrame({"time": np.arange(len(history)), "value": history})

    sns.lineplot(data=spark_df, x="time", y="value", ax=inset_ax, color=status_colors[metric["status"]], linewidth=1.5)
    inset_ax.fill_between(
        spark_df["time"], spark_df["value"].min(), spark_df["value"], color=status_colors[metric["status"]], alpha=0.2
    )
    inset_ax.set_xticks([])
    inset_ax.set_yticks([])
    inset_ax.set_xlabel("")
    inset_ax.set_ylabel("")
    for spine in inset_ax.spines.values():
        spine.set_visible(False)

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.grid(False)

    # Metric name (top)
    ax.text(5, 9.3, metric["name"], fontsize=10, fontweight="bold", color=INK_SOFT, ha="center", va="top")

    # Main KPI value (center, prominent)
    value_text = f"{metric['value']:,}{metric['unit']}" if metric["unit"] else f"{metric['value']:,}"
    ax.text(
        5,
        6.2,
        value_text,
        fontsize=26,
        fontweight="bold",
        color=status_colors[metric["status"]],
        ha="center",
        va="center",
    )

    # Change indicator with directional arrow
    change = metric["change"]
    arrow = "▲" if change >= 0 else "▼"

    # Lower is better for operational metrics; higher is better for usage/throughput
    decrease_is_good = metric["name"] in ["CPU Usage", "Memory", "Response Time", "Error Rate"]
    if decrease_is_good:
        change_color = "#0072B2" if change < 0 else "#CC79A7"
    else:
        change_color = "#0072B2" if change >= 0 else "#CC79A7"

    ax.text(
        5,
        4.0,
        f"{arrow} {abs(change):.1f}%",
        fontsize=10,
        fontweight="bold",
        color=change_color,
        ha="center",
        va="center",
    )

# Style
fig.suptitle(
    "dashboard-metrics-tiles · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.98
)

plt.tight_layout(rect=[0, 0, 1, 0.95])

# Save — no bbox_inches so figsize×dpi stays exactly 3200×1800
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
