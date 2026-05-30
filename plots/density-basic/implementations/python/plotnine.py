""" anyplot.ai
density-basic: Basic Density Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-30
"""

import os
import sys


# Remove script dir from sys.path to avoid shadowing the plotnine package
_script_dir = os.path.dirname(os.path.abspath(__file__))
for _p in [_script_dir, "", "."]:
    while _p in sys.path:
        sys.path.remove(_p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    after_stat,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_area,
    geom_line,
    geom_rug,
    geom_vline,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint position 1 — always first series

# Data — bimodal test score distribution (150 main + 50 high achievers)
np.random.seed(42)
test_scores = np.concatenate([np.random.normal(72, 10, 150), np.random.normal(88, 5, 50)])
test_scores = np.clip(test_scores, 0, 100)

df = pd.DataFrame({"score": test_scores})

# Title with length-aware font sizing
title = "density-basic · python · plotnine · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fs = max(8, round(12 * ratio))

# Plot — layered density with bimodal emphasis
plot = (
    ggplot(df, aes(x="score"))
    + geom_area(aes(y=after_stat("density")), stat="density", fill=BRAND, alpha=0.3, color="none")
    + geom_line(aes(y=after_stat("density")), stat="density", color=BRAND, size=1.8)
    + geom_vline(xintercept=72, linetype="dashed", color=INK_SOFT, size=0.9, alpha=0.75)
    + geom_vline(xintercept=88, linetype="dashed", color=INK_SOFT, size=0.9, alpha=0.75)
    + geom_rug(color=INK_MUTED, alpha=0.5, size=0.6)
    + annotate("text", x=72, y=0.034, label="Main Group (μ ≈ 72)", size=3.5, color=INK)
    + annotate("text", x=89, y=0.029, label="High Achievers (μ ≈ 88)", size=3.5, color=INK)
    + labs(x="Test Score (points)", y="Probability Density", title=title)
    + scale_x_continuous(breaks=range(45, 101, 10))
    + scale_y_continuous(expand=(0, 0, 0.2, 0))
    + coord_cartesian(xlim=(45, 102))
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK_SOFT),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=title_fs, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        panel_border=element_blank(),
        axis_line=element_line(color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
