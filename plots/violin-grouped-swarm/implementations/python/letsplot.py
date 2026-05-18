""" anyplot.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_violin,
    ggplot,
    ggsize,
    labs,
    position_dodge,
    position_jitterdodge,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Drug efficacy across dosage levels and treatment groups
np.random.seed(42)

categories = ["Low Dose", "Medium Dose", "High Dose"]
groups = ["Placebo", "Treatment"]

data = []
for cat in categories:
    for grp in groups:
        if cat == "Low Dose":
            base = 3.0 if grp == "Placebo" else 4.2
            spread = 1.2 if grp == "Placebo" else 0.8
        elif cat == "Medium Dose":
            base = 3.5 if grp == "Placebo" else 6.1
            spread = 1.3 if grp == "Placebo" else 0.9
        else:  # High Dose
            base = 3.8 if grp == "Placebo" else 7.5
            spread = 1.4 if grp == "Placebo" else 1.0

        n = 45
        values = np.random.normal(base, spread, n)
        values = np.clip(values, 1, 10)

        for v in values:
            data.append({"Dosage": cat, "Group": grp, "Efficacy Score": v})

df = pd.DataFrame(data)

# Plot
plot = (
    ggplot(df, aes(x="Dosage", y="Efficacy Score", fill="Group", color="Group"))
    + geom_violin(alpha=0.5, position=position_dodge(width=0.75), size=0.6, trim=False)
    + geom_point(alpha=0.6, size=2.0, position=position_jitterdodge(jitter_width=0.1, dodge_width=0.75))
    + scale_fill_manual(values=OKABE_ITO[:2])
    + scale_color_manual(values=OKABE_ITO[:2])
    + labs(
        x="Dosage Level",
        y="Efficacy Score",
        title="violin-grouped-swarm · Python · letsplot · anyplot.ai",
        fill="Group",
        color="Group",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.2),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
