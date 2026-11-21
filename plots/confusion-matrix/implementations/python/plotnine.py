"""anyplot.ai
confusion-matrix: Confusion Matrix Heatmap
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_gradient,
    scale_x_discrete,
    scale_y_discrete,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential ramp from positions 1 and 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TRUE_LABEL = "True Label"  # role: true_labels
PREDICTED_LABEL = "Predicted Label"  # role: predicted_labels
CLASS_NAMES = "Class"  # role: class_names
COUNT = "Sample Count"  # role: extra

# Data: replace this block with your own labeled square matrix, for example df = pd.read_csv("matrix.csv", index_col=0)
class_names = ["Negative", "Neutral", "Positive"]
df = pd.DataFrame(
    [
        [85, 12, 3],  # Negative: mostly correct, some confused with Neutral
        [8, 72, 20],  # Neutral: harder to classify, confused with both
        [4, 15, 81],  # Positive: mostly correct, some confused with Neutral
    ],
    index=pd.Index(class_names, name=CLASS_NAMES),
    columns=pd.Index(class_names, name=CLASS_NAMES),
)

# Plot: reads only df and the constants above
long = df.rename_axis(index=TRUE_LABEL, columns=PREDICTED_LABEL).stack().rename(COUNT).reset_index()
true_order = df.index.tolist()
pred_order = df.columns.tolist()

# Label color flips at the midpoint of the value range so every count stays legible
values = df.to_numpy(dtype=float)
midpoint = (np.nanmax(values) + np.nanmin(values)) / 2
long["text_color"] = long[COUNT].apply(lambda v: "#FAF8F1" if pd.notna(v) and v >= midpoint else "#1A1A17")

plot = (
    ggplot(long, aes(x=PREDICTED_LABEL, y=TRUE_LABEL, fill=COUNT))
    + geom_tile(color=PAGE_BG, size=1.5)
    + geom_text(aes(label=COUNT, color="text_color"), size=18, fontweight="bold", show_legend=False)
    + scale_fill_gradient(low=IMPRINT_PALETTE[0], high=IMPRINT_PALETTE[2])
    + scale_color_identity()
    + scale_x_discrete(limits=pred_order)
    + scale_y_discrete(limits=true_order[::-1])
    + labs(title="confusion-matrix · python · plotnine · anyplot.ai")
    + coord_fixed(ratio=1)
    + theme_minimal()
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        text=element_text(size=9, color=INK),
        axis_title=element_text(size=12, weight="bold", color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        plot_title=element_text(size=13, weight="bold", ha="center", color=INK),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=9, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
