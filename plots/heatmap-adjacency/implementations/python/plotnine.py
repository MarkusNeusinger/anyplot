"""anyplot.ai
heatmap-adjacency: Network Adjacency Matrix Heatmap
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Created: 2026-05-08
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_tile,
    geom_vline,
    ggplot,
    labs,
    scale_fill_gradient,
    scale_x_discrete,
    scale_y_discrete,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
ABSENT_CELL = "#E0DED7" if THEME == "light" else "#2A2A25"

# Imprint palette: first position for the weak end, third for the strong end of the sequential ramp
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SOURCE = "Source Researcher"  # role: source
TARGET = "Target Researcher"  # role: target
WEIGHT = "Collaboration Strength"  # role: weight
FIELD = "Field"  # role: extra

# Data: researcher collaboration network, one row per directed edge (an undirected tie appears in both directions).
# Replace this block with your own edge list, for example df = pd.read_csv("edges.csv")
rng = np.random.default_rng(42)
fields = {"Physics": "P", "Biology": "B", "CompSci": "C"}
n_per_field = 10
nodes = [(f"{prefix}{i + 1:02d}", field) for field, prefix in fields.items() for i in range(n_per_field)]

rows = []
for a, (name_a, field_a) in enumerate(nodes):
    for b in range(a + 1, len(nodes)):
        name_b, field_b = nodes[b]
        # Within a field: dense, strong ties. Across fields: sparse, weaker ties.
        if field_a == field_b:
            tie = rng.random() < 0.72
            weight = rng.uniform(0.45, 1.0)
        else:
            tie = rng.random() < 0.09
            weight = rng.uniform(0.05, 0.38)
        if tie:
            rows.append((name_a, name_b, field_a, weight))
            rows.append((name_b, name_a, field_b, weight))

df = (
    pd.DataFrame(rows, columns=[SOURCE, TARGET, FIELD, WEIGHT])
    .assign(_order=lambda t: t[SOURCE].map({name: i for i, (name, _) in enumerate(nodes)}))
    .sort_values(["_order", TARGET])
    .drop(columns="_order")
    .reset_index(drop=True)
)

# Plot: reads only df and the constants above
# Node order follows the data (grouped by field), so communities form blocks on the diagonal
node_order = df[SOURCE].unique().tolist()
field_of = df.drop_duplicates(SOURCE).set_index(SOURCE)[FIELD].loc[node_order]
boundaries = [i + 0.5 for i in range(1, len(node_order)) if field_of.iloc[i] != field_of.iloc[i - 1]]

anyplot_theme = theme(
    figure_size=(6, 6),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=ABSENT_CELL),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    panel_border=element_blank(),
    axis_line=element_line(color=INK_SOFT),
    axis_ticks=element_line(color=INK_SOFT),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_text_x=element_text(angle=45, ha="right", color=INK_SOFT, size=8),
    plot_title=element_text(color=INK, size=12, ha="center"),
    legend_background=element_rect(fill=ELEVATED_BG, color=None),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=9),
)

plot = (
    ggplot(df, aes(x=TARGET, y=SOURCE, fill=WEIGHT))
    + geom_tile()
    + geom_vline(xintercept=boundaries, color=INK, size=0.5, alpha=0.5, linetype="dashed")
    + geom_hline(
        yintercept=len(node_order) + 1 - np.array(boundaries), color=INK, size=0.5, alpha=0.5, linetype="dashed"
    )
    + scale_fill_gradient(low=IMPRINT_PALETTE[0], high=IMPRINT_PALETTE[2], name=WEIGHT.replace(" ", "\n"))
    + scale_x_discrete(limits=node_order)
    + scale_y_discrete(limits=node_order[::-1])
    + labs(title="heatmap-adjacency · python · plotnine · anyplot.ai")
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
