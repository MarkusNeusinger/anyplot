""" anyplot.ai
campbell-basic: Campbell Diagram
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
ANYPLOT_AMBER = "#DDCC77"  # warning / caution — semantic anchor for critical condition

# Imprint palette: all eight positions, one per mode in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
ENGINE_ORDERS = [1, 2, 3]  # excitation orders drawn as lines from the origin

# Columns: set these to your table's column names
SPEED = "Rotational Speed (RPM)"  # role: speed
MODES = ["1st Bending", "2nd Bending", "1st Torsional", "Axial", "3rd Bending"]  # role: frequency_mode_
ENGINE_ORDER = "Engine Order"  # role: engine_order
CRITICAL_SPEED = "Critical Speed"  # role: critical_speeds
FREQUENCY_AXIS = "Frequency (Hz)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("modes.csv")
rpm = np.linspace(0, 4000, 200)
df = pd.DataFrame(
    {
        SPEED: rpm,
        MODES[0]: 40 + 0.004 * rpm - 2.0e-7 * rpm**2,
        MODES[1]: 80 - 0.0025 * rpm + 1.0e-7 * rpm**2,
        MODES[2]: 105 + 0.0008 * rpm,
        MODES[3]: 145 - 0.006 * rpm + 5.0e-7 * rpm**2,
        MODES[4]: 170 + 0.006 * rpm - 4.0e-7 * rpm**2,
    }
)

# Plot: reads only df and the constants above
speed_rpm = df[SPEED].to_numpy()
speed_hz = speed_rpm / 60
mode_labels = list(MODES)
modes = [df[m].to_numpy() for m in mode_labels]
x_max = np.nanmax(speed_rpm)
y_max = np.ceil(np.nanmax(modes) * 1.05 / 20) * 20

# Critical speeds: where an engine order line crosses a mode curve (linear interpolation)
critical_speeds, critical_freqs = [], []
for mode in modes:
    for eo in ENGINE_ORDERS:
        diff = mode - eo * speed_hz
        for idx in np.where(np.diff(np.sign(diff)))[0]:
            t = abs(diff[idx]) / (abs(diff[idx]) + abs(diff[idx + 1]))
            critical_speeds.append(speed_rpm[idx] + t * (speed_rpm[idx + 1] - speed_rpm[idx]))
            critical_freqs.append(mode[idx] + t * (mode[idx + 1] - mode[idx]))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Mode curves
for i, mode in enumerate(modes):
    ax.plot(speed_rpm, mode, linewidth=2.5, color=IMPRINT_PALETTE[i], zorder=3, solid_capstyle="round")

# End-of-line labels, spaced apart vertically
end_vals = [
    (mode[-1], label, IMPRINT_PALETTE[i]) for i, (mode, label) in enumerate(zip(modes, mode_labels, strict=False))
]
end_vals.sort(key=lambda v: v[0])
min_gap = 0.05 * y_max
positions = [v[0] for v in end_vals]
for i in range(1, len(positions)):
    if positions[i] - positions[i - 1] < min_gap:
        positions[i] = positions[i - 1] + min_gap
for y_pos, (_, label, color) in zip(positions, end_vals, strict=False):
    ax.annotate(
        label,
        xy=(x_max, y_pos),
        xytext=(6, 0),
        textcoords="offset points",
        fontsize=8,
        color=color,
        fontweight="bold",
        va="center",
        zorder=4,
        annotation_clip=False,
    )

# Engine order lines with labels rotated to the line's angle in data space
for eo in ENGINE_ORDERS:
    eo_line = eo * speed_hz
    visible = eo_line <= y_max
    ax.plot(
        speed_rpm[visible], eo_line[visible], linewidth=1.5, color=INK_SOFT, linestyle=(0, (8, 4)), alpha=0.7, zorder=2
    )
    target_freq = y_max * 0.13
    target_rpm = target_freq * 60 / eo
    if target_rpm < 0.967 * x_max:
        ax.annotate(
            f"{eo}×",
            xy=(target_rpm, target_freq),
            fontsize=9,
            color=INK_SOFT,
            fontweight="bold",
            ha="center",
            va="bottom",
            rotation=np.degrees(np.arctan(eo / 60)),
            transform_rotates_text=True,
            rotation_mode="anchor",
            zorder=4,
            bbox={"boxstyle": "round,pad=0.15", "facecolor": ELEVATED_BG, "edgecolor": "none", "alpha": 0.85},
        )

# Critical speed markers
ax.scatter(
    critical_speeds, critical_freqs, s=100, color=ANYPLOT_AMBER, edgecolors=INK, linewidth=1.0, zorder=6, marker="D"
)

# Style
title = "campbell-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

ax.set_xlabel(SPEED, fontsize=10, color=INK)
ax.set_ylabel(FREQUENCY_AXIS, fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=10)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))

for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_linewidth(0.6)
    ax.spines[spine].set_color(INK_SOFT)

ax.set_xlim(np.nanmin(speed_rpm), x_max)
ax.set_ylim(0, y_max)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK)
ax.set_axisbelow(True)

# Legend below the axes, clear of every curve and marker
eo_handle = Line2D([0], [0], color=INK_SOFT, linewidth=1.5, linestyle=(0, (8, 4)), alpha=0.7)
crit_handle = Line2D(
    [0], [0], marker="D", color="none", markerfacecolor=ANYPLOT_AMBER, markeredgecolor=INK, markersize=7
)
handles = [Line2D([0], [0], color=IMPRINT_PALETTE[i], linewidth=2.5) for i in range(len(modes))] + [
    eo_handle,
    crit_handle,
]
legend_labels = mode_labels + [f"{ENGINE_ORDER} ({min(ENGINE_ORDERS)}×–{max(ENGINE_ORDERS)}×)", CRITICAL_SPEED]

leg = ax.legend(
    handles,
    legend_labels,
    fontsize=8,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.17),
    ncol=7,
    framealpha=0.92,
    edgecolor=INK_SOFT,
    borderpad=0.5,
    handlelength=1.4,
    columnspacing=1.0,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.09, right=0.86, top=0.91, bottom=0.22)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
