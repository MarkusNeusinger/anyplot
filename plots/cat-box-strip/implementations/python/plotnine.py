""" pyplots.ai
cat-box-strip: Box Plot with Strip Overlay
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_text,
    geom_boxplot,
    geom_jitter,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data - Plant growth measurements across fertilizer types
np.random.seed(42)

categories = ["Control", "Fertilizer A", "Fertilizer B", "Fertilizer C"]
n_per_group = 40

data = []
# Control: lower values, moderate spread
control = np.random.normal(loc=25, scale=5, size=n_per_group)
# Fertilizer A: moderate improvement
fert_a = np.random.normal(loc=35, scale=6, size=n_per_group)
# Fertilizer B: good improvement, tighter distribution
fert_b = np.random.normal(loc=42, scale=4, size=n_per_group)
# Fertilizer C: best results but with outliers (bimodal)
fert_c = np.concatenate(
    [
        np.random.normal(loc=48, scale=4, size=n_per_group - 5),
        np.random.normal(loc=30, scale=3, size=5),  # Some underperformers
    ]
)

for cat, vals in zip(categories, [control, fert_a, fert_b, fert_c], strict=True):
    for v in vals:
        data.append({"Fertilizer": cat, "Growth (cm)": v})

df = pd.DataFrame(data)
df["Fertilizer"] = pd.Categorical(df["Fertilizer"], categories=categories, ordered=True)

# Colors - Python Blue and Yellow + accessible complements
colors = ["#306998", "#FFD43B", "#5A9BD5", "#70AD47"]

# Plot
plot = (
    ggplot(df, aes(x="Fertilizer", y="Growth (cm)", fill="Fertilizer"))
    + geom_boxplot(alpha=0.7, width=0.6, outlier_shape="", size=1)
    + geom_jitter(aes(color="Fertilizer"), width=0.15, alpha=0.6, size=3, show_legend=False)
    + scale_fill_manual(values=colors)
    + scale_color_manual(values=colors)
    + labs(x="Treatment Group", y="Plant Growth (cm)", title="cat-box-strip · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_position="right",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
