""" anyplot.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order, one per clade
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
TAXON = "Taxon"  # role: species_names
PARENT = "Parent"  # role: extra
BRANCH = "Branch length (substitutions per site)"  # role: branch_lengths
CLADE = "Clade"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("tree.csv")
# Catarrhine primates from mitochondrial DNA (simplified branch lengths), one row per node:
# (Macaque, (Gibbon, (Orangutan, (Gorilla, (Chimpanzee, Human))))) in Newick terms
df = pd.DataFrame(
    [
        ("Catarrhini", None, 0.0, None),
        ("Macaque", "Catarrhini", 0.26, "Old World monkeys"),
        ("Hominoidea", "Catarrhini", 0.07, None),
        ("Gibbon", "Hominoidea", 0.19, "Gibbons"),
        ("Hominidae", "Hominoidea", 0.04, "Great apes"),
        ("Orangutan", "Hominidae", 0.15, "Great apes"),
        ("Homininae", "Hominidae", 0.03, "Great apes"),
        ("Gorilla", "Homininae", 0.10, "Great apes"),
        ("Hominini", "Homininae", 0.02, "Great apes"),
        ("Chimpanzee", "Hominini", 0.065, "Great apes"),
        ("Human", "Hominini", 0.065, "Great apes"),
    ],
    columns=[TAXON, PARENT, BRANCH, CLADE],
)

# Plot: rectangular layout; x is the summed branch length from the root, tips are spread evenly in depth-first order
parent_of = df.set_index(TAXON)[PARENT].to_dict()
branch_of = df.set_index(TAXON)[BRANCH].fillna(0.0).to_dict()
clade_of = df.set_index(TAXON)[CLADE].to_dict()
children = {parent: group[TAXON].tolist() for parent, group in df.dropna(subset=[PARENT]).groupby(PARENT, sort=False)}
root = df.loc[df[PARENT].isna(), TAXON].iloc[0]

order = [root]  # breadth-first: every parent comes before its children
for taxon in order:
    order.extend(children.get(taxon, []))
depth = {root: 0.0}
for taxon in order[1:]:
    depth[taxon] = depth[parent_of[taxon]] + float(branch_of[taxon])

tips = []
stack = [root]
while stack:
    taxon = stack.pop()
    if taxon in children:
        stack.extend(reversed(children[taxon]))
    else:
        tips.append(taxon)
height = {taxon: float(i) for i, taxon in enumerate(tips)}
for taxon in reversed(order):
    if taxon in children:
        height[taxon] = sum(height[child] for child in children[taxon]) / len(children[taxon])

clades = [clade for clade in df[CLADE].drop_duplicates() if not pd.isna(clade)]
segments = {clade: [] for clade in [*clades, None]}
for taxon in order[1:]:  # the branch into each node, in that node's clade colour
    key = None if pd.isna(clade_of[taxon]) else clade_of[taxon]
    segments[key] += [(depth[parent_of[taxon]], height[taxon]), (depth[taxon], height[taxon]), (None, None)]
for taxon, kids in children.items():  # the connector joining a node's children, in the node's clade colour
    key = None if pd.isna(clade_of[taxon]) else clade_of[taxon]
    lows, highs = min(height[kid] for kid in kids), max(height[kid] for kid in kids)
    segments[key] += [(depth[taxon], lows), (depth[taxon], highs), (None, None)]

clade_colors = [IMPRINT_PALETTE[i] for i in range(len(clades))]
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    # branch series per clade, the shared ancestral stems in neutral ink, then the tip markers per clade
    colors=(*clade_colors, INK, *clade_colors),
    value_colors=(INK,) * (2 * len(clades) + 1),  # tip labels in theme ink, whatever the marker colour
    guide_stroke_color=RULE,
    major_guide_stroke_color=RULE,
    guide_stroke_dasharray="none",
    major_guide_stroke_dasharray="none",
    title_font_size=66,
    label_font_size=46,
    major_label_font_size=46,
    legend_font_size=46,
    value_font_size=8,
    value_label_font_size=50,
    opacity=1,
    opacity_hover=1,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=7,
)

max_depth = max(depth.values())
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="tree-phylogenetic · python · pygal · anyplot.ai",
    x_title=BRANCH,
    xrange=(0, max_depth * 1.3),
    range=(-0.6, len(tips) - 0.4),
    show_y_labels=False,
    show_x_guides=True,
    show_y_guides=False,
    show_dots=False,
    allow_interruptions=True,
    print_labels=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=max(len(clades), 1),
    legend_box_size=40,
    truncate_legend=-1,
    spacing=24,
    margin=40,
)

for clade in clades:
    chart.add(str(clade), segments[clade])
chart.add(None, segments[None])
for clade in clades:
    # two no-break spaces keep the species name clear of its tip marker
    tip_points = [
        {"value": (depth[tip], height[tip]), "label": f"  {tip}"} for tip in tips if clade_of[tip] == clade
    ]
    chart.add(None, tip_points, stroke=False, show_dots=True, dots_size=14)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
