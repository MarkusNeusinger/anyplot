""" anyplot.ai
heatmap-adjacency: Network Adjacency Matrix Heatmap
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-16
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_gradient,
    theme,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions; imprint_seq runs from position 1 to position 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SEQ_LOW, SEQ_HIGH = IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]

# Columns: set these to your table's column names
SOURCE = "Researcher"  # role: source
TARGET = "Researcher"  # role: target
WEIGHT = "Collaboration strength"  # role: weight

# Data: replace this block with your own square matrix, for example
# df = pd.read_csv("adjacency.csv", index_col=0); rows and columns share the node order,
# absent edges are NaN
np.random.seed(42)
names = [
    "Alice", "Bob", "Carol", "Dan", "Eve", "Frank", "Grace", "Hank", "Iris", "Jack",  # Dept A
    "Kate", "Leo", "Mia", "Ned", "Olivia", "Paul", "Quinn", "Rose", "Sam", "Tina",  # Dept B
    "Uma", "Victor", "Wendy", "Xavier", "Yara", "Zane", "Anna", "Blake", "Cleo", "Derek",  # Dept C
]  # fmt: skip
dept = np.arange(len(names)) // 10
same_dept = dept[:, None] == dept[None, :]
has_edge = np.triu(np.random.rand(len(names), len(names)) < np.where(same_dept, 0.70, 0.12), k=1)
strength = np.where(
    same_dept, np.random.uniform(0.4, 1.0, same_dept.shape), np.random.uniform(0.05, 0.35, same_dept.shape)
)
upper = np.where(has_edge, strength, np.nan)
matrix = np.where(np.isnan(upper), upper.T, upper)  # undirected: mirror across the diagonal
df = pd.DataFrame(matrix, index=names, columns=names)

# Plot: reads only df and the constants above
order = list(df.index)
long = df.rename_axis(index="row", columns="col").stack(future_stack=True).rename(WEIGHT).reset_index()
long["row"] = pd.Categorical(long["row"], categories=order[::-1], ordered=True)  # first node at the top
long["col"] = pd.Categorical(long["col"], categories=order, ordered=True)

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid=element_blank(),
    axis_title=element_text(color=INK, size=14),
    axis_text=element_text(color=INK_SOFT, size=9),
    axis_text_x=element_text(color=INK_SOFT, size=9, angle=90, hjust=1),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=11),
    legend_title=element_text(color=INK, size=12),
)

plot = (
    ggplot(long, aes(x="col", y="row", fill=WEIGHT))
    + geom_tile()
    + scale_fill_gradient(low=SEQ_LOW, high=SEQ_HIGH, na_value=PAGE_BG, name=WEIGHT.replace(" ", "\n", 1))
    + labs(title="heatmap-adjacency · python · letsplot · anyplot.ai", x=SOURCE, y=TARGET)
    + anyplot_theme
    + ggsize(600, 600)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
