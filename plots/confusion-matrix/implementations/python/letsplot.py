"""anyplot.ai
confusion-matrix: Confusion Matrix Heatmap
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-09
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_identity,
    scale_fill_gradient,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: imprint_seq runs from position 1 to position 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LIGHT_TEXT = "#FAF8F1"  # annotation color on the deep cells of the colormap
DEEP_CELL_SHARE = 0.5  # cells above this share of the largest count get light text

# Columns: set these to your table's column names
TRUE_LABEL = "True Label"  # role: true_labels
PRED_LABEL = "Predicted Label"  # role: predicted_labels
COUNT = "Count"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
# One row per classified sample; the example expands a 4-class result (rows = true, columns = predicted)
_classes = ["Cat", "Dog", "Bird", "Fish"]
_counts = [
    [45, 8, 3, 2],  # Cat: sometimes confused with Dog
    [6, 52, 4, 1],  # Dog: sometimes confused with Cat
    [2, 3, 38, 5],  # Bird: sometimes confused with Fish
    [1, 2, 7, 41],  # Fish: sometimes confused with Bird
]
df = pd.DataFrame(
    [
        (t, p)
        for t, row in zip(_classes, _counts, strict=True)
        for p, n in zip(_classes, row, strict=True)
        for _ in range(n)
    ],
    columns=[TRUE_LABEL, PRED_LABEL],
)

# Plot
class_names = list(dict.fromkeys(list(df[TRUE_LABEL].dropna()) + list(df[PRED_LABEL].dropna())))
matrix = pd.crosstab(
    pd.Categorical(df[TRUE_LABEL], categories=class_names),
    pd.Categorical(df[PRED_LABEL], categories=class_names),
    dropna=False,
)
matrix.index.name, matrix.columns.name = TRUE_LABEL, PRED_LABEL
long = matrix.stack().rename(COUNT).reset_index()
row_total = matrix.sum(axis=1).clip(lower=1)
row_share = (matrix.div(row_total, axis=0) * 100).round().stack().to_numpy().astype(int)
long["Label"] = [f"{c}\n({p}%)" for c, p in zip(long[COUNT], row_share, strict=True)]
long["text_color"] = [LIGHT_TEXT if c > long[COUNT].max() * DEEP_CELL_SHARE else INK for c in long[COUNT]]

# Rows run top to bottom, so reverse the true labels for the diagonal to fall from top-left
long[TRUE_LABEL] = pd.Categorical(long[TRUE_LABEL], categories=class_names[::-1], ordered=True)
long[PRED_LABEL] = pd.Categorical(long[PRED_LABEL], categories=class_names, ordered=True)

plot = (
    ggplot(long, aes(x=PRED_LABEL, y=TRUE_LABEL, fill=COUNT))
    + geom_tile(color=PAGE_BG, size=1.5, tooltips="none")
    + geom_text(aes(label="Label", color="text_color"), size=5, fontface="bold")
    + scale_color_identity()
    + scale_fill_gradient(low=IMPRINT_PALETTE[0], high=IMPRINT_PALETTE[2], name=COUNT)
    + labs(
        title="confusion-matrix · python · letsplot · anyplot.ai",
        caption="Cell labels: count (share of the true class, row-normalized)",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=14, face="bold", color=INK),
        plot_caption=element_text(size=10, color=INK_SOFT),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=11, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=11, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        panel_grid=element_blank(),
    )
    + ggsize(600, 600)
)

# Save PNG (scale 4x = 2400 x 2400 px) and interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
