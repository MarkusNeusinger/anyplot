""" anyplot.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-06-02
"""

import os
import sys


# Remove script dir from sys.path to prevent self-import (file is named altair.py)
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.dirname(os.path.abspath(__file__))]

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — positions 1-5 for the 5 project phases
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
# Amber semantic anchor: "caution" role suits dependency lines (delays propagate)
DEP_COLOR = "#DDCC77"

# Data — Software Development Project with Dependencies
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

group_order = ["Requirements", "Design", "Development", "Testing", "Deployment"]
# Imprint positions 1→5 in canonical order (green, lavender, blue, ochre, matte-red)
group_colors = {g: IMPRINT_PALETTE[i] for i, g in enumerate(group_order)}

# Build display rows with ordinal task ordering (group headers + indented tasks)
task_order = []
chart_rows = []
for grp in group_order:
    grp_tasks = df[df["group"] == grp]
    label = f"▸ {grp}"
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

# Dependency data: 2 points per arrow using shared ordinal Y scale
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

# Title — 49 chars, under 67 baseline → use default 16px
title_str = "gantt-dependencies · python · altair · anyplot.ai"
title_fs = round(16 * min(1.0, 67 / len(title_str)))

# Y-axis: conditional bold + larger font for group headers
y_axis = alt.Axis(
    labelFontSize=alt.ExprRef("indexof(datum.value, '▸') >= 0 ? 18 : 16"),
    labelFontWeight=alt.ExprRef("indexof(datum.value, '▸') >= 0 ? 'bold' : 'normal'"),
    labelColor=INK_SOFT,
    labelLimit=270,
    ticks=False,
    domain=False,
    labelPadding=8,
)

# Task bars — colored by group, native bottom legend for phases
task_bars = (
    alt.Chart(chart_df[~chart_df["is_group"]])
    .mark_bar(cornerRadius=4)
    .encode(
        x=alt.X(
            "start:T",
            title="Project Timeline (2024)",
            axis=alt.Axis(format="%b %d", labelFontSize=16, titleFontSize=18, labelColor=INK_SOFT, titleColor=INK),
        ),
        x2="end:T",
        y=alt.Y("task:N", sort=task_order, title=None, axis=y_axis),
        color=alt.Color(
            "group:N",
            scale=alt.Scale(domain=group_order, range=[group_colors[g] for g in group_order]),
            legend=alt.Legend(
                orient="bottom",
                direction="horizontal",
                title=None,
                labelFontSize=16,
                symbolSize=280,
                symbolType="square",
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
                padding=8,
                labelColor=INK_SOFT,
                cornerRadius=4,
            ),
        ),
        tooltip=[
            "task:N",
            alt.Tooltip("start:T", format="%Y-%m-%d"),
            alt.Tooltip("end:T", format="%Y-%m-%d"),
            "group:N",
        ],
    )
)

# Group summary bars — thin, INK-colored to sit on the structural layer
group_bars = (
    alt.Chart(chart_df[chart_df["is_group"]])
    .mark_bar(cornerRadius=3, size=12, opacity=0.9)
    .encode(
        x="start:T",
        x2="end:T",
        y=alt.Y("task:N", sort=task_order),
        color=alt.value(INK),
        tooltip=["task:N", alt.Tooltip("start:T", format="%Y-%m-%d"), alt.Tooltip("end:T", format="%Y-%m-%d")],
    )
)

# Dependency lines — amber dashed (caution: delays propagate)
dep_lines = (
    alt.Chart(dep_line_df)
    .mark_line(strokeWidth=3.5, opacity=0.9, color=DEP_COLOR, strokeDash=[8, 4])
    .encode(x="x:T", y=alt.Y("task:N", sort=task_order), detail="dep_id:N")
)

# Arrowheads at successor start — size=300 for clear visibility
arrow_heads = (
    alt.Chart(dep_arrow_df)
    .mark_point(shape="triangle-right", size=300, filled=True, color=DEP_COLOR, opacity=0.95)
    .encode(x="x:T", y=alt.Y("task:N", sort=task_order))
)

# Dependency label — positioned above the chart area as a subtitle line
dep_label_df = pd.DataFrame([{"x": "2024-04-01", "label": "── ── ▶  Finish-to-start dependency"}])
dep_label = (
    alt.Chart(dep_label_df)
    .mark_text(fontSize=14, color=DEP_COLOR, align="right", fontStyle="italic")
    .encode(x=alt.X("x:T", axis=None), text="label:N")
    .properties(width=500, height=22)
)

# Main chart — inner view sized to land within 3200×1800 after vl-convert padding
main = alt.layer(group_bars, task_bars, dep_lines, arrow_heads).properties(
    width=500, height=280, title=alt.Title(title_str, fontSize=title_fs, color=INK, anchor="middle")
)

chart = (
    alt.vconcat(main, dep_label, spacing=2)
    .configure_axisX(grid=True, gridOpacity=0.15, gridDash=[3, 3], gridColor=INK)
    .configure_axisY(grid=False)
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        labelFontSize=16,
        symbolSize=280,
        padding=8,
        cornerRadius=4,
    )
    .properties(background=PAGE_BG)
)

# Save PNG then pad to exact 3200×1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        "Shrink chart .properties(width=, height=) and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
