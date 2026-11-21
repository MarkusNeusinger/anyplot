"""anyplot.ai
shap-summary: SHAP Summary Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_vline,
    ggplot,
    labs,
    position_jitter,
    scale_color_gradient2,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: diverging ends (blue = low, red = high) and a neutral mid that stays visible on both pages
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
LOW_COLOR = IMPRINT_PALETTE[2]
HIGH_COLOR = IMPRINT_PALETTE[4]
MID_COLOR = "#8E8C82"

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature_names
SHAP_VALUE = "SHAP value (impact on prediction)"  # role: shap_values
FEATURE_VALUE = "Feature value"  # role: feature_values

# Data: replace this block with your own table, for example df = pd.read_csv("shap.csv")
np.random.seed(42)
n_samples = 250
names = [
    "Radius",
    "Texture",
    "Perimeter",
    "Area",
    "Smoothness",
    "Compactness",
    "Concavity",
    "Concave Points",
    "Symmetry",
    "Fractal Dimension",
    "Gray Mean",
    "Gray Std",
    "Radius SE",
    "Texture SE",
    "Perimeter SE",
]
shap_matrix = np.zeros((n_samples, len(names)))
value_matrix = np.zeros((n_samples, len(names)))
for i in range(len(names)):
    scale = np.random.uniform(0.3, 1.5)
    center = np.random.uniform(-0.5, 0.5)
    shap_matrix[:, i] = np.random.normal(center, scale, n_samples)
    value_matrix[:, i] = np.random.uniform(0, 1, n_samples)
df = pd.DataFrame(
    {FEATURE: np.repeat(names, n_samples), SHAP_VALUE: shap_matrix.T.ravel(), FEATURE_VALUE: value_matrix.T.ravel()}
)

# Plot
# Most important feature (largest mean |SHAP|) on top: ggplot draws the first category at the bottom
importance = df[SHAP_VALUE].abs().groupby(df[FEATURE]).mean().sort_values()
df[FEATURE] = pd.Categorical(df[FEATURE], categories=importance.index.tolist(), ordered=True)
mid_value = df[FEATURE_VALUE].mean()

plot = (
    ggplot(df, aes(x=SHAP_VALUE, y=FEATURE, color=FEATURE_VALUE))
    + geom_vline(xintercept=0, color=INK_SOFT, size=0.5, alpha=0.7)
    + geom_point(size=1.0, alpha=0.75, position=position_jitter(width=0, height=0.22, random_state=42))
    + scale_color_gradient2(low=LOW_COLOR, mid=MID_COLOR, high=HIGH_COLOR, midpoint=mid_value)
    + labs(title="shap-summary · python · plotnine · anyplot.ai", color="Feature value\n(low → high)")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        plot_title=element_text(size=12, color=INK, weight="bold"),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
