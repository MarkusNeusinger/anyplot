""" anyplot.ai
line-navigator: Line Chart with Mini Navigator
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-27
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

BRAND = "#009E73"  # anyplot palette position 1 — always first series
SELECTION = "#BD8233"  # anyplot palette position 4 — ochre, selection window edges

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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data — production server CPU utilization over 2 years (daily averages)
np.random.seed(42)
dates = pd.date_range("2023-01-01", periods=730, freq="D")

trend = np.linspace(0, 10, 730)
weekly_cycle = 6 * np.sin(2 * np.pi * np.arange(730) / 7)
seasonal = 5 * np.cos(2 * np.pi * np.arange(730) / 365)
spikes = np.random.exponential(scale=3, size=730) * (np.random.rand(730) < 0.05)
noise = np.random.randn(730) * 3
cpu = np.clip(32 + trend + weekly_cycle + seasonal + spikes + noise, 8, 95)

df = pd.DataFrame({"date": dates, "cpu_pct": cpu})

# Selection: 3-month window in the second year
start_idx, end_idx = 450, 545
selected_start = dates[start_idx]
selected_end = dates[end_idx]
df_selected = df[(df["date"] >= selected_start) & (df["date"] <= selected_end)]

# Figure layout: main detail chart (80%) + slim navigator (20%)
fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
gs = fig.add_gridspec(2, 1, height_ratios=[4, 1], hspace=0.30, left=0.09, right=0.97, top=0.90, bottom=0.11)
ax_main = fig.add_subplot(gs[0])
ax_nav = fig.add_subplot(gs[1])

# Main chart — detail view of selected range
ax_main.set_facecolor(PAGE_BG)
sns.lineplot(data=df_selected, x="date", y="cpu_pct", ax=ax_main, linewidth=2.0, color=BRAND)
ax_main.set_xlabel("")
ax_main.set_ylabel("CPU Usage (%)", fontsize=10, color=INK)
ax_main.set_title("line-navigator · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax_main.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax_main.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax_main.set_axisbelow(True)
ax_main.spines["top"].set_visible(False)
ax_main.spines["right"].set_visible(False)
ax_main.spines["left"].set_color(INK_SOFT)
ax_main.spines["bottom"].set_color(INK_SOFT)
ax_main.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax_main.xaxis.set_major_locator(mdates.MonthLocator())

date_label = f"{selected_start.strftime('%b %Y')} – {selected_end.strftime('%b %Y')}"
ax_main.text(0.98, 0.97, date_label, transform=ax_main.transAxes, fontsize=8, color=INK_MUTED, va="top", ha="right")

# Navigator — full 2-year overview
ax_nav.set_facecolor(PAGE_BG)
sns.lineplot(data=df, x="date", y="cpu_pct", ax=ax_nav, linewidth=0.8, color=BRAND, alpha=0.6)
# Shade non-selected regions
ax_nav.axvspan(dates[0], selected_start, color=INK_MUTED, alpha=0.25, zorder=1)
ax_nav.axvspan(selected_end, dates[-1], color=INK_MUTED, alpha=0.25, zorder=1)
# Subtle fill inside selection window
ax_nav.axvspan(selected_start, selected_end, color=BRAND, alpha=0.08, zorder=2)
# Selection edge markers (resize handles)
ax_nav.axvline(x=selected_start, color=SELECTION, linewidth=1.5, zorder=3)
ax_nav.axvline(x=selected_end, color=SELECTION, linewidth=1.5, zorder=3)

ax_nav.set_xlabel("Date", fontsize=10, color=INK)
ax_nav.set_ylabel("")
ax_nav.tick_params(axis="x", labelsize=7, colors=INK_SOFT)
ax_nav.set_yticks([])
ax_nav.spines["top"].set_visible(False)
ax_nav.spines["right"].set_visible(False)
ax_nav.spines["left"].set_visible(False)
ax_nav.spines["bottom"].set_color(INK_SOFT)
ax_nav.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax_nav.xaxis.set_major_locator(mdates.YearLocator())

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
