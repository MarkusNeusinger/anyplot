""" pyplots.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: pygal 3.1.0 | Python 3.14
Quality: 81/100 | Updated: 2026-03-06
"""

import re
from datetime import date, timedelta

import cairosvg
import pygal
from pygal.style import Style


# Software Development Project with Dependencies
# Each tuple: (task_id, task_name, category, start_date, end_date, depends_on_ids)
tasks = [
    (1, "Requirements Gathering", "Requirements", date(2025, 1, 6), date(2025, 1, 17), []),
    (2, "Stakeholder Interviews", "Requirements", date(2025, 1, 20), date(2025, 1, 31), [1]),
    (3, "Requirements Document", "Requirements", date(2025, 2, 3), date(2025, 2, 14), [2]),
    (4, "Architecture Design", "Design", date(2025, 2, 17), date(2025, 2, 28), [3]),
    (5, "UI/UX Design", "Design", date(2025, 2, 17), date(2025, 3, 7), [3]),
    (6, "Database Schema", "Design", date(2025, 3, 3), date(2025, 3, 14), [4]),
    (7, "API Specification", "Design", date(2025, 3, 3), date(2025, 3, 14), [4]),
    (8, "Backend Development", "Development", date(2025, 3, 17), date(2025, 4, 11), [6, 7]),
    (9, "Frontend Development", "Development", date(2025, 3, 17), date(2025, 4, 11), [5, 7]),
    (10, "Integration", "Development", date(2025, 4, 14), date(2025, 4, 25), [8, 9]),
    (11, "Unit Testing", "Testing", date(2025, 4, 14), date(2025, 5, 2), [8]),
    (12, "Integration Testing", "Testing", date(2025, 4, 28), date(2025, 5, 9), [10]),
    (13, "User Acceptance Testing", "Testing", date(2025, 5, 12), date(2025, 5, 23), [12]),
    (14, "Deployment Prep", "Deployment", date(2025, 5, 12), date(2025, 5, 19), [12]),
    (15, "Production Deployment", "Deployment", date(2025, 5, 26), date(2025, 5, 30), [13, 14]),
    (16, "Post-Launch Support", "Deployment", date(2025, 6, 2), date(2025, 6, 13), [15]),
]

task_by_id = {t[0]: t for t in tasks}
reference = date(2025, 1, 1)

categories = ["Requirements", "Design", "Development", "Testing", "Deployment"]
cat_colors = {
    "Requirements": "#306998",
    "Design": "#E6A817",
    "Development": "#2A9D8F",
    "Testing": "#E76F51",
    "Deployment": "#7B68AE",
}

# Critical path: tasks with zero float (longest dependency chain)
critical_ids = {1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 13, 15, 16}

# Phase aggregate spans
phase_spans = {}
for cat in categories:
    cat_tasks = [t for t in tasks if t[2] == cat]
    phase_spans[cat] = (min(t[3] for t in cat_tasks), max(t[4] for t in cat_tasks))

all_dates = [d for t in tasks for d in (t[3], t[4])]
start_day = (min(all_dates) - reference).days - 5
end_day = (max(all_dates) - reference).days + 5
day_range = end_day - start_day

# Display rows bottom-to-top (pygal x_labels[0] = bottom row)
display_rows = []
for cat in reversed(categories):
    for t in reversed([t for t in tasks if t[2] == cat]):
        display_rows.append(("task", t))
    display_rows.append(("phase", cat))

num_rows = len(display_rows)

# Build HorizontalStackedBar data: transparent offset + colored category duration
# This uses pygal's stacking to position Gantt bars at correct timeline positions
offset_data = []
cat_series = {c: [] for c in categories}

