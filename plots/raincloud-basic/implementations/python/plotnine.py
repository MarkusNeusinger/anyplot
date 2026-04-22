""" pyplots.ai
raincloud-basic: Basic Raincloud Plot
Library: plotnine 0.15.3 | Python 3.14
Quality: 94/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_flip,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_boxplot,
    geom_jitter,
    geom_violin,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_y_continuous,
    stage,
    theme,
    theme_minimal,
)


# Data - Reaction times (ms) for three experimental conditions
np.random.seed(42)

control = np.random.normal(450, 60, 80)
treatment_a = np.random.normal(380, 50, 80)
treatment_b = np.concatenate([np.random.normal(350, 40, 50), np.random.normal(500, 45, 30)])

df = pd.DataFrame(
    {
        "condition": (
            ["Control"] * len(control) + ["Treatment A"] * len(treatment_a) + ["Treatment B"] * len(treatment_b)
        ),
        "reaction_time": np.concatenate([control, treatment_a, treatment_b]),
    }
)
df["condition"] = pd.Categorical(df["condition"], categories=["Treatment B", "Treatment A", "Control"], ordered=True)

# Colors — refined palette with deeper saturation and harmony
colors = {"Control": "#2B5B8A", "Treatment A": "#E8A838", "Treatment B": "#3A8A5C"}

# Cloud shift (positive = right on pre-flip x-axis = upward after coord_flip)
cloud_shift = 0.15

# Plot - horizontal raincloud via coord_flip
# Before flip: x=condition (categorical), y=reaction_time (numeric)
# After flip: categories on y-axis, values on x-axis
plot = (
    ggplot(df, aes(x="condition", y="reaction_time", fill="condition", color="condition"))
    # Cloud (half-violin) - style="right" extends in positive x-direction = upward after flip
    + geom_violin(
        aes(x=stage("condition", after_scale="x+{0}".format(cloud_shift))),
        style="right",
        trim=True,
        scale="width",
        size=0.3,
        alpha=0.8,
        show_legend=False,
    )
    # Boxplot - centered on category baseline
    + geom_boxplot(width=0.06, outlier_shape="", fill="white", color="#444444", size=0.5, alpha=0.95, show_legend=False)
    # Rain (jittered points) - nudged in negative x-direction = downward after flip
    + geom_jitter(
        aes(x=stage("condition", after_scale="x-0.18")), width=0.06, height=0, size=2.2, alpha=0.55, show_legend=False
    )
    # Annotation: highlight bimodal distribution in Treatment B
    # In pre-flip coordinates: x=category position, y=reaction_time
    # Treatment B is category index 1 (0-based). Annotation arrow pointing to the two peaks.
    + annotate(
        "text",
        x=0.55,
        y=425,
        label="← Bimodal: two distinct\n     response clusters",
        size=11,
        color="#2A2A2A",
        ha="center",
        fontstyle="italic",
    )
    + annotate("segment", x=0.7, xend=0.95, y=370, yend=350, size=0.5, color="#666666", linetype="dashed")
    + annotate("segment", x=0.7, xend=0.95, y=480, yend=500, size=0.5, color="#666666", linetype="dashed")
    # Annotation: Treatment A shifted left
    + annotate(
        "text",
        x=1.55,
        y=290,
        label="Faster responses\nvs. Control →",
        size=10,
        color="#2A2A2A",
        ha="left",
        fontstyle="italic",
    )
    + scale_fill_manual(values=colors)
    + scale_color_manual(values=colors)
    + scale_y_continuous(expand=(0.02, 0, 0.08, 0))
    + coord_flip()
    + labs(x="Experimental Condition", y="Reaction Time (ms)", title="raincloud-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#2A2A2A"),
        axis_title=element_text(size=20, weight="bold"),
        axis_text=element_text(size=16, color="#444444"),
        plot_title=element_text(size=24, weight="bold", color="#1A1A1A"),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color="#E0E0E0", size=0.4),
        panel_border=element_blank(),
        plot_background=element_rect(fill="#FAFAFA", color="none"),
        panel_background=element_rect(fill="#FAFAFA", color="none"),
        legend_position="none",
        plot_margin=0.02,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
