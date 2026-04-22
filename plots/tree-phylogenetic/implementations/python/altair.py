""" pyplots.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd


# Primate phylogenetic tree data (simplified example)
# Based on approximate evolutionary relationships from mitochondrial DNA studies
np.random.seed(42)

# Define tree structure manually with (parent, child, branch_length)
# Tree structure: Primates -> (Hominidae, Cercopithecidae)
# Hominidae -> (Homininae, Pongo)
# Homininae -> (Homo, Pan)
# Pan -> (P.troglodytes, P.paniscus)
# Cercopithecidae -> (Macaca, Papio)

edges = [
    ("Root", "Hominoidea", 0.15),
    ("Root", "Cercopithecidae", 0.18),
    ("Hominoidea", "Hominidae", 0.08),
    ("Hominoidea", "Hylobatidae", 0.12),
    ("Hominidae", "Homininae", 0.05),
    ("Hominidae", "Pongo pygmaeus", 0.09),
    ("Homininae", "Homo sapiens", 0.03),
    ("Homininae", "Pan", 0.02),
    ("Pan", "Pan troglodytes", 0.015),
    ("Pan", "Pan paniscus", 0.015),
    ("Hylobatidae", "Hylobates lar", 0.06),
    ("Cercopithecidae", "Macaca mulatta", 0.10),
    ("Cercopithecidae", "Papio anubis", 0.11),
]

# Species labels (leaf nodes)
leaf_nodes = {
    "Homo sapiens": "Human",
    "Pan troglodytes": "Chimpanzee",
    "Pan paniscus": "Bonobo",
    "Pongo pygmaeus": "Orangutan",
    "Hylobates lar": "Gibbon",
    "Macaca mulatta": "Rhesus Macaque",
    "Papio anubis": "Olive Baboon",
}

# Build adjacency list
children = {}
branch_lengths = {}
for parent, child, length in edges:
    if parent not in children:
        children[parent] = []
    children[parent].append(child)
    branch_lengths[(parent, child)] = length


# Calculate y-positions for leaf nodes (spread evenly)
def get_leaves(node):
    if node not in children:
        return [node]
    leaves = []
    for child in children[node]:
        leaves.extend(get_leaves(child))
    return leaves


all_leaves = get_leaves("Root")
n_leaves = len(all_leaves)
leaf_y = {leaf: i for i, leaf in enumerate(all_leaves)}


# Calculate x-positions based on cumulative branch lengths from root
def calc_x_positions(node, current_x=0):
    positions = {node: current_x}
    if node in children:
        for child in children[node]:
            child_x = current_x + branch_lengths[(node, child)]
            positions.update(calc_x_positions(child, child_x))
    return positions


x_positions = calc_x_positions("Root")


# Calculate y-positions (internal nodes = average of children)
def calc_y_positions(node):
    if node not in children:
        return {node: leaf_y[node]}
    positions = {}
    child_ys = []
    for child in children[node]:
        child_positions = calc_y_positions(child)
        positions.update(child_positions)
        child_ys.append(child_positions[child])
    positions[node] = np.mean(child_ys)
    return positions


y_positions = calc_y_positions("Root")

# Create line segments for the tree (horizontal and vertical lines)
lines_data = []
for parent, child, _length in edges:
    parent_x = x_positions[parent]
    parent_y = y_positions[parent]
    child_x = x_positions[child]
    child_y = y_positions[child]

    # Horizontal line from parent to child's x
    lines_data.append({"x": parent_x, "y": parent_y, "x2": parent_x, "y2": child_y, "type": "vertical"})
    # Vertical line at child's y from parent_x to child_x
    lines_data.append({"x": parent_x, "y": child_y, "x2": child_x, "y2": child_y, "type": "horizontal"})

lines_df = pd.DataFrame(lines_data)

# Create node points for leaf labels
nodes_data = []
for node in all_leaves:
    label = leaf_nodes.get(node, node)
    nodes_data.append({"x": x_positions[node], "y": y_positions[node], "label": label, "species": node})

nodes_df = pd.DataFrame(nodes_data)

# Create internal node points
internal_nodes = [n for n in x_positions.keys() if n not in all_leaves and n != "Root"]
internal_data = [{"x": x_positions[n], "y": y_positions[n], "name": n} for n in internal_nodes]
internal_df = pd.DataFrame(internal_data)

# Define color palette - Python colors
branch_color = "#306998"  # Python Blue
node_color = "#FFD43B"  # Python Yellow
text_color = "#2d2d2d"  # Dark gray for text

# Create the tree branches using rule marks
branches = (
    alt.Chart(lines_df).mark_rule(strokeWidth=4, color=branch_color).encode(x="x:Q", y="y:Q", x2="x2:Q", y2="y2:Q")
)

# Create leaf node points
leaf_points = (
    alt.Chart(nodes_df)
    .mark_circle(size=400, color=node_color, stroke=branch_color, strokeWidth=2)
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), tooltip=["species:N", "label:N"])
)

# Create leaf labels
leaf_labels = (
    alt.Chart(nodes_df)
    .mark_text(align="left", baseline="middle", dx=15, fontSize=20, fontWeight="bold", color=text_color)
    .encode(x="x:Q", y="y:Q", text="label:N")
)

# Create internal node points (smaller)
internal_points = (
    alt.Chart(internal_df)
    .mark_circle(size=200, color=branch_color, stroke="#ffffff", strokeWidth=2)
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), tooltip=["name:N"])
)

# Create scale bar data
max_x = max(x_positions.values())
scale_bar_length = 0.05  # 0.05 substitutions per site
scale_bar_data = pd.DataFrame([{"x": 0.02, "y": -0.8, "x2": 0.02 + scale_bar_length, "y2": -0.8}])

scale_bar = (
    alt.Chart(scale_bar_data).mark_rule(strokeWidth=4, color=text_color).encode(x="x:Q", y="y:Q", x2="x2:Q", y2="y2:Q")
)

scale_bar_label = (
    alt.Chart(pd.DataFrame([{"x": 0.02 + scale_bar_length / 2, "y": -1.2, "text": "0.05 subs/site"}]))
    .mark_text(fontSize=16, color=text_color)
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Combine all layers
chart = (
    alt.layer(branches, internal_points, leaf_points, leaf_labels, scale_bar, scale_bar_label)
    .properties(
        width=1400,
        height=800,
        title=alt.Title(
            "Primate Evolution · tree-phylogenetic · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            color=text_color,
            subtitle="Phylogenetic tree based on mitochondrial DNA divergence",
            subtitleFontSize=18,
            subtitleColor="#666666",
        ),
    )
    .configure_axis(labelFontSize=16, titleFontSize=20, gridColor="#e0e0e0", gridOpacity=0.3, domainColor=text_color)
    .configure_view(strokeWidth=0)
)

# Customize axes
chart = chart.encode(
    x=alt.X(
        "x:Q", title="Evolutionary Distance (substitutions per site)", scale=alt.Scale(domain=[-0.02, max_x + 0.15])
    ),
    y=alt.Y(
        "y:Q",
        title="",
        scale=alt.Scale(domain=[-1.5, n_leaves - 0.5]),
        axis=alt.Axis(labels=False, ticks=False, domain=False),
    ),
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
