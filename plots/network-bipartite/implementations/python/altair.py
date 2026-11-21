""" anyplot.ai
network-bipartite: Bipartite Network Graph
Library: altair 6.3.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
"""

import os
import sys


# Remove script directory from sys.path to avoid importing local altair.py
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 for the first set, position 2 for the second
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SOURCE = "Author"  # role: source
TARGET = "Paper"  # role: target

# Data: replace this block with your own edge list, for example df = pd.read_csv("edges.csv")
# Researcher-paper affiliation network (bibliometrics): one row per authorship
np.random.seed(42)
authors = [
    "Chen, L.",
    "Smith, R.",
    "Patel, A.",
    "Kim, J.",
    "Müller, K.",
    "Davis, M.",
    "López, C.",
    "Nguyen, T.",
    "Brown, E.",
    "Ivanova, S.",
    "Ahmed, F.",
    "Wilson, G.",
]
papers = [f"P{i + 1:02d}" for i in range(15)]
rows = []
for author in authors:
    n_papers = np.random.randint(2, 5)
    for paper in np.random.choice(papers, size=n_papers, replace=False):
        rows.append({SOURCE: author, TARGET: paper})
df = pd.DataFrame(rows).drop_duplicates()

# Plot: reads only df and the constants above
SET_A, SET_B = SOURCE, TARGET
title = "network-bipartite · python · altair · anyplot.ai"
xscale = alt.Scale(domain=[0.0, 1.0])
yscale = alt.Scale(domain=[0.0, 1.05])


def column_nodes(names, x, set_name):
    """Nodes of one set in a column, ordered as in df, with their degree."""
    degree = df[set_name].value_counts()
    return pd.DataFrame(
        {
            "node": names,
            "x": x,
            "y": np.linspace(0.08, 0.88, len(names)),
            "set": set_name,
            "degree": [int(degree.get(n, 0)) for n in names],
        }
    )


nodes_a = column_nodes(list(df[SET_A].unique()), 0.24, SET_A)
nodes_b = column_nodes(sorted(df[SET_B].unique()), 0.76, SET_B)
nodes = pd.concat([nodes_a, nodes_b], ignore_index=True)

# Edge coordinates: one rule segment per row of df
pos_a = nodes_a.set_index("node")[["x", "y"]]
pos_b = nodes_b.set_index("node")[["x", "y"]]
edges = pd.DataFrame(
    {
        "x": pos_a.loc[df[SET_A], "x"].to_numpy(),
        "y": pos_a.loc[df[SET_A], "y"].to_numpy(),
        "x2": pos_b.loc[df[SET_B], "x"].to_numpy(),
        "y2": pos_b.loc[df[SET_B], "y"].to_numpy(),
    }
)

x_enc = alt.X("x:Q", scale=xscale, axis=None)
y_enc = alt.Y("y:Q", scale=yscale, axis=None)

edges_chart = (
    alt.Chart(edges)
    .mark_rule(color=INK_SOFT, opacity=0.3, strokeWidth=0.6)
    .encode(x=x_enc, y=y_enc, x2="x2:Q", y2="y2:Q")
)

# Nodes: size encodes degree, color encodes set membership
nodes_chart = (
    alt.Chart(nodes)
    .mark_circle(stroke=PAGE_BG, strokeWidth=1, opacity=1)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(
            "set:N",
            title="Node set",
            sort=None,
            scale=alt.Scale(domain=[SET_A, SET_B], range=IMPRINT_PALETTE[:2]),
            legend=alt.Legend(titleFontSize=11, labelFontSize=10, orient="bottom-right", padding=4),
        ),
        size=alt.Size("degree:Q", scale=alt.Scale(range=[30, 200]), legend=None),
        tooltip=["node:N", "set:N", "degree:Q"],
    )
)

# Labels sit on the outer side of each column
labels_a = (
    alt.Chart(nodes_a)
    .mark_text(align="right", dx=-12, fontSize=10, color=INK_SOFT)
    .encode(x=x_enc, y=y_enc, text="node:N")
)
labels_b = (
    alt.Chart(nodes_b)
    .mark_text(align="left", dx=12, fontSize=10, color=INK_SOFT)
    .encode(x=x_enc, y=y_enc, text="node:N")
)

# Column headings name the sets in their colors
headers = pd.DataFrame(
    {"x": [0.24, 0.76], "y": [0.98, 0.98], "text": [SET_A + "s", SET_B + "s"], "set": [SET_A, SET_B]}
)
headers_chart = (
    alt.Chart(headers)
    .mark_text(fontSize=13, fontWeight="bold")
    .encode(
        x=x_enc,
        y=y_enc,
        text="text:N",
        color=alt.Color("set:N", legend=None, scale=alt.Scale(domain=[SET_A, SET_B], range=IMPRINT_PALETTE[:2])),
    )
)

chart = (
    alt.layer(edges_chart, nodes_chart, labels_a, labels_b, headers_chart)
    .properties(width=620, height=320, title=alt.Title(title), background=PAGE_BG)
    .configure_view(fill=PAGE_BG, strokeOpacity=0)
    .configure_title(color=INK, fontSize=16, anchor="start", offset=8)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds target {TW}x{TH}")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
