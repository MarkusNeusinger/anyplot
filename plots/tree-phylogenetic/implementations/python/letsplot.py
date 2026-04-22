""" pyplots.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import re

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()


# Simple Newick parser for phylogenetic tree
def parse_newick(newick_str):
    """Parse Newick format string into tree structure."""
    newick_str = newick_str.strip().rstrip(";")
    node_id = [0]

    def parse_node(s, parent_id=None, depth=0):
        nodes = []
        s = s.strip()

        # Check if this is a leaf node (no parentheses)
        if "(" not in s:
            # Leaf: name:length or just name
            match = re.match(r"([^:]*):?([\d.]*)", s)
            name = match.group(1) if match else s
            length = float(match.group(2)) if match and match.group(2) else 0.1
            node_id[0] += 1
            return [
                {"id": node_id[0], "name": name, "length": length, "parent": parent_id, "depth": depth, "children": []}
            ]

        # Internal node: find matching parentheses
        if s.startswith("("):
            # Find the matching closing parenthesis
            level = 0
            children_str = ""
            remaining = ""
            for i, c in enumerate(s):
                if c == "(":
                    level += 1
                elif c == ")":
                    level -= 1
                    if level == 0:
                        children_str = s[1:i]
                        remaining = s[i + 1 :]
                        break

            # Parse branch length for this internal node
            match = re.match(r":?([\d.]*)", remaining)
            length = float(match.group(1)) if match and match.group(1) else 0.1

            node_id[0] += 1
            current_id = node_id[0]
            current_node = {
                "id": current_id,
                "name": "",
                "length": length,
                "parent": parent_id,
                "depth": depth,
                "children": [],
            }
            nodes.append(current_node)

            # Split children by comma at level 0
            children = []
            level = 0
            current = ""
            for c in children_str:
                if c == "(":
                    level += 1
                elif c == ")":
                    level -= 1
                if c == "," and level == 0:
                    children.append(current.strip())
                    current = ""
                else:
                    current += c
            if current.strip():
                children.append(current.strip())

            # Parse each child
            for child_str in children:
                child_nodes = parse_node(child_str, current_id, depth + 1)
                nodes.extend(child_nodes)
                current_node["children"].extend([n["id"] for n in child_nodes if n["parent"] == current_id])

        return nodes

    return parse_node(newick_str)


# Primate phylogenetic tree (based on mitochondrial DNA)
newick = "((((Human:0.1,Chimpanzee:0.12):0.08,Gorilla:0.2):0.15,(Orangutan:0.25,Gibbon:0.28):0.1):0.2,(Macaque:0.35,(Baboon:0.3,Mandrill:0.32):0.05):0.15)"

nodes = parse_newick(newick)

# Build node dictionary for easy lookup
node_dict = {n["id"]: n for n in nodes}


# Calculate x positions (cumulative branch length from root)
def calc_x_positions(node_dict):
    # Find root (node with no parent)
    root = [n for n in node_dict.values() if n["parent"] is None][0]

    def assign_x(node_id, parent_x=0):
        node = node_dict[node_id]
        node["x"] = parent_x + node["length"]
        for child_id in node["children"]:
            assign_x(child_id, node["x"])

    assign_x(root["id"], 0)


# Calculate y positions (spacing for leaves, centered for internal nodes)
def calc_y_positions(node_dict):
    # Get leaves in order
    leaves = [n for n in node_dict.values() if not n["children"]]
    leaves.sort(key=lambda n: n["id"])

    # Assign y positions to leaves
    for i, leaf in enumerate(leaves):
        leaf["y"] = i

    # Calculate y for internal nodes (average of children)
    def get_y(node_id):
        node = node_dict[node_id]
        if "y" in node:
            return node["y"]
        child_ys = [get_y(cid) for cid in node["children"]]
        node["y"] = sum(child_ys) / len(child_ys)
        return node["y"]

    for node in node_dict.values():
        get_y(node["id"])


calc_x_positions(node_dict)
calc_y_positions(node_dict)

# Build segments for the tree (horizontal and vertical lines)
segments = []
for node in node_dict.values():
    if node["parent"] is not None:
        parent = node_dict[node["parent"]]
        # Horizontal segment from parent x to node x at node y
        segments.append({"x": parent["x"], "xend": node["x"], "y": node["y"], "yend": node["y"], "type": "horizontal"})
        # Vertical segment at parent x from parent y to node y
        segments.append(
            {"x": parent["x"], "xend": parent["x"], "y": parent["y"], "yend": node["y"], "type": "vertical"}
        )

df_segments = pd.DataFrame(segments)

# Get leaf labels
leaves = [n for n in node_dict.values() if not n["children"]]
df_labels = pd.DataFrame([{"x": n["x"] + 0.02, "y": n["y"], "label": n["name"]} for n in leaves])

# Get internal node points
df_nodes = pd.DataFrame([{"x": n["x"], "y": n["y"]} for n in node_dict.values()])

# Define clade colors for visualization
clade_colors = {
    "Human": "#306998",
    "Chimpanzee": "#306998",
    "Gorilla": "#306998",
    "Orangutan": "#FFD43B",
    "Gibbon": "#FFD43B",
    "Macaque": "#22C55E",
    "Baboon": "#22C55E",
    "Mandrill": "#22C55E",
}

df_labels["color"] = df_labels["label"].map(clade_colors)

# Create the phylogenetic tree plot
plot = (
    ggplot()
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_segments, color="#306998", size=1.5)
    + geom_point(aes(x="x", y="y"), data=df_nodes, color="#306998", size=4)
    + geom_point(aes(x="x", y="y", color="color"), data=df_labels, size=6, show_legend=False)
    + geom_text(aes(x="x", y="y", label="label"), data=df_labels, hjust=0, size=14, family="sans-serif")
    + scale_color_identity()
    + scale_x_continuous(limits=[0, 0.85])
    + labs(
        title="Primate Evolution · tree-phylogenetic · letsplot · pyplots.ai",
        x="Evolutionary Distance (substitutions per site)",
        y="",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_blank(),
        axis_text_x=element_text(size=16),
        axis_text_y=element_blank(),
        axis_ticks_y=element_blank(),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color="#E5E5E5", size=0.5),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
