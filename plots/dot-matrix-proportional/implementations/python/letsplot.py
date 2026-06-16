""" anyplot.ai
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

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data — clinical trial side effect profile (n = 100 patients)
categories = ["No Side Effects", "Mild Effects", "Moderate Effects", "Severe Effects"]
counts = [72, 18, 7, 3]
total = sum(counts)  # 100
COLS = 10

dot_labels = []
for cat, cnt in zip(categories, counts, strict=True):
    dot_labels.extend([cat] * cnt)

legend_labels = [f"{cat}  (n={cnt})" for cat, cnt in zip(categories, counts, strict=True)]
legend_map = dict(zip(categories, legend_labels, strict=True))

df = pd.DataFrame(
    {"col": [i % COLS for i in range(total)], "row": [-(i // COLS) for i in range(total)], "group": dot_labels}
)
df["legend"] = pd.Categorical(df["group"].map(legend_map), categories=legend_labels, ordered=True)

# Plot
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
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_blank(),
    legend_position="right",
)

plot = (
    ggplot(df, aes(x="col", y="row", color="legend"))  # noqa: F405
    + geom_point(size=8, alpha=0.95)  # noqa: F405
    + scale_color_manual(values=IMPRINT)  # noqa: F405
    + labs(title="dot-matrix-proportional · letsplot · anyplot.ai")  # noqa: F405
    + theme_void()  # noqa: F405
    + ggsize(1200, 1200)  # noqa: F405
    + anyplot_theme
)

# Save
export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)
export_ggsave(plot, filename=f"plot-{THEME}.html", path=".")
