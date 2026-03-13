"""pyplots.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-13
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Simulated Phase II Oncology Trial (25 patients, 2 treatment arms)
np.random.seed(42)

n_patients = 25
patient_ids = [f"PT-{i + 1:03d}" for i in range(n_patients)]
arms = np.random.choice(["Arm A (Combo)", "Arm B (Mono)"], n_patients, p=[0.52, 0.48])
durations = np.round(np.random.gamma(shape=4, scale=5, size=n_patients), 1)
durations = np.clip(durations, 3, 48)

events_list = []
for i in range(n_patients):
    pid = patient_ids[i]
    dur = durations[i]

    if np.random.rand() < 0.65:
        t = np.round(np.random.uniform(2, min(dur * 0.5, 12)), 1)
        events_list.append({"patient_id": pid, "time": t, "event_type": "Partial Response"})

        if np.random.rand() < 0.35:
            t_cr = np.round(np.random.uniform(t + 2, min(dur * 0.8, dur - 1)), 1)
            events_list.append({"patient_id": pid, "time": t_cr, "event_type": "Complete Response"})

    if np.random.rand() < 0.4:
        t_pd = np.round(np.random.uniform(dur * 0.5, dur), 1)
        events_list.append({"patient_id": pid, "time": t_pd, "event_type": "Progressive Disease"})

    if np.random.rand() < 0.3:
        events_list.append({"patient_id": pid, "time": dur, "event_type": "Ongoing"})

events_df = pd.DataFrame(events_list)

# Build bar dataframe sorted by duration
bar_df = pd.DataFrame({"patient_id": patient_ids, "duration": durations, "arm": arms})
bar_df = bar_df.sort_values("duration", ascending=True).reset_index(drop=True)
bar_df["y_pos"] = range(len(bar_df))
bar_df["x_start"] = 0.0

# Map patient y positions and arm info to events
y_map = dict(zip(bar_df["patient_id"], bar_df["y_pos"]))
events_df["y_pos"] = events_df["patient_id"].map(y_map)

# Plot - Horizontal bars for each patient colored by treatment arm
plot = (
    ggplot()
    + geom_segment(
        aes(x="x_start", xend="duration", y="y_pos", yend="y_pos", color="arm"), data=bar_df, size=8, alpha=0.75
    )
    + geom_point(aes(x="time", y="y_pos", color="event_type", shape="event_type"), data=events_df, size=5)
    + scale_y_continuous(breaks=list(bar_df["y_pos"]), labels=list(bar_df["patient_id"]), expand=[0.03, 0.03])
    + scale_x_continuous(name="Time on Study (Weeks)")
    + scale_color_manual(
        values={
            "Arm A (Combo)": "#306998",
            "Arm B (Mono)": "#8E44AD",
            "Partial Response": "#E67E22",
            "Complete Response": "#27AE60",
            "Progressive Disease": "#C0392B",
            "Ongoing": "#2C3E50",
        },
        name="Legend",
    )
    + scale_shape_manual(
        values={"Partial Response": 17, "Complete Response": 8, "Progressive Disease": 18, "Ongoing": 4},
        name="Clinical Event",
    )
    + labs(title="swimmer-clinical-timeline · letsplot · pyplots.ai", x="Time on Study (Weeks)", y="Patient")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=26, face="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=13),
        legend_title=element_text(size=18),
        legend_text=element_text(size=15),
        legend_position="right",
        panel_grid_major_x=element_line(color="#E5E5E5", size=0.5),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", scale=3, path=".")
ggsave(plot, "plot.html", path=".")

if os.path.exists("lets-plot-images"):
    import shutil

    shutil.rmtree("lets-plot-images")
