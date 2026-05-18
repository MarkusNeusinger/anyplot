""" anyplot.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
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
    geom_violin,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data: Reaction times (ms) across 4 experimental conditions
np.random.seed(42)

conditions = ["Control", "Low Dose", "Medium Dose", "High Dose"]
n_per_group = 50

data = []
for condition in conditions:
    if condition == "Control":
        # Normal distribution centered at 450ms
        values = np.random.normal(450, 60, n_per_group)
    elif condition == "Low Dose":
        # Slightly faster, narrower distribution
        values = np.random.normal(420, 50, n_per_group)
    elif condition == "Medium Dose":
        # Faster with some variability
        values = np.random.normal(380, 70, n_per_group)
    else:  # High Dose
        # Fastest but bimodal (some responders, some non-responders)
        responders = np.random.normal(320, 40, n_per_group // 2)
        non_responders = np.random.normal(400, 35, n_per_group - n_per_group // 2)
        values = np.concatenate([responders, non_responders])

    for v in values:
        data.append({"Condition": condition, "Reaction Time": v})

df = pd.DataFrame(data)

# Ensure categorical order
df["Condition"] = pd.Categorical(df["Condition"], categories=conditions, ordered=True)

# Create plot with violin and overlaid swarm points
plot = (
    ggplot(df, aes(x="Condition", y="Reaction Time"))
    + geom_violin(aes(fill="Condition"), alpha=0.4, size=1.2)
    + geom_jitter(aes(color="Condition"), width=0.12, height=0, size=3.5, alpha=0.85)
    + scale_fill_manual(values=OKABE_ITO)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=24, color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        legend_position="none",
    )
    + labs(x="Experimental Condition", y="Reaction Time (ms)", title="violin-swarm · Python · letsplot · anyplot.ai")
    + ggsize(1600, 900)
)

# Save PNG (scale 3x for 4800 × 2700 px) and HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