for row_type, row_data in display_rows:
    if row_type == "phase":
        cat = row_data
        ps, pe = phase_spans[cat]
        offset = (ps - reference).days - start_day
        dur = (pe - ps).days
        offset_data.append(offset)
        for c in categories:
            if c == cat:
                cat_series[c].append({"value": dur, "style": "fill-opacity:0.3;stroke-width:2.5;stroke-opacity:0.6"})
            else:
                cat_series[c].append(None)
    else:
        tid, name, category, s, e, deps = row_data
        offset = (s - reference).days - start_day
        dur = (e - s).days
        offset_data.append(offset)
        is_crit = tid in critical_ids
        for c in categories:
            if c == category:
                style = (
                    "fill-opacity:0.95;stroke:#2a2a2a;stroke-width:2.5"
                    if is_crit
                    else "fill-opacity:0.65;stroke-dasharray:8,4;stroke-width:1;stroke:#999"
                )
                cat_series[c].append({"value": dur, "style": style})
            else:
                cat_series[c].append(None)

# Row labels
row_labels = []
for row_type, row_data in display_rows:
    if row_type == "phase":
        row_labels.append(f"\u25b6 {row_data}")
    else:
        row_labels.append(f"  {row_data[1]}")

# Style: first color transparent (offset series), then category colors
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#dddddd",
    colors=("rgba(0,0,0,0)", "#306998", "#E6A817", "#2A9D8F", "#E76F51", "#7B68AE"),
    title_font_size=56,
    label_font_size=24,
    major_label_font_size=26,
    legend_font_size=26,
    value_font_size=20,
    font_family="Consolas, monospace",
)

# Month boundary positions for value axis guides
month_positions = [(date(2025, m, 1) - reference).days - start_day for m in range(1, 7)]

chart = pygal.HorizontalStackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="gantt-dependencies \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=False,
    print_values=False,
    show_y_guides=True,
    show_x_guides=False,
    show_y_labels=True,
    show_x_labels=True,
    y_labels=month_positions,
    value_formatter=lambda v: (reference + timedelta(days=int(round(v)) + start_day)).strftime("%b %Y"),
    margin=60,
    margin_bottom=180,
    spacing=4,
    range=(0, day_range),
    rounded_bars=6,
)

chart.x_labels = row_labels

# Add real data series - pygal renders the actual bars
chart.add("", offset_data)
for cat in categories:
    chart.add(cat, cat_series[cat])

# Render SVG with pygal's charting engine
svg_string = chart.render().decode("utf-8")

# Extract plot area coordinates from rendered SVG for arrow positioning
plot_left, plot_top, plot_w, plot_h = 580, 140, 4100, 2200

m1 = re.search(r'class="plot[^"]*"[^>]*transform="translate\(([\d.]+)[, ]+([\d.]+)\)"', svg_string)
if not m1:
    m1 = re.search(r'transform="translate\(([\d.]+)[, ]+([\d.]+)\)"[^>]*class="plot', svg_string)
if m1:
    plot_left, plot_top = float(m1.group(1)), float(m1.group(2))

m2 = re.search(r'class="plot_background"[^>]*width="([\d.]+)"[^>]*height="([\d.]+)"', svg_string)
if not m2:
    m2 = re.search(r'width="([\d.]+)"[^>]*height="([\d.]+)"[^>]*class="plot_background"', svg_string)
if m2:
    plot_w, plot_h = float(m2.group(1)), float(m2.group(2))

row_h = plot_h / num_rows

# Calculate bar positions from data values for dependency arrows
bar_pos = {}
for i, (row_type, row_data) in enumerate(display_rows):
    if row_type != "task":
        continue
    tid, _, _, s, e, _ = row_data
    off = (s - reference).days - start_day
    dur = (e - s).days
    bar_pos[tid] = {
        "xs": plot_left + (off / day_range) * plot_w,
        "xe": plot_left + ((off + dur) / day_range) * plot_w,
        "yc": plot_top + plot_h - (i + 0.5) * row_h,
    }

# Custom SVG elements: arrow markers, dependency arrows, legend
custom = []

# Arrowhead markers for critical and non-critical dependency arrows
custom.append(
    "<defs>"
    '<marker id="darr" markerWidth="14" markerHeight="10" refX="13" refY="5" orient="auto">'
    '<polygon points="0 0,14 5,0 10" fill="#777"/>'
    "</marker>"
    '<marker id="carr" markerWidth="14" markerHeight="10" refX="13" refY="5" orient="auto">'
    '<polygon points="0 0,14 5,0 10" fill="#c0392b"/>'
    "</marker>"
    "</defs>"
)

