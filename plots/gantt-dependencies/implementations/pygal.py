"""pyplots.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: pygal 3.1.0 | Python 3.14
"""

from datetime import date

import cairosvg
import pygal
from pygal.style import Style


# Software Development Project with Dependencies
# Each tuple: (task_id, task_name, category, start_date, end_date, depends_on_ids)
tasks = [
    # Requirements Phase
    (1, "Requirements Gathering", "Requirements", date(2025, 1, 6), date(2025, 1, 17), []),
    (2, "Stakeholder Interviews", "Requirements", date(2025, 1, 20), date(2025, 1, 31), [1]),
    (3, "Requirements Document", "Requirements", date(2025, 2, 3), date(2025, 2, 14), [2]),
    # Design Phase
    (4, "Architecture Design", "Design", date(2025, 2, 17), date(2025, 2, 28), [3]),
    (5, "UI/UX Design", "Design", date(2025, 2, 17), date(2025, 3, 7), [3]),
    (6, "Database Schema", "Design", date(2025, 3, 3), date(2025, 3, 14), [4]),
    (7, "API Specification", "Design", date(2025, 3, 3), date(2025, 3, 14), [4]),
    # Development Phase
    (8, "Backend Development", "Development", date(2025, 3, 17), date(2025, 4, 11), [6, 7]),
    (9, "Frontend Development", "Development", date(2025, 3, 17), date(2025, 4, 11), [5, 7]),
    (10, "Integration", "Development", date(2025, 4, 14), date(2025, 4, 25), [8, 9]),
    # Testing Phase
    (11, "Unit Testing", "Testing", date(2025, 4, 14), date(2025, 5, 2), [8]),
    (12, "Integration Testing", "Testing", date(2025, 4, 28), date(2025, 5, 9), [10]),
    (13, "User Acceptance Testing", "Testing", date(2025, 5, 12), date(2025, 5, 23), [12]),
    # Deployment Phase
    (14, "Deployment Prep", "Deployment", date(2025, 5, 12), date(2025, 5, 19), [12]),
    (15, "Production Deployment", "Deployment", date(2025, 5, 26), date(2025, 5, 30), [13, 14]),
    (16, "Post-Launch Support", "Deployment", date(2025, 6, 2), date(2025, 6, 13), [15]),
]

task_by_id = {t[0]: t for t in tasks}
reference_date = date(2025, 1, 1)

categories_in_order = ["Requirements", "Design", "Development", "Testing", "Deployment"]
category_colors = {
    "Requirements": "#306998",
    "Design": "#E6A817",
    "Development": "#2A9D8F",
    "Testing": "#E76F51",
    "Deployment": "#7B68AE",
}

# Compute phase aggregate spans
phase_spans = {}
for cat in categories_in_order:
    phase_starts = [t[3] for t in tasks if t[2] == cat]
    phase_ends = [t[4] for t in tasks if t[2] == cat]
    phase_spans[cat] = (min(phase_starts), max(phase_ends))

all_dates = []
for _, _, _, start, end, _ in tasks:
    all_dates.extend([start, end])
min_date = min(all_dates)
max_date = max(all_dates)

# Build display rows in bottom-to-top order (pygal HorizontalBar renders x_labels[0] at bottom)
# Visual order top-to-bottom: Req header, Req tasks, Design header, Design tasks, ..., Deploy tasks
# So bottom-to-top: Deploy tasks (reversed), Deploy header, ..., Req tasks (reversed), Req header
display_rows = []
for cat in reversed(categories_in_order):
    cat_tasks = [t for t in tasks if t[2] == cat]
    for t in reversed(cat_tasks):
        display_rows.append(("task", t))
    display_rows.append(("phase", cat))

num_rows = len(display_rows)

# Custom style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=tuple(category_colors[c] for c in categories_in_order),
    title_font_size=56,
    label_font_size=26,
    major_label_font_size=26,
    legend_font_size=26,
    value_font_size=22,
    tooltip_font_size=22,
)

# Create pygal HorizontalBar chart as base
chart = pygal.HorizontalBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="gantt-dependencies \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=False,
    print_values=False,
    show_y_guides=False,
    show_x_guides=False,
    show_x_labels=False,
    margin=60,
    margin_bottom=180,
    spacing=8,
    range=(0, 100),
)

