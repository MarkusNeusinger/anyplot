""" pyplots.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-13
"""

import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Data - Simulated Phase II oncology trial with 25 patients across two arms
np.random.seed(42)

n_patients = 25
patient_ids = [f"PT-{i + 1:03d}" for i in range(n_patients)]
arms = np.array(["Arm A"] * 13 + ["Arm B"] * 12)

durations = np.concatenate([np.random.uniform(4, 48, 13), np.random.uniform(6, 44, 12)])
durations = np.round(durations, 1)

ongoing = np.array([False] * n_patients)
ongoing_indices = [0, 3, 7, 14, 18, 22]
for idx in ongoing_indices:
    ongoing[idx] = True

# Colorblind-safe palette: avoid red-green distinction
event_markers = {
    "partial_response": ("^", "#E8A838", "Partial Response", 200),
    "complete_response": ("*", "#2196F3", "Complete Response", 380),
    "progressive_disease": ("D", "#D32F2F", "Progressive Disease", 200),
    "adverse_event": ("X", "#8E24AA", "Adverse Event", 180),
}

events = []
for i in range(n_patients):
    patient_events = []
    dur = durations[i]
    if dur > 8:
        pr_time = np.random.uniform(4, min(dur * 0.5, 12))
        patient_events.append(("partial_response", round(pr_time, 1)))
        if dur > 20 and np.random.random() > 0.5:
            cr_time = np.random.uniform(pr_time + 4, min(dur * 0.8, dur - 2))
            patient_events.append(("complete_response", round(cr_time, 1)))
    if not ongoing[i] and dur > 12 and np.random.random() > 0.4:
        pd_time = np.random.uniform(dur * 0.6, dur - 1)
        patient_events.append(("progressive_disease", round(pd_time, 1)))
    if dur > 10 and np.random.random() > 0.75:
        ae_time = np.random.uniform(2, min(dur * 0.7, dur - 1))
        patient_events.append(("adverse_event", round(ae_time, 1)))
    events.append(patient_events)

sort_idx = np.argsort(durations)
patient_ids = [patient_ids[i] for i in sort_idx]
durations = durations[sort_idx]
arms = arms[sort_idx]
ongoing = ongoing[sort_idx]
events = [events[i] for i in sort_idx]

# Identify patients with complete response for storytelling highlight
cr_patients = [i for i in range(n_patients) if any(e[0] == "complete_response" for e in events[i])]

# Plot
arm_colors = {"Arm A": "#306998", "Arm B": "#7B68AE"}

fig, ax = plt.subplots(figsize=(16, 9))
fig.patch.set_facecolor("#FAFAFA")
ax.set_facecolor("#FAFAFA")

# Draw bars with highlight for complete responders
bar_rects = []
for i in range(n_patients):
    color = arm_colors[arms[i]]
    alpha = 0.95 if i in cr_patients else 0.7
    lw = 1.2 if i in cr_patients else 0.5
    ec = "#333333" if i in cr_patients else "white"
    rect = mpatches.FancyBboxPatch(
        (0, i - 0.3),
        durations[i],
        0.6,
        boxstyle=mpatches.BoxStyle.Round(pad=0, rounding_size=0.15),
        facecolor=color,
        alpha=alpha,
        edgecolor=ec,
        linewidth=lw,
    )
    ax.add_patch(rect)

    if ongoing[i]:
        ax.annotate(
            "",
            xy=(durations[i] + 1.5, i),
            xytext=(durations[i], i),
            arrowprops={"arrowstyle": "-|>", "color": color, "lw": 2.5, "mutation_scale": 16},
        )

    for event_type, event_time in events[i]:
        marker, mcolor, _, msize = event_markers[event_type]
        ax.scatter(
            event_time,
            i,
            marker=marker,
            color=mcolor,
            s=msize,
            zorder=5,
            edgecolors="white",
            linewidth=1.0,
            path_effects=[pe.withStroke(linewidth=2, foreground="white")],
        )

# Data cutoff line
max_dur = durations.max()
cutoff_x = max_dur + 0.5
ax.axvline(x=cutoff_x, color="#999999", linestyle="--", linewidth=1.2, alpha=0.6)
ax.text(
    cutoff_x - 1.0,
    n_patients - 0.3,
    "Data cutoff",
    fontsize=11,
    color="#777777",
    ha="right",
    va="top",
    fontstyle="italic",
    rotation=90,
)

# Annotate longest complete responder for storytelling
if cr_patients:
    best_cr = max(cr_patients, key=lambda p: durations[p])
    cr_time = [t for etype, t in events[best_cr] if etype == "complete_response"][0]
    ax.annotate(
        f"CR at week {cr_time:.0f}",
        xy=(cr_time, best_cr),
        xytext=(cr_time + 5, best_cr + 1.8),
        fontsize=12,
        fontweight="bold",
        color="#1565C0",
        arrowprops={"arrowstyle": "->", "color": "#1565C0", "lw": 1.5, "connectionstyle": "arc3,rad=0.2"},
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#E3F2FD", "edgecolor": "#1565C0", "alpha": 0.9},
    )

# Style
ax.set_yticks(range(n_patients))
ax.set_yticklabels(patient_ids, fontsize=14, fontfamily="monospace")
ax.set_xlabel("Time on Study (weeks)", fontsize=20)
ax.set_ylabel("Patient", fontsize=20)
ax.set_title("swimmer-clinical-timeline \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="x", labelsize=16)
ax.tick_params(axis="y", labelsize=14)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.5)
ax.spines["left"].set_color("#CCCCCC")
ax.spines["bottom"].set_linewidth(0.5)
ax.spines["bottom"].set_color("#CCCCCC")
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, color="#888888")
ax.set_xlim(0, None)
ax.set_ylim(-0.8, n_patients - 0.2)

# Legend using matplotlib handles
arm_a_patch = mpatches.Patch(color="#306998", label="Arm A", alpha=0.85)
arm_b_patch = mpatches.Patch(color="#7B68AE", label="Arm B", alpha=0.85)
legend_elements = [arm_a_patch, arm_b_patch]
for _etype, (marker, mcolor, label, _) in event_markers.items():
    legend_elements.append(
        plt.Line2D(
            [0],
            [0],
            marker=marker,
            color="w",
            markerfacecolor=mcolor,
            markersize=12,
            label=label,
            markeredgecolor="white",
            markeredgewidth=0.8,
            linestyle="None",
        )
    )
legend_elements.append(
    plt.Line2D(
        [0], [0], marker=">", color="w", markerfacecolor="#555555", markersize=10, label="Ongoing", linestyle="None"
    )
)

legend = ax.legend(
    handles=legend_elements,
    fontsize=16,
    loc="lower right",
    framealpha=0.95,
    edgecolor="#CCCCCC",
    fancybox=True,
    shadow=True,
    borderpad=1.0,
)
legend.get_frame().set_linewidth(0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
