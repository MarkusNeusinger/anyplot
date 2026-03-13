""" pyplots.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-13
"""

import matplotlib.patches as mpatches
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

event_markers = {
    "partial_response": ("^", "#E8A838", "Partial Response", 180),
    "complete_response": ("*", "#2ECC71", "Complete Response", 350),
    "progressive_disease": ("D", "#E74C3C", "Progressive Disease", 180),
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
    events.append(patient_events)

sort_idx = np.argsort(durations)
patient_ids = [patient_ids[i] for i in sort_idx]
durations = durations[sort_idx]
arms = arms[sort_idx]
ongoing = ongoing[sort_idx]
events = [events[i] for i in sort_idx]

# Plot
arm_colors = {"Arm A": "#306998", "Arm B": "#7B68AE"}

fig, ax = plt.subplots(figsize=(16, 9))

for i in range(n_patients):
    color = arm_colors[arms[i]]
    ax.barh(i, durations[i], height=0.6, color=color, alpha=0.85, edgecolor="white", linewidth=0.5)

    if ongoing[i]:
        ax.annotate(
            "",
            xy=(durations[i] + 1.2, i),
            xytext=(durations[i], i),
            arrowprops={"arrowstyle": "->", "color": color, "lw": 2.5, "mutation_scale": 15},
        )

    for event_type, event_time in events[i]:
        marker, mcolor, _, msize = event_markers[event_type]
        ax.scatter(event_time, i, marker=marker, color=mcolor, s=msize, zorder=5, edgecolors="white", linewidth=0.8)

# Style
ax.set_yticks(range(n_patients))
ax.set_yticklabels(patient_ids, fontsize=11)
ax.set_xlabel("Time on Study (weeks)", fontsize=20)
ax.set_ylabel("Patient", fontsize=20)
ax.set_title("swimmer-clinical-timeline \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="x", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.set_xlim(0, None)

arm_a_patch = mpatches.Patch(color="#306998", label="Arm A")
arm_b_patch = mpatches.Patch(color="#7B68AE", label="Arm B")
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
        [0], [0], marker=">", color="w", markerfacecolor="#306998", markersize=10, label="Ongoing", linestyle="None"
    )
)

ax.legend(handles=legend_elements, fontsize=14, loc="lower right", framealpha=0.9, edgecolor="#cccccc")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
