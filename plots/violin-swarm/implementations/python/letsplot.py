"""anyplot.ai
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column constants
CONDITION = "Experimental Condition"  # role: category
REACTION = "Reaction Time (ms)"  # role: value

# Data: reaction times (ms) across 4 experimental conditions
rng = np.random.default_rng(42)
n_per_group = 50
conditions = ["Control", "Low Dose", "Medium Dose", "High Dose"]
values = {
    "Control": rng.normal(450, 60, n_per_group),
    "Low Dose": rng.normal(420, 50, n_per_group),
    "Medium Dose": rng.normal(380, 70, n_per_group),
    # Fastest but bimodal: some responders, some non-responders
    "High Dose": np.concatenate(
        [rng.normal(320, 40, n_per_group // 2), rng.normal(400, 35, n_per_group - n_per_group // 2)]
    ),
}
df = pd.DataFrame(
    {
        CONDITION: np.repeat(conditions, [len(values[c]) for c in conditions]),
        REACTION: np.concatenate([values[c] for c in conditions]),
    }
)

# Plot
plot = (
    ggplot(df, aes(x=CONDITION, y=REACTION))
    + geom_violin(aes(fill=CONDITION), alpha=0.4, size=0.8, trim=True)
    + geom_jitter(aes(color=CONDITION), width=0.1, height=0, size=2.5, alpha=0.85)
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + scale_color_manual(values=IMPRINT_PALETTE)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.2),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=16, color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        legend_position="none",
    )
    + labs(title="violin-swarm · python · letsplot · anyplot.ai")
    + ggsize(800, 450)
)

# Save PNG (scale 4x = 3200 × 1800 px) and HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
