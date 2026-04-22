""" pyplots.ai
campbell-basic: Campbell Diagram
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-02-15
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter


# Data
speed_rpm = np.linspace(0, 6000, 200)
speed_hz = speed_rpm / 60

# Natural frequency modes (Hz) - realistic gyroscopic effects
mode_1_bending = 18 + 0.004 * speed_rpm - 1.5e-7 * speed_rpm**2
mode_2_bending = 48 - 0.003 * speed_rpm + 2.0e-7 * speed_rpm**2
mode_1_torsional = 58 + 0.0004 * speed_rpm
mode_axial = 78 - 0.005 * speed_rpm + 4.0e-7 * speed_rpm**2
mode_3_bending = 92 + 0.005 * speed_rpm - 3.5e-7 * speed_rpm**2

modes = [mode_1_bending, mode_2_bending, mode_1_torsional, mode_axial, mode_3_bending]
mode_labels = ["1st Bending", "2nd Bending", "1st Torsional", "Axial", "3rd Bending"]
mode_colors = ["#306998", "#E8833A", "#2B9EB3", "#984EA3", "#A65628"]

engine_orders = [1, 2, 3]
eo_freq = {eo: eo * speed_hz for eo in engine_orders}

# Find critical speed intersections via sign changes
op_min, op_max = 2500, 4500
critical_speeds, critical_freqs, critical_mlabels = [], [], []
for mode, mlabel in zip(modes, mode_labels, strict=True):
    for eo in engine_orders:
        diff = mode - eo * speed_hz
        for idx in np.where(np.diff(np.sign(diff)))[0]:
            t = abs(diff[idx]) / (abs(diff[idx]) + abs(diff[idx + 1]))
            rpm = speed_rpm[idx] + t * (speed_rpm[idx + 1] - speed_rpm[idx])
            freq = mode[idx] + t * (mode[idx + 1] - mode[idx])
            if 100 < rpm < 5900:
                critical_speeds.append(rpm)
                critical_freqs.append(freq)
                critical_mlabels.append(mlabel)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
y_max = 120

# Operating range shading
ax.axvspan(op_min, op_max, alpha=0.07, color="#306998", zorder=0)
ax.axvline(op_min, color="#306998", linewidth=1.2, linestyle=":", alpha=0.5, zorder=1)
ax.axvline(op_max, color="#306998", linewidth=1.2, linestyle=":", alpha=0.5, zorder=1)
ax.text(
    (op_min + op_max) / 2,
    3,
    "Operating Range",
    fontsize=13,
    color="#306998",
    ha="center",
    va="bottom",
    fontstyle="italic",
    alpha=0.6,
)

# Mode curves
for mode, _label, color in zip(modes, mode_labels, mode_colors, strict=True):
    ax.plot(speed_rpm, mode, linewidth=2.8, color=color, zorder=3, solid_capstyle="round")

# End-of-line labels with vertical de-collision
end_vals = [(mode[-1], label, color) for mode, label, color in zip(modes, mode_labels, mode_colors, strict=True)]
end_vals.sort(key=lambda x: x[0])
min_gap = 4.5  # minimum Hz gap between adjacent labels
positions = [v[0] for v in end_vals]
for i in range(1, len(positions)):
    if positions[i] - positions[i - 1] < min_gap:
        positions[i] = positions[i - 1] + min_gap
for y_pos, (_, label, color) in zip(positions, end_vals, strict=True):
    ax.annotate(
        label,
        xy=(speed_rpm[-1], y_pos),
        xytext=(8, 0),
        textcoords="offset points",
        fontsize=10,
        color=color,
        fontweight="bold",
        va="center",
        zorder=4,
    )

# Engine order lines with rotated labels
for eo in engine_orders:
    eo_line = eo_freq[eo]
    visible = eo_line <= y_max
    ax.plot(
        speed_rpm[visible], eo_line[visible], linewidth=1.8, color="#AAAAAA", linestyle=(0, (8, 4)), alpha=0.6, zorder=2
    )
    target_freq = y_max * 0.28
    target_rpm = target_freq * 60 / eo
    if target_rpm < 5800:
        slope_display = (eo / 60) * (9 / y_max) / (16 / 6000)
        angle_deg = np.degrees(np.arctan(slope_display))
        ax.annotate(
            f"{eo}×",
            xy=(target_rpm, target_freq),
            fontsize=14,
            color="#777777",
            fontweight="bold",
            ha="center",
            va="bottom",
            rotation=angle_deg,
            rotation_mode="anchor",
            zorder=4,
            bbox={"boxstyle": "round,pad=0.15", "facecolor": "white", "edgecolor": "none", "alpha": 0.8},
        )

# Critical speed markers
cs_arr, cf_arr = np.array(critical_speeds), np.array(critical_freqs)
in_op = (cs_arr >= op_min) & (cs_arr <= op_max)

if np.any(~in_op):
    ax.scatter(
        cs_arr[~in_op], cf_arr[~in_op], s=200, color="#D62728", edgecolors="white", linewidth=1.5, zorder=5, alpha=0.45
    )

if np.any(in_op):
    ax.scatter(
        cs_arr[in_op], cf_arr[in_op], s=350, color="#D62728", edgecolors="white", linewidth=2, zorder=6, marker="D"
    )
    # Annotate critical intersections inside operating range with well-separated offsets
    op_s, op_f, op_m = cs_arr[in_op], cf_arr[in_op], np.array(critical_mlabels)[in_op]
    order = np.argsort(op_f)
    n = len(order)
    for rank, si in enumerate(order):
        # Alternate left/right with increasing vertical spread to avoid overlap
        sign = 1 if rank % 2 == 0 else -1
        dx = sign * 35
        dy = -30 + rank * (60 / max(n - 1, 1))
        ax.annotate(
            op_m[si],
            xy=(op_s[si], op_f[si]),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=11,
            color="#B71C1C",
            fontweight="bold",
            arrowprops={"arrowstyle": "-|>", "color": "#B71C1C", "lw": 1.0, "shrinkB": 4},
            zorder=7,
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": "#FFF3F3",
                "edgecolor": "#B71C1C",
                "alpha": 0.9,
                "linewidth": 0.7,
            },
        )

# Style
ax.set_xlabel("Rotational Speed (RPM)", fontsize=20)
ax.set_ylabel("Frequency (Hz)", fontsize=20)
ax.set_title("campbell-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_linewidth(0.6)
    ax.spines[spine].set_color("#555555")
ax.set_xlim(0, 6000)
ax.set_ylim(0, y_max)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color="#CCCCCC")
ax.xaxis.grid(True, alpha=0.08, linewidth=0.4, color="#CCCCCC")

# Format x-axis with thousand separator for readability
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))

# Compact two-column legend positioned in upper-left to avoid covering data
eo_handle = Line2D([0], [0], color="#AAAAAA", linewidth=1.8, linestyle=(0, (8, 4)), alpha=0.6)
crit_outside = Line2D(
    [0], [0], marker="o", color="none", markerfacecolor="#D62728", markeredgecolor="white", markersize=10, alpha=0.5
)
crit_inside = Line2D(
    [0], [0], marker="D", color="none", markerfacecolor="#D62728", markeredgecolor="white", markersize=10
)
op_handle = Patch(facecolor="#306998", alpha=0.12, edgecolor="none")

handles = [Line2D([0], [0], color=c, linewidth=2.8) for c in mode_colors] + [
    eo_handle,
    crit_outside,
    crit_inside,
    op_handle,
]
labels = mode_labels + ["Engine Order (1×–3×)", "Critical Speed", "Critical (op. range)", "Operating Range"]

ax.legend(
    handles,
    labels,
    fontsize=11,
    loc="upper left",
    ncol=2,
    framealpha=0.92,
    edgecolor="#DDDDDD",
    borderpad=0.5,
    labelspacing=0.4,
    handlelength=1.4,
    columnspacing=1.0,
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
