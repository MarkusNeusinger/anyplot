""" pyplots.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-13
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)

n_patients = 25
patient_ids = [f"PT-{i + 1:03d}" for i in range(n_patients)]
arms = np.random.choice(["Arm A (Combo)", "Arm B (Mono)"], n_patients, p=[0.52, 0.48])
durations = np.round(np.random.uniform(4, 48, n_patients), 1)
durations = np.sort(durations)[::-1]

ongoing_mask = np.random.choice([True, False], n_patients, p=[0.3, 0.7])

events_list = []
for i, pid in enumerate(patient_ids):
    dur = durations[i]
    if dur > 8:
        pr_time = np.round(np.random.uniform(4, min(dur * 0.5, 16)), 1)
        events_list.append({"patient_id": pid, "time": pr_time, "event_type": "Partial Response"})
    if dur > 20 and np.random.random() > 0.5:
        cr_time = np.round(np.random.uniform(12, min(dur * 0.7, 30)), 1)
        events_list.append({"patient_id": pid, "time": cr_time, "event_type": "Complete Response"})
    if not ongoing_mask[i] and dur > 6:
        pd_time = np.round(dur - np.random.uniform(0, 3), 1)
        events_list.append({"patient_id": pid, "time": pd_time, "event_type": "Progressive Disease"})
    if ongoing_mask[i]:
        events_list.append({"patient_id": pid, "time": dur, "event_type": "Ongoing"})

bars_df = pd.DataFrame({"patient_id": patient_ids, "duration": durations, "arm": arms, "ongoing": ongoing_mask})

sort_order = bars_df.sort_values("duration", ascending=True)["patient_id"].tolist()

events_df = pd.DataFrame(events_list)
events_df = events_df.merge(bars_df[["patient_id", "arm"]], on="patient_id")

# Colorblind-safe event palette (no red-green pair)
event_shape_map = {
    "Partial Response": "triangle-up",
    "Complete Response": "cross",
    "Progressive Disease": "diamond",
    "Ongoing": "triangle-right",
}
event_color_map = {
    "Partial Response": "#4DAF4A",
    "Complete Response": "#FF7F00",
    "Progressive Disease": "#984EA3",
    "Ongoing": "#777777",
}

# Interactive selection for highlighting by treatment arm
arm_selection = alt.selection_point(fields=["arm"], bind="legend")

# Plot - bars with selection-driven opacity for storytelling
bars = (
    alt.Chart(bars_df)
    .mark_bar(height=16, cornerRadiusEnd=3)
    .encode(
        x=alt.X(
            "duration:Q",
            title="Time on Study (Weeks)",
            axis=alt.Axis(titleFontSize=22, labelFontSize=16, tickSize=0, gridOpacity=0.15),
        ),
        y=alt.Y("patient_id:N", title=None, sort=sort_order, axis=alt.Axis(labelFontSize=14, tickSize=0)),
        color=alt.Color(
            "arm:N",
            title="Treatment Arm",
            scale=alt.Scale(domain=["Arm A (Combo)", "Arm B (Mono)"], range=["#306998", "#E8863A"]),
            legend=alt.Legend(
                titleFontSize=16,
                labelFontSize=14,
                orient="none",
                legendX=20,
                legendY=950,
                direction="horizontal",
                symbolSize=200,
                symbolStrokeWidth=0,
                titleOrient="left",
                padding=8,
                fillColor="white",
                strokeColor="#ddd",
                cornerRadius=4,
            ),
        ),
        opacity=alt.condition(arm_selection, alt.value(1.0), alt.value(0.25)),
    )
    .add_params(arm_selection)
)

# Median duration reference rule for visual context
median_dur = float(np.median(durations))
rule_df = pd.DataFrame({"median": [median_dur]})
median_rule = alt.Chart(rule_df).mark_rule(strokeDash=[6, 4], strokeWidth=1.5, color="#888888").encode(x="median:Q")
median_label = (
    alt.Chart(rule_df)
    .mark_text(align="left", dx=4, dy=-8, fontSize=13, color="#666666", fontStyle="italic")
    .encode(x="median:Q", y=alt.value(0), text=alt.value(f"Median: {median_dur:.0f} wk"))
)

# Plot - event markers with colorblind-safe palette
markers = (
    alt.Chart(events_df)
    .mark_point(filled=True, size=250, stroke="white", strokeWidth=1.0)
    .encode(
        x=alt.X("time:Q"),
        y=alt.Y("patient_id:N", sort=sort_order),
        shape=alt.Shape(
            "event_type:N",
            title="Clinical Event",
            scale=alt.Scale(domain=list(event_shape_map.keys()), range=list(event_shape_map.values())),
            legend=alt.Legend(
                titleFontSize=16,
                labelFontSize=14,
                orient="none",
                legendX=370,
                legendY=950,
                direction="horizontal",
                symbolSize=200,
                symbolStrokeWidth=0,
                titleOrient="left",
                padding=8,
                fillColor="white",
                strokeColor="#ddd",
                cornerRadius=4,
            ),
        ),
        color=alt.Color(
            "event_type:N",
            scale=alt.Scale(domain=list(event_color_map.keys()), range=list(event_color_map.values())),
            legend=None,
        ),
        tooltip=["patient_id:N", "event_type:N", alt.Tooltip("time:Q", title="Week")],
        opacity=alt.condition(arm_selection, alt.value(1.0), alt.value(0.25)),
    )
)

# Combine and style
chart = (
    (bars + median_rule + median_label + markers)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "swimmer-clinical-timeline · altair · pyplots.ai",
            fontSize=26,
            fontWeight="normal",
            anchor="start",
            offset=12,
        ),
    )
    .configure_axis(grid=False)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
