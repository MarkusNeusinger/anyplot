"""pyplots.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: plotly 6.5.2 | Python 3.14
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

# Colorblind-safe palette (avoids red-green pairing)
group_colors = {
    "Requirements": "#306998",
    "Design": "#FFD43B",
    "Development": "#4ECDC4",
    "Testing": "#AB63FA",
    "Deployment": "#FF7F0E",
}

# Compute critical path by backward traversal from project end
task_deps = {row["task"]: row["depends_on"] for _, row in df.iterrows()}
task_ends = {row["task"]: row["end"] for _, row in df.iterrows()}

all_predecessors = {dep for deps in task_deps.values() for dep in deps}
terminal_tasks = [t for t in task_deps if t not in all_predecessors]
last_task = max(terminal_tasks, key=lambda t: task_ends[t])

critical_path = set()
critical_edges = set()
current = last_task
while current:
    critical_path.add(current)
    deps = task_deps[current]
    if not deps:
        break
    binding = max(deps, key=lambda d: task_ends[d])
    critical_edges.add((binding, current))
    current = binding

# Build ordered task list (group headers + indented tasks)
group_order = ["Requirements", "Design", "Development", "Testing", "Deployment"]
groups_agg = df.groupby("group").agg({"start": "min", "end": "max"}).reset_index()

ordered_items = []
task_y_labels = {}
for group in group_order:
    ordered_items.append({"label": f"\u25bc {group}", "is_group": True, "group": group})
    for _, row in df[df["group"] == group].sort_values("start").iterrows():
        label = f"   {row['task']}"
        ordered_items.append({"label": label, "is_group": False, "task": row})
        task_y_labels[row["task"]] = label

y_categories = [item["label"] for item in ordered_items]

# Create figure
fig = go.Figure()

# Draw bars using go.Bar with horizontal orientation and base parameter
for group in group_order:
    color = group_colors[group]
    g = groups_agg[groups_agg["group"] == group].iloc[0]
    dur_ms = (g["end"] - g["start"]).total_seconds() * 1000

    # Group summary bar (wider, shown in legend)
    fig.add_trace(
        go.Bar(
            y=[f"\u25bc {group}"],
            x=[dur_ms],
            base=[g["start"]],
            orientation="h",
            name=group,
            legendgroup=group,
            marker={"color": color, "line": {"width": 0}},
            width=0.7,
            hovertemplate=(
                f"<b>{group} Phase</b><br>"
                f"Start: {g['start'].strftime('%b %d, %Y')}<br>"
                f"End: {g['end'].strftime('%b %d, %Y')}<extra></extra>"
            ),
        )
    )

    # Individual task bars (narrower, hidden from legend)
    for _, task in df[df["group"] == group].sort_values("start").iterrows():
        is_cp = task["task"] in critical_path
        label = task_y_labels[task["task"]]
        dur_ms = (task["end"] - task["start"]).total_seconds() * 1000
        dur_days = (task["end"] - task["start"]).days

        fig.add_trace(
            go.Bar(
                y=[label],
                x=[dur_ms],
                base=[task["start"]],
                orientation="h",
                showlegend=False,
                legendgroup=group,
                marker={
                    "color": color,
                    "opacity": 0.95 if is_cp else 0.55,
                    "line": {"width": 1.5 if is_cp else 0, "color": "rgba(0,0,0,0.25)" if is_cp else "rgba(0,0,0,0)"},
                },
                width=0.45,
                hovertemplate=(
                    f"<b>{task['task']}</b>" + (" \u26a1 Critical Path" if is_cp else "") + f"<br>Phase: {group}<br>"
                    f"Start: {task['start'].strftime('%b %d, %Y')}<br>"
                    f"End: {task['end'].strftime('%b %d, %Y')}<br>"
                    f"Duration: {dur_days} days<extra></extra>"
                ),
            )
        )

# Dependency arrows (critical path edges highlighted)
for _, task in df.iterrows():
    for dep in task["depends_on"]:
        if dep in task_y_labels:
            pred = df[df["task"] == dep].iloc[0]
            is_cp_edge = (dep, task["task"]) in critical_edges

            fig.add_annotation(
                x=task["start"],
                y=task_y_labels[task["task"]],
                ax=pred["end"],
                ay=task_y_labels[dep],
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                showarrow=True,
                arrowhead=3,
                arrowsize=1.3,
                arrowwidth=2.8 if is_cp_edge else 1.3,
                arrowcolor="#C0392B" if is_cp_edge else "#BBBBBB",
                opacity=0.9 if is_cp_edge else 0.4,
            )

# Layout
fig.update_layout(
    title={
        "text": "gantt-dependencies \u00b7 plotly \u00b7 pyplots.ai",
        "font": {"size": 32, "color": "#2C3E50"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Timeline (2024)", "font": {"size": 24}},
        "tickfont": {"size": 16},
        "type": "date",
        "tickformat": "%b %d",
        "gridcolor": "rgba(0,0,0,0.06)",
        "showgrid": True,
        "dtick": 7 * 24 * 60 * 60 * 1000,
        "tickangle": 45,
    },
    yaxis={"tickfont": {"size": 16}, "categoryorder": "array", "categoryarray": y_categories[::-1], "showgrid": False},
    barmode="overlay",
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
    margin={"l": 240, "r": 50, "t": 120, "b": 110},
    height=900,
    width=1600,
)

# Dependency legend annotations
fig.add_annotation(
    x=0.99,
    y=-0.12,
    xref="paper",
    yref="paper",
    text="\u2501\u2501\u25b6 Critical Path",
    showarrow=False,
    font={"size": 15, "color": "#C0392B"},
    xanchor="right",
)
fig.add_annotation(
    x=0.99,
    y=-0.16,
    xref="paper",
    yref="paper",
    text="\u2500\u2500\u25b6 Dependency (finish-to-start)",
    showarrow=False,
    font={"size": 15, "color": "#999999"},
    xanchor="right",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
