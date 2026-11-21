""" anyplot.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 79/100 | Updated: 2026-11-21
"""

import os

import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    theme,
    theme_void,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SCALE_BAR = 0.1  # branch length shown by the scale bar

# Column names
NODE = "node"  # role: species_names
PARENT = "parent"  # role: newick_string
LENGTH = "branch length"  # role: branch_lengths
CLADE = "clade"  # derived grouping of the tree, used for color

# Data: primate phylogeny (mitochondrial DNA), one row per node, tips are the species
df = pd.DataFrame(
    [
        ("Primates", "", 0.00, "Haplorrhini"),
        ("Lemur", "Primates", 0.45, "Strepsirrhini"),
        ("Haplorrhini", "Primates", 0.15, "Haplorrhini"),
        ("Catarrhini", "Haplorrhini", 0.10, "Haplorrhini"),
        ("Cercopithecidae", "Catarrhini", 0.10, "Old World monkeys"),
        ("Macaque", "Cercopithecidae", 0.20, "Old World monkeys"),
        ("Baboon", "Cercopithecidae", 0.20, "Old World monkeys"),
        ("Hominoidea", "Catarrhini", 0.10, "Hominoidea"),
        ("Gibbon", "Hominoidea", 0.15, "Gibbons"),
        ("Homininae", "Hominoidea", 0.10, "Hominoidea"),
        ("Orangutan", "Hominoidea", 0.20, "Orangutan"),
        ("Gorilla", "Homininae", 0.15, "Gorilla"),
        ("Hominini", "Homininae", 0.10, "Hominini"),
        ("Human", "Hominini", 0.10, "Hominini"),
        ("Chimpanzee", "Hominini", 0.10, "Hominini"),
    ],
    columns=[NODE, PARENT, LENGTH, CLADE],
)

# Layout: x is the summed branch length from the root, y spreads the tips in tree order
children = df.groupby(PARENT)[NODE].apply(list).to_dict()
length = df.set_index(NODE)[LENGTH].to_dict()
clade = df.set_index(NODE)[CLADE].to_dict()
root = df.loc[df[PARENT] == "", NODE].iloc[0]

x_pos, y_pos = {root: 0.0}, {}
tip_order = []


def place(node):
    kids = children.get(node, [])
    if not kids:
        y_pos[node] = float(len(tip_order))
        tip_order.append(node)
        return
    for kid in kids:
        x_pos[kid] = x_pos[node] + length[kid]
        place(kid)
    y_pos[node] = sum(y_pos[k] for k in kids) / len(kids)


place(root)

# Right-angled branches: a horizontal segment per node and a vertical connector across its children
rows = []
for node, parent in zip(df[NODE], df[PARENT], strict=True):
    if parent:
        rows.append((x_pos[parent], x_pos[node], y_pos[node], y_pos[node], clade[node]))
    kids = children.get(node, [])
    if kids:
        rows.append((x_pos[node], x_pos[node], min(y_pos[k] for k in kids), max(y_pos[k] for k in kids), clade[node]))
X, XEND, Y, YEND, SPECIES = "x", "xend", "y", "yend", "species"
segments = pd.DataFrame(rows, columns=[X, XEND, Y, YEND, CLADE])
tips = pd.DataFrame({X: [x_pos[t] for t in tip_order], Y: [y_pos[t] for t in tip_order], SPECIES: tip_order})
clade_order = list(dict.fromkeys(df[CLADE]))

x_max = max(x_pos.values())
y_max = len(tip_order) - 1

# Plot
plot = (
    ggplot()
    + geom_segment(segments, aes(x=X, xend=XEND, y=Y, yend=YEND, color=CLADE), size=1.4, lineend="round")
    + geom_point(tips, aes(x=X, y=Y), size=2.6, color=INK)
    + geom_text(tips, aes(x=X, y=Y, label=SPECIES), ha="left", nudge_x=x_max * 0.025, size=11, color=INK)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=clade_order)
    + annotate("segment", x=0.0, xend=SCALE_BAR, y=-1.2, yend=-1.2, size=1.4, color=INK_SOFT)
    + annotate("text", x=SCALE_BAR / 2, y=-1.8, label=f"{SCALE_BAR} substitutions / site", size=9, color=INK_SOFT)
    + labs(title="tree-phylogenetic · python · plotnine · anyplot.ai", color="Clade")
    + coord_cartesian(xlim=(-0.03, x_max * 1.6), ylim=(-2.2, y_max + 0.6))
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=12, ha="center", color=INK),
        legend_position=(0.97, 0.5),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_key=element_blank(),
        plot_margin=0.03,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
