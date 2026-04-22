""" pyplots.ai
icicle-basic: Basic Icicle Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure


# Data - File system hierarchy with nested folders and file sizes
nodes = [
    {"name": "Root", "parent": None, "value": 0},
    {"name": "Documents", "parent": "Root", "value": 0},
    {"name": "Media", "parent": "Root", "value": 0},
    {"name": "Code", "parent": "Root", "value": 0},
    {"name": "Reports", "parent": "Documents", "value": 350},
    {"name": "Contracts", "parent": "Documents", "value": 250},
    {"name": "Notes", "parent": "Documents", "value": 150},
    {"name": "Images", "parent": "Media", "value": 500},
    {"name": "Videos", "parent": "Media", "value": 800},
    {"name": "Audio", "parent": "Media", "value": 300},
    {"name": "Python", "parent": "Code", "value": 400},
    {"name": "JavaScript", "parent": "Code", "value": 350},
    {"name": "Data", "parent": "Code", "value": 200},
]

# Build tree structure
node_dict = {n["name"]: n for n in nodes}
children = {n["name"]: [] for n in nodes}
for n in nodes:
    if n["parent"]:
        children[n["parent"]].append(n["name"])


# Calculate leaf values for parent nodes (sum of children)
def calc_value(name):
    if children[name]:
        return sum(calc_value(c) for c in children[name])
    return node_dict[name]["value"]


for n in nodes:
    n["computed_value"] = calc_value(n["name"])


# Assign levels (depth in tree)
def assign_level(name, level):
    node_dict[name]["level"] = level
    for c in children[name]:
        assign_level(c, level + 1)


assign_level("Root", 0)
max_level = max(n["level"] for n in nodes)

# Colors by level - Python Blue to Yellow gradient
level_colors = ["#306998", "#4A7DAA", "#6591BC", "#FFD43B"]


# Calculate positions for icicle layout (horizontal, top-down)
# Each level is a row, width proportional to value
def layout_icicle(name, x_start, x_end, rects):
    node = node_dict[name]
    level = node["level"]

    # Rectangle for this node
    rect = {
        "name": name,
        "level": level,
        "x_start": x_start,
        "x_end": x_end,
        "y_start": max_level - level,
        "y_end": max_level - level + 1,
        "value": node["computed_value"],
        "color": level_colors[min(level, len(level_colors) - 1)],
    }
    rects.append(rect)

    # Layout children
    if children[name]:
        total_child_value = sum(node_dict[c]["computed_value"] for c in children[name])
        current_x = x_start
        for c in children[name]:
            child_value = node_dict[c]["computed_value"]
            child_width = (x_end - x_start) * (child_value / total_child_value)
            layout_icicle(c, current_x, current_x + child_width, rects)
            current_x += child_width


rects = []
layout_icicle("Root", 0, 100, rects)

# Prepare data for Bokeh
x_centers = [(r["x_start"] + r["x_end"]) / 2 for r in rects]
y_centers = [(r["y_start"] + r["y_end"]) / 2 for r in rects]
widths = [r["x_end"] - r["x_start"] for r in rects]
heights = [0.95 for r in rects]  # Slight gap between levels
colors = [r["color"] for r in rects]
names = [r["name"] for r in rects]
values = [r["value"] for r in rects]

source = ColumnDataSource(
    data={
        "x": x_centers,
        "y": y_centers,
        "width": widths,
        "height": heights,
        "color": colors,
        "name": names,
        "value": values,
    }
)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="File System Structure · icicle-basic · bokeh · pyplots.ai",
    x_range=(-12, 102),
    y_range=(-0.3, max_level + 0.8),
    tools="",
    toolbar_location=None,
)

# Draw rectangles
p.rect(
    x="x",
    y="y",
    width="width",
    height="height",
    source=source,
    fill_color="color",
    line_color="white",
    line_width=3,
    fill_alpha=0.9,
)

# Add labels for rectangles with sufficient width
for r in rects:
    rect_width = r["x_end"] - r["x_start"]
    x_center = (r["x_start"] + r["x_end"]) / 2
    y_center = (r["y_start"] + r["y_end"]) / 2

    # Only label if rectangle is wide enough
    if rect_width > 4:
        font_size = "24pt" if rect_width > 20 else ("20pt" if rect_width > 10 else "16pt")
        label_text = r["name"]
        if r["level"] > 0 and rect_width > 6:
            label_text = f"{r['name']} ({r['value']} MB)"

        label = Label(
            x=x_center,
            y=y_center,
            text=label_text,
            text_align="center",
            text_baseline="middle",
            text_font_size=font_size,
            text_color="white" if r["level"] < 3 else "#1a1a1a",
        )
        p.add_layout(label)

# Styling
p.title.text_font_size = "36pt"
p.title.align = "center"

# Hide axes for cleaner look
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Remove outline
p.outline_line_color = None

# Background
p.background_fill_color = "#fafafa"

# Add level labels on the left
level_labels = ["Root", "Categories", "Subcategories"]
for i, label_text in enumerate(level_labels[: max_level + 1]):
    label = Label(
        x=-1,
        y=max_level - i + 0.5,
        text=label_text,
        text_align="right",
        text_baseline="middle",
        text_font_size="20pt",
        text_color="#666666",
    )
    p.add_layout(label)

# Save as PNG and HTML
export_png(p, filename="plot.png")
output_file("plot.html", title="icicle-basic · bokeh · pyplots.ai")
save(p)
