"""pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-15
"""

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
    geom_point,
    geom_polygon,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    scale_size_continuous,
    scale_x_continuous,
    scale_y_reverse,
    theme,
    theme_minimal,
)


# Data - 15 RCTs comparing drug vs placebo (log odds ratios)
np.random.seed(42)
n_studies = 15
true_effect = 0.3

std_errors = np.concatenate(
    [np.random.uniform(0.05, 0.15, 5), np.random.uniform(0.15, 0.30, 5), np.random.uniform(0.30, 0.55, 5)]
)
effect_sizes = true_effect + np.random.normal(0, std_errors)

# Add publication bias (shift small studies toward positive)
bias_mask = std_errors > 0.35
effect_sizes[bias_mask] += np.random.uniform(0.05, 0.2, bias_mask.sum())

summary_effect = np.average(effect_sizes, weights=1 / std_errors**2)

# Weight proportional to inverse variance for sizing
weights = 1 / std_errors**2
weight_normalized = weights / weights.max()

# Classify studies by position relative to funnel bounds for storytelling
lower_ci = summary_effect - 1.96 * std_errors
upper_ci = summary_effect + 1.96 * std_errors
outside_funnel = (effect_sizes < lower_ci) | (effect_sizes > upper_ci)
region = np.where(outside_funnel, "Outside funnel", "Inside funnel")

studies_df = pd.DataFrame(
    {
        "effect_size": effect_sizes,
        "std_error": std_errors,
        "weight": weight_normalized,
        "region": pd.Categorical(region, categories=["Inside funnel", "Outside funnel"]),
        "study": [f"Study {i + 1}" for i in range(n_studies)],
    }
)

# Funnel boundary lines (pseudo 95% CI)
se_range = np.linspace(0, 0.6, 200)
funnel_lines = pd.DataFrame(
    {
        "effect": np.concatenate([summary_effect - 1.96 * se_range, summary_effect + 1.96 * se_range]),
        "se": np.concatenate([se_range, se_range]),
        "side": ["lower"] * len(se_range) + ["upper"] * len(se_range),
    }
)

# Funnel polygon for shaded region
se_max = 0.6
funnel_poly = pd.DataFrame(
    {"x": [summary_effect, summary_effect - 1.96 * se_max, summary_effect + 1.96 * se_max], "y": [0, se_max, se_max]}
)

# Plot
plot = (
    ggplot()
    # Shaded funnel region
    + geom_polygon(funnel_poly, aes(x="x", y="y"), fill="#306998", alpha=0.06)
    # Funnel boundary lines
    + geom_line(funnel_lines, aes(x="effect", y="se", group="side"), color="#8FAFC7", linetype="dashed", size=0.8)
    # Summary effect line
    + annotate("segment", x=summary_effect, xend=summary_effect, y=0, yend=0.6, color="#306998", size=1.3)
    # Null effect reference line
    + geom_vline(xintercept=0, color="#AAAAAA", linetype="dotted", size=0.7)
    # Study points: sized by weight, colored by funnel position
    + geom_point(studies_df, aes(x="effect_size", y="std_error", size="weight", color="region"), alpha=0.85, stroke=0.4)
    + scale_size_continuous(range=(3, 9), guide=None)
    + scale_color_manual(values={"Inside funnel": "#306998", "Outside funnel": "#D4652A"}, name=" ")
    # Annotation for publication bias
    + annotate(
        "text",
        x=summary_effect + 0.55,
        y=0.56,
        label="Asymmetry suggests\npublication bias",
        size=10,
        color="#D4652A",
        fontstyle="italic",
        ha="center",
    )
    # Annotation for summary effect
    + annotate(
        "text",
        x=summary_effect + 0.02,
        y=0.02,
        label=f"Pooled effect = {summary_effect:.2f}",
        size=9,
        color="#306998",
        ha="left",
        va="top",
    )
    # Null effect label
    + annotate("text", x=-0.02, y=0.02, label="Null", size=9, color="#999999", ha="right", va="top")
    + scale_y_reverse(limits=(0.65, -0.02))
    + scale_x_continuous(breaks=np.arange(-0.6, 1.4, 0.2).round(1).tolist())
    + labs(x="Log Odds Ratio", y="Standard Error", title="funnel-meta-analysis · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", color="#2C3E50"),
        axis_title=element_text(size=20, color="#34495E"),
        axis_text=element_text(size=16, color="#5D6D7E"),
        panel_grid_major=element_line(color="#E8E8E8", size=0.4),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#FAFBFC", color="none"),
        plot_background=element_rect(fill="white", color="none"),
        legend_position=(0.15, 0.12),
        legend_background=element_rect(fill="white", alpha=0.8, color="none"),
        legend_text=element_text(size=14),
        axis_line=element_line(color="#BDC3C7", size=0.5),
    )
)

# Save
plot.save("plot.png", dpi=300)
