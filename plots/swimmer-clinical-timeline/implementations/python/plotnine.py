""" pyplots.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-13
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_vline,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_shape_manual,
    scale_x_continuous,
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
    if np.random.random() < 0.60:
        t = np.round(np.random.uniform(4, min(dur * 0.5, 16)), 1)
        events.append({"patient_id": pid, "time": t, "event_type": "Partial Response"})
    if np.random.random() < 0.25:
        t = np.round(np.random.uniform(min(dur * 0.3, 12), min(dur * 0.7, 30)), 1)
        events.append({"patient_id": pid, "time": t, "event_type": "Complete Response"})
    if np.random.random() < 0.35:
        t = np.round(np.random.uniform(dur * 0.5, dur * 0.95), 1)
        events.append({"patient_id": pid, "time": t, "event_type": "Progressive Disease"})
    if row["ongoing"]:
        events.append({"patient_id": pid, "time": dur, "event_type": "Ongoing"})

events_df = pd.DataFrame(events)
events_df["patient_id"] = pd.Categorical(
    events_df["patient_id"], categories=bar_df["patient_id"].tolist(), ordered=True
)

# Compute storytelling statistics
median_a = bar_df.loc[bar_df["arm"] == "Arm A (Combo)", "duration"].median()
median_b = bar_df.loc[bar_df["arm"] == "Arm B (Mono)", "duration"].median()
n_responders = events_df[events_df["event_type"].isin(["Partial Response", "Complete Response"])][
    "patient_id"
].nunique()
response_rate = n_responders / n_patients * 100

# Distinct arm colors - teal vs amber for strong contrast
arm_colors = {"Arm A (Combo)": "#306998", "Arm B (Mono)": "#CF8A2E"}

# Colorblind-safe event markers: blue-orange-purple palette avoids red-green
event_colors = {
    "Partial Response": "#E69F00",
    "Complete Response": "#0072B2",
    "Progressive Disease": "#9467BD",
    "Ongoing": "#2C2C2C",
}
event_shapes = {"Partial Response": "^", "Complete Response": "D", "Progressive Disease": "s", "Ongoing": ">"}

# Plot
plot = (
    ggplot()
    # Median duration reference lines for storytelling
    + geom_vline(xintercept=median_a, linetype="dashed", color="#306998", alpha=0.4, size=0.8)
    + geom_vline(xintercept=median_b, linetype="dotted", color="#CF8A2E", alpha=0.4, size=0.8)
    # Patient bars
    + geom_segment(
        data=bar_df,
        mapping=aes(x=0, xend="duration", y="patient_id", yend="patient_id", color="arm"),
        size=6,
        lineend="butt",
    )
    # Event markers
    + geom_point(
        data=events_df,
        mapping=aes(x="time", y="patient_id", shape="event_type", fill="event_type"),
        size=5.5,
        color="white",
        stroke=0.6,
    )
    # Scales with plotnine-specific guides for legend customization
    + scale_color_manual(values=arm_colors, name="Treatment Arm")
    + scale_shape_manual(values=event_shapes, name="Clinical Event")
    + scale_fill_manual(values=event_colors, name="Clinical Event")
    + scale_y_discrete(limits=bar_df["patient_id"].tolist())
    + scale_x_continuous(breaks=range(0, 55, 6))
    # coord_cartesian for tight axis limits without clipping data
    + coord_cartesian(xlim=(0, max(durations) + 2))
    # plotnine-specific guide customization with override_aes
    + guides(
        color=guide_legend(order=1, override_aes={"size": 5}),
        shape=guide_legend(order=2, override_aes={"size": 5, "stroke": 0.4}),
        fill=guide_legend(order=2),
    )
    # Median annotations positioned clearly below bottom patients
    + annotate(
        "label",
        x=median_a + 0.5,
        y=2,
        label=f"Median A: {median_a:.0f}w",
        size=10,
        color="#306998",
        fill="#EAF0F7",
        fontweight="bold",
        ha="left",
        va="center",
        label_padding=0.3,
    )
    + annotate(
        "label",
        x=median_b + 0.5,
        y=4,
        label=f"Median B: {median_b:.0f}w",
        size=10,
        color="#CF8A2E",
        fill="#FDF3E7",
        fontweight="bold",
        ha="left",
        va="center",
        label_padding=0.3,
    )
    + annotate(
        "label",
        x=max(durations) - 1,
        y=n_patients - 1,
        label=f"ORR: {response_rate:.0f}% ({n_responders}/{n_patients})",
        size=11,
        color="#0072B2",
        fill="#EDF6FC",
        ha="right",
        va="top",
        alpha=0.95,
        label_padding=0.5,
    )
    + labs(
        title="swimmer-clinical-timeline \u00b7 plotnine \u00b7 pyplots.ai", x="Time on Study (weeks)", y="Patient ID"
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", margin={"b": 14}),
        axis_title_x=element_text(size=20, margin={"t": 12}),
        axis_title_y=element_text(size=20, margin={"r": 12}),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=14, family="monospace"),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        legend_background=element_rect(fill="#FAFAFA", color="#CCCCCC", size=0.5),
        legend_key=element_rect(fill="white", color="none"),
        legend_key_size=18,
        legend_key_spacing=8,
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color="#E8E8E8", size=0.3),
        panel_border=element_blank(),
        plot_background=element_rect(fill="white", color="none"),
        panel_background=element_rect(fill="white", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, width=16, height=9)
