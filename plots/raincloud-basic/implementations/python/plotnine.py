"""anyplot.ai
raincloud-basic: Basic Raincloud Plot
Library: plotnine | Python 3.13
Quality: pending | Updated: 2026-05-26
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_flip,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_boxplot,
    geom_jitter,
    geom_violin,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_y_continuous,
    stage,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# anyplot palette — first series ALWAYS #009E73
ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — reaction times (ms) for three experimental conditions
np.random.seed(42)
control = np.random.normal(450, 60, 80)
treatment_a = np.random.normal(380, 50, 80)
treatment_b = np.concatenate([np.random.normal(350, 40, 50), np.random.normal(500, 45, 30)])

df = pd.DataFrame(
    {
        "condition": (
            ["Control"] * len(control) + ["Treatment A"] * len(treatment_a) + ["Treatment B"] * len(treatment_b)
        ),
        "reaction_time": np.concatenate([control, treatment_a, treatment_b]),
    }
)
df["condition"] = pd.Categorical(df["condition"], categories=["Treatment B", "Treatment A", "Control"], ordered=True)

# Category → anyplot palette positions 1, 2, 3 (brand green is Control, the reference group)
colors = {"Control": ANYPLOT_PALETTE[0], "Treatment A": ANYPLOT_PALETTE[1], "Treatment B": ANYPLOT_PALETTE[2]}

cloud_shift = 0.15

# Plot — horizontal raincloud via coord_flip
# Pre-flip: x=condition (categorical), y=reaction_time. After flip: categories on y, values on x.
plot = (
    ggplot(df, aes(x="condition", y="reaction_time", fill="condition", color="condition"))
    # Cloud (half-violin) — style="right" extends positive x = upward after flip
    + geom_violin(
        aes(x=stage("condition", after_scale="x+{0}".format(cloud_shift))),
        style="right",
        trim=True,
        scale="width",
        size=0.3,
        alpha=0.78,
        show_legend=False,
    )
    # Boxplot — centered on category baseline, theme-adaptive fill/edge
    + geom_boxplot(
        width=0.06, outlier_shape="", fill=ELEVATED_BG, color=INK_SOFT, size=0.5, alpha=0.95, show_legend=False
    )
    # Rain (jittered points) — nudged negative x = downward after flip
    + geom_jitter(
        aes(x=stage("condition", after_scale="x-0.18")), width=0.06, height=0, size=3.0, alpha=0.6, show_legend=False
    )
    # Annotation: bimodal callout for Treatment B (category index 1, 0-based)
    + annotate(
        "text",
        x=0.55,
        y=425,
        label="← Bimodal: two distinct\n     response clusters",
        size=13,
        color=INK_SOFT,
        ha="center",
        fontstyle="italic",
    )
    + annotate("segment", x=0.7, xend=0.95, y=370, yend=350, size=0.5, color=INK_MUTED, linetype="dashed")
    + annotate("segment", x=0.7, xend=0.95, y=480, yend=500, size=0.5, color=INK_MUTED, linetype="dashed")
    # Annotation: Treatment A shifted left
    + annotate(
        "text",
        x=1.55,
        y=290,
        label="Faster responses\nvs. Control →",
        size=12,
        color=INK_SOFT,
        ha="left",
        fontstyle="italic",
    )
    + scale_fill_manual(values=colors)
    + scale_color_manual(values=colors)
    + scale_y_continuous(expand=(0.02, 0, 0.08, 0))
    + coord_flip()
    + labs(x="Experimental Condition", y="Reaction Time (ms)", title="raincloud-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.15),
        panel_border=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_position="none",
        plot_margin=0.02,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
