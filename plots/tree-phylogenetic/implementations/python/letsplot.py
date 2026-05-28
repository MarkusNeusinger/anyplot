""" anyplot.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-15
"""

import os
import re

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]


def parse_newick(newick_str):
    """Parse Newick format string into tree structure."""
    newick_str = newick_str.strip().rstrip(";")
    node_id = [0]

    def parse_node(s, parent_id=None, depth=0):
        nodes = []
        s = s.strip()

        if "(" not in s:
            match = re.match(r"([^:]*):?([\d.]*)", s)
            name = match.group(1) if match else s
            length = float(match.group(2)) if match and match.group(2) else 0.1
            node_id[0] += 1
            return [
                {"id": node_id[0], "name": name, "length": length, "parent": parent_id, "depth": depth, "children": []}
            ]

        if s.startswith("("):
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

            for child_str in children:
                child_nodes = parse_node(child_str, current_id, depth + 1)
                nodes.extend(child_nodes)
                current_node["children"].extend([n["id"] for n in child_nodes if n["parent"] == current_id])

        return nodes

    return parse_node(newick_str)


newick = "((((Human:0.1,Chimpanzee:0.12):0.08,Gorilla:0.2):0.15,(Orangutan:0.25,Gibbon:0.28):0.1):0.2,(Macaque:0.35,(Baboon:0.3,Mandrill:0.32):0.05):0.15)"

nodes = parse_newick(newick)

node_dict = {n["id"]: n for n in nodes}


def calc_x_positions(node_dict):
    root = [n for n in node_dict.values() if n["parent"] is None][0]

    def assign_x(node_id, parent_x=0):
        node = node_dict[node_id]
        node["x"] = parent_x + node["length"]
        for child_id in node["children"]:
            assign_x(child_id, node["x"])

    assign_x(root["id"], 0)


def calc_y_positions(node_dict):
    leaves = [n for n in node_dict.values() if not n["children"]]
    leaves.sort(key=lambda n: n["id"])

    for i, leaf in enumerate(leaves):
        leaf["y"] = i

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

segments = []
for node in node_dict.values():
    if node["parent"] is not None:
        parent = node_dict[node["parent"]]
        segments.append({"x": parent["x"], "xend": node["x"], "y": node["y"], "yend": node["y"], "type": "horizontal"})
        segments.append(
            {"x": parent["x"], "xend": parent["x"], "y": parent["y"], "yend": node["y"], "type": "vertical"}
        )

df_segments = pd.DataFrame(segments)

leaves = [n for n in node_dict.values() if not n["children"]]
df_labels = pd.DataFrame([{"x": n["x"] + 0.02, "y": n["y"], "label": n["name"]} for n in leaves])

df_nodes = pd.DataFrame([{"x": n["x"], "y": n["y"]} for n in node_dict.values()])

clade_colors = {
    "Human": IMPRINT[0],
    "Chimpanzee": IMPRINT[0],
    "Gorilla": IMPRINT[0],
    "Orangutan": IMPRINT[1],
    "Gibbon": IMPRINT[1],
    "Macaque": IMPRINT[2],
    "Baboon": IMPRINT[2],
    "Mandrill": IMPRINT[2],
}

df_labels["color"] = df_labels["label"].map(clade_colors)

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major_x=element_line(color=GRID_COLOR, size=0.3),
    panel_grid_major_y=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title_x=element_text(size=20, color=INK),
    axis_title_y=element_blank(),
    axis_text_x=element_text(size=16, color=INK_SOFT),
    axis_text_y=element_blank(),
    axis_ticks_y=element_blank(),
    axis_line_y=element_blank(),
    plot_title=element_text(size=24, face="bold", color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=16, color=INK_SOFT),
)

plot = (
    ggplot()
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_segments, color=IMPRINT[0], size=1.5)
    + geom_point(aes(x="x", y="y"), data=df_nodes, color=IMPRINT[0], size=4)
    + geom_point(aes(x="x", y="y", color="color"), data=df_labels, size=6, show_legend=False)
    + geom_text(aes(x="x", y="y", label="label"), data=df_labels, hjust=0, size=14, color=INK_SOFT, family="sans-serif")
    + scale_color_identity()
    + scale_x_continuous(limits=[0, 0.85])
    + labs(
        title="Primate Evolution · tree-phylogenetic · letsplot · anyplot.ai",
        x="Evolutionary Distance (substitutions per site)",
    )
    + theme_minimal()
    + anyplot_theme
    + ggsize(1600, 900)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
