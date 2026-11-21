""" anyplot.ai
forest-basic: Meta-Analysis Forest Plot
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-21
"""

import os
import sys


sys.path = [p for p in sys.path if p != "" and "/forest-basic" not in p]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_errorbarh,
    geom_point,
    geom_polygon,
    geom_text,
    geom_vline,
    ggplot,
    labs,
    scale_size_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is the single series
BRAND = "#009E73"

# Constants
NULL_EFFECT = 0  # a mean difference of zero means no effect
Z_95 = 1.96  # normal quantile of a 95 % confidence interval

# Columns: set these to your table's column names
STUDY = "Study"  # role: study
EFFECT = "Mean Difference (Treatment - Control)"  # role: effect_size
CI_LOWER = "Lower 95% CI"  # role: ci_lower
CI_UPPER = "Upper 95% CI"  # role: ci_upper
WEIGHT = "Weight (%)"  # role: weight

# Data: replace this block with your own table, for example df = pd.read_csv("studies.csv")
# Meta-analysis of randomized controlled trials, treatment vs control
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
        EFFECT: [-0.45, -0.22, -0.38, -0.15, -0.52, -0.31, -0.08, -0.41, -0.25, -0.35],
        CI_LOWER: [-0.72, -0.48, -0.61, -0.42, -0.81, -0.55, -0.35, -0.68, -0.51, -0.58],
        CI_UPPER: [-0.18, 0.04, -0.15, 0.12, -0.23, -0.07, 0.19, -0.14, 0.01, -0.12],
        WEIGHT: [9.8, 11.2, 10.5, 8.7, 7.3, 10.9, 9.1, 8.4, 11.8, 12.3],
    }
)

# Plot: reads only df and the constants above
studies = df.copy()
n_studies = len(studies)

# Pooled estimate: weighted mean effect, standard error from the inverse variances of the study intervals
pooled_effect = (studies[EFFECT] * studies[WEIGHT]).sum() / studies[WEIGHT].sum()
study_se = (studies[CI_UPPER] - studies[CI_LOWER]) / (2 * Z_95)
pooled_se = np.sqrt(1 / (1 / study_se**2).sum())
pooled_lower = pooled_effect - Z_95 * pooled_se
pooled_upper = pooled_effect + Z_95 * pooled_se

# Rows run top to bottom in the data's order, the pooled row sits below at 0
studies["y_pos"] = np.arange(n_studies, 0, -1)
studies["marker_size"] = studies[WEIGHT] * 0.3
studies["label"] = [
    f"{e:.2f} [{lo:.2f}, {hi:.2f}]"
    for e, lo, hi in zip(studies[EFFECT], studies[CI_LOWER], studies[CI_UPPER], strict=True)
]

diamond = pd.DataFrame({"x": [pooled_lower, pooled_effect, pooled_upper, pooled_effect], "y": [0, 0.3, 0, -0.3]})

# Text columns sit left and right of the data, axis limits follow the data's span
low = min(studies[CI_LOWER].min(), pooled_lower)
high = max(studies[CI_UPPER].max(), pooled_upper)
span = high - low
x_left = low - 0.5 * span
x_right = high + 0.08 * span
x_min = x_left - 0.05 * span
x_max = x_right + 0.42 * span
studies["x_left"] = x_left
studies["x_right"] = x_right

pooled_left = pd.DataFrame({"x": [x_left], "y": [0], "label": ["Pooled"]})
pooled_right = pd.DataFrame(
    {"x": [x_right], "y": [0], "label": [f"{pooled_effect:.2f} [{pooled_lower:.2f}, {pooled_upper:.2f}]"]}
)

plot = (
    ggplot()
    + geom_vline(xintercept=NULL_EFFECT, linetype="dashed", color=INK_SOFT, size=0.5, alpha=0.6)
    + geom_errorbarh(aes(y="y_pos", xmin=CI_LOWER, xmax=CI_UPPER), data=studies, height=0.25, size=0.6, color=BRAND)
    + geom_point(aes(x=EFFECT, y="y_pos", size="marker_size"), data=studies, color=BRAND, fill=BRAND)
    + scale_size_identity()
    + geom_polygon(aes(x="x", y="y"), data=diamond, fill=BRAND, color=BRAND, size=0.6, alpha=0.7)
    + geom_text(aes(x="x_left", y="y_pos", label=STUDY), data=studies, ha="left", size=7.5, color=INK)
    + geom_text(aes(x="x_right", y="y_pos", label="label"), data=studies, ha="left", size=6.5, color=INK_SOFT)
    + geom_text(aes(x="x", y="y", label="label"), data=pooled_left, ha="left", size=7.5, fontweight="bold", color=INK)
    + geom_text(
        aes(x="x", y="y", label="label"), data=pooled_right, ha="left", size=6.5, fontweight="bold", color=INK_SOFT
    )
    + labs(x=EFFECT, y="", title="forest-basic · python · plotnine · anyplot.ai")
    + scale_x_continuous(breaks=np.arange(-0.8, 0.41, 0.2).round(1).tolist(), limits=(x_min, x_max))
    + scale_y_continuous(breaks=[], limits=(-1, n_studies + 1.5))
    + theme(
        figure_size=(8, 4.5),
        panel_background=element_rect(fill=PAGE_BG, color=None),
        plot_background=element_rect(fill=PAGE_BG, color=None),
        panel_grid_major_x=element_line(color=INK, size=0.15, alpha=0.10),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        axis_text_x=element_text(size=8, color=INK_SOFT),
        axis_text_y=element_blank(),
        axis_title_x=element_text(size=10, color=INK),
        axis_title_y=element_blank(),
        plot_title=element_text(size=12, ha="center", color=INK),
        axis_ticks_major_y=element_blank(),
        legend_position="none",
        panel_border=element_rect(color=INK_SOFT, fill=None),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
