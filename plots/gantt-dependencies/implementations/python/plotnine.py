""" anyplot.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 89/100 | Updated: 2026-06-02
"""

import os
from datetime import datetime, timedelta

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_datetime,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — 4 project phases (canonical order, positions 1–4)
group_colors = {"Requirements": "#009E73", "Design": "#C475FD", "Development": "#4467A3", "Testing": "#BD8233"}

# Data: software development project with finish-to-start dependencies
tasks_data = [
    {
        "task": "Gather Requirements",
        "start": datetime(2024, 1, 1),
        "end": datetime(2024, 1, 10),
        "group": "Requirements",
        "depends_on": [],
    },
    {
        "task": "Document Specs",
        "start": datetime(2024, 1, 10),
        "end": datetime(2024, 1, 17),
        "group": "Requirements",
        "depends_on": ["Gather Requirements"],
    },
    {
        "task": "Review & Approve",
        "start": datetime(2024, 1, 17),
        "end": datetime(2024, 1, 20),
        "group": "Requirements",
        "depends_on": ["Document Specs"],
    },
    {
        "task": "System Architecture",
        "start": datetime(2024, 1, 20),
        "end": datetime(2024, 1, 30),
        "group": "Design",
        "depends_on": ["Review & Approve"],
    },
    {
        "task": "Database Design",
        "start": datetime(2024, 1, 30),
        "end": datetime(2024, 2, 7),
        "group": "Design",
        "depends_on": ["System Architecture"],
    },
    {
        "task": "UI/UX Mockups",
        "start": datetime(2024, 1, 20),
        "end": datetime(2024, 2, 3),
        "group": "Design",
        "depends_on": ["Review & Approve"],
    },
    {
        "task": "Backend API",
        "start": datetime(2024, 2, 7),
        "end": datetime(2024, 2, 28),
        "group": "Development",
        "depends_on": ["Database Design"],
    },
    {
        "task": "Frontend Components",
        "start": datetime(2024, 2, 3),
        "end": datetime(2024, 2, 25),
        "group": "Development",
        "depends_on": ["UI/UX Mockups"],
    },
    {
        "task": "Integration",
        "start": datetime(2024, 2, 28),
        "end": datetime(2024, 3, 8),
        "group": "Development",
        "depends_on": ["Backend API", "Frontend Components"],
    },
    {
        "task": "Unit Testing",
        "start": datetime(2024, 2, 28),
        "end": datetime(2024, 3, 8),
        "group": "Testing",
        "depends_on": ["Backend API"],
    },
    {
        "task": "Integration Testing",
        "start": datetime(2024, 3, 8),
        "end": datetime(2024, 3, 15),
        "group": "Testing",
        "depends_on": ["Integration"],
    },
    {
        "task": "User Acceptance",
        "start": datetime(2024, 3, 15),
        "end": datetime(2024, 3, 21),
        "group": "Testing",
        "depends_on": ["Integration Testing"],
    },
]

df = pd.DataFrame(tasks_data)

# Critical path: longest finish-to-start chain through the project
critical_path_tasks = {
    "Gather Requirements",
    "Document Specs",
    "Review & Approve",
    "System Architecture",
    "Database Design",
    "Backend API",
    "Integration",
    "Integration Testing",
    "User Acceptance",
}

# Build y-axis positions — group header above each group's tasks
group_order = ["Requirements", "Design", "Development", "Testing"]
task_labels = {}
y_pos = 0
group_positions = {}
task_positions = {}

for grp in group_order:
    group_positions[grp] = y_pos
    task_labels[y_pos] = f"▸ {grp}"
    y_pos += 1
    for _, row in df[df["group"] == grp].iterrows():
        task_positions[row["task"]] = y_pos
        task_labels[y_pos] = f"   {row['task']}"
        y_pos += 1

# Group aggregate bars spanning each group's full date range
group_data = [
    {
        "y": group_positions[grp],
        "start": df[df["group"] == grp]["start"].min(),
        "end": df[df["group"] == grp]["end"].max(),
        "group": grp,
    }
    for grp in group_order
]

# Task bars split by critical path membership
critical_task_data = []
normal_task_data = []
for _, row in df.iterrows():
    entry = {"y": task_positions[row["task"]], "start": row["start"], "end": row["end"], "group": row["group"]}
    (critical_task_data if row["task"] in critical_path_tasks else normal_task_data).append(entry)

phase_order = pd.CategoricalDtype(categories=group_order, ordered=True)
groups_df = pd.DataFrame(group_data)
groups_df["group"] = groups_df["group"].astype(phase_order)
critical_df = pd.DataFrame(critical_task_data)
critical_df["group"] = critical_df["group"].astype(phase_order)
normal_df = pd.DataFrame(normal_task_data)
normal_df["group"] = normal_df["group"].astype(phase_order)

# L-shaped dependency connectors: vertical leg + horizontal leg + V-arrowhead
arrow_size_days = 1.8
arrow_wing = 0.22

vert_segs = []
horiz_segs = []
arrowhead_segs = []

