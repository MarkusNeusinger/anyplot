""" anyplot.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-06-02
"""

import os
import sys
import time
from pathlib import Path


# Prevent this file from shadowing the installed bokeh package
_this = str(Path(__file__).parent.resolve())
sys.path = [p for p in sys.path if p not in ("", _this)]

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import BoxAnnotation, ColumnDataSource, HoverTool, LabelSet, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint palette + theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint categorical palette — positions 1-4 for 4 project phases
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — software development project with task dependencies
tasks_data = [
    # Requirements Phase
    {
        "task": "Requirements Gathering",
        "start": "2026-01-06",
        "end": "2026-01-10",
        "group": "Requirements",
        "depends_on": [],
    },
    {
        "task": "Stakeholder Review",
        "start": "2026-01-13",
        "end": "2026-01-15",
        "group": "Requirements",
        "depends_on": ["Requirements Gathering"],
    },
    {
        "task": "Requirements Sign-off",
        "start": "2026-01-16",
        "end": "2026-01-17",
        "group": "Requirements",
        "depends_on": ["Stakeholder Review"],
    },
    # Design Phase
    {
        "task": "System Architecture",
        "start": "2026-01-20",
        "end": "2026-01-24",
        "group": "Design",
        "depends_on": ["Requirements Sign-off"],
    },
    {
        "task": "Database Design",
        "start": "2026-01-27",
        "end": "2026-01-30",
        "group": "Design",
        "depends_on": ["System Architecture"],
    },
    {
        "task": "UI/UX Design",
        "start": "2026-01-27",
        "end": "2026-01-31",
        "group": "Design",
        "depends_on": ["System Architecture"],
    },
    # Development Phase
    {
        "task": "Backend Core",
        "start": "2026-02-03",
        "end": "2026-02-14",
        "group": "Development",
        "depends_on": ["Database Design"],
    },
    {
        "task": "Frontend Core",
        "start": "2026-02-03",
        "end": "2026-02-12",
        "group": "Development",
        "depends_on": ["UI/UX Design"],
    },
    {
        "task": "API Integration",
        "start": "2026-02-17",
        "end": "2026-02-21",
        "group": "Development",
        "depends_on": ["Backend Core", "Frontend Core"],
    },
    # Testing Phase
    {
        "task": "Unit Testing",
        "start": "2026-02-17",
        "end": "2026-02-21",
        "group": "Testing",
        "depends_on": ["Backend Core"],
    },
    {
        "task": "Integration Testing",
        "start": "2026-02-24",
        "end": "2026-02-28",
        "group": "Testing",
        "depends_on": ["API Integration", "Unit Testing"],
    },
    {
        "task": "User Acceptance",
        "start": "2026-03-03",
        "end": "2026-03-07",
        "group": "Testing",
        "depends_on": ["Integration Testing"],
    },
]

df = pd.DataFrame(tasks_data)
df["start"] = pd.to_datetime(df["start"])
df["end"] = pd.to_datetime(df["end"])
df["duration"] = (df["end"] - df["start"]).dt.days

task_lookup = {row["task"]: idx for idx, row in df.iterrows()}

# Critical path — forward/backward pass through dependency graph
successors = {row["task"]: [] for _, row in df.iterrows()}
for _, row in df.iterrows():
    for dep in row["depends_on"]:
        if dep in successors:
            successors[dep].append(row["task"])

lp_to = {}
for _, row in df.iterrows():
    task = row["task"]
    dur = row["duration"]
    if not row["depends_on"]:
        lp_to[task] = dur
    else:
        lp_to[task] = max(lp_to[dep] for dep in row["depends_on"] if dep in lp_to) + dur

lp_from = {}
for _, row in df.sort_values("end", ascending=False).iterrows():
    task = row["task"]
    dur = row["duration"]
    if not successors[task]:
        lp_from[task] = dur
    else:
        lp_from[task] = dur + max(lp_from[s] for s in successors[task])

max_lp = max(lp_to.values())
critical_tasks = {t for t in lp_to if lp_to[t] + lp_from[t] - df.iloc[task_lookup[t]]["duration"] == max_lp}

# Imprint palette positions 1–4 for project phases
groups = ["Requirements", "Design", "Development", "Testing"]
group_colors = dict(zip(groups, IMPRINT_PALETTE[:4], strict=False))

# Group aggregate span bars
group_spans = {}
for group in groups:
    gdf = df[df["group"] == group]
    group_spans[group] = {"start": gdf["start"].min(), "end": gdf["end"].max()}

# Y-positions: group header row then indented task rows
y_positions = {}
y_labels = []
y_is_group = []
current_y = 0

