""" pyplots.ai
circlepacking-basic: Circle Packing Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LabelSet, Legend, LegendItem
from bokeh.plotting import figure


np.random.seed(42)

# Build hierarchical data: Technology company budget allocation (in millions)
hierarchy = [
    {"id": "TechCorp", "parent": None, "value": 0, "label": "TechCorp"},
    {"id": "Engineering", "parent": "TechCorp", "value": 0, "label": "Engineering"},
    {"id": "Sales", "parent": "TechCorp", "value": 0, "label": "Sales"},
    {"id": "Operations", "parent": "TechCorp", "value": 0, "label": "Operations"},
    {"id": "Frontend", "parent": "Engineering", "value": 45, "label": "Frontend"},
    {"id": "Backend", "parent": "Engineering", "value": 60, "label": "Backend"},
    {"id": "DevOps", "parent": "Engineering", "value": 35, "label": "DevOps"},
    {"id": "Mobile", "parent": "Engineering", "value": 40, "label": "Mobile"},
    {"id": "Enterprise", "parent": "Sales", "value": 75, "label": "Enterprise"},
    {"id": "SMB", "parent": "Sales", "value": 45, "label": "SMB"},
    {"id": "Partners", "parent": "Sales", "value": 30, "label": "Partners"},
    {"id": "HR", "parent": "Operations", "value": 25, "label": "HR"},
    {"id": "Finance", "parent": "Operations", "value": 30, "label": "Finance"},
    {"id": "Legal", "parent": "Operations", "value": 20, "label": "Legal"},
]

# Build tree structure
nodes = {item["id"]: {**item, "children": [], "x": 0.0, "y": 0.0, "r": 0.0, "depth": 0} for item in hierarchy}
root = None
for _node_id, node in nodes.items():
    if node["parent"] is None:
        root = node
    else:
        parent = nodes[node["parent"]]
        parent["children"].append(node)
        node["depth"] = parent["depth"] + 1

scale_factor = 15

# Compute layout bottom-up using stack-based iteration (no recursion/functions)
# First pass: compute radii for leaves
for node in nodes.values():
    if not node["children"]:
        node["r"] = np.sqrt(node["value"]) * scale_factor

# Process nodes level by level, bottom-up
# Get max depth
max_depth = max(n["depth"] for n in nodes.values())

# Process from bottom to top
for current_depth in range(max_depth, -1, -1):
    nodes_at_depth = [n for n in nodes.values() if n["depth"] == current_depth and n["children"]]

    for node in nodes_at_depth:
        children = node["children"]

        # Pack siblings using simple algorithm
        children.sort(key=lambda c: -c["r"])
        n_children = len(children)

        if n_children == 1:
            children[0]["x"] = 0.0
            children[0]["y"] = 0.0
        elif n_children >= 2:
            c0, c1 = children[0], children[1]
            c0["x"] = 0.0
            c0["y"] = 0.0
            c1["x"] = c0["r"] + c1["r"]
            c1["y"] = 0.0

            if n_children >= 3:
                c2 = children[2]
                d01 = c0["r"] + c1["r"]
                d02 = c0["r"] + c2["r"]
                d12 = c1["r"] + c2["r"]
                x2 = (d02**2 - d12**2 + d01**2) / (2 * d01)
                y2_sq = d02**2 - x2**2
                c2["x"] = x2
                c2["y"] = np.sqrt(max(0, y2_sq))

                # Place remaining circles
                for i in range(3, n_children):
                    ci = children[i]
                    best_score = float("inf")
                    best_pos = (0.0, 0.0)

                    # Try placing tangent to each pair
                    for j in range(i):
                        for k in range(j + 1, i):
                            cj, ck = children[j], children[k]
                            dx = ck["x"] - cj["x"]
                            dy = ck["y"] - cj["y"]
                            d = np.sqrt(dx**2 + dy**2)

                            if d < 1e-10:
                                continue

                            r1 = cj["r"] + ci["r"]
                            r2 = ck["r"] + ci["r"]

                            if d > r1 + r2 + 1e-6 or d < abs(r1 - r2) - 1e-6:
                                continue

                            a = (r1**2 - r2**2 + d**2) / (2 * d)
                            h_sq = r1**2 - a**2
                            if h_sq < 0:
                                continue

                            h = np.sqrt(h_sq)
                            mx = cj["x"] + a * dx / d
                            my = cj["y"] + a * dy / d

                            for px, py in [(mx - h * dy / d, my + h * dx / d), (mx + h * dy / d, my - h * dx / d)]:
                                valid = True
                                for m in range(i):
                                    cm = children[m]
                                    dist = np.sqrt((px - cm["x"]) ** 2 + (py - cm["y"]) ** 2)
                                    if dist < ci["r"] + cm["r"] - 1e-6:
                                        valid = False
                                        break

                                if valid:
                                    cx = sum(children[m]["x"] for m in range(i)) / i
                                    cy = sum(children[m]["y"] for m in range(i)) / i
                                    score = np.sqrt((px - cx) ** 2 + (py - cy) ** 2)
                                    if score < best_score:
                                        best_score = score
                                        best_pos = (px, py)

                    ci["x"], ci["y"] = best_pos

        # Find enclosing circle
        if children:
            min_x = min(c["x"] - c["r"] for c in children)
            max_x = max(c["x"] + c["r"] for c in children)
            min_y = min(c["y"] - c["r"] for c in children)
            max_y = max(c["y"] + c["r"] for c in children)
            cx = (min_x + max_x) / 2
            cy = (min_y + max_y) / 2
            enc_r = max(np.sqrt((c["x"] - cx) ** 2 + (c["y"] - cy) ** 2) + c["r"] for c in children)

            # Center children
            for child in children:
                child["x"] -= cx
                child["y"] -= cy

            node["r"] = enc_r + 30

# Position children relative to parent (top-down)
stack = [(root, 0.0, 0.0)]
while stack:
    current, px, py = stack.pop()
    current["x"] = px
    current["y"] = py
    for child in current["children"]:
        stack.append((child, px + child["x"], py + child["y"]))

# Collect all nodes for plotting
all_circles = []
stack = [root]
while stack:
    current = stack.pop()
    all_circles.append(current)
    stack.extend(current["children"])

# Prepare data for plotting
x_vals = [n["x"] for n in all_circles]
y_vals = [n["y"] for n in all_circles]
radii = [n["r"] for n in all_circles]
depths = [n["depth"] for n in all_circles]
labels = [n["label"] for n in all_circles]
values = [n["value"] for n in all_circles]

# Color palette by depth
depth_colors = ["#306998", "#FFD43B", "#4ECDC4"]
colors = [depth_colors[min(d, 2)] for d in depths]
depth_names = ["Root (Company)", "Division", "Team"]
depth_labels = [depth_names[min(d, 2)] for d in depths]

# Create figure (square aspect, no toolbar)
p = figure(
    width=3600,
    height=3600,
    title="circlepacking-basic · bokeh · pyplots.ai",
    match_aspect=True,
    toolbar_location=None,
    tools="",
)

# Sort by depth and radius for proper layering (draw outer first)
sorted_indices = sorted(range(len(all_circles)), key=lambda i: (depths[i], -radii[i]))

# Draw circles with ColumnDataSource for hover
circle_data = {
    "x": [x_vals[i] for i in sorted_indices],
    "y": [y_vals[i] for i in sorted_indices],
    "radius": [radii[i] for i in sorted_indices],
    "color": [colors[i] for i in sorted_indices],
    "alpha": [0.6 if depths[i] == 0 else (0.65 if depths[i] == 1 else 0.75) for i in sorted_indices],
    "line_width": [3 if depths[i] == 0 else 2 for i in sorted_indices],
    "label": [labels[i] for i in sorted_indices],
    "depth_label": [depth_labels[i] for i in sorted_indices],
    "value": [values[i] for i in sorted_indices],
}
circle_source = ColumnDataSource(data=circle_data)

circles_glyph = p.circle(
    x="x",
    y="y",
    radius="radius",
    fill_color="color",
    fill_alpha="alpha",
    line_color="#333333",
    line_width="line_width",
    source=circle_source,
)

# Add HoverTool for interactivity
hover = HoverTool(
    tooltips=[("Name", "@label"), ("Level", "@depth_label"), ("Budget", "@value{0} M$")],
    renderers=[circles_glyph],
    mode="mouse",
)
p.add_tools(hover)

# Create legend for depth colors
legend_items = []
for color, name in zip(depth_colors, depth_names, strict=True):
    # Create a dummy circle for the legend
    dummy_source = ColumnDataSource(data={"x": [-99999], "y": [-99999], "r": [10]})
    dummy_circle = p.circle(
        x="x", y="y", radius="r", fill_color=color, fill_alpha=0.7, line_color="#333333", source=dummy_source
    )
    legend_items.append(LegendItem(label=name, renderers=[dummy_circle]))

legend = Legend(items=legend_items, location="top_right", label_text_font_size="24pt", glyph_height=40, glyph_width=40)
legend.background_fill_alpha = 0.8
legend.border_line_color = "#333333"
legend.padding = 15
legend.spacing = 10
p.add_layout(legend)

# Prepare labels - for leaf nodes and divisions
label_data = {"x": [], "y": [], "label": []}
for node in all_circles:
    if not node["children"] and node["r"] >= 50:
        label_data["x"].append(node["x"])
        label_data["y"].append(node["y"])
        label_data["label"].append(node["label"])
    elif node["depth"] == 1:
        label_data["x"].append(node["x"])
        label_data["y"].append(node["y"] + node["r"] * 0.7)
        label_data["label"].append(node["label"])

label_source = ColumnDataSource(data=label_data)
label_set = LabelSet(
    x="x",
    y="y",
    text="label",
    source=label_source,
    text_align="center",
    text_baseline="middle",
    text_font_size="28pt",
    text_color="#222222",
    text_font_style="bold",
)
p.add_layout(label_set)

# Style
p.title.text_font_size = "36pt"
p.title.align = "center"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None
p.background_fill_color = "#FAFAFA"

# Set axis ranges
extent = root["r"] * 1.08
p.x_range.start = -extent
p.x_range.end = extent
p.y_range.start = -extent
p.y_range.end = extent

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
