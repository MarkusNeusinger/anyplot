""" pyplots.ai
gantt-basic: Basic Gantt Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-27
"""

from datetime import datetime

import pandas as pd
import plotly.express as px


# Data - Software Development Project Timeline
tasks = [
    {"task": "Requirements Analysis", "start": "2025-01-06", "end": "2025-01-17", "category": "Planning"},
    {"task": "System Design", "start": "2025-01-13", "end": "2025-01-31", "category": "Planning"},
    {"task": "Database Design", "start": "2025-01-27", "end": "2025-02-07", "category": "Design"},
    {"task": "UI/UX Design", "start": "2025-01-27", "end": "2025-02-14", "category": "Design"},
    {"task": "Backend Development", "start": "2025-02-03", "end": "2025-03-14", "category": "Development"},
    {"task": "Frontend Development", "start": "2025-02-10", "end": "2025-03-21", "category": "Development"},
    {"task": "API Integration", "start": "2025-03-03", "end": "2025-03-21", "category": "Development"},
    {"task": "Unit Testing", "start": "2025-03-10", "end": "2025-03-28", "category": "Testing"},
    {"task": "Integration Testing", "start": "2025-03-24", "end": "2025-04-04", "category": "Testing"},
    {"task": "User Acceptance Testing", "start": "2025-04-01", "end": "2025-04-11", "category": "Testing"},
    {"task": "Documentation", "start": "2025-03-17", "end": "2025-04-11", "category": "Deployment"},
    {"task": "Deployment & Launch", "start": "2025-04-07", "end": "2025-04-18", "category": "Deployment"},
]

df = pd.DataFrame(tasks)
df["start"] = pd.to_datetime(df["start"])
df["end"] = pd.to_datetime(df["end"])

# Sort by start date for logical ordering
df = df.sort_values("start").reset_index(drop=True)

# Color palette for categories (colorblind-safe)
color_map = {
    "Planning": "#306998",
    "Design": "#FFD43B",
    "Development": "#4ECDC4",
    "Testing": "#FF6B6B",
    "Deployment": "#95E1A3",
}

# Create Gantt chart using timeline
fig = px.timeline(df, x_start="start", x_end="end", y="task", color="category", color_discrete_map=color_map)

# Reverse y-axis so earliest tasks are at top
fig.update_yaxes(autorange="reversed")

# Add current date line (vertical marker)
today = datetime(2025, 2, 20)
fig.add_shape(
    type="line",
    x0=today,
    x1=today,
    y0=-0.5,
    y1=len(df) - 0.5,
    line={"color": "#E74C3C", "width": 3, "dash": "dash"},
    layer="above",
)
fig.add_annotation(
    x=today,
    y=len(df) - 0.5,
    text="Today",
    showarrow=False,
    font={"size": 18, "color": "#E74C3C", "family": "Arial Black"},
    yanchor="top",
    yshift=-5,
)

# Update layout for 4800x2700 px
fig.update_layout(
    title={
        "text": "Software Development Project · gantt-basic · plotly · pyplots.ai",
        "font": {"size": 32},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Timeline (2025)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "tickformat": "%b %d",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
    },
    yaxis={"title": {"text": "Project Tasks", "font": {"size": 24}}, "tickfont": {"size": 16}, "showgrid": False},
    template="plotly_white",
    legend={
        "title": {"text": "Category", "font": {"size": 20}},
        "font": {"size": 18},
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
    },
    margin={"l": 220, "r": 80, "t": 130, "b": 80},
    bargap=0.3,
)

# Update bar appearance
fig.update_traces(marker={"line": {"color": "white", "width": 1}}, opacity=0.9)

# Save as PNG
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
