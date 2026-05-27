""" anyplot.ai
area-cumulative-flow: Cumulative Flow Diagram for Workflow Analytics
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Created: 2026-05-07
"""

import sys


# Prevent this file from shadowing the installed matplotlib package when run
# from its own directory (sys.path[0] would otherwise resolve to this file).
sys.path.pop(0)

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito positions 1-5 (bottom to top: Done → Backlog)
COLORS = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data: 90-day software Kanban board simulation
np.random.seed(42)
n_days = 90
dates = pd.date_range("2024-01-02", periods=n_days, freq="D")
t = np.arange(n_days)

# Build cumulative counts from Done upward; each layer stacks WIP above the previous
# Done: S-curve — accelerates through the sprint
done_raw = 120 * (1 / (1 + np.exp(-(t - 55) / 12)))
done_raw -= done_raw[0]
done = np.maximum.accumulate(np.maximum(np.round(done_raw + np.random.normal(0, 1.5, n_days)).astype(int), 0))

# Testing: widens as a bottleneck builds from day 15-60, then drains
wip_testing = np.zeros(n_days)
wip_testing[15:60] = np.linspace(0, 28, 45) + np.random.normal(0, 1.5, 45)
wip_testing[60:] = np.linspace(28, 12, n_days - 60) + np.random.normal(0, 1.0, n_days - 60)
wip_testing = np.round(np.maximum(wip_testing, 0)).astype(int)
testing = np.maximum.accumulate(done + wip_testing)

# Development: steady ~14 items, slight oscillation
wip_dev = np.round(14 + 4 * np.sin(2 * np.pi * t / 28) + np.random.normal(0, 1.5, n_days)).astype(int)
wip_dev[:12] = np.round(np.linspace(0, 14, 12)).astype(int)
wip_dev = np.maximum(wip_dev, 2)
development = np.maximum.accumulate(testing + wip_dev)

# Analysis: small buffer of ~8 items
wip_analysis = np.round(8 + np.random.normal(0, 1.2, n_days)).astype(int)
wip_analysis[:7] = np.round(np.linspace(0, 8, 7)).astype(int)
wip_analysis = np.maximum(wip_analysis, 1)
analysis = np.maximum.accumulate(development + wip_analysis)

# Backlog: grows as new work arrives faster than it's pulled
wip_backlog = np.round(22 + np.linspace(0, 12, n_days) + np.random.normal(0, 2.0, n_days)).astype(int)
wip_backlog[:5] = np.round(np.linspace(5, 22, 5)).astype(int)
wip_backlog = np.maximum(wip_backlog, 5)
backlog = np.maximum.accumulate(analysis + wip_backlog)

# Layer contributions (bottom to top in stackplot order)
c_done = done.astype(float)
c_testing = np.maximum(testing - done, 0).astype(float)
c_development = np.maximum(development - testing, 0).astype(float)
c_analysis = np.maximum(analysis - development, 0).astype(float)
c_backlog = np.maximum(backlog - analysis, 0).astype(float)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

stage_labels = ["Done", "Testing", "Development", "Analysis", "Backlog"]

ax.stackplot(
    dates, c_done, c_testing, c_development, c_analysis, c_backlog, labels=stage_labels, colors=COLORS, alpha=0.88
)

# Style
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Cumulative Items", fontsize=20, color=INK)
ax.set_title(
    "Sprint Kanban Board · area-cumulative-flow · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK
)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, length=0)

# X-axis: bi-weekly date ticks
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
plt.setp(ax.get_xticklabels(), rotation=30, ha="right", color=INK_SOFT)
plt.setp(ax.get_yticklabels(), color=INK_SOFT)

ax.set_xlim(dates[0], dates[-1])

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Grid (y-axis only, subtle)
ax.yaxis.grid(True, alpha=0.13, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Shaded region highlighting Testing bottleneck buildup (days 15–60)
ax.axvspan(dates[15], dates[60], alpha=0.07, color=COLORS[1], zorder=0)
mid_bottleneck = dates[15] + (dates[60] - dates[15]) / 2
ax.annotate(
    "Testing Bottleneck",
    xy=(mid_bottleneck, 0.52),
    xycoords=("data", "axes fraction"),
    ha="center",
    va="center",
    fontsize=15,
    color=INK_MUTED,
    style="italic",
)

# Legend — reversed so Backlog appears at top, matching visual stacking order
handles, labels = ax.get_legend_handles_labels()
leg = ax.legend(handles[::-1], labels[::-1], loc="upper left", fontsize=16, framealpha=0.92)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"plot-{THEME}.png")
plt.savefig(_out, dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
