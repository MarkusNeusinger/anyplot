""" anyplot.ai
point-basic: Point Estimate Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-11
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND = "#009E73"

# Data - Research study results with confidence intervals
np.random.seed(42)
categories = ["Treatment A", "Treatment B", "Treatment C", "Control", "Placebo"]
estimates = [4.2, 5.8, 3.1, 2.5, 1.8]
ci_width = [0.9, 1.1, 0.7, 0.8, 0.6]
lower = [e - w for e, w in zip(estimates, ci_width, strict=False)]
upper = [e + w for e, w in zip(estimates, ci_width, strict=False)]

df = pd.DataFrame({"group": categories, "estimate": estimates, "lower": lower, "upper": upper})

# Plot - Horizontal point estimate plot with confidence intervals
plot = (
    ggplot(df, aes(x="group", y="estimate", ymin="lower", ymax="upper"))
    + geom_pointrange(color=BRAND, size=1.5, linewidth=1.5)
    + geom_hline(yintercept=0, linetype="dashed", color=INK_SOFT, size=0.8, alpha=0.5)
    + labs(y="Effect Size (95% CI)", x="Treatment Group", title="point-basic · letsplot · anyplot.ai")
    + coord_flip()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_line(color=RULE, size=0.3),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, color=INK),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
