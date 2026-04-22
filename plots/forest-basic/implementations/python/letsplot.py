""" pyplots.ai
forest-basic: Meta-Analysis Forest Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-27
"""

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data: Meta-analysis of clinical trials comparing treatment vs control
# Effect sizes are log odds ratios (log OR) - null effect at 0
studies = [
    {"study": "Smith 2018", "effect_size": 0.35, "ci_lower": 0.05, "ci_upper": 0.65, "weight": 12.5},
    {"study": "Johnson 2019", "effect_size": -0.12, "ci_lower": -0.45, "ci_upper": 0.21, "weight": 10.2},
    {"study": "Williams 2019", "effect_size": 0.48, "ci_lower": 0.18, "ci_upper": 0.78, "weight": 11.8},
    {"study": "Brown 2020", "effect_size": 0.22, "ci_lower": -0.15, "ci_upper": 0.59, "weight": 9.5},
    {"study": "Davis 2020", "effect_size": 0.55, "ci_lower": 0.20, "ci_upper": 0.90, "weight": 8.7},
    {"study": "Miller 2021", "effect_size": 0.15, "ci_lower": -0.18, "ci_upper": 0.48, "weight": 11.0},
    {"study": "Wilson 2021", "effect_size": 0.42, "ci_lower": 0.12, "ci_upper": 0.72, "weight": 12.0},
    {"study": "Moore 2022", "effect_size": 0.28, "ci_lower": -0.08, "ci_upper": 0.64, "weight": 9.8},
    {"study": "Taylor 2022", "effect_size": 0.65, "ci_lower": 0.28, "ci_upper": 1.02, "weight": 7.5},
    {"study": "Anderson 2023", "effect_size": 0.18, "ci_lower": -0.12, "ci_upper": 0.48, "weight": 12.8},
]

df = pd.DataFrame(studies)

# Calculate pooled estimate (weighted average)
total_weight = df["weight"].sum()
pooled_effect = (df["effect_size"] * df["weight"]).sum() / total_weight
pooled_se = 0.08  # Simplified SE for visualization
pooled_ci_lower = pooled_effect - 1.96 * pooled_se
pooled_ci_upper = pooled_effect + 1.96 * pooled_se

# Order studies by effect size and assign y positions
df = df.sort_values("effect_size", ascending=True).reset_index(drop=True)
df["y_pos"] = range(len(df), 0, -1)

# Scale weights for marker sizes (proportional to study weight)
df["marker_size"] = df["weight"] / df["weight"].max() * 8 + 2

# Create the forest plot
plot = (
    ggplot()
    # Vertical reference line at null effect (0 for log OR)
    + geom_vline(xintercept=0, color="#888888", size=1, linetype="dashed")
    # Confidence interval lines (whiskers)
    + geom_segment(aes(x="ci_lower", xend="ci_upper", y="y_pos", yend="y_pos"), data=df, color="#306998", size=1.5)
    # Point estimates (squares proportional to weight)
    + geom_point(
        aes(x="effect_size", y="y_pos", size="marker_size"),
        data=df,
        color="#306998",
        shape=15,  # Square marker
    )
    # Study labels on y-axis
    + scale_y_continuous(breaks=df["y_pos"].tolist(), labels=df["study"].tolist())
    # Diamond for pooled estimate
    + geom_polygon(
        aes(x="x", y="y"),
        data=pd.DataFrame(
            {"x": [pooled_ci_lower, pooled_effect, pooled_ci_upper, pooled_effect], "y": [-0.5, -1.0, -0.5, 0.0]}
        ),
        fill="#FFD43B",
        color="#306998",
        size=1,
    )
    # Labels and title
    + labs(x="Log Odds Ratio (95% CI)", y="", title="forest-basic · letsplot · pyplots.ai")
    # Theme and sizing
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title_x=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        legend_position="none",
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + scale_size_identity()
    + ggsize(1600, 900)
)

# Add text annotation for pooled estimate using geom_text
pooled_label_df = pd.DataFrame(
    {
        "x": [pooled_effect],
        "y": [-1.8],
        "label": [f"Pooled: {pooled_effect:.2f} [{pooled_ci_lower:.2f}, {pooled_ci_upper:.2f}]"],
    }
)
plot = plot + geom_text(aes(x="x", y="y", label="label"), data=pooled_label_df, size=14, color="#306998")

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", scale=3, path=".")

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
