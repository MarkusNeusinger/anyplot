"""anyplot.ai
campbell-basic: Campbell Diagram
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-05-28
"""

import os

import matplotlib.patches as mpatches
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

ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
ANYPLOT_AMBER = "#DDCC77"

# Data
np.random.seed(42)
rpm = np.linspace(0, 6000, 100)

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

records = []
for mode_name, freq in modes.items():
    for r, f in zip(rpm, freq, strict=False):
        records.append({"RPM": r, "Frequency (Hz)": f, "Mode": mode_name})
df = pd.DataFrame(records)

engine_orders = [1, 2, 3]

critical_speeds, critical_freqs = [], []
for mode_freq in modes.values():
    for order in engine_orders:
        diff = mode_freq - order * rpm / 60
        for idx in np.where(np.diff(np.sign(diff)))[0]:
            t = abs(diff[idx]) / (abs(diff[idx]) + abs(diff[idx + 1]))
            cs_rpm = rpm[idx] + t * (rpm[idx + 1] - rpm[idx])
            cs_freq = order * cs_rpm / 60
            if 100 < cs_rpm < 5900:
                critical_speeds.append(cs_rpm)
                critical_freqs.append(cs_freq)

op_low, op_high = 2800, 4200
in_operating = [op_low <= s <= op_high for s in critical_speeds]

cs_df = pd.DataFrame(
    {
        "RPM": critical_speeds,
        "Frequency (Hz)": critical_freqs,
        "Status": ["In Range" if inside else "Outside" for inside in in_operating],
    }
)

# Plot setup
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

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
fig.set_facecolor(PAGE_BG)

# Operating range highlight (amber = caution)
ax.axvspan(op_low, op_high, color=ANYPLOT_AMBER, alpha=0.10, zorder=0)
ax.axvline(op_low, color=ANYPLOT_AMBER, linewidth=0.8, linestyle="--", alpha=0.6, zorder=1)
ax.axvline(op_high, color=ANYPLOT_AMBER, linewidth=0.8, linestyle="--", alpha=0.6, zorder=1)
ax.text(
    (op_low + op_high) / 2,
    3,
    "Operating\nRange",
    fontsize=7,
    color=ANYPLOT_AMBER,
    ha="center",
    va="bottom",
    fontweight="bold",
    linespacing=1.3,
)

# Natural frequency curves via seaborn lineplot with hue
mode_colors = ANYPLOT_PALETTE[:5]
sns.lineplot(
    data=df,
    x="RPM",
    y="Frequency (Hz)",
    hue="Mode",
    palette=dict(zip(modes.keys(), mode_colors, strict=False)),
    linewidth=2.0,
    ax=ax,
    legend=False,
    hue_order=list(modes.keys()),
)

# Engine order lines (structural reference)
eo_label_x = {1: 4600, 2: 2200, 3: 1400}
for order in engine_orders:
    eo_freq = order * rpm / 60
    ax.plot(rpm, eo_freq, color=INK_SOFT, linewidth=1.2, linestyle="--", alpha=0.65, zorder=2)
    lx = eo_label_x[order]
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

# Critical speed markers via seaborn scatterplot
cs_palette = {"In Range": ANYPLOT_PALETTE[4], "Outside": INK_MUTED}
cs_sizes = {"In Range": 120, "Outside": 45}
sns.scatterplot(
    data=cs_df,
    x="RPM",
    y="Frequency (Hz)",
    hue="Status",
    size="Status",
    palette=cs_palette,
    sizes=cs_sizes,
    ax=ax,
    zorder=5,
    edgecolor=PAGE_BG,
    linewidth=0.8,
    legend=False,
)

# Direct mode labels (right edge, increased vertical separation)
y_offsets = {"1st Bending": -2, "2nd Bending": 3, "1st Torsional": 3, "Axial": -3, "3rd Bending": 0}
for i, (name, freq) in enumerate(modes.items()):
    ax.text(
        6080,
        freq[-1] + y_offsets[name],
        name,
        fontsize=8,
        color=mode_colors[i],
        fontweight="bold",
        va="center",
        ha="left",
        clip_on=False,
    )

# Axes limits and labels
y_max = max(m.max() for m in modes.values())
ax.set_xlim(0, 6000)
ax.set_ylim(0, y_max + 5)

title = "campbell-basic · python · seaborn · anyplot.ai"
title_fontsize = max(8, round(12 * (67 / len(title) if len(title) > 67 else 1.0)))

ax.set_xlabel("Rotational Speed (RPM)", fontsize=10, color=INK)
ax.set_ylabel("Frequency (Hz)", fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8)
ax.grid(True, axis="both", alpha=0.12, linewidth=0.5, color=INK)
ax.set_axisbelow(True)
sns.despine(ax=ax)

# Compact legend: critical speed status + operating range only
cs_in = mpatches.Patch(facecolor=ANYPLOT_PALETTE[4], label="Critical (in range)")
cs_out = mpatches.Patch(facecolor=INK_MUTED, label="Critical (outside)")
op_leg = mpatches.Patch(facecolor=ANYPLOT_AMBER, alpha=0.45, label=f"Operating ({op_low}–{op_high} RPM)")
ax.legend(handles=[cs_in, cs_out, op_leg], fontsize=8, loc="lower right", frameon=True, fancybox=False, framealpha=0.9)

fig.subplots_adjust(left=0.08, right=0.80, top=0.92, bottom=0.12)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400)
