"""pyplots.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-13
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

# Map patient y positions to events
y_map = dict(zip(bar_df["patient_id"], bar_df["y_pos"]))
events_df["y_pos"] = events_df["patient_id"].map(y_map)

# Compute median duration for reference line
median_duration = float(np.median(durations))

# Identify complete responders for storytelling emphasis
cr_patients = set(events_df[events_df["event_type"] == "Complete Response"]["patient_id"])
bar_df["has_cr"] = bar_df["patient_id"].isin(cr_patients)

# Build rectangles for bars (using fill aesthetic, separate from event color)
bar_df["y_min"] = bar_df["y_pos"] - 0.35
bar_df["y_max"] = bar_df["y_pos"] + 0.35
bar_df["x_min"] = 0.0

# Best responder annotation (longest-duration complete responder)
cr_bar = bar_df[bar_df["has_cr"]].sort_values("duration", ascending=False)
best_responder = cr_bar.iloc[0] if len(cr_bar) > 0 else None

# Plot - Separate fill for bars, color/shape for events
plot = (
    ggplot()
    # Subtle highlight bands for complete responders
    + geom_rect(
        aes(xmin="x_min", xmax="duration", ymin="y_min", ymax="y_max"),
        data=bar_df[bar_df["has_cr"]],
        fill="#E8F5E9",
        alpha=0.5,
    )
    # Treatment duration bars using fill for arm distinction
    + geom_rect(aes(xmin="x_min", xmax="duration", ymin="y_min", ymax="y_max", fill="arm"), data=bar_df, alpha=0.8)
    # Median duration reference line
    + geom_vline(xintercept=median_duration, color="#7F8C8D", linetype="dashed", size=0.8)
    # Event markers using color + shape (separate legend)
    + geom_point(aes(x="time", y="y_pos", color="event_type", shape="event_type"), data=events_df, size=8, stroke=1.5)
    # Annotation for median line
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=pd.DataFrame({"x": [median_duration + 0.5], "y": [-1.2], "label": [f"Median: {median_duration:.0f}w"]}),
        size=11,
        hjust=0,
        color="#7F8C8D",
    )
    # Scales - fill for bars, color for events (separate legends)
    + scale_fill_manual(name="Treatment Arm", values={"Arm A (Combo)": "#306998", "Arm B (Mono)": "#8E44AD"})
    + scale_color_manual(
        name="Clinical Event",
        values={
            "Partial Response": "#E67E22",
            "Complete Response": "#2ECC71",
            "Progressive Disease": "#8B0000",
            "Ongoing": "#2C3E50",
        },
    )
    + scale_shape_manual(
        name="Clinical Event",
        values={"Partial Response": 17, "Complete Response": 8, "Progressive Disease": 18, "Ongoing": 4},
    )
    + scale_y_continuous(breaks=list(bar_df["y_pos"]), labels=list(bar_df["patient_id"]), expand=[0.03, 0.03])
    + scale_x_continuous(name="Time on Study (Weeks)", expand=[0.01, 0.02])
    + labs(title="swimmer-clinical-timeline · letsplot · pyplots.ai", x="Time on Study (Weeks)", y="Patient")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=26, face="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=14),
        legend_title=element_text(size=18, face="bold"),
        legend_text=element_text(size=15),
        legend_position="right",
        panel_grid_major_x=element_line(color="#ECECEC", size=0.4),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Add best responder annotation if found
if best_responder is not None:
    plot = plot + geom_text(
        aes(x="x", y="y", label="label"),
        data=pd.DataFrame(
            {
                "x": [float(best_responder["duration"]) * 0.5],
                "y": [float(best_responder["y_pos"]) + 0.55],
                "label": ["Best CR"],
            }
        ),
        size=11,
        hjust=0.5,
        color="#1B7A3D",
        fontface="bold",
    )

# Save
ggsave(plot, "plot.png", scale=3, path=".")
ggsave(plot, "plot.html", path=".")

if os.path.exists("lets-plot-images"):
    import shutil

    shutil.rmtree("lets-plot-images")
