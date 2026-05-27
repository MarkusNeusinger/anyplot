""" anyplot.ai
gantt-basic: Basic Gantt Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-10
"""

import os
import sys


sys.modules.pop("altair", None)
sys.path = [p for p in sys.path if p not in ("", ".", os.getcwd())]

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

tasks = [
    {"task": "Project Planning", "category": "Planning", "start": "2024-01-02", "end": "2024-01-18"},
    {"task": "Requirements Analysis", "category": "Planning", "start": "2024-01-05", "end": "2024-01-25"},
    {"task": "System Architecture", "category": "Design", "start": "2024-01-22", "end": "2024-02-12"},
    {"task": "UI/UX Design", "category": "Design", "start": "2024-01-29", "end": "2024-02-16"},
    {"task": "Database Design", "category": "Design", "start": "2024-02-05", "end": "2024-02-22"},
    {"task": "Backend Development", "category": "Development", "start": "2024-02-19", "end": "2024-04-08"},
    {"task": "Frontend Development", "category": "Development", "start": "2024-02-26", "end": "2024-04-15"},
    {"task": "API Development", "category": "Development", "start": "2024-03-11", "end": "2024-03-29"},
    {"task": "Unit Testing", "category": "Testing", "start": "2024-03-25", "end": "2024-04-22"},
    {"task": "Integration Testing", "category": "Testing", "start": "2024-04-08", "end": "2024-04-29"},
    {"task": "UAT & Bug Fixes", "category": "Testing", "start": "2024-04-22", "end": "2024-05-10"},
    {"task": "Documentation", "category": "Deployment", "start": "2024-04-15", "end": "2024-05-03"},
    {"task": "Deployment Prep", "category": "Deployment", "start": "2024-05-01", "end": "2024-05-13"},
]

df = pd.DataFrame(tasks)
df["start"] = pd.to_datetime(df["start"])
df["end"] = pd.to_datetime(df["end"])

df = df.sort_values("start", ascending=True).reset_index(drop=True)
task_order = df["task"].tolist()

category_map = {
    "Planning": IMPRINT[0],
    "Design": IMPRINT[1],
    "Development": IMPRINT[2],
    "Testing": IMPRINT[3],
    "Deployment": IMPRINT[4],
}

chart = (
    alt.Chart(df)
    .mark_bar(height=32, cornerRadius=3)
    .encode(
        x=alt.X(
            "start:T",
            title="Project Timeline 2024",
            axis=alt.Axis(
                format="%b %d",
                labelFontSize=18,
                titleFontSize=22,
                labelAngle=-45,
                tickCount=14,
                domainColor=INK_SOFT,
                tickColor=INK_SOFT,
                gridColor=INK_SOFT,
                gridOpacity=0.08,
            ),
        ),
        x2="end:T",
        y=alt.Y(
            "task:N",
            title="Tasks",
            sort=task_order,
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelLimit=250, domainColor=INK_SOFT, tickColor=INK_SOFT),
        ),
        color=alt.Color(
            "category:N",
            title="Phase",
            scale=alt.Scale(domain=list(category_map.keys()), range=list(category_map.values())),
            legend=alt.Legend(
                titleFontSize=20,
                labelFontSize=18,
                orient="right",
                titlePadding=15,
                symbolSize=280,
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
                labelColor=INK_SOFT,
                titleColor=INK,
            ),
        ),
        tooltip=[
            alt.Tooltip("task:N", title="Task"),
            alt.Tooltip("category:N", title="Phase"),
            alt.Tooltip("start:T", title="Start Date", format="%B %d, %Y"),
            alt.Tooltip("end:T", title="End Date", format="%B %d, %Y"),
        ],
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title(text="gantt-basic · altair · anyplot.ai", fontSize=28, anchor="middle", offset=20, color=INK),
        background=PAGE_BG,
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(gridColor=INK_SOFT, gridOpacity=0.08, labelColor=INK_SOFT, titleColor=INK)
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.interactive().save(f"plot-{THEME}.html")
