""" anyplot.ai
linked-views-selection: Multiple Linked Views with Selection Sync
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 86/100 | Created: 2026-05-23
"""

import os
import sys


# Remove the script's own directory from sys.path so 'plotnine' resolves to
# the installed package, not this file (which shares the same name).
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_point,
    ggplot,
    guides,
    labs,
    scale_alpha_manual,
    scale_color_manual,
    theme,
)
from sklearn.datasets import load_iris


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

SELECTED_COLOR = "#009E73"
UNSELECTED_COLOR = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data — iris dataset with setosa "brushed" / selected across all views
iris = load_iris(as_frame=True)
df = iris.frame
df.columns = ["sepal_length", "sepal_width", "petal_length", "petal_width", "species_id"]
df["selection"] = df["species_id"].apply(lambda s: "Setosa (selected)" if s == 0 else "Other species")

# Reshape into three coordinated views (different variable pairs per view)
view1 = df[["sepal_length", "sepal_width", "selection"]].rename(columns={"sepal_length": "x", "sepal_width": "y"})
view1["view"] = "Sepal Length vs Width"

view2 = df[["petal_length", "petal_width", "selection"]].rename(columns={"petal_length": "x", "petal_width": "y"})
view2["view"] = "Petal Length vs Width"

view3 = df[["sepal_length", "petal_length", "selection"]].rename(columns={"sepal_length": "x", "petal_length": "y"})
view3["view"] = "Sepal vs Petal Length"

combined = pd.concat([view1, view2, view3], ignore_index=True)
combined["view"] = pd.Categorical(
    combined["view"],
    categories=["Sepal Length vs Width", "Petal Length vs Width", "Sepal vs Petal Length"],
    ordered=True,
)

# Title with length-aware font scaling
title = "linked-views-selection · python · plotnine · anyplot.ai"
title_fontsize = max(8, round(12 * min(1.0, 67 / len(title))))

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_blank(),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
    axis_line=element_blank(),
    axis_title=element_text(color=INK, size=9),
    axis_text=element_text(color=INK_SOFT, size=7),
    plot_title=element_text(color=INK, size=title_fontsize),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_key=element_rect(fill=PAGE_BG),
    legend_text=element_text(color=INK_SOFT, size=7),
    legend_title=element_text(color=INK, size=8),
    legend_position="right",
    strip_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    strip_text=element_text(color=INK, size=8),
)

color_map = {"Setosa (selected)": SELECTED_COLOR, "Other species": UNSELECTED_COLOR}
alpha_map = {"Setosa (selected)": 0.85, "Other species": 0.25}

# Plot — three coordinated scatter views with consistent selection encoding
plot = (
    ggplot(combined, aes("x", "y", color="selection", alpha="selection"))
    + geom_point(size=2.5)
    + facet_wrap("~view", scales="free", ncol=3)
    + scale_color_manual(values=color_map, name="")
    + scale_alpha_manual(values=alpha_map)
    + guides(alpha=False)
    + labs(x="", y="", title=title)
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
