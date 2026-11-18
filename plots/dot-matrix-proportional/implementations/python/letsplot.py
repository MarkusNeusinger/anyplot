"""anyplot.ai
dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 88/100 | Created: 2026-05-08
"""

import os

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot import element_blank, element_rect, element_text, theme
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
COLS = 10  # dots per grid row

# Columns
CATEGORY = "category"  # role: category
COUNT = "count"  # role: count
TOTAL = "total"  # role: total

# Data — clinical trial side effect profile (n = 100 patients)
df = pd.DataFrame(
    {CATEGORY: ["No Side Effects", "Mild Effects", "Moderate Effects", "Severe Effects"], COUNT: [72, 18, 7, 3]}
)

# Plot: one dot per unit, filled left to right and top to bottom
valid = df.dropna(subset=[COUNT])
dots = valid.loc[valid.index.repeat(valid[COUNT].astype(int))].reset_index(drop=True)
dots["label"] = dots[CATEGORY].astype(str) + "  (n=" + dots[COUNT].astype(int).astype(str) + ")"
dots["label"] = pd.Categorical(dots["label"], categories=dots["label"].unique(), ordered=True)
dots["x"] = dots.index % COLS
dots["y"] = -(dots.index // COLS)

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_line=element_blank(),
    axis_ticks=element_blank(),
    plot_title=element_text(color=INK, size=14),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_blank(),
    legend_position="right",
)

plot = (
    ggplot(dots, aes(x="x", y="y", color="label"))  # noqa: F405
    + geom_point(size=7, alpha=0.95)  # noqa: F405
    + scale_color_manual(values=IMPRINT[: df.shape[0]])  # noqa: F405
    + labs(title="dot-matrix-proportional · python · letsplot · anyplot.ai")  # noqa: F405
    + theme_void()  # noqa: F405
    + ggsize(600, 600)  # noqa: F405
    + anyplot_theme
)

# Save
export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
export_ggsave(plot, filename=f"plot-{THEME}.html", path=".")