# Row labels in bottom-to-top order matching display_rows
row_labels = []
for row_type, row_data in display_rows:
    if row_type == "phase":
        row_labels.append(f"\u25b6 {row_data}")
    else:
        row_labels.append(f"  {row_data[1]}")

chart.x_labels = row_labels

# Add placeholder series per category for SVG structure
for cat in categories_in_order:
    chart.add(cat, [None] * num_rows)

svg_string = chart.render().decode("utf-8")

# Plot area coordinates
PLOT_LEFT = 580
PLOT_TOP = 140
PLOT_WIDTH = 4100
PLOT_HEIGHT = 2200

start_day = (min_date - reference_date).days - 5
end_day = (max_date - reference_date).days + 5
day_range = end_day - start_day

row_height = PLOT_HEIGHT / num_rows
task_bar_height = row_height * 0.55
phase_bar_height = row_height * 0.35

bar_positions = {}
custom_elements = []

# Alternating row backgrounds
# display_rows[i] is at y = PLOT_TOP + (num_rows - 1 - i) * row_height (bottom-to-top)
for i in range(num_rows):
    y_top = PLOT_TOP + (num_rows - 1 - i) * row_height
    row_type = display_rows[i][0]
    if row_type == "phase":
        custom_elements.append(
            f'<rect x="{PLOT_LEFT}" y="{y_top:.1f}" width="{PLOT_WIDTH}" '
            f'height="{row_height:.1f}" fill="#f0f0f0" opacity="0.5"/>'
        )
    elif i % 2 == 0:
        custom_elements.append(
            f'<rect x="{PLOT_LEFT}" y="{y_top:.1f}" width="{PLOT_WIDTH}" '
            f'height="{row_height:.1f}" fill="#f8f8f8" opacity="0.4"/>'
        )

# Month guide lines
for month in range(1, 7):
    month_date = date(2025, month, 1)
    day_val = (month_date - reference_date).days
    if start_day <= day_val <= end_day:
        x_pos = PLOT_LEFT + ((day_val - start_day) / day_range) * PLOT_WIDTH
        month_name = month_date.strftime("%b")
        custom_elements.append(
            f'<line x1="{x_pos:.1f}" y1="{PLOT_TOP}" x2="{x_pos:.1f}" '
            f'y2="{PLOT_TOP + PLOT_HEIGHT}" stroke="#d0d0d0" stroke-width="1.5" '
            f'stroke-dasharray="8,4"/>'
        )
        custom_elements.append(
            f'<text x="{x_pos:.1f}" y="{PLOT_TOP + PLOT_HEIGHT + 40}" '
            f'font-family="Consolas, monospace" font-size="28" fill="#555" '
            f'text-anchor="middle">{month_name} 2025</text>'
        )

# X-axis label
custom_elements.append(
    f'<text x="{PLOT_LEFT + PLOT_WIDTH / 2}" y="{PLOT_TOP + PLOT_HEIGHT + 80}" '
    f'font-family="Consolas, monospace" font-size="30" fill="#333" '
    f'text-anchor="middle" font-weight="bold">Project Timeline (Jan \u2013 Jun 2025)</text>'
)

# Phase header bars and task bars
for i, (row_type, row_data) in enumerate(display_rows):
    # Row i renders at y position from bottom (i=0 is bottom row)
    y_center = PLOT_TOP + (num_rows - 1 - i + 0.5) * row_height

    if row_type == "phase":
        cat = row_data
        phase_start, phase_end = phase_spans[cat]
        start_day_val = (phase_start - reference_date).days
        end_day_val = (phase_end - reference_date).days
        x_start = PLOT_LEFT + ((start_day_val - start_day) / day_range) * PLOT_WIDTH
        x_end = PLOT_LEFT + ((end_day_val - start_day) / day_range) * PLOT_WIDTH
        width = x_end - x_start
        y_top = y_center - phase_bar_height / 2
        color = category_colors[cat]

        # Phase aggregate bar
        custom_elements.append(
            f'<rect x="{x_start:.1f}" y="{y_top:.1f}" width="{width:.1f}" '
            f'height="{phase_bar_height:.1f}" fill="{color}" rx="4" ry="4" '
            f'opacity="0.3" stroke="{color}" stroke-width="2.5"/>'
        )
        # Diamond markers at start and end of phase
        ds = 7
        for dx in [x_start, x_end]:
            custom_elements.append(
                f'<polygon points="{dx},{y_center - ds} '
                f"{dx + ds},{y_center} "
                f"{dx},{y_center + ds} "
                f'{dx - ds},{y_center}" '
                f'fill="{color}" opacity="0.8"/>'
            )
    else:
        task_id, task_name, category, start, end, deps = row_data
        start_day_val = (start - reference_date).days
        end_day_val = (end - reference_date).days
        x_start = PLOT_LEFT + ((start_day_val - start_day) / day_range) * PLOT_WIDTH
        x_end = PLOT_LEFT + ((end_day_val - start_day) / day_range) * PLOT_WIDTH
        width = x_end - x_start
        y_top = y_center - task_bar_height / 2
        color = category_colors[category]
        duration = (end - start).days

        bar_positions[task_id] = {"x_start": x_start, "x_end": x_end, "y_center": y_center}

        dep_names = [task_by_id[d][1] for d in deps] if deps else []
        dep_text = f"&#10;Depends on: {', '.join(dep_names)}" if dep_names else ""

        custom_elements.append(
            f'<rect x="{x_start:.1f}" y="{y_top:.1f}" width="{width:.1f}" '
            f'height="{task_bar_height:.1f}" fill="{color}" rx="6" ry="6" opacity="0.9">'
            f"<title>{task_name}&#10;{start.strftime('%b %d')} - {end.strftime('%b %d')} "
            f"({duration} days){dep_text}</title></rect>"
        )