# Alternating row backgrounds
for i in range(num_rows):
    y_top = plot_top + plot_h - (i + 1) * row_h
    row_type = display_rows[i][0]
    if row_type == "phase":
        custom.append(
            f'<rect x="{plot_left}" y="{y_top:.1f}" width="{plot_w}" '
            f'height="{row_h:.1f}" fill="#f0f0f0" opacity="0.5"/>'
        )
    elif i % 2 == 0:
        custom.append(
            f'<rect x="{plot_left}" y="{y_top:.1f}" width="{plot_w}" '
            f'height="{row_h:.1f}" fill="#f8f8f8" opacity="0.4"/>'
        )

# Diamond markers on phase aggregate bars
for i, (row_type, row_data) in enumerate(display_rows):
    if row_type != "phase":
        continue
    cat = row_data
    ps, pe = phase_spans[cat]
    off_s = (ps - reference).days - start_day
    off_e = (pe - reference).days - start_day
    x_s = plot_left + (off_s / day_range) * plot_w
    x_e = plot_left + (off_e / day_range) * plot_w
    yc = plot_top + plot_h - (i + 0.5) * row_h
    color = cat_colors[cat]
    ds = 11
    for dx in [x_s, x_e]:
        custom.append(
            f'<polygon points="{dx},{yc - ds} {dx + ds},{yc} '
            f'{dx},{yc + ds} {dx - ds},{yc}" fill="{color}" opacity="0.8"/>'
        )

# Dependency arrows with visual distinction for critical path
for tid, _, _, _, _, deps in tasks:
    if not deps:
        continue
    tgt = bar_pos[tid]
    for did in deps:
        src = bar_pos[did]
        x1, y1, x2, y2 = src["xe"], src["yc"], tgt["xs"], tgt["yc"]
        mx = x1 + (x2 - x1) * 0.5
        is_crit = tid in critical_ids and did in critical_ids
        if abs(y1 - y2) < 5:
            d = f"M{x1:.0f},{y1:.0f} L{x2:.0f},{y2:.0f}"
        else:
            d = f"M{x1:.0f},{y1:.0f} L{mx:.0f},{y1:.0f} L{mx:.0f},{y2:.0f} L{x2:.0f},{y2:.0f}"
        color, sw, marker, op = (
            ("#c0392b", "3.5", "url(#carr)", "0.85") if is_crit else ("#777", "2", "url(#darr)", "0.55")
        )
        custom.append(
            f'<path d="{d}" stroke="{color}" stroke-width="{sw}" fill="none" opacity="{op}" marker-end="{marker}"/>'
        )

# X-axis timeline label
custom.append(
    f'<text x="{plot_left + plot_w / 2}" y="{plot_top + plot_h + 80}" '
    f'font-family="Consolas, monospace" font-size="30" fill="#333" '
    f'text-anchor="middle" font-weight="bold">Project Timeline (Jan \u2013 Jun 2025)</text>'
)

# Custom legend
ly = plot_top + plot_h + 130
lx = plot_left + 30
sp = 560

for idx, cat in enumerate(categories):
    x = lx + idx * sp
    custom.append(f'<rect x="{x}" y="{ly}" width="24" height="24" fill="{cat_colors[cat]}" rx="4"/>')
    custom.append(
        f'<text x="{x + 34}" y="{ly + 19}" font-family="Consolas, monospace" font-size="26" fill="#333">{cat}</text>'
    )

# Critical path legend entry
cpx = lx + 5 * sp
custom.append(
    f'<line x1="{cpx}" y1="{ly + 12}" x2="{cpx + 40}" y2="{ly + 12}" '
    f'stroke="#c0392b" stroke-width="3.5" marker-end="url(#carr)"/>'
)
custom.append(
    f'<text x="{cpx + 52}" y="{ly + 19}" font-family="Consolas, monospace" '
    f'font-size="26" fill="#333">Critical Path</text>'
)

# Inject custom SVG elements and render PNG
svg_out = svg_string.replace("</svg>", "\n".join(custom) + "\n</svg>")
svg_out = svg_out.replace(">No data<", "><")

cairosvg.svg2png(bytestring=svg_out.encode(), write_to="plot.png")
