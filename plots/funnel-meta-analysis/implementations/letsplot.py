""" pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-15
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data: Meta-analysis of 15 RCTs comparing drug vs placebo
# Effect sizes are log odds ratios, null effect at 0
np.random.seed(42)

studies = [
    {"study": "Adams 2015", "effect_size": 0.42, "std_error": 0.18, "n": 120},
    {"study": "Baker 2016", "effect_size": 0.28, "std_error": 0.22, "n": 85},
    {"study": "Chen 2016", "effect_size": 0.65, "std_error": 0.30, "n": 48},
    {"study": "Davis 2017", "effect_size": -0.08, "std_error": 0.25, "n": 64},
    {"study": "Evans 2017", "effect_size": 0.52, "std_error": 0.12, "n": 280},
    {"study": "Foster 2018", "effect_size": 0.10, "std_error": 0.35, "n": 34},
    {"study": "Garcia 2018", "effect_size": 0.38, "std_error": 0.15, "n": 180},
    {"study": "Hughes 2019", "effect_size": 0.55, "std_error": 0.28, "n": 52},
    {"study": "Ito 2019", "effect_size": 0.30, "std_error": 0.10, "n": 410},
    {"study": "Jensen 2020", "effect_size": 1.05, "std_error": 0.32, "n": 40},
    {"study": "Klein 2020", "effect_size": -0.15, "std_error": 0.14, "n": 205},
    {"study": "Lee 2021", "effect_size": 0.48, "std_error": 0.20, "n": 100},
    {"study": "Morgan 2021", "effect_size": 0.33, "std_error": 0.16, "n": 160},
    {"study": "Nguyen 2022", "effect_size": 0.88, "std_error": 0.30, "n": 46},
    {"study": "Olsen 2023", "effect_size": -0.05, "std_error": 0.38, "n": 28},
]

df = pd.DataFrame(studies)

# Pooled effect estimate (inverse-variance weighted)
weights = 1 / (df["std_error"] ** 2)
pooled_effect = (df["effect_size"] * weights).sum() / weights.sum()

# Classify studies as inside or outside the 95% funnel
df["weight"] = weights / weights.max() * 8 + 3
funnel_bound_upper = pooled_effect + 1.96 * df["std_error"]
funnel_bound_lower = pooled_effect - 1.96 * df["std_error"]
df["position"] = np.where(
    (df["effect_size"] >= funnel_bound_lower) & (df["effect_size"] <= funnel_bound_upper),
    "Inside funnel",
    "Outside funnel",
)

# Pseudo 95% confidence funnel limits
se_max = df["std_error"].max() + 0.05
se_range = np.linspace(0, se_max, 200)
funnel_upper = pooled_effect + 1.96 * se_range
funnel_lower = pooled_effect - 1.96 * se_range

funnel_df = pd.DataFrame(
    {
        "effect_size": np.concatenate([funnel_lower, funnel_upper[::-1]]),
        "std_error": np.concatenate([se_range, se_range[::-1]]),
    }
)

funnel_lines_df = pd.DataFrame(
    {
        "effect_size": np.concatenate([funnel_lower, funnel_upper]),
        "std_error": np.concatenate([se_range, se_range]),
        "side": ["lower"] * len(se_range) + ["upper"] * len(se_range),
    }
)

# Color palette
blue_main = "#306998"
orange_accent = "#D4762C"
gray_light = "#E8E8E8"
gray_mid = "#B0B0B0"
gray_dark = "#555555"

# Plot
plot = (
    ggplot()
    # Funnel confidence region (shaded)
    + geom_polygon(aes(x="effect_size", y="std_error"), data=funnel_df, fill=blue_main, alpha=0.06)
    # Funnel boundary lines (95% CI)
    + geom_line(
        aes(x="effect_size", y="std_error", group="side"),
        data=funnel_lines_df,
        color=blue_main,
        size=0.8,
        linetype="dashed",
        alpha=0.45,
    )
    # Vertical line at pooled effect
    + geom_vline(xintercept=pooled_effect, color=blue_main, size=1.2, alpha=0.8)
    # Vertical dashed reference line at null effect (0)
    + geom_vline(xintercept=0, color=gray_mid, size=0.7, linetype="dashed")
    # Study points — colored by position, sized by weight, with interactive tooltips
    + geom_point(
        aes(x="effect_size", y="std_error", color="position", size="weight"),
        data=df,
        shape=16,
        alpha=0.85,
        tooltips=layer_tooltips()
        .line("@study")
        .line("Effect size|@effect_size")
        .line("Std. error|@std_error")
        .line("N|@n")
        .line("@position"),
    )
    + scale_color_manual(values=[blue_main, orange_accent], name="Classification")
    + scale_size_identity(guide="none")
    # Study labels for key studies (largest and outliers)
    + geom_text(
        aes(x="effect_size", y="std_error", label="study"),
        data=df[df["position"] == "Outside funnel"],
        color=orange_accent,
        size=11,
        nudge_y=-0.025,
        fontface="bold",
        show_legend=False,
    )
    + geom_text(
        aes(x="effect_size", y="std_error", label="study"),
        data=df[df["position"] == "Inside funnel"].nlargest(3, "weight"),
        color=gray_dark,
        size=10,
        nudge_y=-0.02,
        show_legend=False,
    )
    # Annotation: pooled effect value
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=pd.DataFrame(
            {"x": [pooled_effect + 0.03], "y": [0.005], "label": [f"Pooled OR = {np.exp(pooled_effect):.2f}"]}
        ),
        color=blue_main,
        size=11,
        fontface="bold",
        hjust=0,
        show_legend=False,
    )
    # Inverted y-axis (more precise studies at top)
    + scale_y_reverse()
    # Labels
    + labs(
        x="Log Odds Ratio",
        y="Standard Error (precision \u2192)",
        title="funnel-meta-analysis \u00b7 letsplot \u00b7 pyplots.ai",
    )
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold", color=gray_dark),
        axis_title=element_text(size=20, color=gray_dark),
        axis_text=element_text(size=16, color=gray_mid),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color="#F0F0F0", size=0.3),
        panel_grid_minor=element_blank(),
        axis_line=element_blank(),
        legend_position=[0.88, 0.88],
        legend_title=element_text(size=16, face="bold", color=gray_dark),
        legend_text=element_text(size=14, color=gray_dark),
        legend_background=element_rect(fill="white", color=gray_light, size=0.5),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
    )
)

# Save
ggsave(plot, "plot.png", scale=3, path=".")
ggsave(plot, "plot.html", path=".")
