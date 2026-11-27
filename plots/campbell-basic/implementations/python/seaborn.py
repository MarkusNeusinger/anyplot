"""anyplot.ai
campbell-basic: Campbell Diagram
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-28
"""

import os

import matplotlib.patches as mpatches
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
ANYPLOT_AMBER = "#DDCC77"

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
OPERATING_RANGE = (2800, 4200)  # RPM band of normal operation

# Columns: set these to your table's column names
SPEED = "Rotational Speed (RPM)"  # role: speed
MODE_COLS = ["1st Bending", "2nd Bending", "1st Torsional", "Axial", "3rd Bending"]  # role: frequency_mode_
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
        MODE_COLS[1]: 44 - 0.0025 * rpm + 0.8 * np.cos(rpm / 2000),
        MODE_COLS[2]: 52 + 0.0035 * rpm,
        MODE_COLS[3]: 68 - 0.0008 * rpm + 1.0 * np.sin(rpm / 1200),
        MODE_COLS[4]: 82 + 0.0022 * rpm + 0.6 * np.sin(rpm / 1800),
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
op_low, op_high = OPERATING_RANGE
cs_in_df = cs_df[cs_df[CRITICAL_SPEED].between(op_low, op_high)]
cs_out_df = cs_df.drop(cs_in_df.index)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
fig.set_facecolor(PAGE_BG)

# Operating range highlight (amber = caution)
x_axis_tf = ax.get_xaxis_transform()
ax.axvspan(op_low, op_high, color=ANYPLOT_AMBER, alpha=0.10, zorder=0)
ax.axvline(op_low, color=ANYPLOT_AMBER, linewidth=0.8, linestyle="--", alpha=0.6, zorder=1)
ax.axvline(op_high, color=ANYPLOT_AMBER, linewidth=0.8, linestyle="--", alpha=0.6, zorder=1)
ax.text(
    (op_low + op_high) / 2,
    0.03,
    "Operating\nRange",
    transform=x_axis_tf,
    fontsize=7,
    color=ANYPLOT_AMBER,
    ha="center",
    va="bottom",
    fontweight="bold",
    linespacing=1.3,
)

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
for order, label_frac in zip(ENGINE_ORDERS, [0.77, 0.37, 0.23], strict=False):
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

# Critical speed markers via seaborn scatterplot (split by status for independent alpha)
sns.scatterplot(
    data=cs_in_df,
    x=CRITICAL_SPEED,
    y=FREQUENCY,
    color=IMPRINT_PALETTE[4],
    s=120,
    ax=ax,
    zorder=5,
    edgecolor=PAGE_BG,
    linewidth=0.8,
    legend=False,
)
sns.scatterplot(
    data=cs_out_df,
    x=CRITICAL_SPEED,
    y=FREQUENCY,
    color=INK_MUTED,
    s=30,
    alpha=0.7,
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

# Legend below the axes: curves vs engine order lines, critical speed status, operating range
legend_handles = [
    Line2D([0], [0], color=INK, linewidth=2.0, label="Natural frequency mode"),
    Line2D([0], [0], color=INK_SOFT, linewidth=1.2, linestyle="--", label="Engine order line"),
    mpatches.Patch(facecolor=IMPRINT_PALETTE[4], label="Critical (in range)"),
    mpatches.Patch(facecolor=INK_MUTED, label="Critical (outside)"),
    mpatches.Patch(facecolor=ANYPLOT_AMBER, alpha=0.45, label=f"Operating ({op_low}–{op_high} RPM)"),
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
