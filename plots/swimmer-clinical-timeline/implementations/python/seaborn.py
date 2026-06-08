"""anyplot.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-06-08
"""

import os
import sys


# Prevent implementations/python/matplotlib.py from shadowing the installed
# matplotlib package when the script is run from its own directory.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p not in ("", _here)]

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Theme tokens — Imprint palette + adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
ANYPLOT_AMBER = "#DDCC77"

ARM_COLORS = {
    "Arm A (Standard)": IMPRINT_PALETTE[0],  # brand green — first series
    "Arm B (Experimental)": IMPRINT_PALETTE[1],  # lavender
}

EVENT_STYLES = {
    "partial_response": {"marker": "^", "color": IMPRINT_PALETTE[3], "size": 90, "label": "Partial Response"},
    "complete_response": {"marker": "*", "color": IMPRINT_PALETTE[2], "size": 150, "label": "Complete Response"},
    "progressive_disease": {"marker": "D", "color": IMPRINT_PALETTE[4], "size": 75, "label": "Progression"},
    "adverse_event": {"marker": "X", "color": ANYPLOT_AMBER, "size": 75, "label": "Adverse Event"},
}

# Data — Phase II oncology trial, 25 patients across two treatment arms
np.random.seed(42)
n_patients = 25
arms = ["Arm A (Standard)"] * 13 + ["Arm B (Experimental)"] * 12
durations = np.concatenate([np.random.uniform(4, 22, 13), np.random.uniform(3, 18, 12)])
ongoing_mask = np.random.random(n_patients) < 0.28

patient_ids = [f"PT-{i + 1:03d}" for i in range(n_patients)]

# Sort longest bar at top (highest y index)
order = np.argsort(durations)[::-1]
sorted_ids = [patient_ids[i] for i in order]
sorted_dur = durations[order]
sorted_arms = [arms[i] for i in order]
sorted_ongoing = ongoing_mask[order]

# Generate clinical events for each patient
events = []
event_types = list(EVENT_STYLES.keys())
event_probs = [0.50, 0.30, 0.35, 0.25]

for idx, (dur, _arm, _ongoing) in enumerate(zip(sorted_dur, sorted_arms, sorted_ongoing, strict=False)):
    for etype, prob in zip(event_types, event_probs, strict=False):
        if np.random.random() < prob:
            t = np.random.uniform(1.0, dur * 0.85)
            events.append({"patient_idx": idx, "time": t, "event_type": etype})

events_df = pd.DataFrame(events) if events else pd.DataFrame(columns=["patient_idx", "time", "event_type"])

# Apply seaborn theme
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

# Plot — landscape 3200×1800 px (8 in × 4.5 in @ 400 dpi)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Horizontal bars
bar_height = 0.55
for idx, (dur, arm, ongoing) in enumerate(zip(sorted_dur, sorted_arms, sorted_ongoing, strict=False)):
    color = ARM_COLORS[arm]
    ax.barh(idx, dur, height=bar_height, color=color, alpha=0.82, left=0, zorder=2)
    if ongoing:
        ax.annotate(
            "",
            xy=(dur + 0.95, idx),
            xytext=(dur + 0.08, idx),
            arrowprops={"arrowstyle": "-|>", "color": color, "lw": 1.6, "mutation_scale": 11},
            zorder=3,
        )

# Event markers
for etype, style in EVENT_STYLES.items():
    mask = events_df["event_type"] == etype
    if mask.sum() > 0:
        sub = events_df[mask]
        ax.scatter(
            sub["time"],
            sub["patient_idx"],
            marker=style["marker"],
            color=style["color"],
            s=style["size"],
            zorder=5,
            edgecolors=PAGE_BG,
            linewidths=0.5,
            clip_on=True,
        )

# Axes styling
ax.set_yticks(range(n_patients))
ax.set_yticklabels(sorted_ids)
ax.set_xlabel("Time on Study (months)", fontsize=10, color=INK)
ax.set_xlim(0, sorted_dur.max() + 2.8)
ax.set_ylim(-0.65, n_patients - 0.35)

ax.tick_params(axis="x", which="both", length=0, labelsize=8, colors=INK_SOFT)
ax.tick_params(axis="y", which="both", length=0, labelsize=6.5, colors=INK_SOFT)

# Title — 57 chars < 67 baseline, no scaling needed
title = "swimmer-clinical-timeline · python · seaborn · anyplot.ai"
n_chars = len(title)
ratio = 67 / n_chars if n_chars > 67 else 1.0
title_fs = max(8, round(12 * ratio))
ax.set_title(title, fontsize=title_fs, fontweight="medium", color=INK, pad=8)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Vertical grid only (x-axis), behind bars
ax.xaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK, zorder=0)
ax.set_axisbelow(True)

# Legend — treatment arms + event types + ongoing indicator
arm_handles = [mpatches.Patch(color=ARM_COLORS[arm], alpha=0.82, label=arm) for arm in ARM_COLORS]
event_handles = [
    Line2D(
        [0],
        [0],
        marker=style["marker"],
        color="none",
        markerfacecolor=style["color"],
        markersize=7,
        markeredgewidth=0.5,
        markeredgecolor=PAGE_BG,
        label=style["label"],
    )
    for style in EVENT_STYLES.values()
]
ongoing_handle = Line2D(
    [0],
    [0],
    color=INK_SOFT,
    marker=">",
    markerfacecolor=INK_SOFT,
    markersize=5,
    linewidth=1.3,
    label="Still on Treatment",
)

legend = ax.legend(
    handles=arm_handles + event_handles + [ongoing_handle],
    fontsize=7,
    loc="lower right",
    ncol=2,
    framealpha=0.92,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)
legend.get_frame().set_linewidth(0.5)

# Layout — control padding without bbox_inches="tight"
fig.subplots_adjust(left=0.11, right=0.97, top=0.93, bottom=0.10)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close(fig)
