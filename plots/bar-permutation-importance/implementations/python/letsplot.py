""" anyplot.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    as_discrete,
    coord_flip,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_errorbar,
    geom_hline,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_gradient,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: imprint_seq stops (brand green → blue) for the continuous importance
IMPRINT_SEQ = ["#009E73", "#4467A3"]

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
IMPORTANCE_MEAN = "Mean decrease in model score"  # role: importance_mean
IMPORTANCE_STD = "Std across shuffles"  # role: importance_std

# Data: replace this block with your own table, for example df = pd.read_csv("permutation_importance.csv")
np.random.seed(42)
features = [
    "Income Level",
    "Credit Score",
    "Employment Years",
    "Debt Ratio",
    "Account Age",
    "Payment History",
    "Loan Amount",
    "Interest Rate",
    "Property Value",
    "Monthly Expenses",
    "Savings Balance",
    "Number of Accounts",
    "Recent Inquiries",
    "Education Level",
    "Region Code",
]
base_importance = np.array(
    [0.15, 0.12, 0.09, 0.08, 0.06, 0.05, 0.04, 0.03, 0.025, 0.02, 0.015, 0.01, 0.008, 0.005, 0.002]
)
df = pd.DataFrame(
    {
        FEATURE: features,
        IMPORTANCE_MEAN: base_importance + np.random.uniform(-0.005, 0.005, len(features)),
        IMPORTANCE_STD: np.random.uniform(0.003, 0.02, len(features)),
    }
)

# Plot: reads only df and the constants above
bars = df.assign(
    error_low=df[IMPORTANCE_MEAN] - df[IMPORTANCE_STD], error_high=df[IMPORTANCE_MEAN] + df[IMPORTANCE_STD]
)
feature_axis = as_discrete(FEATURE, order_by=IMPORTANCE_MEAN, order=1)  # ascending → highest at top after flip

plot = (
    ggplot(bars, aes(x=feature_axis, y=IMPORTANCE_MEAN))
    + geom_bar(
        aes(fill=IMPORTANCE_MEAN),
        stat="identity",
        width=0.72,
        color=PAGE_BG,
        size=0.3,
        tooltips=layer_tooltips()
        .title(f"@{{{FEATURE}}}")
        .line(f"mean|@{{{IMPORTANCE_MEAN}}}")
        .line(f"std|@{{{IMPORTANCE_STD}}}")
        .format(f"@{{{IMPORTANCE_MEAN}}}", ".4f")
        .format(f"@{{{IMPORTANCE_STD}}}", ".4f"),
    )
    + geom_errorbar(aes(ymin="error_low", ymax="error_high"), width=0.35, size=0.8, color=INK)
    + geom_text(
        aes(y="error_high", label=IMPORTANCE_MEAN),
        label_format=".3f",
        hjust=0,
        nudge_y=bars["error_high"].max() * 0.012,
        size=4.5,
        color=INK_SOFT,
    )
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.8, linetype="dashed")
    + coord_flip()
    + scale_fill_gradient(low=IMPRINT_SEQ[0], high=IMPRINT_SEQ[1], guide="none")
    + scale_y_continuous(expand=[0.1, 0])  # room for the value label past the longest error bar
    + labs(x=FEATURE, y=IMPORTANCE_MEAN, title="bar-permutation-importance · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.2),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=16, color=INK, face="bold"),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_ticks=element_blank(),
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
