""" anyplot.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-28
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data — formula distinct from seaborn sibling (change request)
np.random.seed(42)
complexity = np.linspace(0.5, 10.0, 100)
bias_squared = 3.0 / (1 + 0.7 * complexity)
variance = 0.08 * complexity**1.3
irreducible_error = np.full_like(complexity, 0.25)
total_error = bias_squared + variance + irreducible_error

optimal_idx = int(np.argmin(total_error))
optimal_complexity = float(complexity[optimal_idx])
optimal_error = float(total_error[optimal_idx])

component_order = ["Bias²", "Variance", "Irreducible Error", "Total Error"]
df = pd.DataFrame(
    {
        "complexity": np.tile(complexity, 4),
        "error": np.concatenate([bias_squared, variance, irreducible_error, total_error]),
        "component": pd.Categorical(
            ["Bias²"] * 100 + ["Variance"] * 100 + ["Irreducible Error"] * 100 + ["Total Error"] * 100,
            categories=component_order,
        ),
    }
)

# Curve values at x=10 for right-side direct labels
x_lbl = 10.0
bias_at_lbl = float(3.0 / (1 + 0.7 * x_lbl))
var_at_lbl = float(0.08 * x_lbl**1.3)
irred_at_lbl = 0.25
total_at_lbl = bias_at_lbl + var_at_lbl + irred_at_lbl

label_df = pd.DataFrame(
    {
        "complexity": [x_lbl + 0.3] * 4,
        "error": [bias_at_lbl + 0.05, var_at_lbl + 0.05, irred_at_lbl - 0.12, total_at_lbl + 0.04],
        "label": ["Bias²", "Variance", "Irred.\nError", "Total\nError"],
        "component": pd.Categorical(component_order, categories=component_order),
    }
)

# Shaded underfitting / overfitting zones
under_df = pd.DataFrame({"xmin": [0.4], "xmax": [optimal_complexity], "ymin": [-0.15], "ymax": [3.38]})
over_df = pd.DataFrame({"xmin": [optimal_complexity], "xmax": [10.5], "ymin": [-0.15], "ymax": [3.38]})

# Zone labels
zone_df = pd.DataFrame(
    {
        "x": [optimal_complexity * 0.42, (optimal_complexity + 10.5) * 0.5],
        "y": [3.12, 3.12],
        "label": ["← Underfitting\n(High Bias)", "Overfitting →\n(High Variance)"],
    }
)

# Optimal complexity annotation
opt_df = pd.DataFrame({"x": [optimal_complexity + 0.25], "y": [optimal_error + 0.40], "label": ["Optimal\nComplexity"]})

# Formula annotation
formula_df = pd.DataFrame({"x": [5.25], "y": [2.80], "label": ["Total Error = Bias² + Variance + Irreducible Error"]})

# anyplot palette: Bias²=pos1 (green), Variance=pos2 (purple), Irred.=pos3 (blue), Total=red (semantic error)
color_values = ["#009E73", "#C475FD", "#4467A3", "#AE3030"]
linetype_values = ["dashed", "longdash", "dotted", "solid"]

title_str = "curve-bias-variance-tradeoff · python · letsplot · anyplot.ai"
title_n = len(title_str)
title_size = max(11, round(16 * 67 / title_n)) if title_n > 67 else 16

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_x=element_blank(),
    panel_grid_major_y=element_line(color=INK_SOFT, size=0.12),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=title_size),
    legend_position="none",
)

plot = (
    ggplot(df, aes(x="complexity", y="error", color="component"))
    + geom_rect(
        data=under_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill="#009E73",
        alpha=0.06,
        inherit_aes=False,
    )
    + geom_rect(
        data=over_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill="#AE3030",
        alpha=0.06,
        inherit_aes=False,
    )
    + geom_line(aes(linetype="component"), size=1.0)
    + geom_vline(xintercept=optimal_complexity, linetype="dotdash", color=INK_SOFT, size=0.65)
    + geom_text(
        data=zone_df, mapping=aes(x="x", y="y", label="label"), inherit_aes=False, color=INK_SOFT, size=2.9, hjust=0.5
    )
    + geom_text(data=opt_df, mapping=aes(x="x", y="y", label="label"), inherit_aes=False, color=INK, size=3.2, hjust=0)
    + geom_text(
        data=formula_df,
        mapping=aes(x="x", y="y", label="label"),
        inherit_aes=False,
        color=INK_SOFT,
        size=2.7,
        hjust=0.5,
    )
    + geom_text(
        data=label_df,
        mapping=aes(x="complexity", y="error", label="label", color="component"),
        inherit_aes=False,
        size=3.2,
        hjust=0,
    )
    + scale_color_manual(values=color_values)
    + scale_linetype_manual(values=linetype_values)
    + scale_x_continuous(limits=[0.4, 12.0], breaks=[2, 4, 6, 8, 10])
    + scale_y_continuous(limits=[-0.15, 3.45])
    + labs(x="Model Complexity", y="Prediction Error", title=title_str)
    + ggsize(800, 450)
    + theme_minimal()
    + anyplot_theme
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
