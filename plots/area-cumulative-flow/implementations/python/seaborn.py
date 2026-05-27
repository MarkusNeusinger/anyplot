""" anyplot.ai
area-cumulative-flow: Cumulative Flow Diagram for Workflow Analytics
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 86/100 | Created: 2026-05-07
"""

import os

import matplotlib.dates as mdates
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

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

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

# Data — 90-day Kanban board simulation
np.random.seed(42)
n_days = 90
dates = pd.date_range("2024-01-15", periods=n_days, freq="D")

# Cumulative items entering each stage (each stage lags and is capped by upstream)
arrivals = np.random.poisson(6, n_days)
backlog_cum = np.cumsum(arrivals).astype(float)

analysis_cum = np.minimum(backlog_cum, np.cumsum(np.random.poisson(5, n_days)).astype(float))
dev_cum = np.minimum(analysis_cum, np.cumsum(np.random.poisson(4, n_days)).astype(float))
testing_cum = np.minimum(dev_cum, np.cumsum(np.random.poisson(4, n_days)).astype(float))
done_cum = np.minimum(testing_cum, np.cumsum(np.random.poisson(4, n_days)).astype(float))

# WIP per stage: vertical band height = items currently in that stage
done_wip = done_cum
testing_wip = testing_cum - done_cum
dev_wip = dev_cum - testing_cum
analysis_wip = analysis_cum - dev_cum
backlog_wip = backlog_cum - analysis_cum

# Plot — stack from bottom (Done) to top (Backlog) per CFD convention
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

stage_labels = ["Done", "Testing", "Development", "Analysis", "Backlog"]
ax.stackplot(
    dates, done_wip, testing_wip, dev_wip, analysis_wip, backlog_wip, labels=stage_labels, colors=IMPRINT, alpha=0.85
)

# Style
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Cumulative Items", fontsize=20, color=INK)
ax.set_title("area-cumulative-flow · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)

ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Legend in visual order — Backlog at top matches its position in the chart
handles, labels = ax.get_legend_handles_labels()
ax.legend(
    handles[::-1],
    labels[::-1],
    loc="upper left",
    fontsize=16,
    framealpha=0.9,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    labelcolor=INK,
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
