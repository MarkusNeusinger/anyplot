"""anyplot.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per clade in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SCALE_BAR = 0.05  # length of the scale bar in branch-length units

# Columns: set these to your table's column names
PARENT = "Parent node"  # role: newick_string
CHILD = "Child node"  # role: extra
LENGTH = "Branch length (substitutions per site)"  # role: branch_lengths
CLADE = "Clade"  # role: extra
LABEL = "Common name"  # role: species_names

# Data: replace this block with your own edge list, for example df = pd.read_csv("tree_edges.csv")
df = pd.DataFrame(
    {
        PARENT: [
            "Root",
            "Root",
            "Hominoidea",
            "Hominoidea",
            "Hominidae",
            "Hominidae",
            "Homininae",
            "Homininae",
            "Pan",
            "Pan",
            "Hylobatidae",
            "Cercopithecidae",
            "Cercopithecidae",
        ],
        CHILD: [
            "Hominoidea",
            "Cercopithecidae",
            "Hominidae",
            "Hylobatidae",
            "Homininae",
            "Pongo pygmaeus",
            "Homo sapiens",
            "Pan",
            "Pan troglodytes",
            "Pan paniscus",
            "Hylobates lar",
            "Macaca mulatta",
            "Papio anubis",
        ],
        LENGTH: [0.15, 0.18, 0.08, 0.12, 0.05, 0.09, 0.03, 0.02, 0.015, 0.015, 0.06, 0.10, 0.11],
        CLADE: [
            "Apes",
            "Old World Monkeys",
            "Apes",
            "Lesser Apes",
            "Apes",
            "Apes",
            "Apes",
            "Apes",
            "Apes",
            "Apes",
            "Lesser Apes",
            "Old World Monkeys",
            "Old World Monkeys",
        ],
        LABEL: [None] * 5
        + ["Orangutan", "Human", None, "Chimpanzee", "Bonobo", "Gibbon", "Rhesus Macaque", "Olive Baboon"],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
clades = list(df[CLADE].unique())
children = df.groupby(PARENT, sort=False)[CHILD].apply(list).to_dict()
edge_length = df.set_index(CHILD)[LENGTH].to_dict()
edge_clade = df.set_index(CHILD)[CLADE].to_dict()
edge_parent = df.set_index(CHILD)[PARENT].to_dict()
common_name = df.set_index(CHILD)[LABEL].to_dict()


def leaves(node):
    if node not in children:
        return [node]
    return [leaf for child in children[node] for leaf in leaves(child)]


ROOT = next(p for p in children if p not in edge_length)  # the node that is never a child
leaf_order = leaves(ROOT)
y_pos = {leaf: float(i) for i, leaf in enumerate(leaf_order)}
x_pos = {ROOT: 0.0}


def place(node):
    for child in children.get(node, []):
        x_pos[child] = x_pos[node] + edge_length[child]
        place(child)
    if node in children:
        y_pos[node] = float(np.mean([y_pos[child] for child in children[node]]))


place(ROOT)

# Right-angled branches: a vertical connector at the parent, a horizontal run to the child
segments = []
for child, parent in edge_parent.items():
    segments.append(
        {"x": x_pos[parent], "y": y_pos[parent], "x2": x_pos[parent], "y2": y_pos[child], CLADE: edge_clade[child]}
    )
    segments.append(
        {"x": x_pos[parent], "y": y_pos[child], "x2": x_pos[child], "y2": y_pos[child], CLADE: edge_clade[child]}
    )
segments = pd.DataFrame(segments)


def node_table(names):
    return pd.DataFrame(
        {
            "name": names,
            "label": [common_name.get(n) or n for n in names],
            "x": [x_pos[n] for n in names],
            "y": [y_pos[n] for n in names],
            CLADE: [edge_clade[n] for n in names],
        }
    )


leaf_df = node_table(leaf_order)
internal_df = node_table([n for n in children if n != ROOT])

clade_field = CLADE.translate(ESCAPE)
clade_color = alt.Color(
    clade_field, type="nominal", title=CLADE, sort=None, scale=alt.Scale(domain=clades, range=IMPRINT_PALETTE)
)

branches = (
    alt.Chart(segments)
    .mark_rule(strokeWidth=2.5)
    .encode(
        x=alt.X("x:Q", title=LENGTH, scale=alt.Scale(domain=[-0.01, max(x_pos.values()) * 1.45])),
        y=alt.Y("y:Q", title=None, scale=alt.Scale(domain=[-2.0, len(leaf_order) - 0.5]), axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=clade_color,
        tooltip=[alt.Tooltip(clade_field, type="nominal", title=CLADE)],
    )
)

internal_points = (
    alt.Chart(internal_df)
    .mark_circle(size=60, opacity=1)
    .encode(
        x="x:Q",
        y="y:Q",
        color=clade_color,
        tooltip=[alt.Tooltip("name:N", title="Node"), alt.Tooltip(clade_field, type="nominal", title=CLADE)],
    )
)

leaf_points = (
    alt.Chart(leaf_df)
    .mark_circle(size=110, opacity=1)
    .encode(
        x="x:Q",
        y="y:Q",
        color=clade_color,
        tooltip=[
            alt.Tooltip("name:N", title="Species"),
            alt.Tooltip("label:N", title=LABEL),
            alt.Tooltip(clade_field, type="nominal", title=CLADE),
        ],
    )
)

leaf_labels = (
    alt.Chart(leaf_df)
    .mark_text(align="left", baseline="middle", dx=9, fontSize=11, fontWeight="bold", color=INK)
    .encode(x="x:Q", y="y:Q", text="label:N")
)

# Scale bar drawn in the same branch-length units as the x axis
bar_y = -1.0
bar = pd.DataFrame([{"x": 0.0, "x2": SCALE_BAR, "y": bar_y, "text": f"{SCALE_BAR:g} substitutions per site"}])
scale_bar = alt.Chart(bar).mark_rule(strokeWidth=2.5, color=INK_SOFT).encode(x="x:Q", x2="x2:Q", y="y:Q")
scale_bar_label = (
    alt.Chart(bar)
    .mark_text(align="left", baseline="top", dy=6, fontSize=10, color=INK_SOFT)
    .encode(x="x:Q", y="y:Q", text="text:N")
)

chart = (
    alt.layer(branches, internal_points, leaf_points, leaf_labels, scale_bar, scale_bar_label)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(
            "Primate Evolution · tree-phylogenetic · python · altair · anyplot.ai",
            fontSize=16,
            anchor="middle",
            color=INK,
            subtitle="Phylogenetic relationships with evolutionary distance",
            subtitleFontSize=11,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        titleColor=INK,
        labelColor=INK_SOFT,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
    )
    .configure_title(color=INK)
    .configure_legend(
        orient="bottom-right",
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=11,
        symbolType="stroke",
        symbolStrokeWidth=3,
        padding=6,
    )
    .configure_view(fill=PAGE_BG, stroke=None)
)

# Save: pad up to the canonical canvas, never crop
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
if w < TW or h < TH:
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