for group in groups:
    y_positions[f"__group__{group}"] = current_y
    y_labels.append((current_y, group))
    y_is_group.append(True)
    current_y += 1
    for task in df[df["group"] == group]["task"].tolist():
        y_positions[task] = current_y
        y_labels.append((current_y, f"   {task}"))
        y_is_group.append(False)
        current_y += 1

max_y = current_y

# Title — 48 chars < 67 char baseline, no scaling needed → 50pt
title_text = "gantt-dependencies · python · bokeh · anyplot.ai"
n_title = len(title_text)
title_fs = f"{max(34, round(50 * 67 / n_title))}pt" if n_title > 67 else "50pt"

# Figure — 3200×1800 landscape canvas (hard rule)
p = figure(
    width=3200,
    height=1800,
    x_axis_type="datetime",
    y_range=(max_y + 0.5, -0.5),
    title=title_text,
    x_axis_label="Timeline (Weeks)",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=50,
    min_border_top=110,
    min_border_right=60,
)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = title_fs
p.title.text_color = INK
p.title.text_font_style = "bold"

p.xaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.visible = False

p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.12
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_alpha = 0.0

# Alternating row bands (theme-adaptive subtle tint)
for i in range(max_y):
    if i % 2 == 0:
        p.add_layout(
            BoxAnnotation(
                bottom=i - 0.5, top=i + 0.5, fill_color=INK, fill_alpha=0.04, level="underlay", line_color=None
            )
        )

# Group aggregate span bars (semi-transparent)
group_renderers = {}
for group in groups:
    span = group_spans[group]
    y = y_positions[f"__group__{group}"]
    src = ColumnDataSource(data={"y": [y], "left": [span["start"]], "right": [span["end"]]})
    r = p.hbar(y="y", left="left", right="right", height=0.7, color=group_colors[group], alpha=0.2, source=src)
    group_renderers[group] = r

# Task bars — per-group renderers so legend swatches show full-saturation phase colors
group_task_renderers = {}
for group in groups:
    gdf = df[df["group"] == group]
    gys, glefts, grights = [], [], []
    gnames, ggroups, gstarts, gends, gdurations, gdeps, gcrit = [], [], [], [], [], [], []
    for _, row in gdf.iterrows():
        gys.append(y_positions[row["task"]])
        glefts.append(row["start"])
        grights.append(row["end"])
        gnames.append(row["task"])
        ggroups.append(row["group"])
        gstarts.append(row["start"].strftime("%b %d, %Y"))
        gends.append(row["end"].strftime("%b %d, %Y"))
        gdurations.append(f"{row['duration']} days")
        deps = row["depends_on"]
        gdeps.append(", ".join(deps) if deps else "None")
        gcrit.append("★ Critical Path" if row["task"] in critical_tasks else "")
    gsrc = ColumnDataSource(
        data={
            "y": gys,
            "left": glefts,
            "right": grights,
            "task_name": gnames,
            "group_name": ggroups,
            "start_str": gstarts,
            "end_str": gends,
            "duration": gdurations,
            "dependencies": gdeps,
            "critical": gcrit,
        }
    )
    gr = p.hbar(
        y="y",
        left="left",
        right="right",
        height=0.5,
        fill_color=group_colors[group],
        fill_alpha=0.9,
        line_color=PAGE_BG,
        line_width=1,
        source=gsrc,
    )
    group_task_renderers[group] = gr

# Critical path border overlay (dark outline on critical tasks)
for _, row in df.iterrows():
    if row["task"] in critical_tasks:
        y = y_positions[row["task"]]
        src = ColumnDataSource(data={"y": [y], "left": [row["start"]], "right": [row["end"]]})
        p.hbar(y="y", left="left", right="right", height=0.54, fill_alpha=0, line_color=INK, line_width=5, source=src)

# Dependency arrows — improved visibility for non-critical (theme-adaptive INK_SOFT)
crit_arrow_xs, crit_arrow_ys = [], []
norm_arrow_xs, norm_arrow_ys = [], []
crit_head_xs, crit_head_ys = [], []
norm_head_xs, norm_head_ys = [], []

