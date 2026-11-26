"""anyplot.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
COMPLEXITY = "Model Complexity"  # role: model_complexity
ERROR = "Prediction Error"  # role: total_error
COMPONENT = "Component"  # role: extra

# Constants
BIAS, VARIANCE, IRREDUCIBLE, TOTAL = "Bias²", "Variance", "Irreducible Error", "Total Error"
COMPONENT_ORDER = [BIAS, VARIANCE, IRREDUCIBLE, TOTAL]

# Data: replace this block with your own table, for example df = pd.read_csv("errors.csv")
complexity = np.linspace(0.5, 10.0, 100)
bias_squared = 3.0 / (1 + 0.7 * complexity)
variance = 0.08 * complexity**1.3
irreducible_error = np.full_like(complexity, 0.25)
total_error = bias_squared + variance + irreducible_error
df = pd.DataFrame(
    {
        COMPLEXITY: np.tile(complexity, 4),
        ERROR: np.concatenate([bias_squared, variance, irreducible_error, total_error]),
        COMPONENT: pd.Categorical(np.repeat(COMPONENT_ORDER, len(complexity)), categories=COMPONENT_ORDER),
    }
)

# Plot
total = df[df[COMPONENT] == TOTAL]
optimal = total.loc[total[ERROR].idxmin()]
optimal_complexity = float(optimal[COMPLEXITY])
optimal_error = float(optimal[ERROR])

x_min, x_max = float(df[COMPLEXITY].min()), float(df[COMPLEXITY].max())
y_min = float(df[ERROR].min()) - 0.15
y_max = float(df[ERROR].max()) * 1.35
zone_top = y_max * 0.98
zone_label_y = y_max * 0.92

# Direct labels at the right end of each curve
last = df.loc[df.groupby(COMPONENT, observed=True)[COMPLEXITY].idxmax()].set_index(COMPONENT)
label_offsets = {BIAS: 0.15, VARIANCE: 0.05, IRREDUCIBLE: -0.22, TOTAL: 0.04}
label_text = {BIAS: BIAS, VARIANCE: VARIANCE, IRREDUCIBLE: "Irred.\nError", TOTAL: "Total\nError"}
label_df = pd.DataFrame(
    {
        COMPLEXITY: x_max + 0.3,
        ERROR: [float(last.loc[c, ERROR]) + label_offsets[c] for c in COMPONENT_ORDER],
        "label": [label_text[c] for c in COMPONENT_ORDER],
        COMPONENT: pd.Categorical(COMPONENT_ORDER, categories=COMPONENT_ORDER),
    }
)

# Shaded underfitting / overfitting zones
under_df = pd.DataFrame({"xmin": [x_min - 0.1], "xmax": [optimal_complexity], "ymin": [y_min], "ymax": [zone_top]})
over_df = pd.DataFrame({"xmin": [optimal_complexity], "xmax": [x_max + 0.5], "ymin": [y_min], "ymax": [zone_top]})

# Zone labels
zone_df = pd.DataFrame(
    {
        "x": [(x_min + optimal_complexity) / 2, (optimal_complexity + x_max) / 2 + 0.25],
        "y": [zone_label_y, zone_label_y],
        "label": ["← Underfitting\n(High Bias)", "Overfitting →\n(High Variance)"],
    }
)

# Optimal complexity annotation
opt_df = pd.DataFrame({"x": [optimal_complexity + 0.25], "y": [optimal_error + 0.40], "label": ["Optimal\nComplexity"]})

# Formula annotation, below the zone labels
formula_df = pd.DataFrame(
    {"x": [optimal_complexity + 0.25], "y": [y_max * 0.74], "label": [f"{TOTAL} = {BIAS} + {VARIANCE} + {IRREDUCIBLE}"]}
)

# Imprint palette: Bias²=pos1 (green), Variance=pos2 (purple), Irred.=pos3 (blue), Total=red (semantic error)
color_values = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[1], IMPRINT_PALETTE[2], IMPRINT_PALETTE[4]]
linetype_values = ["dashed", "longdash", "dotted", "solid"]

title_str = "curve-bias-variance-tradeoff · python · letsplot · anyplot.ai"
title_n = len(title_str)
title_size = max(11, round(16 * 67 / title_n)) if title_n > 67 else 16

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_border=element_blank(),
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
    ggplot(df, aes(x=COMPLEXITY, y=ERROR, color=COMPONENT))
    + geom_rect(
        data=under_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill="#009E73",
        color=PAGE_BG,
        alpha=0.06,
        inherit_aes=False,
    )
    + geom_rect(
        data=over_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill="#AE3030",
        color=PAGE_BG,
        alpha=0.06,
        inherit_aes=False,
    )
    + geom_line(aes(linetype=COMPONENT), size=1.0, tooltips=layer_tooltips([COMPONENT, ERROR]))
    + geom_vline(xintercept=optimal_complexity, linetype="dotdash", color=INK_SOFT, size=0.65)
    + geom_text(
        data=zone_df, mapping=aes(x="x", y="y", label="label"), inherit_aes=False, color=INK_SOFT, size=4.0, hjust=0.5
    )
    + geom_text(data=opt_df, mapping=aes(x="x", y="y", label="label"), inherit_aes=False, color=INK, size=3.9, hjust=0)
    + geom_text(
        data=formula_df, mapping=aes(x="x", y="y", label="label"), inherit_aes=False, color=INK_SOFT, size=4.0, hjust=0
    )
    + geom_text(
        data=label_df,
        mapping=aes(x=COMPLEXITY, y=ERROR, label="label", color=COMPONENT),
        inherit_aes=False,
        size=3.9,
        hjust=0,
    )
    + scale_color_manual(values=color_values)
    + scale_linetype_manual(values=linetype_values)
    + scale_x_continuous(limits=[x_min - 0.1, x_max + 2.0])
    + scale_y_continuous(limits=[y_min, y_max])
    + labs(title=title_str)
    + ggsize(800, 450)
    + theme_classic()
    + anyplot_theme
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
