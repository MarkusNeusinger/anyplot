""" pyplots.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: plotly 6.5.2 | Python 3.14
Quality: 83/100 | Updated: 2026-02-25
"""

import pandas as pd
import plotly.graph_objects as go


# Data - Software Development Project with phases and dependencies
tasks = [
    # Requirements Phase
    {
        "task": "Requirements Gathering",
        "start": "2024-03-01",
        "end": "2024-03-08",
        "group": "Requirements",
        "depends_on": [],
    },
    {
        "task": "Requirements Analysis",
        "start": "2024-03-08",
        "end": "2024-03-12",
        "group": "Requirements",
        "depends_on": ["Requirements Gathering"],
    },
    {
        "task": "Requirements Sign-off",
        "start": "2024-03-12",
        "end": "2024-03-14",
        "group": "Requirements",
        "depends_on": ["Requirements Analysis"],
    },
    # Design Phase
    {
        "task": "System Architecture",
        "start": "2024-03-14",
        "end": "2024-03-20",
        "group": "Design",
        "depends_on": ["Requirements Sign-off"],
    },
    {
        "task": "Database Design",
        "start": "2024-03-20",
        "end": "2024-03-26",
        "group": "Design",
        "depends_on": ["System Architecture"],
    },
    {
        "task": "UI/UX Design",
        "start": "2024-03-20",
        "end": "2024-03-28",
        "group": "Design",
        "depends_on": ["System Architecture"],
    },
    {
        "task": "Design Review",
        "start": "2024-03-28",
        "end": "2024-03-30",
        "group": "Design",
        "depends_on": ["Database Design", "UI/UX Design"],
    },
    # Development Phase
    {
        "task": "Backend API Development",
        "start": "2024-03-30",
        "end": "2024-04-15",
        "group": "Development",
        "depends_on": ["Design Review"],
    },
    {
        "task": "Frontend Development",
        "start": "2024-03-30",
        "end": "2024-04-16",
        "group": "Development",
        "depends_on": ["Design Review"],
    },
    {
        "task": "Database Implementation",
        "start": "2024-03-30",
        "end": "2024-04-08",
        "group": "Development",
        "depends_on": ["Design Review"],
    },
    {
        "task": "Integration",
        "start": "2024-04-16",
        "end": "2024-04-22",
        "group": "Development",
        "depends_on": ["Backend API Development", "Frontend Development", "Database Implementation"],
    },
    # Testing Phase
    {
        "task": "Unit Testing",
        "start": "2024-04-08",
        "end": "2024-04-20",
        "group": "Testing",
        "depends_on": ["Database Implementation"],
    },
    {
        "task": "Integration Testing",
        "start": "2024-04-22",
        "end": "2024-04-30",
        "group": "Testing",
        "depends_on": ["Integration"],
    },
    {
        "task": "User Acceptance Testing",
        "start": "2024-04-30",
        "end": "2024-05-07",
        "group": "Testing",
        "depends_on": ["Integration Testing"],
    },
    {
        "task": "Bug Fixes",
        "start": "2024-05-01",
        "end": "2024-05-10",
        "group": "Testing",
        "depends_on": ["Unit Testing"],
    },
    # Deployment Phase
    {
        "task": "Deployment Preparation",
        "start": "2024-05-07",
        "end": "2024-05-10",
        "group": "Deployment",
        "depends_on": ["User Acceptance Testing"],
    },
    {
        "task": "Production Deployment",
        "start": "2024-05-10",
        "end": "2024-05-12",
        "group": "Deployment",
        "depends_on": ["Deployment Preparation", "Bug Fixes"],
    },
    {
        "task": "Post-Deployment Review",
        "start": "2024-05-12",
        "end": "2024-05-14",
        "group": "Deployment",
        "depends_on": ["Production Deployment"],
    },
]

df = pd.DataFrame(tasks)
df["start"] = pd.to_datetime(df["start"])
df["end"] = pd.to_datetime(df["end"])

# Color palette for groups
group_colors = {
    "Requirements": "#306998",
    "Design": "#FFD43B",
    "Development": "#4ECDC4",
    "Testing": "#FF6B6B",
    "Deployment": "#95E1A3",
}

# Calculate group summary bars
groups = df.groupby("group").agg({"start": "min", "end": "max"}).reset_index()
group_order = ["Requirements", "Design", "Development", "Testing", "Deployment"]

