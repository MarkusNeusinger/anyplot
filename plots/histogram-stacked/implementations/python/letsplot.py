"""anyplot.ai
histogram-stacked: Stacked Histogram
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
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

# Imprint palette - first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BIN_WIDTH = 5

# Column names
SCORE = "score"  # role: values
CLASS = "class"  # role: group

# Data - Test scores from three different classes
np.random.seed(42)
class_a = np.random.normal(loc=72, scale=10, size=150)  # Average performers
class_b = np.random.normal(loc=78, scale=8, size=120)  # Above average
class_c = np.random.normal(loc=68, scale=12, size=130)  # More varied

df = pd.DataFrame(
    {
        SCORE: np.concatenate([class_a, class_b, class_c]).clip(0, 100),
        CLASS: ["Class A"] * 150 + ["Class B"] * 120 + ["Class C"] * 130,
    }
)

# Plot - Stacked histogram
plot = (
    ggplot(df, aes(x=SCORE, fill=CLASS))
    + geom_histogram(binwidth=BIN_WIDTH, position="stack", color=PAGE_BG, size=0.3)
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + labs(
        x="Test Score (points)",
        y="Number of Students",
        title="histogram-stacked · python · letsplot · anyplot.ai",
        fill="Class",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(color=INK, size=14),
        axis_text=element_text(color=INK_SOFT, size=12),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(color=INK, size=16, face="medium"),
        legend_title=element_text(color=INK, size=14),
        legend_text=element_text(color=INK_SOFT, size=12),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
