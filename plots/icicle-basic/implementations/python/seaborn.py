"""pyplots.ai
icicle-basic: Basic Icicle Chart
Library: seaborn 0.13.2 | Python 3.13
Quality: 82/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch, Rectangle


# Set seaborn style for consistent appearance
sns.set_style("whitegrid")
sns.set_context("poster", font_scale=0.9)

# Hierarchical data: File system structure
# Format: (name, parent, value in MB)
hierarchy_data = [
    ("Root", None, 1000),
    ("Documents", "Root", 350),
    ("Media", "Root", 450),
    ("Projects", "Root", 200),
    ("Reports", "Documents", 150),
    ("Presentations", "Documents", 120),
    ("Templates", "Documents", 80),
    ("Images", "Media", 200),
    ("Videos", "Media", 180),
    ("Audio", "Media", 70),
    ("Q1_Report.pdf", "Reports", 50),
    ("Q2_Report.pdf", "Reports", 60),
    ("Annual.pdf", "Reports", 40),
    ("Sales.pptx", "Presentations", 70),
    ("Training.pptx", "Presentations", 50),
    ("Photos", "Images", 120),
    ("Screenshots", "Images", 80),
    ("Tutorials", "Videos", 100),
    ("Recordings", "Videos", 80),
    ("Code", "Projects", 120),
    ("Designs", "Projects", 80),
]

# Build node dictionary
nodes = {}
for name, parent, value in hierarchy_data:
    nodes[name] = {"name": name, "parent": parent, "value": value, "children": []}

for name, parent, _value in hierarchy_data:
    if parent and parent in nodes:
        nodes[parent]["children"].append(name)

# Calculate levels inline (KISS principle)
levels = {}
for name in nodes:
    level = 0
    current = name
    while nodes[current]["parent"] is not None:
        level += 1
        current = nodes[current]["parent"]
    levels[name] = level

max_level = max(levels.values())

# Calculate totals inline (sum of children or own value if leaf)
totals = {}
sorted_nodes = sorted(nodes.keys(), key=lambda x: levels[x], reverse=True)
for name in sorted_nodes:
    children = nodes[name]["children"]
    if not children:
        totals[name] = nodes[name]["value"]
    else:
        totals[name] = sum(totals[child] for child in children)

# Calculate positions for icicle chart using stack-based iteration
rectangles = []
stack = [("Root", 0.0, 1.0, 0)]

while stack:
    name, x_start, x_end, level = stack.pop()
    width = x_end - x_start
    height = 1.0 / (max_level + 1)
    y = 1.0 - (level + 1) * height

    rectangles.append(
        {"name": name, "x": x_start, "y": y, "width": width, "height": height, "level": level, "value": totals[name]}
    )

    children = nodes[name]["children"]
    if children:
        total_child_value = sum(totals[c] for c in children)
        current_x = x_start
        for child in reversed(children):
            child_fraction = totals[child] / total_child_value
            child_width = width * child_fraction
            stack.append((child, current_x, current_x + child_width, level + 1))
            current_x += child_width

# Create DataFrame for seaborn color mapping
rect_df = pd.DataFrame(rectangles)
n_levels = max_level + 1

# Use seaborn to create color palette based on hierarchy level
palette = sns.color_palette("Blues_r", n_colors=n_levels + 2)[1:-1]
level_colors = {i: palette[i] for i in range(n_levels)}

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Draw rectangles using matplotlib with seaborn-derived colors
gap = 0.005
for _, rect in rect_df.iterrows():
    x = rect["x"] + gap
    y = rect["y"] + gap
    w = max(rect["width"] - 2 * gap, 0.001)
    h = max(rect["height"] - 2 * gap, 0.001)
    level = int(rect["level"])
    color = level_colors[level]

    patch = Rectangle((x, y), w, h, facecolor=color, edgecolor="white", linewidth=2)
    ax.add_patch(patch)

# Add text labels with values for rectangles
for _, rect in rect_df.iterrows():
    level = int(rect["level"])
    # Only label if rectangle is wide enough
    if rect["width"] < 0.03:
        continue

    # Position in center of rectangle
    cx = rect["x"] + rect["width"] / 2
    cy = rect["y"] + rect["height"] / 2

    # Choose font size based on level and available space
    fontsize = 14 if level <= 1 else (12 if level == 2 else 10)
    text_color = "white" if level < 2 else "#1a3a5c"

    # Format value display (in MB)
    value = int(rect["value"])
    if value >= 1000:
        value_str = f"{value / 1000:.1f} GB"
    else:
        value_str = f"{value} MB"

    # Determine available characters based on rectangle width
    name = rect["name"]
    available_chars = max(6, int(rect["width"] * 120))

    # Decide what to display based on available space
    if len(name) <= available_chars:
        # Full name fits
        display_text = f"{name}\n{value_str}"
    elif available_chars >= 10:
        # Medium space: abbreviate name smartly
        if "." in name and len(name.split(".")[-1]) <= 4:
            # Preserve file extension
            ext = "." + name.split(".")[-1]
            base_chars = available_chars - len(ext) - 2
            if base_chars > 0:
                name = name[:base_chars] + ".." + ext
            else:
                name = name[: available_chars - 2] + "…"
        else:
            name = name[: available_chars - 1] + "…"
        display_text = f"{name}\n{value_str}"
    else:
        # Small: just show value
        display_text = value_str

    ax.text(
        cx,
        cy,
        display_text,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight="bold",
        color=text_color,
        linespacing=1.2,
    )

# Configure axes
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect("auto")
ax.axis("off")

# Title with exact spec format: {spec-id} · {library} · pyplots.ai
ax.set_title("icicle-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Add legend for hierarchy levels using seaborn palette
legend_labels = ["Root", "Category", "Subcategory", "Files"][:n_levels]
legend_patches = [
    Patch(facecolor=palette[i], edgecolor="white", linewidth=1.5, label=legend_labels[i]) for i in range(n_levels)
]
ax.legend(
    handles=legend_patches,
    loc="lower right",
    fontsize=14,
    framealpha=0.95,
    title="Hierarchy Level",
    title_fontsize=16,
    edgecolor="#cccccc",
)

# Use seaborn's despine for clean appearance
sns.despine(left=True, bottom=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
