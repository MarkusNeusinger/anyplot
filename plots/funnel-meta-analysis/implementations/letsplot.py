"""pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-15
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data: Meta-analysis of 15 RCTs comparing drug vs placebo
# Effect sizes are log odds ratios, null effect at 0
np.random.seed(42)

studies = [
    {"study": "Adams 2015", "effect_size": 0.42, "std_error": 0.18},
    {"study": "Baker 2016", "effect_size": 0.28, "std_error": 0.22},
    {"study": "Chen 2016", "effect_size": 0.65, "std_error": 0.30},
    {"study": "Davis 2017", "effect_size": 0.15, "std_error": 0.25},
    {"study": "Evans 2017", "effect_size": 0.52, "std_error": 0.12},
    {"study": "Foster 2018", "effect_size": 0.10, "std_error": 0.35},
    {"study": "Garcia 2018", "effect_size": 0.38, "std_error": 0.15},
    {"study": "Hughes 2019", "effect_size": 0.55, "std_error": 0.28},
    {"study": "Ito 2019", "effect_size": 0.30, "std_error": 0.10},
    {"study": "Jensen 2020", "effect_size": 0.72, "std_error": 0.32},
    {"study": "Klein 2020", "effect_size": 0.25, "std_error": 0.14},
    {"study": "Lee 2021", "effect_size": 0.48, "std_error": 0.20},
    {"study": "Morgan 2021", "effect_size": 0.33, "std_error": 0.16},
    {"study": "Nguyen 2022", "effect_size": 0.60, "std_error": 0.26},
    {"study": "Olsen 2023", "effect_size": 0.20, "std_error": 0.38},
]

df = pd.DataFrame(studies)

# Pooled effect estimate (inverse-variance weighted)
weights = 1 / (df["std_error"] ** 2)
pooled_effect = (df["effect_size"] * weights).sum() / weights.sum()

# Pseudo 95% confidence funnel limits
se_range = np.linspace(0, df["std_error"].max() + 0.05, 200)
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

# Plot
plot = (
    ggplot()
    # Funnel confidence region (shaded)
    + geom_polygon(aes(x="effect_size", y="std_error"), data=funnel_df, fill="#306998", alpha=0.08)
    # Funnel boundary lines (95% CI)
    + geom_line(
        aes(x="effect_size", y="std_error", group="side"),
        data=funnel_lines_df,
        color="#306998",
        size=1,
        linetype="dashed",
        alpha=0.5,
    )
    # Vertical line at pooled effect
    + geom_vline(xintercept=pooled_effect, color="#306998", size=1.2)
    # Vertical dashed reference line at null effect (0)
    + geom_vline(xintercept=0, color="#888888", size=0.8, linetype="dashed")
    # Study points
    + geom_point(
        aes(x="effect_size", y="std_error"), data=df, color="#306998", fill="white", size=5, shape=21, stroke=1.5
    )
    # Inverted y-axis (more precise studies at top)
    + scale_y_reverse()
    # Labels
    + labs(x="Log Odds Ratio", y="Standard Error", title="funnel-meta-analysis · letsplot · pyplots.ai")
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#e5e5e5", size=0.5),
        panel_grid_minor=element_blank(),
    )
)

# Save
ggsave(plot, "plot.png", scale=3, path=".")
ggsave(plot, "plot.html", path=".")
