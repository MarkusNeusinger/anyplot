"""pyplots.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: altair 6.0.0 | Python 3.14
"""

import altair as alt
import pandas as pd


# Data - Software Development Project with Dependencies
tasks_data = [
    # Requirements Phase
    {
        "task": "Requirements Gathering",
        "start": "2024-01-01",
        "end": "2024-01-15",
        "group": "Requirements",
        "depends_on": None,
        "task_id": "REQ1",
    },
    {
        "task": "Requirements Review",
        "start": "2024-01-16",
        "end": "2024-01-22",
        "group": "Requirements",
        "depends_on": "REQ1",
        "task_id": "REQ2",
    },
    # Design Phase
    {
        "task": "System Architecture",
        "start": "2024-01-23",
        "end": "2024-02-05",
        "group": "Design",
        "depends_on": "REQ2",
        "task_id": "DES1",
    },
    {
        "task": "Database Design",
        "start": "2024-02-06",
        "end": "2024-02-15",
        "group": "Design",
        "depends_on": "DES1",
        "task_id": "DES2",
    },
    {
        "task": "UI/UX Design",
        "start": "2024-02-06",
        "end": "2024-02-20",
        "group": "Design",
        "depends_on": "DES1",
        "task_id": "DES3",
    },
    # Development Phase
    {
        "task": "Backend Development",
        "start": "2024-02-16",
        "end": "2024-03-20",
        "group": "Development",
        "depends_on": "DES2",
        "task_id": "DEV1",
    },
    {
        "task": "Frontend Development",
        "start": "2024-02-21",
        "end": "2024-03-25",
        "group": "Development",
        "depends_on": "DES3",
        "task_id": "DEV2",
    },
    {
        "task": "API Integration",
        "start": "2024-03-21",
        "end": "2024-04-05",
        "group": "Development",
        "depends_on": "DEV1",
        "task_id": "DEV3",
    },
    # Testing Phase
    {
        "task": "Unit Testing",
        "start": "2024-03-26",
        "end": "2024-04-10",
        "group": "Testing",
        "depends_on": "DEV2",
        "task_id": "TST1",
    },
    {
        "task": "Integration Testing",
        "start": "2024-04-06",
        "end": "2024-04-20",
        "group": "Testing",
        "depends_on": "DEV3",
        "task_id": "TST2",
    },
    {
        "task": "User Acceptance Testing",
        "start": "2024-04-21",
        "end": "2024-05-05",
        "group": "Testing",
        "depends_on": "TST2",
        "task_id": "TST3",
    },
    # Deployment Phase
    {
        "task": "Deployment Prep",
        "start": "2024-05-06",
        "end": "2024-05-12",
        "group": "Deployment",
        "depends_on": "TST3",
        "task_id": "DPL1",
    },
    {
        "task": "Production Deploy",
        "start": "2024-05-13",
        "end": "2024-05-15",
        "group": "Deployment",
        "depends_on": "DPL1",
        "task_id": "DPL2",
    },
]

df = pd.DataFrame(tasks_data)
df["start"] = pd.to_datetime(df["start"])
df["end"] = pd.to_datetime(df["end"])
task_lookup = {r["task_id"]: r for _, r in df.iterrows()}

# Distinct colorblind-safe palette (purple for Development instead of similar blue)
group_colors = {
    "Requirements": "#306998",
    "Design": "#E69F00",
    "Development": "#7B2D8E",
    "Testing": "#56B4E9",
    "Deployment": "#009E73",
}
dep_color = "#CC5A71"
group_order = ["Requirements", "Design", "Development", "Testing", "Deployment"]

# Build display rows with ordinal task ordering
task_order = []
chart_rows = []
for grp in group_order:
    grp_tasks = df[df["group"] == grp]
    label = f"\u25b8 {grp}"
    task_order.append(label)
    chart_rows.append(
        {
            "task": label,
            "start": grp_tasks["start"].min(),
            "end": grp_tasks["end"].max(),
            "group": grp,
            "is_group": True,
        }
    )
    for _, r in grp_tasks.iterrows():
        display = f"  {r['task']}"
        task_order.append(display)
        chart_rows.append({"task": display, "start": r["start"], "end": r["end"], "group": grp, "is_group": False})

chart_df = pd.DataFrame(chart_rows)

