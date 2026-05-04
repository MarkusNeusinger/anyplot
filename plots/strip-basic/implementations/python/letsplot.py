""" anyplot.ai
strip-basic: Basic Strip Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-04
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
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1

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

# Plot
plot = (
    ggplot(df, aes(x="Department", y="Score"))
    + geom_jitter(color=BRAND, size=4, alpha=0.65, width=0.25, height=0, seed=42)
    + labs(x="Department", y="Survey Score (points)", title="strip-basic · letsplot · anyplot.ai")
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        axis_title=element_text(color=INK, size=20),
        axis_text=element_text(color=INK_SOFT, size=16),
        plot_title=element_text(color=INK, size=24),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.3),
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
