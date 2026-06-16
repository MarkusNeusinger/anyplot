""" anyplot.ai
cat-box-strip: Box Plot with Strip Overlay
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-13
"""

import os
import pathlib

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
BOX_COLOR = "#009E73"  # Brand green - first series
POINT_COLOR = "#C475FD"  # Vermillion - second series

# Data - Uptime scores across service tiers
np.random.seed(42)

tiers = ["Basic", "Professional", "Enterprise", "Elite"]
n_per_tier = [32, 38, 35, 28]

data = []
for tier, n in zip(tiers, n_per_tier, strict=True):
    if tier == "Basic":
        # Lower uptime, more variability
        scores = np.concatenate(
            [
                np.random.normal(94.5, 2.5, n - 2),
                np.array([88.2, 91.5]),  # Some lower outliers
            ]
        )
    elif tier == "Professional":
        # Moderate uptime, consistent
        scores = np.random.normal(97.8, 1.8, n)
    elif tier == "Enterprise":
        # High uptime, tight distribution
        scores = np.concatenate(
            [
                np.random.normal(99.2, 0.9, n - 1),
                np.array([96.5]),  # One lower performer
            ]
        )
    else:  # Elite
        # Very high uptime, minimal variance
        scores = np.random.normal(99.7, 0.5, n)

    scores = np.clip(scores, 85, 100)
    for score in scores:
        data.append({"Service Tier": tier, "Uptime (%)": score})

df = pd.DataFrame(data)

# Custom theme
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major_y=element_line(color=INK_SOFT, size=0.3),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=24),
)

# Plot - box plot with jittered strip overlay
plot = (
    ggplot(df, aes(x="Service Tier", y="Uptime (%)"))
    + geom_boxplot(fill=BOX_COLOR, color=INK_SOFT, alpha=0.7, width=0.5, outlier_alpha=0)
    + geom_jitter(color=POINT_COLOR, size=4, alpha=0.65, width=0.12)
    + labs(title="cat-box-strip · letsplot · anyplot.ai", x="Service Tier", y="Uptime (%)")
    + theme_minimal()
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save
output_dir = pathlib.Path.cwd()
ggsave(plot, str(output_dir / f"plot-{THEME}.png"), scale=3)
ggsave(plot, str(output_dir / f"plot-{THEME}.html"))
