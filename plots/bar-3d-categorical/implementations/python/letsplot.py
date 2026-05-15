""" anyplot.ai
bar-3d-categorical: 3D Bar Chart for Categorical Comparison
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 40/100 | Created: 2026-05-15
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
GRID_COLOR = "#D0CFC8" if THEME == "light" else "#333330"

OKABE_ITO = {"High School": "#009E73", "Bachelor's": "#D55E00", "Graduate": "#0072B2"}

# Data — job satisfaction scores by age group and education level
np.random.seed(42)
age_groups = ["18–34", "35–49", "50–64", "65+"]
edu_levels = ["High School", "Bachelor's", "Graduate"]

base = {"High School": [6.1, 5.7, 5.4, 5.8], "Bachelor's": [7.0, 7.3, 6.8, 7.1], "Graduate": [7.7, 8.0, 7.5, 7.8]}

rows = []
for edu, scores in base.items():
    for age, score in zip(age_groups, scores, strict=False):
        noise = np.random.uniform(-0.2, 0.2)
        val = round(score + noise, 1)
        rows.append({"Age Group": age, "Education": edu, "Satisfaction": val, "Label": f"{val:.1f}"})

df = pd.DataFrame(rows)

# Plot
plot = (
    ggplot(df, aes(x="Age Group", y="Satisfaction", fill="Education"))
    + geom_bar(stat="identity", position="dodge", width=0.75, color=PAGE_BG, size=0.4)
    + geom_text(aes(label="Label"), position=position_dodge(0.75), vjust=-0.5, size=11, color=INK_SOFT)
    + scale_fill_manual(values=OKABE_ITO)
    + scale_x_discrete(limits=age_groups)
    + scale_y_continuous(limits=[0, 10.5])
    + labs(
        x="Age Group",
        y="Satisfaction Score (0–10)",
        title="bar-3d-categorical · letsplot · anyplot.ai",
        fill="Education",
    )
    + theme_classic()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=GRID_COLOR, size=0.5),
        axis_title=element_text(color=INK, size=20),
        axis_text=element_text(color=INK_SOFT, size=16),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(color=INK, size=24),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=16),
        legend_title=element_text(color=INK, size=16),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
