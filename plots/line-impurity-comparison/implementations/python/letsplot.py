"""anyplot.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
P = "Probability of class 1 (p)"  # role: p
GINI = "Gini: 2p(1−p)"  # role: extra
ENTROPY = "Entropy: −Σ pᵢ log₂ pᵢ"  # role: extra
CRITERION = ""  # role: extra
IMPURITY = "Impurity measure (normalized)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("impurity.csv")
p = np.linspace(0, 1, 200)
with np.errstate(divide="ignore", invalid="ignore"):
    entropy = -p * np.log2(p) - (1 - p) * np.log2(1 - p)
df = pd.DataFrame({P: p, GINI: 2 * p * (1 - p), ENTROPY: np.nan_to_num(entropy, nan=0.0)})

# Plot: reads only df and the constants above
long = df.melt(id_vars=P, var_name=CRITERION, value_name=IMPURITY)
peaks = long.loc[long.groupby(CRITERION, sort=False)[IMPURITY].idxmax()]
peak_p = peaks[P].mean()
top = long[IMPURITY].max()
bottom = long[IMPURITY].min()
x_lo, x_hi = df[P].min(), df[P].max()
span_x = x_hi - x_lo
span_y = top - bottom

# Text positions derived from the data range and the curves
label_df = pd.DataFrame({P: [peak_p], IMPURITY: [top + 0.11 * span_y], "label": ["Maximum uncertainty"]})
arrow_df = pd.DataFrame({"x": [peak_p], "y": [top + 0.07 * span_y], "xend": [peak_p], "yend": [top + 0.03 * span_y]})
guide_df = pd.DataFrame({"x": [peak_p], "y": [bottom], "xend": [peak_p], "yend": [top + 0.03 * span_y]})
region_x = x_lo + 0.72 * span_x
region_df = pd.DataFrame(
    {
        P: [region_x],
        IMPURITY: [(np.interp(region_x, df[P], df[GINI]) + np.interp(region_x, df[P], df[ENTROPY])) / 2],
        "label": ["Shaded region:\ndifference between metrics"],
    }
)
edge_df = pd.DataFrame(
    {
        P: [x_lo + 0.07 * span_x, x_hi - 0.07 * span_x],
        IMPURITY: [bottom + 0.06 * span_y] * 2,
        "label": [f"p → {x_lo:g}: both → 0", f"p → {x_hi:g}: both → 0"],
        "hjust": [0.0, 1.0],
    }
)

plot = (
    ggplot()  # noqa: F405
    + geom_ribbon(  # noqa: F405
        data=df,
        mapping=aes(x=P, ymin=GINI, ymax=ENTROPY),  # noqa: F405
        fill=IMPRINT_PALETTE[2],
        alpha=0.18,
        tooltips="none",
    )
    + geom_line(  # noqa: F405
        data=long,
        mapping=aes(x=P, y=IMPURITY, color=CRITERION),  # noqa: F405
        size=1.5,
    )
    + geom_segment(  # noqa: F405
        aes(x="x", y="y", xend="xend", yend="yend"),  # noqa: F405
        data=guide_df,
        color=INK_SOFT,
        size=0.5,
        linetype="dashed",
        tooltips="none",
    )
    + geom_segment(  # noqa: F405
        aes(x="x", y="y", xend="xend", yend="yend"),  # noqa: F405
        data=arrow_df,
        color=INK_SOFT,
        size=0.6,
        arrow=arrow(angle=25, length=8, type="closed"),  # noqa: F405
        tooltips="none",
    )
    + geom_point(  # noqa: F405
        aes(x=P, y=IMPURITY, color=CRITERION),  # noqa: F405
        data=peaks,
        size=6,
        shape=21,
        fill=PAGE_BG,
        stroke=2,
        tooltips="none",
    )
    + geom_text(  # noqa: F405
        data=label_df,
        mapping=aes(x=P, y=IMPURITY, label="label"),  # noqa: F405
        size=4,
        color=INK,
        fontface="bold italic",
    )
    + geom_text(  # noqa: F405
        data=region_df,
        mapping=aes(x=P, y=IMPURITY, label="label"),  # noqa: F405
        size=3.5,
        color=INK_SOFT,
        fontface="italic",
    )
    + geom_text(  # noqa: F405
        data=edge_df,
        mapping=aes(x=P, y=IMPURITY, label="label", hjust="hjust"),  # noqa: F405
        size=3,
        color=INK_MUTED,
        fontface="italic",
    )
    + scale_color_manual(values=IMPRINT_PALETTE)  # noqa: F405
    + scale_x_continuous(breaks=list(np.linspace(x_lo, x_hi, 11)), limits=[x_lo, x_hi])  # noqa: F405
    + scale_y_continuous(  # noqa: F405
        breaks=list(np.linspace(0, 1, 6)), limits=[bottom - 0.08 * span_y, top + 0.16 * span_y]
    )
    + labs(  # noqa: F405
        title="line-impurity-comparison · python · letsplot · anyplot.ai",
        subtitle=(
            f"Both criteria peak at maximum uncertainty (p = {peak_p:g}), "
            "explaining why Gini and entropy yield similar tree structures"
        ),
    )
    + ggsize(800, 450)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        axis_text=element_text(size=10, color=INK_SOFT),  # noqa: F405
        axis_title=element_text(size=12, color=INK),  # noqa: F405
        plot_title=element_text(size=16, face="bold", color=INK),  # noqa: F405
        plot_subtitle=element_text(size=10, color=INK_SOFT, face="italic"),  # noqa: F405
        legend_text=element_text(size=10, color=INK_SOFT),  # noqa: F405
        legend_title=element_blank(),  # noqa: F405
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
        legend_position="bottom",
        panel_grid_major=element_line(color=GRID, size=0.3),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_line=element_blank(),  # noqa: F405
        axis_ticks=element_blank(),  # noqa: F405
        plot_margin=[20, 20, 10, 10],
    )
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
