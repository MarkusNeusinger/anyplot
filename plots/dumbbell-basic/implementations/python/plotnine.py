"""anyplot.ai
dumbbell-basic: Basic Dumbbell Chart
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 87/100 | Updated: 2026-06-30
"""

import os
import sys


# Prevent script directory from shadowing the plotnine package
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — hybrid-v3 sort order
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data: Employee satisfaction scores before and after workplace policy changes
categories_raw = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations", "Customer Support", "Product"]
before_scores_raw = [65, 58, 72, 45, 68, 52, 40, 75]
after_scores_raw = [82, 71, 78, 73, 75, 68, 62, 88]

differences_raw = [a - b for a, b in zip(after_scores_raw, before_scores_raw, strict=True)]
sorted_data = sorted(
    zip(categories_raw, before_scores_raw, after_scores_raw, differences_raw, strict=True), key=lambda x: x[3]
)
categories = [d[0] for d in sorted_data]
before_scores = [d[1] for d in sorted_data]
after_scores = [d[2] for d in sorted_data]
differences = [d[3] for d in sorted_data]

df_segments = pd.DataFrame(
    {
        "category": categories,
        "start": before_scores,
        "end": after_scores,
        "label_x": [(s + e) / 2 for s, e in zip(before_scores, after_scores, strict=True)],
        "label": [f"+{d}" for d in differences],
    }
)

df_points = pd.DataFrame(
    {
        "category": categories * 2,
        "value": before_scores + after_scores,
        "period": ["Before"] * len(categories) + ["After"] * len(categories),
    }
)

df_segments["category"] = pd.Categorical(df_segments["category"], categories=categories, ordered=True)
df_points["category"] = pd.Categorical(df_points["category"], categories=categories, ordered=True)
df_points["period"] = pd.Categorical(df_points["period"], categories=["Before", "After"], ordered=True)

plot = (
    ggplot()
    + geom_segment(
        aes(x="start", xend="end", y="category", yend="category"), data=df_segments, color=INK_SOFT, size=0.8, alpha=0.5
    )
    + geom_point(aes(x="value", y="category", color="period"), data=df_points, size=4.0)
    + geom_text(aes(x="label_x", y="category", label="label"), data=df_segments, color=INK_MUTED, size=3.0, nudge_y=0.3)
    + scale_color_manual(values={"Before": IMPRINT[0], "After": IMPRINT[1]})
    + scale_x_continuous(limits=(30, 100), breaks=[30, 40, 50, 60, 70, 80, 90, 100])
    + labs(
        x="Satisfaction Score",
        y="Department",
        title="Employee Satisfaction · dumbbell-basic · plotnine · anyplot.ai",
        color="",
    )
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=12, color=INK, weight="bold"),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_position="right",
        panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_blank(),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
