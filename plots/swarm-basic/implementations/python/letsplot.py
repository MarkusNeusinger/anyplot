""" anyplot.ai
swarm-basic: Basic Swarm Plot
Library: letsplot 4.11.0 | Python 3.13.14
Quality: 88/100 | Updated: 2026-07-26
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
    geom_crossbar,
    geom_sina,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme-adaptive chrome tokens (Imprint palette + surface tokens)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Performance scores across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Support"]
n_per_group = [45, 38, 52, 40]

data = []
for dept, n in zip(departments, n_per_group, strict=True):
    if dept == "Engineering":
        # Higher scores, moderate spread
        scores = np.random.normal(82, 8, n)
    elif dept == "Marketing":
        # Mid-range scores, wider spread
        scores = np.random.normal(75, 12, n)
    elif dept == "Sales":
        # Bimodal distribution (high and low performers)
        scores = np.concatenate([np.random.normal(65, 6, n // 2), np.random.normal(88, 5, n - n // 2)])
    else:  # Support
        # Lower average, tight distribution with some outliers
        scores = np.concatenate([np.random.normal(70, 6, n - 3), [45, 48, 95]])

    scores = np.clip(scores, 0, 100)
    for score in scores:
        data.append({"Department": dept, "Performance Score": score})

df = pd.DataFrame(data)

# Calculate means for each department
means = df.groupby("Department")["Performance Score"].mean().reset_index()
means.columns = ["Department", "mean"]

title = "swarm-basic · python · letsplot · anyplot.ai"

# Plot
plot = (
    ggplot(df, aes(x="Department", y="Performance Score"))
    + geom_sina(aes(color="Department", fill="Department"), size=4, alpha=0.7, seed=42, scale="width")
    + geom_crossbar(aes(x="Department", y="mean", ymin="mean", ymax="mean"), data=means, width=0.5, size=1.5, color=INK)
    + scale_color_manual(values=IMPRINT_PALETTE)
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + labs(x="Department", y="Performance Score", title=title)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        legend_position="none",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.3),
    )
    + ggsize(800, 450)
)

# Save PNG (scale=4 gives 3200x1800)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)

# Save HTML for interactive version
ggsave(plot, f"plot-{THEME}.html", path=".")
