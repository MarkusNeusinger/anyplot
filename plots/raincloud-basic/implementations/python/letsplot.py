""" pyplots.ai
raincloud-basic: Basic Raincloud Plot
Library: letsplot 4.8.2 | Python 3.14
Quality: 94/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from lets_plot import *
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Reaction times (ms) for three experimental conditions
np.random.seed(42)

# Control group: normal distribution centered at 450ms
control = np.random.normal(450, 60, 80)

# Treatment A: faster responses, centered at 380ms
treatment_a = np.random.normal(380, 50, 80)

# Treatment B: bimodal distribution — two widely separated response clusters
treatment_b = np.concatenate([np.random.normal(300, 30, 50), np.random.normal(540, 35, 30)])

# Build dataframe
df = pd.DataFrame(
    {
        "condition": ["Control"] * len(control)
        + ["Treatment A"] * len(treatment_a)
        + ["Treatment B"] * len(treatment_b),
        "reaction_time": np.concatenate([control, treatment_a, treatment_b]),
    }
)

# Color palette (mapped to display order: Treatment B, Treatment A, Control)
palette = {"Control": "#306998", "Treatment A": "#FFD43B", "Treatment B": "#5BA85B"}

# Category display order (bottom to top): Treatment B, Treatment A, Control
cat_order = ["Treatment B", "Treatment A", "Control"]

# Create raincloud plot: half-violin (cloud) + box plot + jittered points (rain)
# Y-axis: Treatment B=0, Treatment A=1, Control=2
plot = (
    ggplot(df, aes(x="reaction_time", y="condition", fill="condition", color="condition"))
    # Half-violin (cloud) - nudged above category baseline
    + geom_violin(trim=False, show_half=1, size=0.8, alpha=0.7, position=position_nudge(y=0.12))
    # Box plot - wider for clear quartile readability
    + geom_boxplot(
        width=0.18,
        outlier_size=0,
        outlier_alpha=0,
        fill="white",
        color="#333333",
        size=0.8,
        alpha=0.95,
        show_legend=False,
    )
    # Jittered points (rain) - positioned below category baseline
    + geom_jitter(
        width=0,
        height=0.06,
        size=3.5,
        alpha=0.6,
        shape=21,
        stroke=0.3,
        show_legend=False,
        position=position_nudge(y=-0.16),
    )
    # Annotation: Treatment A faster responses (Treatment A = index 1)
    + geom_text(
        x=580, y=1.55, label="~70ms faster mean\nthan Control", size=10, color="#8B7500", fontface="italic", hjust=0
    )
    # Arrow from label toward Treatment A
    + geom_segment(x=570, y=1.45, xend=420, yend=1.15, color="#8B7500", size=0.5, arrow=arrow(length=8, type="closed"))
    # Annotation: Treatment B bimodal (Treatment B = index 0, bottom)
    + geom_text(
        x=580, y=0.55, label="Two distinct\nresponse clusters", size=10, color="#3D7A3D", fontface="italic", hjust=0
    )
    # Arrow pointing to Treatment B fast cluster (~300ms)
    + geom_segment(x=570, y=0.35, xend=310, yend=0.12, color="#3D7A3D", size=0.5, arrow=arrow(length=8, type="closed"))
    # Arrow pointing to Treatment B slow cluster (~540ms)
    + geom_segment(x=585, y=0.3, xend=545, yend=0.12, color="#3D7A3D", size=0.5, arrow=arrow(length=8, type="closed"))
    # Scales
    + scale_fill_manual(values=palette)
    + scale_color_manual(values=palette)
    + scale_y_discrete(limits=cat_order)
    + scale_x_continuous(limits=[200, 700])
    # Labels and title
    + labs(
        x="Reaction Time (ms)", y="Experimental Condition", title="raincloud-basic \u00b7 letsplot \u00b7 pyplots.ai"
    )
    # Refined theme — custom styling without flavor to avoid conflicts
    + theme(
        plot_title=element_text(size=24, face="bold"),
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),
        panel_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),
        axis_title_x=element_text(size=20, margin=[12, 0, 0, 0]),
        axis_title_y=element_text(size=20, margin=[0, 12, 0, 0]),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16, face="bold"),
        axis_ticks=element_blank(),
        axis_line_x=element_line(color="#CCCCCC", size=0.5),
        axis_line_y=element_blank(),
        legend_position="none",
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color="rgba(0, 0, 0, 0.08)", size=0.4),
        plot_margin=[40, 40, 30, 20],
    )
    + ggsize(1600, 900)
)

# Save outputs
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