# Dependency arrows
arrow_color = "#555555"
for task_id, _task_name, _category, _start, _end, deps in tasks:
    if not deps:
        continue
    target_pos = bar_positions[task_id]
    for dep_id in deps:
        source_pos = bar_positions[dep_id]
        x1 = source_pos["x_end"]
        y1 = source_pos["y_center"]
        x2 = target_pos["x_start"]
        y2 = target_pos["y_center"]
        mid_x = x1 + (x2 - x1) * 0.5

        if abs(y1 - y2) < 5:
            path = f"M {x1:.1f},{y1:.1f} L {x2:.1f},{y2:.1f}"
        else:
            path = f"M {x1:.1f},{y1:.1f} L {mid_x:.1f},{y1:.1f} L {mid_x:.1f},{y2:.1f} L {x2:.1f},{y2:.1f}"
        custom_elements.append(
            f'<path d="{path}" stroke="{arrow_color}" stroke-width="3.5" '
            f'fill="none" opacity="0.85" marker-end="url(#arrowhead)"/>'
        )

# Arrowhead marker
arrowhead_def = """
<defs>
  <marker id="arrowhead" markerWidth="14" markerHeight="10" refX="13" refY="5" orient="auto">
    <polygon points="0 0, 14 5, 0 10" fill="#555555" opacity="0.9"/>
  </marker>
</defs>
"""

# Custom legend - well below month labels to avoid overlap
legend_y = PLOT_TOP + PLOT_HEIGHT + 130
legend_x_start = PLOT_LEFT + 50
legend_spacing = 620

for idx, cat in enumerate(categories_in_order):
    lx = legend_x_start + idx * legend_spacing
    color = category_colors[cat]
    custom_elements.append(f'<rect x="{lx}" y="{legend_y}" width="24" height="24" fill="{color}" rx="4" ry="4"/>')
    custom_elements.append(
        f'<text x="{lx + 34}" y="{legend_y + 19}" '
        f'font-family="Consolas, monospace" font-size="26" fill="#333">{cat}</text>'
    )

# Dependency arrow legend entry
arrow_legend_x = legend_x_start + 5 * legend_spacing
custom_elements.append(
    f'<line x1="{arrow_legend_x}" y1="{legend_y + 12}" '
    f'x2="{arrow_legend_x + 40}" y2="{legend_y + 12}" '
    f'stroke="{arrow_color}" stroke-width="3.5" marker-end="url(#arrowhead)"/>'
)
custom_elements.append(
    f'<text x="{arrow_legend_x + 52}" y="{legend_y + 19}" '
    f'font-family="Consolas, monospace" font-size="26" fill="#333">Dependency</text>'
)

# Inject custom elements into SVG
svg_output = svg_string.replace("</svg>", f"{arrowhead_def}\n</svg>")
all_elements = "\n".join(custom_elements)
svg_output = svg_output.replace("</svg>", f"{all_elements}\n</svg>")
svg_output = svg_output.replace(">No data<", "><")

cairosvg.svg2png(bytestring=svg_output.encode(), write_to="plot.png")
