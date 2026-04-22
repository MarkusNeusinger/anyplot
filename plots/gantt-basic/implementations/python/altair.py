""" pyplots.ai
gantt-basic: Basic Gantt Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-27
"""

import altair as alt
import pandas as pd


# Data: Software development project phases
tasks = [
    {"task": "Requirements", "category": "Planning", "start": "2024-01-01", "end": "2024-01-15"},
    {"task": "System Design", "category": "Planning", "start": "2024-01-10", "end": "2024-01-28"},
    {"task": "UI Mockups", "category": "Design", "start": "2024-01-20", "end": "2024-02-05"},
    {"task": "Database Schema", "category": "Design", "start": "2024-01-25", "end": "2024-02-10"},
    {"task": "Backend Development", "category": "Development", "start": "2024-02-01", "end": "2024-03-15"},
    {"task": "Frontend Development", "category": "Development", "start": "2024-02-10", "end": "2024-03-20"},
    {"task": "API Integration", "category": "Development", "start": "2024-03-01", "end": "2024-03-25"},
    {"task": "Unit Testing", "category": "Testing", "start": "2024-03-10", "end": "2024-04-01"},
    {"task": "Integration Testing", "category": "Testing", "start": "2024-03-20", "end": "2024-04-10"},
    {"task": "User Acceptance", "category": "Testing", "start": "2024-04-01", "end": "2024-04-15"},
    {"task": "Documentation", "category": "Deployment", "start": "2024-04-05", "end": "2024-04-18"},
    {"task": "Deployment", "category": "Deployment", "start": "2024-04-15", "end": "2024-04-22"},
]

df = pd.DataFrame(tasks)
df["start"] = pd.to_datetime(df["start"])
df["end"] = pd.to_datetime(df["end"])

# Order tasks by start date for logical display
df = df.sort_values("start", ascending=False).reset_index(drop=True)
task_order = df["task"].tolist()

# Color scheme using Python Blue/Yellow and colorblind-safe colors
category_colors = {
    "Planning": "#306998",  # Python Blue
    "Design": "#FFD43B",  # Python Yellow
    "Development": "#4C9A2A",  # Green
    "Testing": "#C73E1D",  # Red-orange
    "Deployment": "#8B5CF6",  # Purple
}

# Create the Gantt chart
chart = (
    alt.Chart(df)
    .mark_bar(height=35, cornerRadius=4)
    .encode(
        x=alt.X(
            "start:T",
            title="Timeline",
            axis=alt.Axis(format="%b %d", labelFontSize=16, titleFontSize=20, labelAngle=-45, tickCount=12),
        ),
        x2="end:T",
        y=alt.Y(
            "task:N", title="Tasks", sort=task_order, axis=alt.Axis(labelFontSize=16, titleFontSize=20, labelLimit=200)
        ),
        color=alt.Color(
            "category:N",
            title="Phase",
            scale=alt.Scale(domain=list(category_colors.keys()), range=list(category_colors.values())),
            legend=alt.Legend(titleFontSize=18, labelFontSize=16, orient="right", titlePadding=10, symbolSize=300),
        ),
        tooltip=[
            alt.Tooltip("task:N", title="Task"),
            alt.Tooltip("category:N", title="Phase"),
            alt.Tooltip("start:T", title="Start", format="%B %d, %Y"),
            alt.Tooltip("end:T", title="End", format="%B %d, %Y"),
        ],
    )
    .properties(
        width=1400,
        height=800,
        title=alt.Title(text="gantt-basic · altair · pyplots.ai", fontSize=28, anchor="middle", offset=20),
    )
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save as PNG (1400 * 3 = 4200, close to 4800; adjusted for bar chart proportions)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart.interactive().save("plot.html")
