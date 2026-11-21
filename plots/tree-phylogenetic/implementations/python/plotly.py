"""anyplot.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per clade in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SCALE_BAR = 0.1  # length of the scale bar, in substitutions per site

# Columns: set these to your table's column names
NODE = "Node"  # role: species_names
PARENT = "Parent"  # role: extra
LENGTH = "Branch length (substitutions per site)"  # role: branch_lengths
CLADE = "Clade"  # role: extra

# Data: replace this block with your own tree as an edge list, one row per node, parents before children
# Old World monkeys, mitochondrial DNA; the root has no parent and no clade
df = pd.DataFrame(
    {
        NODE: [
            "Root",
            "Cercopithecinae",
            "Papionini",
            "Macaque-Baboon",
            "Macaque",
            "Baboon",
            "Mandrill",
            "Gelada",
            "Cercopithecini",
            "Patas",
            "Guenon-Talapoin",
            "Guenon",
            "Talapoin",
            "Langur",
        ],
        PARENT: [
            None,
            "Root",
            "Cercopithecinae",
            "Papionini",
            "Macaque-Baboon",
            "Macaque-Baboon",
            "Papionini",
            "Papionini",
            "Cercopithecinae",
            "Cercopithecini",
            "Cercopithecini",
            "Guenon-Talapoin",
            "Guenon-Talapoin",
            "Root",
        ],
        LENGTH: [0.0, 0.18, 0.10, 0.10, 0.12, 0.14, 0.26, 0.25, 0.07, 0.26, 0.05, 0.19, 0.12, 0.48],
        CLADE: [
            None,
            None,
            "Papionini",
            "Papionini",
            "Papionini",
            "Papionini",
            "Papionini",
            "Papionini",
            "Cercopithecini",
            "Cercopithecini",
            "Cercopithecini",
            "Cercopithecini",
            "Cercopithecini",
            "Colobinae",
        ],
    }
)

# Plot: reads only df and the constants above
parent_of = dict(zip(df[NODE], df[PARENT], strict=True))
clade_of = dict(zip(df[NODE], df[CLADE], strict=True))
children = {}
for node, parent in parent_of.items():
    if not pd.isna(parent):
        children.setdefault(parent, []).append(node)

# Distance from the root: cumulative branch lengths (parents come before children in df)
dist = {}
for node, length in zip(df[NODE], df[LENGTH], strict=True):
    parent = parent_of[node]
    dist[node] = length if pd.isna(parent) else dist[parent] + length

# Tips take evenly spaced rows from the table order; internal nodes sit at the mean of their children
leaves = [n for n in df[NODE] if n not in children]
row = {leaf: len(leaves) - 1 - i for i, leaf in enumerate(leaves)}
for node in reversed(list(df[NODE])):
    if node in children:
        row[node] = sum(row[c] for c in children[node]) / len(children[node])

clades = list(dict.fromkeys(c for c in df[CLADE] if not pd.isna(c)))
clade_color = {c: IMPRINT_PALETTE[i] for i, c in enumerate(clades)}

fig = go.Figure()

# Branches: one right-angled path per node, grouped by clade; backbone branches stay neutral
for clade in [None, *clades]:
    xs, ys = [], []
    for node, parent in parent_of.items():
        if pd.isna(parent) or (clade_of[node] if not pd.isna(clade_of[node]) else None) != clade:
            continue
        xs += [dist[parent], dist[node], None, dist[parent], dist[parent], None]
        ys += [row[node], row[node], None, row[node], row[parent], None]
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            line={"color": INK_SOFT if clade is None else clade_color[clade], "width": 2.5},
            name=clade,
            showlegend=clade is not None,
            hoverinfo="skip",
        )
    )

# Tips with species labels
fig.add_trace(
    go.Scatter(
        x=[dist[n] for n in leaves],
        y=[row[n] for n in leaves],
        mode="markers+text",
        marker={
            "size": 10,
            "color": [clade_color[clade_of[n]] for n in leaves],
            "line": {"width": 1.2, "color": INK_SOFT},
        },
        text=leaves,
        textposition="middle right",
        textfont={"size": 12, "color": INK},
        hovertemplate="%{text}<br>Distance: %{x:.2f}<extra></extra>",
        showlegend=False,
    )
)

# Internal nodes
internal = [n for n in df[NODE] if n in children]
fig.add_trace(
    go.Scatter(
        x=[dist[n] for n in internal],
        y=[row[n] for n in internal],
        mode="markers",
        marker={"size": 6, "color": INK_SOFT},
        text=internal,
        hovertemplate="%{text}<br>Distance: %{x:.2f}<extra></extra>",
        showlegend=False,
    )
)

# Scale bar below the lowest tip, drawn in the same units as the branches
bar_y = min(row.values()) - 1.1
fig.add_trace(
    go.Scatter(
        x=[0, SCALE_BAR],
        y=[bar_y, bar_y],
        mode="lines",
        line={"color": INK, "width": 2.5},
        showlegend=False,
        hoverinfo="skip",
    )
)
fig.add_annotation(
    x=SCALE_BAR / 2,
    y=bar_y - 0.5,
    text=f"{SCALE_BAR:g} substitutions/site",
    showarrow=False,
    font={"size": 11, "color": INK_SOFT},
)

# Style
x_max = max(dist.values())
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={
        "text": "Old World Monkeys · tree-phylogenetic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Distance from root (substitutions per site)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [-0.03 * x_max, x_max * 1.2],
        "showgrid": False,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "range": [bar_y - 1.1, max(row.values()) + 0.8],
        "showticklabels": False,
        "showgrid": False,
        "zeroline": False,
    },
    legend={
        "orientation": "h",
        "x": 0.5,
        "xanchor": "center",
        "y": 1.0,
        "yanchor": "bottom",
        "font": {"size": 11, "color": INK_SOFT},
    },
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 40, "r": 30, "t": 80, "b": 55},
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