for _, row in df.iterrows():
    for dep_name in row["depends_on"]:
        if dep_name not in task_positions:
            continue
        dep_row = df[df["task"] == dep_name].iloc[0]
        x_bend = dep_row["end"]
        x_target = row["start"]
        y_dep = task_positions[dep_name]
        y_task = task_positions[row["task"]]
        is_crit = dep_name in critical_path_tasks and row["task"] in critical_path_tasks

        vert_segs.append({"x_start": x_bend, "x_end": x_bend, "y_start": y_dep, "y_end": y_task, "critical": is_crit})
        horiz_segs.append(
            {
                "x_start": x_bend,
                "x_end": x_target - timedelta(days=arrow_size_days * 0.3),
                "y_start": y_task,
                "y_end": y_task,
                "critical": is_crit,
            }
        )
        # V-arrowhead: two lines converging at x_target
        arrowhead_segs.append(
            {
                "x_start": x_target - timedelta(days=arrow_size_days),
                "x_end": x_target,
                "y_start": y_task - arrow_wing,
                "y_end": y_task,
                "critical": is_crit,
            }
        )
        arrowhead_segs.append(
            {
                "x_start": x_target - timedelta(days=arrow_size_days),
                "x_end": x_target,
                "y_start": y_task + arrow_wing,
                "y_end": y_task,
                "critical": is_crit,
            }
        )

vert_df = pd.DataFrame(vert_segs)
horiz_df = pd.DataFrame(horiz_segs)
arrowhead_df = pd.DataFrame(arrowhead_segs)

crit_vert = vert_df[vert_df["critical"]]
norm_vert = vert_df[~vert_df["critical"]]
crit_horiz = horiz_df[horiz_df["critical"]]
norm_horiz = horiz_df[~horiz_df["critical"]]
crit_heads = arrowhead_df[arrowhead_df["critical"]]
norm_heads = arrowhead_df[~arrowhead_df["critical"]]

# Milestone diamonds at key phase-handoff points
milestones = pd.DataFrame(
    [
        {"x": datetime(2024, 1, 20), "y": task_positions["Review & Approve"]},
        {"x": datetime(2024, 2, 7), "y": task_positions["Database Design"]},
        {"x": datetime(2024, 2, 28), "y": task_positions["Backend API"]},
        {"x": datetime(2024, 3, 21), "y": task_positions["User Acceptance"]},
    ]
)

y_breaks = list(task_labels.keys())
y_labels_list = [task_labels[y] for y in y_breaks]

title = "gantt-dependencies · python · plotnine · anyplot.ai"
n = len(title)
title_fontsize = max(round(12 * 67 / n) if n > 67 else 12, 8)

plot = (
    ggplot()
    # Non-critical task bars (subdued)
    + geom_segment(
        data=normal_df,
        mapping=aes(x="start", xend="end", y="y", yend="y", color="group"),
        size=2,
        lineend="butt",
        alpha=0.5,
    )
    # Critical path task bars (prominent)
    + geom_segment(
        data=critical_df,
        mapping=aes(x="start", xend="end", y="y", yend="y", color="group"),
        size=2.5,
        lineend="butt",
        alpha=1.0,
    )
    # Group aggregate bars (boldest — slightly reduced to ease vertical crowding)
    + geom_segment(
        data=groups_df,
        mapping=aes(x="start", xend="end", y="y", yend="y", color="group"),
        size=3.5,
        lineend="butt",
        alpha=0.85,
    )
    # Non-critical connectors
    + geom_segment(
        data=norm_vert,
        mapping=aes(x="x_start", xend="x_end", y="y_start", yend="y_end"),
        color=INK_SOFT,
        size=0.4,
        alpha=0.7,
    )
    + geom_segment(
        data=norm_horiz,
        mapping=aes(x="x_start", xend="x_end", y="y_start", yend="y_end"),
        color=INK_SOFT,
        size=0.4,
        alpha=0.7,
    )
    + geom_segment(
        data=norm_heads,
        mapping=aes(x="x_start", xend="x_end", y="y_start", yend="y_end"),
        color=INK_SOFT,
        size=0.6,
        alpha=0.75,
    )
    # Critical path connectors (bolder, theme-ink color)
    + geom_segment(
        data=crit_vert,
        mapping=aes(x="x_start", xend="x_end", y="y_start", yend="y_end"),
        color=INK,
        size=0.6,
        alpha=0.9,
    )
    + geom_segment(
        data=crit_horiz,
        mapping=aes(x="x_start", xend="x_end", y="y_start", yend="y_end"),
        color=INK,
        size=0.6,
        alpha=0.9,
    )
    + geom_segment(
        data=crit_heads,
        mapping=aes(x="x_start", xend="x_end", y="y_start", yend="y_end"),
        color=INK,
        size=0.9,
        alpha=0.95,
    )
    # Milestone diamonds at phase-handoff points
    + geom_point(
        data=milestones, mapping=aes(x="x", y="y"), shape="D", size=2, color="#AE3030", fill="#AE3030", alpha=0.9
    )
    # Scales
    + scale_color_manual(values=group_colors, name="Project Phase", limits=group_order)
    + scale_y_continuous(breaks=y_breaks, labels=y_labels_list, trans="reverse")
    + scale_x_datetime(
        date_breaks="1 week", date_labels="%b %d", limits=(datetime(2023, 12, 29), datetime(2024, 3, 22))
    )
    # Labels
    + labs(
        title=title,
        subtitle="Bold bars & dark arrows = Critical Path  |  Subdued bars & muted arrows = Non-critical",
        x="Date (2024)",
        y="",
    )
    # Theme — Imprint palette chrome, theme-adaptive backgrounds and text
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=title_fontsize, weight="bold", color=INK, margin={"b": 3}),
        plot_subtitle=element_text(size=7, color=INK_SOFT, margin={"b": 5}),
        axis_title_x=element_text(size=10, color=INK),
        axis_text_x=element_text(size=7, color=INK_SOFT, rotation=45, ha="right"),
        axis_text_y=element_text(size=7, color=INK_SOFT, ha="right"),
        legend_title=element_text(size=8, weight="bold", color=INK),
        legend_text=element_text(size=7, color=INK_SOFT),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_key_size=8,
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color=INK, size=0.2, alpha=0.15),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_line=element_line(color=INK_SOFT),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
