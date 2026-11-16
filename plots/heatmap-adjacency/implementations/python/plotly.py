"""anyplot.ai
heatmap-adjacency: Network Adjacency Matrix Heatmap
Library: plotly 6.7.0 | Python 3.13.13
Quality: 81/100 | Updated: 2026-11-16
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential colormap (single polarity): brand green to blue
IMPRINT_SEQ = [[0.0, "#009E73"], [1.0, "#4467A3"]]

# Constants
ABSENT_BELOW = 0.05  # co-occurrence below this strength counts as "no edge" and stays background-colored

# Columns: set these to your table's labels
SOURCE = "Source term"  # role: source
TARGET = "Target term"  # role: target
WEIGHT = "Co-occurrence strength"  # role: weight

# Data: replace this block with your own square matrix, rows and columns indexed by (group, term), nodes ordered by group
np.random.seed(42)
domains = {
    "Machine Learning": ["neural net", "gradient", "backprop", "optimizer", "dropout", "attention"],
    "Neuroscience": ["synapse", "cortex", "dendrite", "neuron", "hippocampus", "axon"],
    "Genomics": ["DNA", "RNA", "gene", "protein", "chromosome", "mutation"],
    "Chemistry": ["molecule", "catalyst", "reaction", "bond", "polymer", "enzyme"],
    "Physics": ["quantum", "photon", "entropy", "wave", "spin", "field"],
}
pairs = [(domain, term) for domain, terms in domains.items() for term in terms]
n_nodes = len(pairs)
weights = np.zeros((n_nodes, n_nodes))
for i in range(n_nodes):
    for j in range(i + 1, n_nodes):
        if pairs[i][0] == pairs[j][0]:
            weights[i, j] = weights[j, i] = np.random.uniform(0.55, 1.0)
        else:
            weights[i, j] = weights[j, i] = np.random.uniform(0.0, 0.12)
index = pd.MultiIndex.from_tuples(pairs, names=["Research domain", SOURCE])
df = pd.DataFrame(weights, index=index, columns=pd.MultiIndex.from_tuples(pairs, names=["Research domain", TARGET]))

# Plot: reads only df and the constants above
terms = df.index.get_level_values(-1)
groups = df.index.get_level_values(0)  # a flat index has one level: no group boundaries
n = len(df)
boundaries = [i for i in range(1, n) if groups[i] != groups[i - 1]]

# Absent edges become gaps, so the page background shows through and cannot be mistaken for a weak edge
z = df.to_numpy(dtype=float)
z = np.where(z < ABSENT_BELOW, np.nan, z)

fig = go.Figure(
    go.Heatmap(
        z=z,
        x=terms,
        y=terms,
        colorscale=IMPRINT_SEQ,
        zmin=0,
        zmax=np.nanmax(z),
        xgap=1,
        ygap=1,
        colorbar={
            "title": {"text": WEIGHT.replace(" ", "<br>", 1), "font": {"size": 12, "color": INK}, "side": "right"},
            "tickfont": {"size": 10, "color": INK_SOFT},
            "thickness": 14,
            "len": 0.75,
            "outlinewidth": 0,
        },
        hoverongaps=False,
        hovertemplate="%{y} ↔ %{x}<br>Strength: %{z:.2f}<extra></extra>",
    )
)

# Cluster boundary lines separating research domains
for b in boundaries:
    fig.add_shape(type="line", x0=b - 0.5, x1=b - 0.5, y0=-0.5, y1=n - 0.5, line={"color": INK, "width": 1.5})
    fig.add_shape(type="line", x0=-0.5, x1=n - 0.5, y0=b - 0.5, y1=b - 0.5, line={"color": INK, "width": 1.5})

# Style
title = "Research Domain Co-occurrence · heatmap-adjacency · python · plotly · anyplot.ai"
title_size = max(11, round(16 * min(1.0, 67 / len(title))))
fig.update_layout(
    autosize=False,
    width=600,
    height=600,
    title={"text": title, "font": {"size": title_size, "color": INK}, "x": 0.5, "xanchor": "center"},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis={
        "title": {"text": TARGET, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickangle": -45,
        "showgrid": False,
        "zeroline": False,
        "showline": False,
        "constrain": "domain",
    },
    yaxis={
        "title": {"text": SOURCE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "zeroline": False,
        "showline": False,
        "autorange": "reversed",
        "scaleanchor": "x",
        "constrain": "domain",
    },
    margin={"l": 100, "r": 40, "t": 60, "b": 105},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
