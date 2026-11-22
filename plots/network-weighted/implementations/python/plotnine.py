"""anyplot.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_size_continuous,
    theme,
    theme_void,
)


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
EDGES = ["Source", "Target"]  # role: edges
WEIGHT = "Trade volume (billion USD)"  # role: weight

# Data: replace this block with your own edge list, for example df = pd.read_csv("edges.csv")
df = pd.DataFrame(
    [
        ("USA", "China", 580),
        ("USA", "Canada", 620),
        ("USA", "Mexico", 550),
        ("USA", "Japan", 180),
        ("USA", "Germany", 160),
        ("USA", "UK", 130),
        ("USA", "S.Korea", 140),
        ("China", "Japan", 280),
        ("China", "S.Korea", 240),
        ("China", "Germany", 170),
        ("China", "Australia", 150),
        ("China", "India", 90),
        ("Germany", "France", 180),
        ("Germany", "UK", 140),
        ("Germany", "Japan", 45),
        ("France", "UK", 80),
        ("Japan", "S.Korea", 70),
        ("Canada", "Mexico", 35),
        ("India", "UK", 30),
        ("Brazil", "USA", 75),
        ("Brazil", "China", 95),
        ("Australia", "Japan", 55),
    ],
    columns=[*EDGES, WEIGHT],
)

# Plot: reads only df and the constants above
# Nodes in order of first appearance, placed on a slightly wobbling circle
names = list(pd.unique(df[EDGES].to_numpy().ravel()))
angles = np.linspace(0, 2 * np.pi, len(names), endpoint=False)
radius = 4.0 + 0.3 * np.sin(np.arange(len(names)) * 1.5)
nodes = pd.DataFrame({"id": names, "x": radius * np.cos(angles), "y": radius * np.sin(angles)})
pos = nodes.set_index("id")

# Weighted degree (sum of connected edge weights) sizes each node
nodes["weighted_degree"] = [df.loc[(df[EDGES[0]] == n) | (df[EDGES[1]] == n), WEIGHT].sum() for n in names]
span = nodes["weighted_degree"].max() - nodes["weighted_degree"].min()
nodes["node_size"] = 2.5 + (nodes["weighted_degree"] - nodes["weighted_degree"].min()) / span * 5.5

edges = pd.DataFrame(
    {
        "x": pos.loc[df[EDGES[0]], "x"].to_numpy(),
        "y": pos.loc[df[EDGES[0]], "y"].to_numpy(),
        "xend": pos.loc[df[EDGES[1]], "x"].to_numpy(),
        "yend": pos.loc[df[EDGES[1]], "y"].to_numpy(),
        "weight": df[WEIGHT].to_numpy(),
    }
)
legend_breaks = np.round(np.linspace(df[WEIGHT].min(), df[WEIGHT].max(), 3), -1).tolist()

plot = (
    ggplot()
    # Edges: thickness mapped to trade weight
    + geom_segment(
        data=edges,
        mapping=aes(x="x", y="y", xend="xend", yend="yend", size="weight"),
        color=IMPRINT_PALETTE[2],
        alpha=0.55,
    )
    # Nodes drawn on top, one layer per node so each carries its own size outside the edge legend
    + [
        geom_point(
            data=nodes.iloc[[i]],
            mapping=aes(x="x", y="y"),
            size=nodes["node_size"].iloc[i],
            color=INK,
            stroke=0.75,
            fill=IMPRINT_PALETTE[0],
        )
        for i in range(len(nodes))
    ]
    + geom_text(data=nodes, mapping=aes(x="x", y="y", label="id"), size=7, color=INK, fontweight="bold", nudge_y=0.65)
    + scale_size_continuous(range=(0.4, 3), name=f"{WEIGHT}".replace(" (", "\n("), breaks=legend_breaks)
    + labs(
        title="network-weighted · python · plotnine · anyplot.ai",
        subtitle="Edge thickness represents bilateral trade volume between countries",
    )
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK),
        plot_subtitle=element_text(size=9, ha="center", color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=7, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
        plot_margin=0.05,
    )
    + guides(size=guide_legend(override_aes={"alpha": 0.8}))
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
