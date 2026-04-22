""" pyplots.ai
box-grouped: Grouped Box Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_boxplot,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data: Employee performance scores by department and experience level
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Operations"]
experience_levels = ["Junior", "Mid-Level", "Senior"]

data = []
for dept in departments:
    for exp in experience_levels:
        n = 40
        # Create realistic distributions with variation
        if exp == "Junior":
            base = 60 + np.random.choice([0, 5, 10])
            spread = 12
        elif exp == "Mid-Level":
            base = 72 + np.random.choice([0, 3, 6])
            spread = 10
        else:  # Senior
            base = 82 + np.random.choice([0, 2, 4])
            spread = 8

        # Add department-specific variation
        dept_offset = {"Engineering": 3, "Marketing": 0, "Sales": -2, "Operations": 1}[dept]
        values = np.random.normal(base + dept_offset, spread, n)

        # Add some outliers for boxplot visualization
        if np.random.random() > 0.5:
            outlier_low = base - 3 * spread + np.random.randn(2) * 2
            outlier_high = base + 3 * spread + np.random.randn(2) * 2
            values = np.concatenate([values, outlier_low, outlier_high])

        for v in values:
            data.append({"Department": dept, "Experience": exp, "Performance Score": v})

df = pd.DataFrame(data)

# Ensure proper ordering
df["Experience"] = pd.Categorical(df["Experience"], categories=experience_levels, ordered=True)
df["Department"] = pd.Categorical(df["Department"], categories=departments, ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="Department", y="Performance Score", fill="Experience"))
    + geom_boxplot(alpha=0.85, outlier_size=3, outlier_alpha=0.7, width=0.7)
    + scale_fill_manual(values=["#306998", "#FFD43B", "#4CAF50"])
    + labs(
        title="box-grouped · letsplot · pyplots.ai", x="Department", y="Performance Score (%)", fill="Experience Level"
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title=element_text(size=22),
        axis_text=element_text(size=18),
        axis_text_x=element_text(size=18),
        legend_title=element_text(size=20),
        legend_text=element_text(size=18),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
