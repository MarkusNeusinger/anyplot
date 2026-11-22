"""anyplot.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
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

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: x
SOURCE = "Energy source"  # role: category
SOURCES = ["Solar", "Wind", "Hydro", "Natural Gas"]  # role: y
LOWERS = ["Solar lower", "Wind lower", "Hydro lower", "Natural Gas lower"]  # role: y_lower
UPPERS = ["Solar upper", "Wind upper", "Hydro upper", "Natural Gas upper"]  # role: y_upper

# Data: replace this block with your own table, for example df = pd.read_csv("energy.csv")
# Quarterly energy consumption (TWh) by source; bounds are the 90% interval around each source's own value
np.random.seed(42)
n_quarters = 32
phase = np.linspace(0, 8 * np.pi, n_quarters)
ramp = np.linspace(0, 1, n_quarters)
solar = 20 + 40 * ramp + 8 * np.sin(phase)
wind = 35 + 30 * ramp + 12 * np.sin(phase + np.pi / 2)
hydro = 50 + 15 * np.sin(phase - np.pi / 4)
gas = 80 - 25 * ramp + 5 * np.random.randn(n_quarters)
spread = [3 + 5 * ramp, 5 + 6 * ramp, 4 + 2 * np.abs(np.sin(phase)), 6 + 4 * ramp]
centers = [solar, wind, hydro, gas]
columns = {QUARTER: pd.date_range(start="2016-01-01", periods=n_quarters, freq="QS")}
for name, lo, hi, c, w in zip(SOURCES, LOWERS, UPPERS, centers, spread, strict=True):
    columns.update({name: c, lo: c - w, hi: c + w})
df = pd.DataFrame(columns)

# Plot: reads only df and the constants above
df = df.set_index(QUARTER)
values, lower, upper = df[SOURCES], df[LOWERS], df[UPPERS]
lower.columns = upper.columns = SOURCES
stack = values.cumsum(axis=1)  # stacked central edge of each series
band_lo = stack - (values - lower)  # bands follow the stacked edge, same half-width as the series' own bounds
band_hi = stack + (upper - values)
base = stack.shift(axis=1, fill_value=0.0)  # top of the layer below; zero for the lowest series
x = values.index

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, name in enumerate(values.columns):
    color = IMPRINT_PALETTE[i]
    ax.fill_between(x, base[name], stack[name], color=color, alpha=0.85, label=name, zorder=3)
    ax.fill_between(x, band_lo[name], band_hi[name], color=color, alpha=0.25, linewidth=0, zorder=2)
    ax.plot(x, band_lo[name], color=color, linewidth=0.5, alpha=0.5, linestyle=":", zorder=1)
    ax.plot(x, band_hi[name], color=color, linewidth=0.5, alpha=0.5, linestyle=":", zorder=1)
    ax.plot(x, stack[name], color=color, linewidth=1.8, zorder=4, solid_capstyle="round")

# Style
title = "area-stacked-confidence · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(QUARTER, fontsize=10, color=INK)
ax.set_ylabel("Energy consumption (TWh)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_ylim(0, np.nanmax(band_hi.to_numpy()) * 1.05)
ax.margins(x=0)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.grid(True, alpha=0.1, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
fig.autofmt_xdate(rotation=45)

legend = ax.legend(
    loc="upper left", fontsize=8, framealpha=0.95, title=f"{SOURCE} (shaded: 90% CI bands)", title_fontsize=8
)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
legend.get_frame().set_linewidth(1)
for text in legend.get_texts():
    text.set_color(INK_SOFT)
legend.get_title().set_color(INK)

# Callout: the lowest layer, drawn only when it grew over the period
first, last = values.iloc[0, 0], values.iloc[-1, 0]
if last > first:
    mid = len(x) // 2
    ax.annotate(
        f"{values.columns[0]} up {last / first - 1:.0%}",
        xy=(x[mid], stack.iloc[mid, 0] * 0.5),
        xytext=(40, -4),
        textcoords="offset points",
        fontsize=8,
        color=INK,
        bbox={
            "boxstyle": "round,pad=0.4",
            "facecolor": ELEVATED_BG,
            "edgecolor": INK_SOFT,
            "alpha": 0.9,
            "linewidth": 0.8,
        },
        arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.0},
        zorder=6,
    )

fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.2)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
