""" anyplot.ai
network-bipartite: Bipartite Network Graph
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 77/100 | Updated: 2026-11-21
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    scale_size,
    theme,
    xlim,
    ylim,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SOURCE = "Student"  # role: source
TARGET = "Course"  # role: target

# Data: replace this block with your own edge list, for example df = pd.read_csv("enrollments.csv")
df = pd.DataFrame(
    [
        ("Alice", "Calculus"),
        ("Alice", "Statistics"),
        ("Alice", "Machine Learning"),
        ("Bob", "Data Structures"),
        ("Bob", "Algorithms"),
        ("Bob", "Databases"),
        ("Carol", "Calculus"),
        ("Carol", "Linear Algebra"),
        ("Carol", "Statistics"),
        ("David", "Machine Learning"),
        ("David", "Computer Vision"),
        ("David", "Networks"),
        ("Emma", "Statistics"),
        ("Emma", "Machine Learning"),
        ("Emma", "Data Structures"),
        ("Frank", "Algorithms"),
        ("Frank", "Operating Systems"),
        ("Frank", "Databases"),
        ("Grace", "Calculus"),
        ("Grace", "Linear Algebra"),
        ("Henry", "Machine Learning"),
        ("Henry", "Networks"),
        ("Henry", "Computer Vision"),
        ("Iris", "Data Structures"),
        ("Iris", "Algorithms"),
        ("Iris", "Operating Systems"),
        ("James", "Calculus"),
        ("James", "Statistics"),
        ("Kate", "Machine Learning"),
        ("Kate", "Statistics"),
        ("Kate", "Linear Algebra"),
        ("Leo", "Databases"),
        ("Leo", "Networks"),
        ("Leo", "Operating Systems"),
    ],
    columns=[SOURCE, TARGET],
)

# Plot: reads only df and the constants above
sources = list(df[SOURCE].unique())
targets = list(df[TARGET].unique())
n_sources = len(sources)
n_targets = len(targets)

# Vertical positions: sources at x=0, targets at x=1 (vertically centered)
target_offset = (n_sources - n_targets) / 2.0
source_y = {s: float(i) for i, s in enumerate(sources)}
target_y = {t: float(i) + target_offset for i, t in enumerate(targets)}

# Edge dataframe
edges_df = pd.DataFrame({"x": 0.0, "y": df[SOURCE].map(source_y), "xend": 1.0, "yend": df[TARGET].map(target_y)})

# Node dataframes (separate for label positioning)
source_degree = df[SOURCE].value_counts()
target_degree = df[TARGET].value_counts()
source_nodes = pd.DataFrame(
    {
        "name": sources,
        "x": 0.0,
        "x_label": -0.06,
        "y": [source_y[s] for s in sources],
        "group": SOURCE + "s",
        "degree": [source_degree[s] for s in sources],
    }
)
target_nodes = pd.DataFrame(
    {
        "name": targets,
        "x": 1.0,
        "x_label": 1.06,
        "y": [target_y[t] for t in targets],
        "group": TARGET + "s",
        "degree": [target_degree[t] for t in targets],
    }
)
nodes_df = pd.concat([source_nodes, target_nodes], ignore_index=True)

# Theme
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=11),
)

title = "network-bipartite · python · letsplot · anyplot.ai"

plot = (
    ggplot()
    + geom_segment(
        data=edges_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color=INK_MUTED, alpha=0.3, size=0.3
    )
    + geom_point(data=nodes_df, mapping=aes(x="x", y="y", fill="group", size="degree"), color=PAGE_BG, shape=21)
    + geom_text(data=source_nodes, mapping=aes(x="x_label", y="y", label="name"), hjust=1, color=INK, size=5)
    + geom_text(data=target_nodes, mapping=aes(x="x_label", y="y", label="name"), hjust=0, color=INK, size=5)
    + scale_fill_manual(values={SOURCE + "s": IMPRINT_PALETTE[0], TARGET + "s": IMPRINT_PALETTE[1]})
    + scale_size(range=[3, 8], name="Connections")
    + labs(title=title, fill="Group")
    + anyplot_theme
    + ggsize(800, 450)
    + xlim(-0.45, 1.45)
    + ylim(-0.5, n_sources - 0.5)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
