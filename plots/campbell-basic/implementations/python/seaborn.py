""" pyplots.ai
campbell-basic: Campbell Diagram
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 92/100 | Created: 2026-02-15
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data
np.random.seed(42)
rpm = np.linspace(0, 6000, 100)

# Natural frequency modes (Hz) with more dramatic gyroscopic speed dependence
mode_1_bending = 15 + 0.0018 * rpm + 1.2 * np.sin(rpm / 1500)
mode_2_bending = 44 - 0.0025 * rpm + 0.8 * np.cos(rpm / 2000)
mode_1_torsional = 52 + 0.0035 * rpm
mode_axial = 68 - 0.0008 * rpm + 1.0 * np.sin(rpm / 1200)
mode_3_bending = 82 + 0.0022 * rpm + 0.6 * np.sin(rpm / 1800)

modes = {
    "1st Bending": mode_1_bending,
    "2nd Bending": mode_2_bending,
    "1st Torsional": mode_1_torsional,
    "Axial": mode_axial,
    "3rd Bending": mode_3_bending,
}

# Build a DataFrame for seaborn plotting
records = []
for mode_name, freq in modes.items():
    for r, f in zip(rpm, freq, strict=True):
        records.append({"RPM": r, "Frequency (Hz)": f, "Mode": mode_name})
df = pd.DataFrame(records)

# Engine order lines: frequency = order * rpm / 60
engine_orders = [1, 2, 3]

# Find critical speed intersections
critical_speeds, critical_freqs, critical_mode_labels = [], [], []
for mode_name, mode_freq in modes.items():
    for order in engine_orders:
        diff = mode_freq - order * rpm / 60
        sign_changes = np.where(np.diff(np.sign(diff)))[0]
        for idx in sign_changes:
            t = abs(diff[idx]) / (abs(diff[idx]) + abs(diff[idx + 1]))
            cs_rpm = rpm[idx] + t * (rpm[idx + 1] - rpm[idx])
            cs_freq = order * cs_rpm / 60
            if 100 < cs_rpm < 5900:
                critical_speeds.append(cs_rpm)
                critical_freqs.append(cs_freq)
                critical_mode_labels.append(mode_name)

# Operating range for storytelling
op_low, op_high = 2800, 4200

# Identify which critical speeds fall within the operating range
in_operating = [(op_low <= s <= op_high) for s in critical_speeds]
cs_sizes = [280 if inside else 120 for inside in in_operating]
cs_colors = ["#B80000" if inside else "#D67070" for inside in in_operating]
cs_edge = ["#FFFFFF" if inside else "#E0C0C0" for inside in in_operating]

# Plot
sns.set_context("talk", font_scale=1.1)
sns.set_style("ticks", {"axes.grid": True, "grid.alpha": 0.15, "grid.linestyle": ":"})
fig, ax = plt.subplots(figsize=(16, 9))

# Operating range shading (danger zone storytelling)
ax.axvspan(op_low, op_high, color="#FFF3E0", alpha=0.55, zorder=0)
ax.axvline(op_low, color="#E8822A", linewidth=1.2, linestyle=":", alpha=0.6, zorder=1)
ax.axvline(op_high, color="#E8822A", linewidth=1.2, linestyle=":", alpha=0.6, zorder=1)
ax.text(
    (op_low + op_high) / 2,
    2.5,
    "Operating Range",
    fontsize=13,
    color="#C06000",
    ha="center",
    va="bottom",
    fontweight="bold",
    bbox={"boxstyle": "round,pad=0.2", "fc": "#FFF3E0", "ec": "none", "alpha": 0.9},
)

# Natural frequency curves via seaborn
mode_palette = ["#306998", "#E8822A", "#2CA02C", "#9467BD", "#17BECF"]
g = sns.lineplot(
    data=df,
    x="RPM",
    y="Frequency (Hz)",
    hue="Mode",
    palette=mode_palette,
    linewidth=2.8,
    ax=ax,
    legend=True,
    hue_order=list(modes.keys()),
)

# Direct mode labels near right end of each curve
label_offsets = {"1st Bending": -3, "2nd Bending": 3, "1st Torsional": -3, "Axial": 3, "3rd Bending": -3}
for i, (mode_name, mode_freq) in enumerate(modes.items()):
    y_end = mode_freq[-1]
    ax.text(
        6050,
        y_end + label_offsets[mode_name],
        mode_name,
        fontsize=12,
        color=mode_palette[i],
        fontweight="bold",
        va="center",
        ha="left",
        clip_on=False,
    )

# Engine order lines with increased prominence
eo_color = "#777777"
eo_label_positions = {1: 4600, 2: 2200, 3: 1400}
for order in engine_orders:
    eo_freq = order * rpm / 60
    ax.plot(rpm, eo_freq, color=eo_color, linewidth=2.0, linestyle="--", alpha=0.85, zorder=2)
    lx = eo_label_positions[order]
    ly = order * lx / 60
    ax.text(
        lx,
        ly + 2,
        f"{order}x",
        fontsize=14,
        color="#444444",
        fontweight="bold",
        va="bottom",
        ha="center",
        bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "#bbbbbb", "alpha": 0.9},
    )

# Critical speed markers — larger and red inside operating range, smaller outside
for s, f, sz, c, ec in zip(critical_speeds, critical_freqs, cs_sizes, cs_colors, cs_edge, strict=True):
    ax.scatter(s, f, color=c, s=sz, zorder=5, edgecolors=ec, linewidth=1.8)

# Build manual legend entries
mode_handles = [
    plt.Line2D([0], [0], color=mode_palette[i], linewidth=2.8, label=name) for i, name in enumerate(modes.keys())
]
eo_handle = plt.Line2D([0], [0], color=eo_color, linewidth=2.0, linestyle="--", alpha=0.85, label="Engine Orders")
cs_danger = plt.Line2D(
    [0],
    [0],
    marker="o",
    color="w",
    markerfacecolor="#B80000",
    markersize=12,
    markeredgecolor="white",
    markeredgewidth=1.5,
    label="Critical (in range)",
)
cs_safe = plt.Line2D(
    [0],
    [0],
    marker="o",
    color="w",
    markerfacecolor="#D67070",
    markersize=8,
    markeredgecolor="#E0C0C0",
    markeredgewidth=1.2,
    label="Critical (outside)",
)
op_patch = mpatches.Patch(
    facecolor="#FFF3E0", edgecolor="#E8822A", alpha=0.7, linewidth=1.2, label=f"Operating ({op_low}\u2013{op_high} RPM)"
)

# Remove seaborn auto-legend and build custom
ax.get_legend().remove()
ax.legend(
    handles=mode_handles + [eo_handle, cs_danger, cs_safe, op_patch],
    fontsize=12,
    loc="upper center",
    frameon=True,
    fancybox=False,
    edgecolor="#cccccc",
    framealpha=0.95,
    ncol=3,
    bbox_to_anchor=(0.5, 0.98),
)

# Tighten axis limits — data max is ~96 Hz, set y-limit accordingly
y_max = max(m.max() for m in modes.values())
ax.set_xlim(0, 6000)
ax.set_ylim(0, y_max + 6)

ax.set_xlabel("Rotational Speed (RPM)", fontsize=20)
ax.set_ylabel("Frequency (Hz)", fontsize=20)
ax.set_title("campbell-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
sns.despine(ax=ax)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
