"""anyplot.ai
campbell-basic: Campbell Diagram
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
ENGINE_ORDERS = [1, 2, 3]  # excitation orders drawn as lines from the origin

# Columns: set these to your table's column names
SPEED = "Rotational Speed (RPM)"  # role: speed
MODE_COLS = ["1st Bending", "2nd Bending", "1st Torsional", "Axial"]  # role: frequency_mode_
FREQUENCY = "Frequency (Hz)"  # role: extra
MODE = "Mode"  # role: extra
ENGINE_ORDER = "Engine order"  # role: engine_order
CRITICAL_SPEED = "Critical speed (RPM)"  # role: critical_speeds

# Data: replace this block with your own table, one row per speed and one column per mode
rpm = np.linspace(0, 6000, 100)
df = pd.DataFrame(
    {
        SPEED: rpm,
        MODE_COLS[0]: 15 + 0.0018 * rpm + 1.2 * np.sin(rpm / 1500),
        MODE_COLS[1]: 125 - 0.0025 * rpm + 0.8 * np.cos(rpm / 2000),
        MODE_COLS[2]: 52 + 0.0035 * rpm,
        MODE_COLS[3]: 140 - 0.0008 * rpm + 1.0 * np.sin(rpm / 1200),
    }
)

# Plot
clean = df.dropna()  # crossings need complete rows; a missing value stays a gap in the curves
speed = clean[SPEED].to_numpy()
speed_max = np.nanmax(df[SPEED].to_numpy())
n_modes = len(MODE_COLS)
mode_colors = IMPRINT_PALETTE[:n_modes]
long = df.melt(id_vars=SPEED, value_vars=MODE_COLS, var_name=MODE, value_name=FREQUENCY)

# Critical speeds: sign change of (mode - order line), linearly interpolated
crossings = []
for mode_name in MODE_COLS:
    for order in ENGINE_ORDERS:
        diff = clean[mode_name].to_numpy() - order * speed / 60
        for idx in np.where(np.diff(np.sign(diff)))[0]:
            t = abs(diff[idx]) / (abs(diff[idx]) + abs(diff[idx + 1]))
            cs_rpm = speed[idx] + t * (speed[idx + 1] - speed[idx])
            if speed_max / 60 < cs_rpm < speed_max * 59 / 60:
                crossings.append({CRITICAL_SPEED: cs_rpm, FREQUENCY: order * cs_rpm / 60, ENGINE_ORDER: order})
cs_df = pd.DataFrame(crossings, columns=[CRITICAL_SPEED, FREQUENCY, ENGINE_ORDER])

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
fig.set_facecolor(PAGE_BG)

# Natural frequency curves via seaborn lineplot with hue
sns.lineplot(
    data=long,
    x=SPEED,
    y=FREQUENCY,
    hue=MODE,
    hue_order=MODE_COLS,
    palette=mode_colors,
    linewidth=2.0,
    ax=ax,
    legend=False,
)

# Engine order lines (structural reference), labeled at fractions of the speed range
for order, label_frac in zip(ENGINE_ORDERS, [0.77, 0.22, 0.12], strict=False):
    ax.plot(speed, order * speed / 60, color=INK_SOFT, linewidth=1.2, linestyle="--", alpha=0.65, zorder=2)
    lx = label_frac * speed_max
    ax.text(
        lx,
        order * lx / 60 + 1.5,
        f"{order}x",
        fontsize=8,
        color=INK_SOFT,
        fontweight="bold",
        va="bottom",
        ha="center",
        bbox={"boxstyle": "round,pad=0.12", "fc": ELEVATED_BG, "ec": INK_SOFT, "alpha": 0.85, "linewidth": 0.5},
    )

# Critical speed markers via seaborn scatterplot (ink fill, a colour no mode curve uses)
sns.scatterplot(
    data=cs_df,
    x=CRITICAL_SPEED,
    y=FREQUENCY,
    color=INK,
    s=70,
    ax=ax,
    zorder=5,
    edgecolor=PAGE_BG,
    linewidth=0.8,
    legend=False,
)

# Axes limits
y_max = np.nanmax(df[MODE_COLS].to_numpy())
ax.set_xlim(0, speed_max)
ax.set_ylim(0, y_max * 1.05)

# Direct mode labels at the right edge, pushed apart so neighbours never touch
end_freq = df[MODE_COLS].ffill().iloc[-1]
order_by_freq = end_freq.sort_values().index
min_gap = 0.075 * y_max
label_y = {}
previous = -np.inf
for name in order_by_freq:
    label_y[name] = max(end_freq[name], previous + min_gap)
    previous = label_y[name]
for i, name in enumerate(MODE_COLS):
    ax.text(
        speed_max * 1.013,
        label_y[name],
        name,
        fontsize=8,
        color=mode_colors[i],
        fontweight="bold",
        va="center",
        ha="left",
        clip_on=False,
    )

title = "campbell-basic · python · seaborn · anyplot.ai"
title_fontsize = max(8, round(12 * (67 / len(title) if len(title) > 67 else 1.0)))

ax.set_xlabel(SPEED, fontsize=10, color=INK)
ax.set_ylabel(FREQUENCY, fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8)
ax.grid(True, axis="both", alpha=0.12, linewidth=0.5, color=INK)
ax.set_axisbelow(True)
sns.despine(ax=ax)

# Legend below the axes: curves vs engine order lines vs critical speeds
legend_handles = [
    Line2D([0], [0], color=INK_SOFT, linewidth=2.0, label="Natural frequency mode"),
    Line2D([0], [0], color=INK_SOFT, linewidth=1.2, linestyle="--", label="Engine order line"),
    Line2D(
        [0],
        [0],
        marker="o",
        linestyle="none",
        markerfacecolor=INK,
        markeredgecolor=PAGE_BG,
        markersize=7,
        label="Critical speed",
    ),
]
fig.legend(
    handles=legend_handles,
    fontsize=8,
    loc="lower center",
    bbox_to_anchor=(0.5, 0.015),
    ncol=len(legend_handles),
    frameon=True,
    fancybox=False,
    framealpha=0.9,
    columnspacing=1.2,
    handlelength=1.8,
)

fig.subplots_adjust(left=0.08, right=0.80, top=0.92, bottom=0.2)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400)
