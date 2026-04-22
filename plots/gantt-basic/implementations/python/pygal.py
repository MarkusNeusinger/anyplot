""" pyplots.ai
gantt-basic: Basic Gantt Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-27
"""

from datetime import date

import cairosvg
import pygal
from pygal.style import Style


# Custom style for large canvas (4800x2700)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#2E8B57", "#DC143C", "#9370DB"),
    title_font_size=60,
    label_font_size=28,
    major_label_font_size=28,
    legend_font_size=28,
    value_font_size=24,
    tooltip_font_size=24,
)

# Project data: Software Development Project
# Each tuple: (task_name, category, start_date, end_date)
tasks = [
    ("Requirements Analysis", "Planning", date(2025, 1, 6), date(2025, 1, 17)),
    ("System Design", "Planning", date(2025, 1, 13), date(2025, 1, 31)),
    ("Database Design", "Design", date(2025, 1, 27), date(2025, 2, 7)),
    ("UI/UX Design", "Design", date(2025, 1, 20), date(2025, 2, 14)),
    ("Backend Development", "Development", date(2025, 2, 3), date(2025, 3, 14)),
    ("Frontend Development", "Development", date(2025, 2, 10), date(2025, 3, 21)),
    ("API Integration", "Development", date(2025, 3, 3), date(2025, 3, 21)),
    ("Unit Testing", "Testing", date(2025, 3, 10), date(2025, 3, 28)),
    ("Integration Testing", "Testing", date(2025, 3, 24), date(2025, 4, 11)),
    ("User Acceptance Testing", "Testing", date(2025, 4, 7), date(2025, 4, 18)),
    ("Documentation", "Deployment", date(2025, 4, 7), date(2025, 4, 18)),
    ("Deployment", "Deployment", date(2025, 4, 14), date(2025, 4, 25)),
]

# Reference date for calculations
reference_date = date(2025, 1, 1)

# Category colors matching the style
category_colors = {
    "Planning": "#306998",
    "Design": "#FFD43B",
    "Development": "#2E8B57",
    "Testing": "#DC143C",
    "Deployment": "#9370DB",
}

# Calculate date range
all_dates = []
for _, _, start, end in tasks:
    all_dates.extend([start, end])
min_date = min(all_dates)
max_date = max(all_dates)

# X-axis range in days
start_day = (min_date - reference_date).days - 3
end_day = (max_date - reference_date).days + 3
day_range = end_day - start_day

# Create task labels for y-axis
task_labels = [t[0] for t in tasks]
num_tasks = len(tasks)

# Create pygal HorizontalBar chart as base structure
chart = pygal.HorizontalBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="Software Development Timeline · gantt-basic · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=24,
    print_values=False,
    show_y_guides=False,
    show_x_guides=False,  # Hide default x guides
    show_x_labels=False,  # Hide default 0-100 labels
    margin=60,
    spacing=20,
    range=(0, 100),
)

# Set task names as y-axis labels
chart.x_labels = task_labels

# Add placeholder series for legend (one per category)
categories_in_order = ["Planning", "Design", "Development", "Testing", "Deployment"]
for cat in categories_in_order:
    chart.add(cat, [None] * num_tasks)

# Render base SVG
svg_string = chart.render().decode("utf-8")

# Pygal coordinates (from actual SVG: transform="translate(466, 140)", plot size 4273.6x2368)
PLOT_ORIGIN_X = 466
PLOT_ORIGIN_Y = 140
PLOT_WIDTH = 4273.6
PLOT_HEIGHT = 2368.0

# Convert to absolute coordinates for injection
PLOT_LEFT = PLOT_ORIGIN_X
PLOT_TOP = PLOT_ORIGIN_Y

row_height = PLOT_HEIGHT / num_tasks
bar_height = row_height * 0.55

# Build custom Gantt bar rectangles
bar_elements = []

for i, (task_name, category, start, end) in enumerate(tasks):
    start_day_val = (start - reference_date).days
    end_day_val = (end - reference_date).days

    # Convert days to x position
    x_start = PLOT_LEFT + ((start_day_val - start_day) / day_range) * PLOT_WIDTH
    x_end = PLOT_LEFT + ((end_day_val - start_day) / day_range) * PLOT_WIDTH
    width = x_end - x_start

    # Y position (pygal HorizontalBar has first item at bottom, so reverse index)
    reversed_i = num_tasks - 1 - i
    y_center = PLOT_TOP + (reversed_i + 0.5) * row_height
    y_top = y_center - bar_height / 2

    color = category_colors[category]
    duration = (end - start).days

    bar_elements.append(
        f'<rect x="{x_start:.1f}" y="{y_top:.1f}" width="{width:.1f}" '
        f'height="{bar_height:.1f}" fill="{color}" rx="6" ry="6" opacity="0.9">'
        f"<title>{task_name}&#10;{start.strftime('%b %d')} - {end.strftime('%b %d')} "
        f"({duration} days)</title></rect>"
    )

# Add month markers and labels
month_markers = []
for month in range(1, 5):
    month_date = date(2025, month, 1)
    day_val = (month_date - reference_date).days
    if start_day <= day_val <= end_day:
        x_pos = PLOT_LEFT + ((day_val - start_day) / day_range) * PLOT_WIDTH
        month_name = month_date.strftime("%b")
        # Vertical guide line
        month_markers.append(
            f'<line x1="{x_pos:.1f}" y1="{PLOT_TOP}" x2="{x_pos:.1f}" '
            f'y2="{PLOT_TOP + PLOT_HEIGHT}" stroke="#bbb" stroke-width="2" '
            f'stroke-dasharray="8,4"/>'
        )
        # Month label
        month_markers.append(
            f'<text x="{x_pos:.1f}" y="{PLOT_TOP + PLOT_HEIGHT + 40}" '
            f'font-family="Consolas, monospace" font-size="28" fill="#333" '
            f'text-anchor="middle">{month_name} 1</text>'
        )

# X-axis title
month_markers.append(
    f'<text x="{PLOT_LEFT + PLOT_WIDTH / 2}" y="{PLOT_TOP + PLOT_HEIGHT + 90}" '
    f'font-family="Consolas, monospace" font-size="32" fill="#333" '
    f'text-anchor="middle">Timeline (2025)</text>'
)

# Inject custom elements before </svg>
all_elements = "\n".join(bar_elements + month_markers)
svg_output = svg_string.replace("</svg>", f"{all_elements}\n</svg>")

# Remove "No data" text that appears from empty series
svg_output = svg_output.replace(">No data<", "><")

# Save outputs
with open("plot.html", "w") as f:
    f.write(svg_output)

cairosvg.svg2png(bytestring=svg_output.encode(), write_to="plot.png")