# Dependency data: 2 points per arrow using "task" field for shared ordinal Y scale
dep_line_rows = []
dep_arrow_rows = []
dep_id = 0
for _, r in df.iterrows():
    if r["depends_on"] and r["depends_on"] in task_lookup:
        pred = task_lookup[r["depends_on"]]
        dep_line_rows.append({"x": pred["end"], "task": f"  {pred['task']}", "dep_id": dep_id})
        dep_line_rows.append({"x": r["start"], "task": f"  {r['task']}", "dep_id": dep_id})
        dep_arrow_rows.append({"x": r["start"], "task": f"  {r['task']}"})
        dep_id += 1
dep_line_df = pd.DataFrame(dep_line_rows)
dep_arrow_df = pd.DataFrame(dep_arrow_rows)

# Ordinal Y axis with conditional bold for group headers
y_axis = alt.Axis(
    labelFontSize=alt.ExprRef("indexof(datum.value, '\u25b8') >= 0 ? 17 : 16"),
    labelFontWeight=alt.ExprRef("indexof(datum.value, '\u25b8') >= 0 ? 'bold' : 'normal'"),
    labelLimit=300,
    ticks=False,
    domain=False,
    labelPadding=10,
)

# Task bars with color encoding per group
task_bars = (
    alt.Chart(chart_df[~chart_df["is_group"]])
    .mark_bar(cornerRadius=4)
    .encode(
        x=alt.X(
            "start:T",
            title="Project Timeline (2024)",
            axis=alt.Axis(format="%b %d", labelFontSize=16, titleFontSize=20),
        ),
        x2="end:T",
        y=alt.Y("task:N", sort=task_order, title=None, axis=y_axis),
        color=alt.Color(
            "group:N", scale=alt.Scale(domain=group_order, range=[group_colors[g] for g in group_order]), legend=None
        ),
        tooltip=[
            "task:N",
            alt.Tooltip("start:T", format="%Y-%m-%d"),
            alt.Tooltip("end:T", format="%Y-%m-%d"),
            "group:N",
        ],
    )
)

# Group summary bars (thinner, dark charcoal)
group_bars = (
    alt.Chart(chart_df[chart_df["is_group"]])
    .mark_bar(cornerRadius=3, size=14, opacity=0.85)
    .encode(
        x="start:T",
        x2="end:T",
        y=alt.Y("task:N", sort=task_order),
        color=alt.value("#2C3E50"),
        tooltip=["task:N", alt.Tooltip("start:T", format="%Y-%m-%d"), alt.Tooltip("end:T", format="%Y-%m-%d")],
    )
)

# Dependency lines (prominent dashed, shared ordinal Y)
dep_lines = (
    alt.Chart(dep_line_df)
    .mark_line(strokeWidth=3.5, opacity=0.85, color=dep_color, strokeDash=[8, 4])
    .encode(x="x:T", y=alt.Y("task:N", sort=task_order), detail="dep_id:N")
)

# Arrowheads at successor start
arrow_heads = (
    alt.Chart(dep_arrow_df)
    .mark_point(shape="triangle-right", size=200, filled=True, color=dep_color, opacity=0.9)
    .encode(x="x:T", y=alt.Y("task:N", sort=task_order))
)

# Custom legend with phases and dependency indicator
legend_data = pd.DataFrame(
    [{"phase": g, "color": group_colors[g], "order": i} for i, g in enumerate(group_order)]
    + [{"phase": "Dependency", "color": dep_color, "order": 5}]
)
legend_marks = (
    alt.Chart(legend_data)
    .mark_rect(width=22, height=16, cornerRadius=3)
    .encode(
        x=alt.X("phase:N", sort=alt.EncodingSortField(field="order"), axis=None, title=None),
        color=alt.Color("color:N", scale=None),
    )
)
legend_text = (
    alt.Chart(legend_data)
    .mark_text(dy=24, fontSize=16)
    .encode(x=alt.X("phase:N", sort=alt.EncodingSortField(field="order"), axis=None, title=None), text="phase:N")
)
legend = alt.layer(legend_marks, legend_text).properties(width=600, height=50)

# Combine layers
main = alt.layer(group_bars, task_bars, dep_lines, arrow_heads).properties(
    width=1400,
    height=700,
    title=alt.Title("gantt-dependencies \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="middle"),
)

chart = (
    alt.vconcat(main, legend, spacing=20)
    .configure_axisX(grid=True, gridOpacity=0.15, gridDash=[3, 3])
    .configure_axisY(grid=False)
    .configure_view(strokeWidth=0)
)

chart.save("plot.png", scale_factor=3.0)
