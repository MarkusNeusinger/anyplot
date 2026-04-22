""" pyplots.ai
raincloud-basic: Basic Raincloud Plot
Library: altair 6.0.0 | Python 3.14
Quality: 94/100 | Created: 2025-12-25
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Reaction times (ms) for different treatment conditions
np.random.seed(42)

control = np.random.normal(450, 60, 80)
treatment_a = np.random.normal(380, 50, 80)
treatment_b = np.concatenate([np.random.normal(340, 25, 50), np.random.normal(460, 35, 30)])

data = pd.DataFrame(
    {
        "condition": ["Control"] * 80 + ["Treatment A"] * 80 + ["Treatment B"] * 80,
        "reaction_time": np.concatenate([control, treatment_a, treatment_b]),
    }
)

# Map conditions to numeric y positions with spacing
condition_order = ["Control", "Treatment A", "Treatment B"]
condition_map = {c: i * 1.5 for i, c in enumerate(condition_order)}
data["condition_num"] = data["condition"].map(condition_map)

# Jitter positions for rain — BELOW baseline
data["jitter_pos"] = data["condition_num"] + np.random.uniform(-0.30, -0.08, len(data))

# Box plot statistics per condition (streamlined)
box_rows = []
for cond in condition_order:
    vals = data.loc[data["condition"] == cond, "reaction_time"]
    q1, med, q3 = vals.quantile([0.25, 0.5, 0.75])
    iqr = q3 - q1
    box_rows.append(
        {
            "condition": cond,
            "condition_num": condition_map[cond],
            "q1": q1,
            "median": med,
            "q3": q3,
            "lower_w": max(q1 - 1.5 * iqr, vals.min()),
            "upper_w": min(q3 + 1.5 * iqr, vals.max()),
        }
    )
box_df = pd.DataFrame(box_rows)

# Color palette: Python Blue, dark gold (high contrast), fresh green
colors = ["#306998", "#D4A017", "#4CAF50"]

# Tighten x domain to actual data range
x_min = data["reaction_time"].min()
x_max = data["reaction_time"].max()
x_pad = (x_max - x_min) * 0.06
x_scale = alt.Scale(domain=[round(x_min - x_pad, -1), round(x_max + x_pad, -1)])
y_domain = [-0.5, 3.9]
x_axis = alt.Axis(
    titleFontSize=22,
    titleFontWeight="bold",
    titleColor="#333333",
    labelFontSize=18,
    labelColor="#555555",
    grid=True,
    gridOpacity=0.25,
    gridColor="#d0d0d0",
    gridDash=[3, 3],
    domainColor="#999999",
    tickColor="#999999",
    tickCount=8,
)

# Half-violin cloud — extends ABOVE baseline
violin = (
    alt.Chart(data)
    .transform_density(
        "reaction_time",
        as_=["reaction_time", "density"],
        groupby=["condition", "condition_num"],
        extent=[round(x_min - x_pad, -1), round(x_max + x_pad, -1)],
    )
    .transform_calculate(violin_pos="datum.condition_num + 0.04 + datum.density * 105")
    .mark_area(orient="vertical", opacity=0.55, interpolate="monotone")
    .encode(
        x=alt.X("reaction_time:Q", title="Reaction Time (ms)", scale=x_scale, axis=x_axis),
        y=alt.Y("condition_num:Q", axis=None, scale=alt.Scale(domain=y_domain)),
        y2="violin_pos:Q",
        color=alt.Color(
            "condition:N",
            scale=alt.Scale(domain=condition_order, range=colors),
            legend=alt.Legend(
                title="Condition",
                titleFontSize=20,
                titleFontWeight="bold",
                labelFontSize=18,
                orient="none",
                legendX=1350,
                legendY=50,
                fillColor="white",
                strokeColor="#cccccc",
                padding=14,
                cornerRadius=6,
                symbolSize=200,
                direction="vertical",
            ),
        ),
        tooltip=[
            alt.Tooltip("condition:N", title="Condition"),
            alt.Tooltip("reaction_time:Q", title="Reaction Time (ms)", format=".0f"),
        ],
    )
)

# Box plot — WHITE fill with dark outline to distinguish from cloud
box_iqr = (
    alt.Chart(box_df)
    .mark_bar(height=18, stroke="#333333", strokeWidth=2, cornerRadius=2, fill="white", fillOpacity=0.85)
    .encode(
        x=alt.X("q1:Q", scale=x_scale),
        x2="q3:Q",
        y=alt.Y("condition_num:Q", axis=None, scale=alt.Scale(domain=y_domain)),
    )
)

# Median line — contrasting red
box_median = (
    alt.Chart(box_df)
    .mark_tick(thickness=3.5, color="#E8413C", orient="vertical")
    .encode(x=alt.X("median:Q", scale=x_scale), y=alt.Y("condition_num:Q", axis=None, scale=alt.Scale(domain=y_domain)))
)

# Whisker lines
box_whiskers = (
    alt.Chart(box_df)
    .mark_rule(strokeWidth=1.5, color="#555555")
    .encode(
        x=alt.X("lower_w:Q", scale=x_scale),
        x2="upper_w:Q",
        y=alt.Y("condition_num:Q", axis=None, scale=alt.Scale(domain=y_domain)),
    )
)

# Whisker caps
whisker_cap_data = pd.concat(
    [
        box_df[["condition_num", "lower_w"]].rename(columns={"lower_w": "x"}),
        box_df[["condition_num", "upper_w"]].rename(columns={"upper_w": "x"}),
    ]
)
whisker_cap_data["y1"] = whisker_cap_data["condition_num"] - 0.06
whisker_cap_data["y2"] = whisker_cap_data["condition_num"] + 0.06
whisker_caps = (
    alt.Chart(whisker_cap_data)
    .mark_rule(strokeWidth=1.5, color="#555555")
    .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y1:Q", axis=None, scale=alt.Scale(domain=y_domain)), y2="y2:Q")
)

# Jittered strip — rain BELOW baseline
strip = (
    alt.Chart(data)
    .mark_circle(size=45, opacity=0.5, stroke="#444444", strokeWidth=0.4)
    .encode(
        x=alt.X("reaction_time:Q", scale=x_scale),
        y=alt.Y("jitter_pos:Q", axis=None),
        color=alt.Color("condition:N", scale=alt.Scale(domain=condition_order, range=colors)),
        tooltip=[
            alt.Tooltip("condition:N", title="Condition"),
            alt.Tooltip("reaction_time:Q", title="Reaction Time (ms)", format=".1f"),
        ],
    )
)

# Annotation: highlight Treatment B bimodality
annotation_data = pd.DataFrame(
    [{"x": 340, "y": 3.0 + 0.65, "text": "Peak 1"}, {"x": 460, "y": 3.0 + 0.50, "text": "Peak 2"}]
)
bimodal_labels = (
    alt.Chart(annotation_data)
    .mark_text(fontSize=16, fontStyle="italic", color="#444444", fontWeight="bold")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q", axis=None), text="text:N")
)

arrow_data = pd.DataFrame([{"x": 355, "y": 3.0 + 0.58, "x2": 445, "y2": 3.0 + 0.53}])
bimodal_arrow = (
    alt.Chart(arrow_data)
    .mark_rule(strokeDash=[4, 3], color="#777777", strokeWidth=1.5)
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q", axis=None), x2="x2:Q", y2="y2:Q")
)

note_data = pd.DataFrame([{"x": 400, "y": 3.0 + 0.78, "text": "Bimodal distribution"}])
bimodal_note = (
    alt.Chart(note_data)
    .mark_text(fontSize=15, color="#555555", fontStyle="italic")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q", axis=None), text="text:N")
)

# Median value annotations on box plots
median_labels = (
    alt.Chart(box_df)
    .transform_calculate(label_y="datum.condition_num + 0.18")
    .mark_text(fontSize=14, color="#E8413C", fontWeight="bold", dy=-14)
    .encode(
        x=alt.X("median:Q", scale=x_scale),
        y=alt.Y("condition_num:Q", axis=None, scale=alt.Scale(domain=y_domain)),
        text=alt.Text("median:Q", format=".0f"),
    )
)

# Y-axis tick labels
y_label_data = pd.DataFrame({"condition": condition_order, "y_pos": [0, 1.5, 3.0]})
y_labels = (
    alt.Chart(y_label_data)
    .transform_calculate(x=str(round(x_min - x_pad, -1)))
    .mark_text(fontSize=20, fontWeight="bold", align="right", baseline="middle", dx=-25, clip=False, color="#333333")
    .encode(x=alt.X("x:Q"), y=alt.Y("y_pos:Q", axis=None, scale=alt.Scale(domain=y_domain)), text="condition:N")
)

# Compose all layers
chart = (
    alt.layer(
        violin,
        box_whiskers,
        whisker_caps,
        box_iqr,
        box_median,
        median_labels,
        strip,
        bimodal_labels,
        bimodal_arrow,
        bimodal_note,
        y_labels,
    )
    .resolve_scale(y="shared", x="shared")
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "raincloud-basic · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            offset=20,
            color="#333333",
            fontWeight="bold",
        ),
    )
    .configure(padding={"left": 140, "right": 20, "top": 10, "bottom": 40})
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        gridColor="#d0d0d0",
        gridOpacity=0.25,
        domainColor="#999999",
        tickColor="#999999",
    )
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
