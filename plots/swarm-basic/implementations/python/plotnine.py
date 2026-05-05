""" anyplot.ai
swarm-basic: Basic Swarm Plot
Library: plotnine 0.15.3 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-05
"""

import sys


sys.path.pop(0)  # prevent this file from shadowing the installed plotnine package

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_point,
    ggplot,
    labs,
    position_jitter,
    scale_color_manual,
    stat_summary,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Patient biomarker levels across treatment groups
np.random.seed(42)

treatment_groups = ["Placebo", "Low Dose", "Medium Dose", "High Dose"]

distributions = {
    "Placebo": {"mean": 45, "std": 12, "n": 50},
    "Low Dose": {"mean": 55, "std": 10, "n": 45},
    "Medium Dose": {"mean": 68, "std": 8, "n": 55},
    "High Dose": {"mean": 75, "std": 6, "n": 40},
}

data = []
for group, params in distributions.items():
    values = np.random.normal(params["mean"], params["std"], params["n"])
    values = np.clip(values, 20, 100)
    data.extend([(group, value) for value in values])

df = pd.DataFrame(data, columns=["treatment", "biomarker"])
df["treatment"] = pd.Categorical(df["treatment"], categories=treatment_groups, ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="treatment", y="biomarker", color="treatment"))
    + geom_point(position=position_jitter(width=0.3, height=0, random_state=42), size=3.5, alpha=0.75)
    + stat_summary(fun_y=np.median, geom="point", size=8, shape="D", color=INK)
    + scale_color_manual(values=OKABE_ITO)
    + labs(x="Treatment Group", y="Biomarker Level (ng/mL)", title="swarm-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.08),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.04),
        axis_title=element_text(color=INK, size=20),
        axis_text=element_text(color=INK_SOFT, size=16),
        plot_title=element_text(color=INK, size=24),
        legend_position="none",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300)