for _, row in df.iterrows():
    task_name = row["task"]
    task_y = y_positions[task_name]
    task_start_ms = row["start"].value / 1e6
    is_task_critical = task_name in critical_tasks

    for dep_name in row["depends_on"]:
        if dep_name in task_lookup:
            dep_row = df.iloc[task_lookup[dep_name]]
            dep_end_ms = dep_row["end"].value / 1e6
            dep_y = y_positions[dep_name]
            is_crit_dep = is_task_critical and dep_name in critical_tasks

            h_offset = 1.0 * 24 * 60 * 60 * 1000
            if task_y != dep_y:
                mid_x = dep_end_ms + h_offset
                xs = [dep_end_ms, mid_x, mid_x, task_start_ms]
                ys = [dep_y, dep_y, task_y, task_y]
            else:
                xs = [dep_end_ms, task_start_ms]
                ys = [dep_y, task_y]

            arrow_size = 3.5 * 24 * 60 * 60 * 1000
            hxs = [task_start_ms - arrow_size, task_start_ms, task_start_ms - arrow_size]
            hys = [task_y - 0.18, task_y, task_y + 0.18]

            if is_crit_dep:
                crit_arrow_xs.append(xs)
                crit_arrow_ys.append(ys)
                crit_head_xs.append(hxs)
                crit_head_ys.append(hys)
            else:
                norm_arrow_xs.append(xs)
                norm_arrow_ys.append(ys)
                norm_head_xs.append(hxs)
                norm_head_ys.append(hys)

dep_renderer = None
if norm_arrow_xs:
    dep_renderer = p.multi_line(
        xs=norm_arrow_xs, ys=norm_arrow_ys, line_color=INK_SOFT, line_width=2.5, line_alpha=0.65
    )
    p.patches(xs=norm_head_xs, ys=norm_head_ys, fill_color=INK_SOFT, fill_alpha=0.65, line_color=INK_SOFT, line_width=1)

crit_dep_renderer = None
if crit_arrow_xs:
    crit_dep_renderer = p.multi_line(xs=crit_arrow_xs, ys=crit_arrow_ys, line_color=INK, line_width=4, line_alpha=0.9)
    p.patches(xs=crit_head_xs, ys=crit_head_ys, fill_color=INK, fill_alpha=0.9, line_color=INK, line_width=1)

# Custom y-axis labels via LabelSet (reduced left padding: 12 days vs previous 14)
group_label_ys, group_label_texts = [], []
task_label_ys, task_label_texts = [], []

for (y, label), is_group in zip(y_labels, y_is_group, strict=True):
    if is_group:
        group_label_ys.append(y)
        group_label_texts.append(label)
    else:
        task_label_ys.append(y)
        task_label_texts.append(label)

label_x = df["start"].min() - pd.Timedelta(days=1)

p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=ColumnDataSource(
            data={"y": group_label_ys, "text": group_label_texts, "x": [label_x] * len(group_label_ys)}
        ),
        text_font_size="30pt",
        text_font_style="bold",
        text_align="right",
        x_offset=-10,
        text_baseline="middle",
        text_color=INK,
    )
)

p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=ColumnDataSource(
            data={"y": task_label_ys, "text": task_label_texts, "x": [label_x] * len(task_label_ys)}
        ),
        text_font_size="22pt",
        text_align="right",
        x_offset=-10,
        text_baseline="middle",
        text_color=INK_SOFT,
    )
)

# X range — 12-day left padding (reduced from 14) to minimise unused canvas space
x_min = df["start"].min() - pd.Timedelta(days=12)
x_max = df["end"].max() + pd.Timedelta(days=2)
p.x_range.start = x_min
p.x_range.end = x_max

# Legend — use full-opacity task-bar renderers so swatches show full-saturation phase colors
legend_items = []
for group in groups:
    legend_items.append(LegendItem(label=group, renderers=[group_task_renderers[group]]))
if dep_renderer:
    legend_items.append(LegendItem(label="Dependency", renderers=[dep_renderer]))
if crit_dep_renderer:
    legend_items.append(LegendItem(label="Critical Path", renderers=[crit_dep_renderer]))

legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="28pt",
    label_text_color=INK_SOFT,
    spacing=12,
    padding=20,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.9,
    border_line_color=INK_SOFT,
    border_line_width=1,
)
p.add_layout(legend)

# Hover tool for interactive HTML
hover = HoverTool(
    renderers=list(group_task_renderers.values()),
    tooltips=[
        ("Task", "@task_name"),
        ("Phase", "@group_name"),
        ("Start", "@start_str"),
        ("End", "@end_str"),
        ("Duration", "@duration"),
        ("Dependencies", "@dependencies"),
        ("Status", "@critical"),
    ],
)
p.add_tools(hover)

# Save interactive HTML
output_file(f"plot-{THEME}.html", title=title_text)
save(p)

# Save PNG via headless Chrome (Selenium + CDP for exact 3200×1800 viewport)
W, H = 3200, 1800
opts = Options()
for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--hide-scrollbars"):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
