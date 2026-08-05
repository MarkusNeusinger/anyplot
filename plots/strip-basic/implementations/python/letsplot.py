""" anyplot.ai
strip-basic: Basic Strip Plot
Library: letsplot 4.11.0 | Python 3.13.14
Quality: 90/100 | Updated: 2026-08-05
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
    geom_jitter,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    stat_summary,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint categorical palette - position 1 is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Survey response scores by department
np.random.seed(42)

departments = ["Marketing", "Engineering", "Sales", "Support"]
data = []

distributions = {"Marketing": (72, 12), "Engineering": (78, 8), "Sales": (68, 15), "Support": (75, 10)}

for dept in departments:
    n_points = np.random.randint(25, 45)
    mean, std = distributions[dept]
    scores = np.clip(np.random.normal(mean, std, n_points), 40, 100)
    for score in scores:
        data.append({"Department": dept, "Score": score})

df = pd.DataFrame(data)

# Plot - individual points per department, jittered to reveal every observation
plot = (
    ggplot(df, aes(x="Department", y="Score"))
    + geom_jitter(aes(color="Department"), size=4, alpha=0.65, width=0.25, height=0, seed=42, show_legend=False)
    # Mean + interquartile reference per department - draws the eye to the
    # Engineering-vs-Sales spread/level contrast that the raw jitter alone hides
    + stat_summary(
        aes(x="Department", y="Score"), fun="mean", fun_min="lq", fun_max="uq", geom="pointrange", color=INK, size=1.1
    )
    + scale_color_manual(values=IMPRINT_PALETTE)
    + labs(x="Department", y="Survey Score (points)", title="strip-basic · python · letsplot · anyplot.ai")
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        axis_title=element_text(color=INK, size=12),
        axis_text=element_text(color=INK_SOFT, size=10),
        plot_title=element_text(color=INK, size=16),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.3),
        panel_border=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
