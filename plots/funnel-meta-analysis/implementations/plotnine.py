""" pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-15
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_line,
    geom_point,
    geom_vline,
    ggplot,
    labs,
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

# Add slight publication bias (shift small studies toward positive)
bias_mask = std_errors > 0.35
effect_sizes[bias_mask] += np.random.uniform(0.05, 0.2, bias_mask.sum())

summary_effect = np.average(effect_sizes, weights=1 / std_errors**2)

studies_df = pd.DataFrame(
    {"effect_size": effect_sizes, "std_error": std_errors, "study": [f"Study {i + 1}" for i in range(n_studies)]}
)

# Funnel lines (pseudo 95% CI)
se_range = np.linspace(0, 0.6, 200)
funnel_df = pd.DataFrame(
    {
        "se": np.concatenate([se_range, se_range]),
        "effect": np.concatenate([summary_effect - 1.96 * se_range, summary_effect + 1.96 * se_range]),
        "side": ["lower"] * len(se_range) + ["upper"] * len(se_range),
    }
)

# Plot
plot = (
    ggplot()
    + geom_line(funnel_df, aes(x="effect", y="se", group="side"), color="#B0B0B0", linetype="dashed", size=0.8)
    + geom_vline(xintercept=summary_effect, color="#306998", size=1.2)
    + geom_vline(xintercept=0, color="#888888", linetype="dotted", size=0.8)
    + geom_point(studies_df, aes(x="effect_size", y="std_error"), color="#306998", fill="#306998", size=4, alpha=0.8)
    + scale_y_reverse()
    + labs(x="Log Odds Ratio", y="Standard Error", title="funnel-meta-analysis · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(alpha=0.2, size=0.5),
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300)
