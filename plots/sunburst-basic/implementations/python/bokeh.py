""" pyplots.ai
sunburst-basic: Basic Sunburst Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

from math import cos, pi, sin

from bokeh.io import export_png, output_file, save
from bokeh.models import Label
from bokeh.plotting import figure


# Data - Company budget hierarchy (Department -> Team -> Project)
# Level 1: Departments
# Level 2: Teams within departments
# Level 3: Projects within teams

hierarchy = [
    # Engineering Department
    {"level_1": "Engineering", "level_2": "Backend", "level_3": "API", "value": 120},
    {"level_1": "Engineering", "level_2": "Backend", "level_3": "Database", "value": 80},
    {"level_1": "Engineering", "level_2": "Frontend", "level_3": "Web App", "value": 100},
    {"level_1": "Engineering", "level_2": "Frontend", "level_3": "Mobile", "value": 60},
    {"level_1": "Engineering", "level_2": "DevOps", "level_3": "Infrastructure", "value": 50},
    # Marketing Department
    {"level_1": "Marketing", "level_2": "Digital", "level_3": "Social Media", "value": 45},
    {"level_1": "Marketing", "level_2": "Digital", "level_3": "SEO", "value": 35},
    {"level_1": "Marketing", "level_2": "Content", "level_3": "Blog", "value": 30},
    {"level_1": "Marketing", "level_2": "Content", "level_3": "Video", "value": 40},
    # Sales Department
    {"level_1": "Sales", "level_2": "Enterprise", "level_3": "EMEA", "value": 70},
    {"level_1": "Sales", "level_2": "Enterprise", "level_3": "APAC", "value": 55},
    {"level_1": "Sales", "level_2": "SMB", "level_3": "Direct", "value": 45},
    # Operations Department
    {"level_1": "Operations", "level_2": "Support", "level_3": "Tier 1", "value": 40},
    {"level_1": "Operations", "level_2": "Support", "level_3": "Tier 2", "value": 25},
    {"level_1": "Operations", "level_2": "HR", "level_3": "Recruiting", "value": 30},
]

# Calculate totals for each level
level_1_totals = {}
level_2_totals = {}
for item in hierarchy:
    l1, l2, val = item["level_1"], item["level_2"], item["value"]
    level_1_totals[l1] = level_1_totals.get(l1, 0) + val
    key = (l1, l2)
    level_2_totals[key] = level_2_totals.get(key, 0) + val

total = sum(item["value"] for item in hierarchy)

# Color palette - consistent colors for each department branch
# Python Blue as base, then colorblind-safe variants
branch_colors = {
    "Engineering": {"base": "#306998", "mid": "#4A90C2", "light": "#6BB3E8"},
    "Marketing": {"base": "#FFD43B", "mid": "#FFE066", "light": "#FFF0A3"},
    "Sales": {"base": "#E74C3C", "mid": "#EF7B6D", "light": "#F5A99B"},
    "Operations": {"base": "#27AE60", "mid": "#52C77E", "light": "#7EDD9E"},
}

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="sunburst-basic · bokeh · pyplots.ai",
    toolbar_location=None,
    tools="",
    x_range=(-1.5, 1.8),
    y_range=(-1.2, 1.2),
)

# Radii for each ring (innermost to outermost)
r1_inner, r1_outer = 0.0, 0.30  # Level 1: Departments (center)
r2_inner, r2_outer = 0.32, 0.60  # Level 2: Teams
r3_inner, r3_outer = 0.62, 0.95  # Level 3: Projects

# Draw Level 1 (innermost ring - Departments)
start_angle = pi / 2  # Start from top
l1_angles = {}  # Store start/end angles for level 1 segments

for l1 in level_1_totals:
    angle_span = (level_1_totals[l1] / total) * 2 * pi
    end_angle = start_angle - angle_span

    p.annular_wedge(
        x=0,
        y=0,
        inner_radius=r1_inner,
        outer_radius=r1_outer,
        start_angle=end_angle,
        end_angle=start_angle,
        fill_color=branch_colors[l1]["base"],
        line_color="white",
        line_width=2,
    )

    # Store angles for child segments
    l1_angles[l1] = {"start": start_angle, "end": end_angle}

    # Add label for Level 1
    mid_angle = (start_angle + end_angle) / 2
    label_r = (r1_inner + r1_outer) / 2 + 0.02
    lx = label_r * cos(mid_angle)
    ly = label_r * sin(mid_angle)
    text_color = "#333333" if l1 == "Marketing" else "white"

    label = Label(
        x=lx,
        y=ly,
        text=l1[:3],  # Abbreviated label
        text_font_size="20pt",
        text_color=text_color,
        text_font_style="bold",
        text_align="center",
        text_baseline="middle",
    )
    p.add_layout(label)

    start_angle = end_angle

# Draw Level 2 (middle ring - Teams)
l2_angles = {}  # Store angles for level 2 segments

for l1 in level_1_totals:
    l1_start = l1_angles[l1]["start"]
    l1_end = l1_angles[l1]["end"]
    l1_span = l1_start - l1_end

    # Get level 2 items for this level 1
    l2_items = [(k, v) for k, v in level_2_totals.items() if k[0] == l1]
    l1_total = level_1_totals[l1]

    current_start = l1_start
    for (_, l2_name), l2_val in l2_items:
        angle_span = (l2_val / l1_total) * l1_span
        end_angle = current_start - angle_span

        p.annular_wedge(
            x=0,
            y=0,
            inner_radius=r2_inner,
            outer_radius=r2_outer,
            start_angle=end_angle,
            end_angle=current_start,
            fill_color=branch_colors[l1]["mid"],
            line_color="white",
            line_width=2,
        )

        # Store angles for level 3 segments
        l2_angles[(l1, l2_name)] = {"start": current_start, "end": end_angle}

        # Add label for Level 2 (only for larger segments)
        if l2_val / total > 0.06:
            mid_angle = (current_start + end_angle) / 2
            label_r = (r2_inner + r2_outer) / 2
            lx = label_r * cos(mid_angle)
            ly = label_r * sin(mid_angle)
            text_color = "#333333" if l1 == "Marketing" else "white"

            label = Label(
                x=lx,
                y=ly,
                text=l2_name[:6],
                text_font_size="16pt",
                text_color=text_color,
                text_align="center",
                text_baseline="middle",
            )
            p.add_layout(label)

        current_start = end_angle

# Draw Level 3 (outermost ring - Projects)
for item in hierarchy:
    l1, l2, l3, val = item["level_1"], item["level_2"], item["level_3"], item["value"]

    l2_start = l2_angles[(l1, l2)]["start"]
    l2_end = l2_angles[(l1, l2)]["end"]
    l2_span = l2_start - l2_end
    l2_total = level_2_totals[(l1, l2)]

    # Find position within the level 2 segment
    # Get all level 3 items for this level 2
    l3_items = [h for h in hierarchy if h["level_1"] == l1 and h["level_2"] == l2]
    l3_idx = next(i for i, h in enumerate(l3_items) if h["level_3"] == l3)

    # Calculate cumulative angle before this item
    cumulative = sum(l3_items[i]["value"] for i in range(l3_idx))
    start_offset = (cumulative / l2_total) * l2_span
    angle_span = (val / l2_total) * l2_span

    seg_start = l2_start - start_offset
    seg_end = seg_start - angle_span

    p.annular_wedge(
        x=0,
        y=0,
        inner_radius=r3_inner,
        outer_radius=r3_outer,
        start_angle=seg_end,
        end_angle=seg_start,
        fill_color=branch_colors[l1]["light"],
        line_color="white",
        line_width=2,
    )

    # Add label for Level 3 (only for larger segments)
    if val / total > 0.04:
        mid_angle = (seg_start + seg_end) / 2
        label_r = (r3_inner + r3_outer) / 2
        lx = label_r * cos(mid_angle)
        ly = label_r * sin(mid_angle)

        label = Label(
            x=lx,
            y=ly,
            text=l3[:5],
            text_font_size="14pt",
            text_color="#333333",
            text_align="center",
            text_baseline="middle",
        )
        p.add_layout(label)

# Add legend on the right
legend_x = 1.15
legend_y_start = 0.7
legend_spacing = 0.15

legend_title = Label(
    x=legend_x,
    y=legend_y_start + 0.15,
    text="Departments",
    text_font_size="22pt",
    text_color="#333333",
    text_font_style="bold",
    text_align="left",
    text_baseline="middle",
)
p.add_layout(legend_title)

for i, (dept, colors) in enumerate(branch_colors.items()):
    y_pos = legend_y_start - i * legend_spacing

    # Color boxes showing the gradient
    for shade, x_offset in [("base", 0), ("mid", 0.06), ("light", 0.12)]:
        p.rect(
            x=legend_x + x_offset,
            y=y_pos,
            width=0.05,
            height=0.08,
            fill_color=colors[shade],
            line_color="white",
            line_width=1,
        )

    # Department name and value
    dept_label = Label(
        x=legend_x + 0.22,
        y=y_pos,
        text=f"{dept} (${level_1_totals[dept]}K)",
        text_font_size="18pt",
        text_color="#333333",
        text_align="left",
        text_baseline="middle",
    )
    p.add_layout(dept_label)

# Add ring level labels
ring_labels = [(0.15, "Dept"), (0.46, "Team"), (0.78, "Project")]

for radius, text in ring_labels:
    label = Label(
        x=radius,
        y=-1.05,
        text=text,
        text_font_size="16pt",
        text_color="#666666",
        text_align="center",
        text_baseline="middle",
    )
    p.add_layout(label)

# Styling
p.title.text_font_size = "32pt"
p.title.text_color = "#333333"
p.title.align = "center"
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None
p.background_fill_color = None
p.border_fill_color = None

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
