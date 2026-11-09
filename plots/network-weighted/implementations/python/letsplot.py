"""anyplot.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-08
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint position 1: a single node series

# Constants
EDGE_WIDTH = (0.6, 5.0)  # line size of the lightest and the heaviest edge
EDGE_ALPHA = 0.55  # translucent edges keep crossings readable
NODE_SIZE = (7.0, 15.0)  # point size of the node with the least and the most total trade
LAYOUT_STEPS = 400  # Fruchterman-Reingold iterations with a linear cooling schedule
EDGE_CLEARANCE = 0.4  # a node closer than this share of the ideal spacing k to a foreign edge is pushed off it

# Columns: set these to your table's column names
SOURCE = "Source"  # role: edges
TARGET = "Target"  # role: extra
WEIGHT = "Trade volume (billion USD)"  # role: weight

# Data: replace this block with your own edge list, for example df = pd.read_csv("trade.csv")
edge_list = [
    ("USA", "China", 550),
    ("USA", "Germany", 180),
    ("USA", "Japan", 220),
    ("USA", "UK", 140),
    ("USA", "Canada", 380),
    ("USA", "Mexico", 420),
    ("USA", "India", 95),
    ("USA", "S.Korea", 130),
    ("China", "Germany", 200),
    ("China", "Japan", 340),
    ("China", "UK", 85),
    ("China", "S.Korea", 290),
    ("China", "Australia", 160),
    ("Germany", "Japan", 55),
    ("Germany", "UK", 150),
    ("Germany", "France", 180),
    ("Germany", "Brazil", 45),
    ("Germany", "Spain", 65),
    ("Germany", "Netherlands", 220),
    ("Japan", "UK", 35),
    ("Japan", "S.Korea", 85),
    ("Japan", "Australia", 70),
    ("UK", "France", 95),
    ("UK", "Italy", 55),
    ("UK", "Netherlands", 80),
    ("France", "Italy", 85),
    ("France", "Spain", 95),
    ("Canada", "Mexico", 75),
    ("Mexico", "Brazil", 40),
    ("Brazil", "India", 30),
    ("India", "Australia", 25),
    ("Italy", "Spain", 45),
    ("Australia", "Netherlands", 35),
]
df = pd.DataFrame(edge_list, columns=[SOURCE, TARGET, WEIGHT])

# Plot: reads only df and the constants above
edges = df.dropna(subset=[SOURCE, TARGET, WEIGHT]).reset_index(drop=True)
countries = list(dict.fromkeys(edges[SOURCE].tolist() + edges[TARGET].tolist()))
n_nodes = len(countries)
index_of = {name: i for i, name in enumerate(countries)}
src = edges[SOURCE].map(index_of).to_numpy()
tgt = edges[TARGET].map(index_of).to_numpy()
weights = edges[WEIGHT].to_numpy(dtype=float)

# Weighted Fruchterman-Reingold layout: every pair repels with k²/d, every edge attracts with
# w·d²/k, so a heavy trade link pulls its two countries together; the step shrinks each round.
# In the second half a node is also pushed off any edge it does not belong to, so no edge
# runs hidden under a third country.
rng = np.random.default_rng(42)
pos = rng.uniform(-1, 1, size=(n_nodes, 2))
k = np.sqrt(4.0 / n_nodes)
w_rel = np.sqrt(weights / weights.max())  # square root keeps the heaviest pairs from collapsing
node_ids = np.arange(n_nodes)[:, None]
foreign = (node_ids != src) & (node_ids != tgt)  # node i is not an endpoint of edge e
for step in range(LAYOUT_STEPS):
    delta = pos[:, None, :] - pos[None, :, :]
    dist = np.maximum(np.linalg.norm(delta, axis=2), 0.01)
    disp = (delta * (k**2 / dist**2)[:, :, None]).sum(axis=1)
    edge_delta = pos[src] - pos[tgt]
    edge_dist = np.maximum(np.linalg.norm(edge_delta, axis=1), 0.01)
    pull = edge_delta * (w_rel * edge_dist / k)[:, None]
    np.add.at(disp, src, -pull)
    np.add.at(disp, tgt, pull)
    if step >= LAYOUT_STEPS // 2:
        seg = -edge_delta
        along = ((pos[:, None, :] - pos[src]) * seg).sum(axis=2) / np.maximum((seg**2).sum(axis=1), 1e-9)
        off = pos[:, None, :] - (pos[src] + np.clip(along, 0, 1)[:, :, None] * seg)
        gap = np.maximum(np.linalg.norm(off, axis=2), 0.01)
        push = np.where(foreign & (gap < EDGE_CLEARANCE * k), k**2 / gap**2, 0.0)
        disp += (off * push[:, :, None]).sum(axis=1)
    temperature = 0.1 * (1 - step / LAYOUT_STEPS) + 0.002
    length = np.maximum(np.linalg.norm(disp, axis=1), 1e-9)
    pos += disp / length[:, None] * np.minimum(length, temperature)[:, None]
pos -= pos.mean(axis=0)
pos = pos / np.abs(pos).max(axis=0) * [3.2, 2.4]

# Weighted degree for node sizing
weighted_degree = np.zeros(n_nodes)
np.add.at(weighted_degree, src, weights)
np.add.at(weighted_degree, tgt, weights)

nodes_df = pd.DataFrame({"x": pos[:, 0], "y": pos[:, 1], "label": countries, "weighted_degree": weighted_degree})
edges_df = pd.DataFrame(
    {"x": pos[src, 0], "y": pos[src, 1], "xend": pos[tgt, 0], "yend": pos[tgt, 1], "weight": weights}
)

# Edge and node sizes are computed here and drawn through an identity size scale: lets-plot
# has one size scale per plot, and a shared scale trained on the edge weights would shrink
# every node to its minimum. Edge width grows linearly with weight between EDGE_WIDTH bounds.
min_w, max_w = weights.min(), weights.max()
width_per_weight = (EDGE_WIDTH[1] - EDGE_WIDTH[0]) / max(max_w - min_w, 1e-9)
edges_df["line_width"] = EDGE_WIDTH[0] + (edges_df["weight"] - min_w) * width_per_weight

# Node diameter grows with the square root of the weighted degree, so its area tracks total trade,
# and the smallest node is still wider than the thickest edge
max_d = nodes_df["weighted_degree"].max()
nodes_df["node_size"] = NODE_SIZE[0] + (NODE_SIZE[1] - NODE_SIZE[0]) * np.sqrt(nodes_df["weighted_degree"] / max_d)

# Legend keys: round trade volumes, one per power-of-ten step inside the data range
step = 10 ** np.floor(np.log10(max(max_w - min_w, 1e-9)))
legend_weights = np.arange(np.ceil(min_w / step) * step, max_w + step * 1e-6, step)
legend_widths = [EDGE_WIDTH[0] + (w - min_w) * width_per_weight for w in legend_weights]

# Edges are translucent, but lets-plot draws line keys opaque: the keys get the color an edge
# shows on the page
ink_rgb, page_rgb = (np.array([int(h[i : i + 2], 16) for i in (1, 3, 5)]) for h in (INK_SOFT, PAGE_BG))
edge_key_color = "#" + "".join(f"{round(c):02X}" for c in EDGE_ALPHA * ink_rgb + (1 - EDGE_ALPHA) * page_rgb)

# Frame the layout with room for the labels above the nodes
x_lim = [nodes_df["x"].min() - 0.6, nodes_df["x"].max() + 0.6]
y_lim = [nodes_df["y"].min() - 0.4, nodes_df["y"].max() + 0.8]

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_blank(),
    panel_grid=element_blank(),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(size=16, face="bold", color=INK),
    plot_subtitle=element_text(size=11, color=INK_SOFT),
    plot_caption=element_text(size=10, color=INK_SOFT),
    legend_title=element_text(size=11, color=INK),
    legend_text=element_text(size=10, color=INK_SOFT),
    legend_background=element_blank(),
    legend_position="right",
)

plot = (
    ggplot()
    # Edges as segments, width from trade volume
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend", size="line_width"),
        data=edges_df,
        color=INK_SOFT,
        alpha=EDGE_ALPHA,
        tooltips=layer_tooltips().line("Trade|@weight B USD"),
    )
    # Nodes drawn on top of the edges, sized by weighted degree
    + geom_point(
        aes(x="x", y="y", size="node_size"),
        data=nodes_df,
        shape=21,
        fill=BRAND,
        color=PAGE_BG,
        stroke=1.0,
        show_legend=False,
        tooltips=layer_tooltips().title("@label").line("Total trade|@weighted_degree B USD"),
    )
    # Node labels on a page-colored plate just above the largest node's radius, so no edge runs
    # through a name
    + geom_label(
        aes(x="x", y="y", label="label"),
        data=nodes_df,
        size=6,
        color=INK,
        fill=PAGE_BG,
        fontface="bold",
        label_size=0,
        label_padding=0.15,
        vjust=0,
        nudge_y=NODE_SIZE[1] / 2 + 1,
        nudge_unit="size",
        tooltips="none",
    )
    + scale_size_identity(
        name=WEIGHT.replace(" (", "\n("),
        breaks=legend_widths,
        labels=[f"{w:g}" for w in legend_weights],
        guide="legend",
    )
    + guides(size=guide_legend(override_aes={"color": edge_key_color}))
    + labs(
        title="network-weighted · python · letsplot · anyplot.ai",
        subtitle="International trade network: edge thickness = bilateral trade volume",
        caption="Node size = each country's total trade with the others shown (weighted degree)",
    )
    + scale_x_continuous(limits=x_lim)
    + scale_y_continuous(limits=y_lim)
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save PNG (scaled 4x for 3200 × 1800 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)

# Save HTML for interactive version
ggsave(plot, f"plot-{THEME}.html", path=".")
