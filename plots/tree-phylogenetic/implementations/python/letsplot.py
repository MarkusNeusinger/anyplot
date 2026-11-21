"""anyplot.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions, one per clade in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
NODE = "Node"  # role: extra
PARENT = "Parent node"  # role: extra
SPECIES = "Species"  # role: species_names
BRANCH = "Branch length (substitutions per site)"  # role: branch_lengths
CLADE = "Clade"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("tree_nodes.csv")
# One row per node: its parent (empty for the root), its branch length and, for tips, species and clade.
newick = "((((Human:0.1,Chimpanzee:0.12):0.08,Gorilla:0.2):0.15,(Orangutan:0.25,Gibbon:0.28):0.1):0.2,(Macaque:0.35,(Baboon:0.3,Mandrill:0.32):0.05):0.15)"
clade_of = {
    "Human": "Hominines",
    "Chimpanzee": "Hominines",
    "Gorilla": "Hominines",
    "Orangutan": "Orangutan and gibbon",
    "Gibbon": "Orangutan and gibbon",
    "Macaque": "Old World monkeys",
    "Baboon": "Old World monkeys",
    "Mandrill": "Old World monkeys",
}


def parse_newick(text):
    """Return one record per node of a Newick string (preorder), with parent ids."""
    rows = []

    def read(pos, parent):
        node_id = len(rows)
        row = {NODE: node_id, PARENT: parent, SPECIES: None, BRANCH: 0.0, CLADE: None}
        rows.append(row)
        if text[pos] == "(":
            pos += 1
            while True:
                pos = read(pos, node_id)
                pos += 1  # skip "," or ")"
                if text[pos - 1] == ")":
                    break
        else:
            end = pos
            while text[end] not in ":,)":
                end += 1
            row[SPECIES] = text[pos:end]
            row[CLADE] = clade_of[row[SPECIES]]
            pos = end
        if pos < len(text) and text[pos] == ":":
            end = pos + 1
            while end < len(text) and text[end] not in ",)":
                end += 1
            row[BRANCH] = float(text[pos + 1 : end])
            pos = end
        return pos

    read(0, None)
    return rows


df = pd.DataFrame(parse_newick(newick.rstrip(";")))

# Plot: reads only df and the constants above
parent_of = dict(zip(df[NODE], df[PARENT], strict=True))
children = {i: [n for n, p in parent_of.items() if p == i] for i in df[NODE]}
length = dict(zip(df[NODE], df[BRANCH], strict=True))

# x: cumulative branch length from the root; y: tips in preorder, inner nodes at the mean of their children
x_pos, y_pos, tip_clades = {}, {}, {}
tips = [n for n in df[NODE] if not children[n]]
y_pos.update({n: float(i) for i, n in enumerate(tips)})
for n, c in zip(df[NODE], df[CLADE], strict=True):
    if not children[n]:
        tip_clades[n] = {c}


def place(node, x0):
    x_pos[node] = x0 + (length[node] if pd.notna(parent_of[node]) else 0.0)
    for child in children[node]:
        place(child, x_pos[node])
    if children[node]:
        y_pos[node] = sum(y_pos[ch] for ch in children[node]) / len(children[node])
        tip_clades[node] = set().union(*(tip_clades[ch] for ch in children[node]))


root = int(df.loc[df[PARENT].isna(), NODE].iloc[0])
place(root, 0.0)

# A branch takes its clade's color when all tips below it share one clade, otherwise the neutral label
clades = list(dict.fromkeys(df[CLADE].dropna()))
MIXED = "Shared ancestry"
node_clade = {n: (next(iter(s)) if len(s) == 1 else MIXED) for n, s in tip_clades.items()}

segments = []
for node, parent in parent_of.items():
    if pd.isna(parent):
        continue
    parent = int(parent)
    segments.append(
        {"x": x_pos[parent], "xend": x_pos[node], "y": y_pos[node], "yend": y_pos[node], "clade": node_clade[node]}
    )
    segments.append(
        {"x": x_pos[parent], "xend": x_pos[parent], "y": y_pos[parent], "yend": y_pos[node], "clade": node_clade[node]}
    )
df_segments = pd.DataFrame(segments)

df_nodes = pd.DataFrame([{"x": x_pos[n], "y": y_pos[n], "clade": node_clade[n]} for n in df[NODE]])
df_labels = pd.DataFrame(
    [
        {"x": x_pos[n] + 0.01 * max(x_pos.values()), "y": y_pos[n], "label": s}
        for n, s in zip(df[NODE], df[SPECIES], strict=True)
        if not children[n]
    ]
)

legend_order = [*clades, MIXED]
clade_colors = [*IMPRINT_PALETTE[: len(clades)], INK_SOFT]

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major_x=element_line(color=GRID_COLOR, size=0.3),
    panel_grid_major_y=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title_x=element_text(size=12, color=INK),
    axis_title_y=element_blank(),
    axis_text_x=element_text(size=10, color=INK_SOFT),
    axis_text_y=element_blank(),
    axis_ticks_y=element_blank(),
    axis_line_y=element_blank(),
    plot_title=element_text(size=16, face="bold", color=INK),
    legend_title=element_text(size=11, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=10, color=INK_SOFT),
)

plot = (
    ggplot()
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend", color="clade"), data=df_segments, size=1.1)
    + geom_point(aes(x="x", y="y", color="clade"), data=df_nodes, size=2.5, show_legend=False)
    + geom_text(aes(x="x", y="y", label="label"), data=df_labels, hjust=0, size=5.5, color=INK_SOFT)
    + scale_color_manual(values=clade_colors, limits=legend_order, name=CLADE)
    + scale_x_continuous(limits=[0, max(x_pos.values()) * 1.3])
    + labs(title="tree-phylogenetic · python · letsplot · anyplot.ai", x=BRANCH)
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
