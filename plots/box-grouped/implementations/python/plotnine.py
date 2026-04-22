""" pyplots.ai
box-grouped: Grouped Box Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_text,
    geom_boxplot,
    ggplot,
    labs,
    position_dodge2,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data: Employee performance scores by department and experience level
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Support"]
experience_levels = ["Junior", "Mid-Level", "Senior"]

data = []
for dept in departments:
    for exp in experience_levels:
        # Create realistic performance distributions that vary by dept and experience
        n = 40
        if dept == "Engineering":
            base = 70 if exp == "Junior" else 78 if exp == "Mid-Level" else 85
            spread = 12 if exp == "Junior" else 10 if exp == "Mid-Level" else 8
        elif dept == "Marketing":
            base = 68 if exp == "Junior" else 75 if exp == "Mid-Level" else 82
            spread = 14 if exp == "Junior" else 11 if exp == "Mid-Level" else 9
        elif dept == "Sales":
            base = 65 if exp == "Junior" else 77 if exp == "Mid-Level" else 88
            spread = 15 if exp == "Junior" else 12 if exp == "Mid-Level" else 7
        else:  # Support
            base = 72 if exp == "Junior" else 76 if exp == "Mid-Level" else 80
            spread = 10 if exp == "Junior" else 9 if exp == "Mid-Level" else 8

        values = np.random.normal(base, spread, n)
        # Add some outliers
        if exp == "Senior" and dept == "Sales":
            values = np.append(values, [55, 98])  # Add outliers
        if exp == "Junior" and dept == "Engineering":
            values = np.append(values, [42, 95])  # Add outliers

        for v in values:
            data.append({"Department": dept, "Experience": exp, "Score": v})

df = pd.DataFrame(data)

# Order experience levels properly
df["Experience"] = pd.Categorical(df["Experience"], categories=experience_levels, ordered=True)

# Custom color palette using Python colors and complementary
colors = ["#306998", "#FFD43B", "#4B8BBE"]  # Python Blue, Python Yellow, Light Blue

# Create grouped box plot
plot = (
    ggplot(df, aes(x="Department", y="Score", fill="Experience"))
    + geom_boxplot(
        position=position_dodge2(preserve="single", padding=0.1), width=0.7, outlier_size=3, outlier_alpha=0.7
    )
    + scale_fill_manual(values=colors)
    + labs(x="Department", y="Performance Score", title="box-grouped · plotnine · pyplots.ai", fill="Experience Level")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
    )
)

# Save
plot.save("plot.png", dpi=300)
