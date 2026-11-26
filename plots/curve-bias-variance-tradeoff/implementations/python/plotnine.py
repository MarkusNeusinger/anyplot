""" anyplot.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 75/100 | Updated: 2026-11-26
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    scale_size_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per curve in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
COMPLEXITY = "Model Complexity"  # role: model_complexity
BIAS = "Bias²"  # role: bias_squared
VARIANCE = "Variance"  # role: variance
IRREDUCIBLE = "Irreducible Error"  # role: irreducible_error
TOTAL = "Total Error"  # role: total_error
ERROR = "Prediction Error"  # role: extra
CURVE = "Curve"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("curves.csv")
complexity = np.linspace(0.1, 10, 100)
bias_sq = 1.0 / (1.0 + complexity * 0.4) ** 0.9
variance = 0.018 * complexity**1.6
irreducible = np.full(len(complexity), 0.20)
df = pd.DataFrame(
    {
        COMPLEXITY: complexity,
        BIAS: bias_sq,
        VARIANCE: variance,
        IRREDUCIBLE: irreducible,
        TOTAL: bias_sq + variance + irreducible,
    }
)

# Plot: reads only df and the constants above
curves = [BIAS, VARIANCE, IRREDUCIBLE, TOTAL]
long_df = df.melt(id_vars=COMPLEXITY, value_vars=curves, var_name=CURVE, value_name=ERROR)
long_df[CURVE] = pd.Categorical(long_df[CURVE], categories=curves)

colors = dict(zip(curves, IMPRINT_PALETTE, strict=False))
linetypes = dict(zip(curves, ["dashed", "dashed", "dotted", "solid"], strict=True))
line_sizes = dict(zip(curves, [0.9, 0.9, 0.7, 1.3], strict=True))

x_min, x_max = df[COMPLEXITY].min(), df[COMPLEXITY].max()
x_span = x_max - x_min
y_top = df[TOTAL].max() * 1.05
opt_idx = df[TOTAL].idxmin()
opt_x = df.loc[opt_idx, COMPLEXITY]
opt_y = df.loc[opt_idx, TOTAL]


# Direct curve labels, each placed on its own curve at a well-separated position
label_x = x_min + x_span * np.array([0.21, 0.79, 0.64, 0.57])
label_y = [
    np.interp(label_x[0], df[COMPLEXITY], df[BIAS]) + 0.06,
    np.interp(label_x[1], df[COMPLEXITY], df[VARIANCE]) + 0.05,
    df[IRREDUCIBLE].iloc[0] - 0.06,
    np.interp(label_x[3], df[COMPLEXITY], df[TOTAL]) + 0.06,
]

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=INK_MUTED, size=0.3),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    panel_border=element_blank(),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    axis_ticks=element_line(color=INK_SOFT, size=0.3),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    plot_title=element_text(color=INK, size=12),
    legend_position="none",
)

plot = (
    ggplot(long_df, aes(x=COMPLEXITY, y=ERROR, color=CURVE, linetype=CURVE, size=CURVE))
    # Underfitting (left) and overfitting (right) zones around the optimum
    + annotate(
        "rect",
        xmin=[x_min, opt_x],
        xmax=[opt_x, x_max * 1.15],
        ymin=[0.0, 0.0],
        ymax=[y_top, y_top],
        fill=INK_MUTED,
        alpha=0.07,
    )
    + geom_line()
    + geom_vline(xintercept=opt_x, color=INK_MUTED, linetype="dashed", size=0.5)
    + annotate("text", x=label_x, y=label_y, label=curves, color=[colors[c] for c in curves], size=3.5, ha="left")
    + annotate(
        "text",
        x=opt_x + 0.025 * x_span,
        y=opt_y - 0.07,
        label="Optimal\nComplexity",
        color=INK_MUTED,
        size=3.2,
        ha="left",
    )
    + annotate(
        "text",
        x=x_min + 0.55 * x_span,
        y=y_top * 0.93 / 1.05,
        label=f"{TOTAL} = {BIAS} + {VARIANCE} + {IRREDUCIBLE}",
        color=INK_SOFT,
        size=3.2,
        ha="center",
    )
    + scale_color_manual(values=colors)
    + scale_linetype_manual(values=linetypes)
    + scale_size_manual(values=line_sizes)
    + scale_x_continuous(
        name=COMPLEXITY,
        breaks=np.linspace(0, x_max, 6),
        labels=["Low", "", "", "", "", "High"],
        limits=(x_min, x_max * 1.15),
    )
    + scale_y_continuous(name=ERROR, limits=(0.0, y_top))
    + labs(title="curve-bias-variance-tradeoff · python · plotnine · anyplot.ai")
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
