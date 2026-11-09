"""anyplot.ai
forest-basic: Meta-Analysis Forest Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
ANYPLOT_NEUTRAL = INK  # pooled total, theme-adaptive

# Imprint palette: studies take position 1
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
NULL_EFFECT = 0.0  # no effect on the log odds ratio scale
Z_95 = 1.96  # normal quantile of a 95% confidence interval
POOLED_LABEL = "Pooled estimate"

# Columns: set these to your table's column names
STUDY = "Study"  # role: study
EFFECT = "Log Odds Ratio of 6-month Smoking Abstinence"  # role: effect_size
CI_LOWER = "CI lower"  # role: ci_lower
CI_UPPER = "CI upper"  # role: ci_upper
WEIGHT = "Weight (%)"  # role: weight

# Data: replace this block with your own table, for example df = pd.read_csv("meta_analysis.csv")
# Meta-analysis of ten randomized trials of nicotine patch vs placebo patch for smoking cessation;
# the effect is the log odds ratio of biochemically verified abstinence at 6 months (> 0 favours the patch)
df = pd.DataFrame(
    {
        STUDY: [
            "Smith 2018",
            "Johnson 2019",
            "Williams 2019",
            "Brown 2020",
            "Davis 2020",
            "Miller 2021",
            "Wilson 2021",
            "Moore 2022",
            "Taylor 2022",
            "Anderson 2023",
        ],
        EFFECT: [0.35, -0.12, 0.48, 0.22, 0.55, 0.15, 0.42, 0.28, 0.65, 0.18],
        CI_LOWER: [0.05, -0.45, 0.18, -0.15, 0.20, -0.18, 0.12, -0.08, 0.28, -0.12],
        CI_UPPER: [0.65, 0.21, 0.78, 0.59, 0.90, 0.48, 0.72, 0.64, 1.02, 0.48],
        WEIGHT: [12.5, 10.2, 11.8, 9.5, 8.7, 11.0, 12.0, 9.8, 7.5, 12.8],
    }
)

# Plot: reads only df and the constants above
studies = df.dropna(subset=[EFFECT, CI_LOWER, CI_UPPER]).sort_values(EFFECT).reset_index(drop=True)
studies["row"] = np.arange(len(studies), 0, -1)

# Pooled estimate: study weights for the centre, inverse variance of the CI-derived SEs for its interval
weights = studies[WEIGHT].fillna(studies[WEIGHT].mean())
pooled_effect = np.average(studies[EFFECT], weights=weights)
study_se = (studies[CI_UPPER] - studies[CI_LOWER]) / (2 * Z_95)
pooled_se = 1 / np.sqrt((1 / study_se**2).sum())
pooled_lower = pooled_effect - Z_95 * pooled_se
pooled_upper = pooled_effect + Z_95 * pooled_se

pooled_row = 0
diamond = pd.DataFrame(
    {
        "x": [pooled_lower, pooled_effect, pooled_upper, pooled_effect],
        "y": [pooled_row, pooled_row - 0.4, pooled_row, pooled_row + 0.4],
    }
)

plot = (
    ggplot()
    + geom_vline(xintercept=NULL_EFFECT, color=INK_SOFT, size=0.8, linetype="dashed")
    + geom_segment(
        aes(x=CI_LOWER, xend=CI_UPPER, y="row", yend="row"), data=studies, color=IMPRINT_PALETTE[0], size=1.0
    )
    + geom_point(aes(x=EFFECT, y="row", size=WEIGHT), data=studies, color=IMPRINT_PALETTE[0], shape=15)
    + geom_polygon(aes(x="x", y="y"), data=diamond, fill=ANYPLOT_NEUTRAL, color=ANYPLOT_NEUTRAL, size=0.5)
    + scale_size_area(max_size=6)
    + scale_y_continuous(
        breaks=studies["row"].tolist() + [pooled_row],
        labels=studies[STUDY].astype(str).tolist() + [POOLED_LABEL],
        limits=[pooled_row - 0.6, len(studies) + 0.6],
    )
    + labs(x=f"{EFFECT} (95% CI)", y="", title="forest-basic · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title_x=element_text(size=12, color=INK),
        axis_text_x=element_text(size=10, color=INK_SOFT),
        axis_text_y=element_text(size=10, color=INK_SOFT),
        axis_line_x=element_line(color=INK_SOFT),
        panel_grid_major_x=element_line(color=GRID, size=0.3),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position="none",
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
