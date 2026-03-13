"""pyplots.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-13
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_point,
    geom_segment,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_shape_manual,
    scale_y_discrete,
    theme,
    theme_minimal,
)


# Data - Simulated Phase II oncology trial with 25 patients across two arms
np.random.seed(42)

n_patients = 25
patient_ids = [f"PT-{i + 1:03d}" for i in range(n_patients)]
arms = np.random.choice(["Arm A (Combo)", "Arm B (Mono)"], size=n_patients, p=[0.52, 0.48])
durations = np.round(np.random.uniform(4, 48, size=n_patients), 1)
durations = np.sort(durations)[::-1]
ongoing = np.random.choice([True, False], size=n_patients, p=[0.24, 0.76])

# Build patient bar data
bar_df = pd.DataFrame({"patient_id": patient_ids, "duration": durations, "arm": arms, "ongoing": ongoing})
bar_df = bar_df.sort_values("duration", ascending=True).reset_index(drop=True)
bar_df["patient_id"] = pd.Categorical(bar_df["patient_id"], categories=bar_df["patient_id"].tolist(), ordered=True)

# Generate clinical events
events = []
for _, row in bar_df.iterrows():
    pid = row["patient_id"]
    dur = row["duration"]
    # Partial response: ~60% of patients, early in treatment
    if np.random.random() < 0.60:
        t = np.round(np.random.uniform(4, min(dur * 0.5, 16)), 1)
        events.append({"patient_id": pid, "time": t, "event_type": "Partial Response"})
    # Complete response: ~25% of patients, after partial
    if np.random.random() < 0.25:
        t = np.round(np.random.uniform(min(dur * 0.3, 12), min(dur * 0.7, 30)), 1)
        events.append({"patient_id": pid, "time": t, "event_type": "Complete Response"})
    # Progressive disease: ~35% of patients, later in treatment
    if np.random.random() < 0.35:
        t = np.round(np.random.uniform(dur * 0.5, dur * 0.95), 1)
        events.append({"patient_id": pid, "time": t, "event_type": "Progressive Disease"})
    # Ongoing arrow marker at end of bar
    if row["ongoing"]:
        events.append({"patient_id": pid, "time": dur, "event_type": "Ongoing"})

events_df = pd.DataFrame(events)
events_df["patient_id"] = pd.Categorical(
    events_df["patient_id"], categories=bar_df["patient_id"].tolist(), ordered=True
)

# Colors for treatment arms
arm_colors = {"Arm A (Combo)": "#306998", "Arm B (Mono)": "#4B8BBE"}

# Event marker shapes and colors
event_colors = {
    "Partial Response": "#FFD43B",
    "Complete Response": "#28A745",
    "Progressive Disease": "#E74C3C",
    "Ongoing": "#333333",
}
event_shapes = {"Partial Response": "^", "Complete Response": "*", "Progressive Disease": "D", "Ongoing": ">"}

# Plot - horizontal bars for each patient
plot = (
    ggplot()
    + geom_segment(
        data=bar_df,
        mapping=aes(x=0, xend="duration", y="patient_id", yend="patient_id", color="arm"),
        size=6,
        lineend="butt",
    )
    + geom_point(
        data=events_df,
        mapping=aes(x="time", y="patient_id", shape="event_type", fill="event_type"),
        size=5,
        color="white",
        stroke=0.5,
    )
    + scale_color_manual(values=arm_colors, name="Treatment Arm")
    + scale_shape_manual(values=event_shapes, name="Clinical Event")
    + scale_fill_manual(values=event_colors, name="Clinical Event")
    + scale_y_discrete(limits=bar_df["patient_id"].tolist())
    + labs(title="swimmer-clinical-timeline · plotnine · pyplots.ai", x="Weeks on Study", y="Patient")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=12),
        legend_title=element_text(size=16),
        legend_text=element_text(size=13),
        legend_position="right",
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color="#CCCCCC", size=0.5, alpha=0.3),
    )
)

# Save
plot.save("plot.png", dpi=300, width=16, height=9)