# Build task list with groups (groups first, then their tasks)
ordered_tasks = []
task_y_labels = {}

for group_name in group_order:
    # Add group summary bar
    label = f"\u25bc {group_name}"
    ordered_tasks.append({"name": label, "is_group": True, "group": group_name})
    # Add tasks in this group
    group_tasks = df[df["group"] == group_name].sort_values("start")
    for _, task in group_tasks.iterrows():
        label = f"   {task['task']}"
        ordered_tasks.append({"name": label, "is_group": False, "task_data": task})
        task_y_labels[task["task"]] = label

# Build y-axis category order (reversed so first task appears at top)
y_categories = [item["name"] for item in ordered_tasks]

# Create figure
fig = go.Figure()

# Add task bars
for item in ordered_tasks:
    if item["is_group"]:
        group_name = item["group"]
        group_data = groups[groups["group"] == group_name].iloc[0]
        fig.add_trace(
            go.Scatter(
                x=[group_data["start"], group_data["end"]],
                y=[item["name"], item["name"]],
                mode="lines",
                line={"color": group_colors[group_name], "width": 20},
                name=group_name,
                showlegend=True,
                legendgroup=group_name,
                hovertemplate=(
                    f"<b>{group_name}</b><br>"
                    f"Start: {group_data['start'].strftime('%Y-%m-%d')}<br>"
                    f"End: {group_data['end'].strftime('%Y-%m-%d')}<extra></extra>"
                ),
            )
        )
    else:
        task = item["task_data"]
        group_name = task["group"]
        duration = (task["end"] - task["start"]).days
        fig.add_trace(
            go.Scatter(
                x=[task["start"], task["end"]],
                y=[item["name"], item["name"]],
                mode="lines",
                line={"color": group_colors[group_name], "width": 14},
                opacity=0.85,
                showlegend=False,
                legendgroup=group_name,
                hovertemplate=(
                    f"<b>{task['task']}</b><br>"
                    f"Start: {task['start'].strftime('%Y-%m-%d')}<br>"
                    f"End: {task['end'].strftime('%Y-%m-%d')}<br>"
                    f"Duration: {duration} days<extra></extra>"
                ),
            )
        )

# Add dependency arrows as annotations with arrowheads
for item in ordered_tasks:
    if not item["is_group"]:
        task = item["task_data"]
        depends_on = task["depends_on"]
        if depends_on:
            for dep in depends_on:
                if dep in task_y_labels:
                    pred_task = df[df["task"] == dep].iloc[0]
                    pred_end = pred_task["end"]
                    curr_start = task["start"]
                    pred_y = task_y_labels[dep]
                    curr_y = task_y_labels[task["task"]]

                    # Annotation arrow from predecessor end to successor start
                    fig.add_annotation(
                        x=curr_start,
                        y=curr_y,
                        ax=pred_end,
                        ay=pred_y,
                        xref="x",
                        yref="y",
                        axref="x",
                        ayref="y",
                        showarrow=True,
                        arrowhead=3,
                        arrowsize=1.2,
                        arrowwidth=1.5,
                        arrowcolor="#555555",
                        opacity=0.7,
                    )

# Layout
fig.update_layout(
    title={
        "text": "gantt-dependencies \u00b7 plotly \u00b7 pyplots.ai",
        "font": {"size": 32, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Timeline (2024)", "font": {"size": 24}},
        "tickfont": {"size": 16},
        "type": "date",
        "tickformat": "%b %d",
        "gridcolor": "rgba(0,0,0,0.08)",
        "showgrid": True,
        "dtick": 7 * 24 * 60 * 60 * 1000,
        "tickangle": 45,
    },
    yaxis={
        "title": {"text": "", "font": {"size": 22}},
        "tickfont": {"size": 15},
        "categoryorder": "array",
        "categoryarray": y_categories[::-1],
        "showgrid": False,
    },
    template="plotly_white",
    legend={
        "title": {"text": "Project Phases", "font": {"size": 20}},
        "font": {"size": 16},
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
        "itemwidth": 30,
    },
    margin={"l": 230, "r": 40, "t": 120, "b": 90},
    height=900,
    width=1600,
)

# Dependency legend annotation
fig.add_annotation(
    x=1.0,
    y=-0.1,
    xref="paper",
    yref="paper",
    text="\u2192 Dependency (finish-to-start)",
    showarrow=False,
    font={"size": 15, "color": "#555555"},
    xanchor="right",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
