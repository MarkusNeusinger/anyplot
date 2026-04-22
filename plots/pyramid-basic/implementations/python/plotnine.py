""" pyplots.ai
pyramid-basic: Basic Pyramid Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_blank,
    element_text,
    geom_col,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data - Population pyramid by age group
age_groups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
male_pop = [4200, 4500, 5100, 5800, 6200, 5500, 4100, 2800, 1200]
female_pop = [4000, 4300, 5000, 5600, 6000, 5700, 4500, 3200, 1800]

# Create DataFrame with male values as negative for left side
df = pd.DataFrame(
    {
        "age_group": age_groups * 2,
        "population": [-m for m in male_pop] + female_pop,
        "gender": ["Male"] * len(age_groups) + ["Female"] * len(age_groups),
    }
)

# Convert age_group to categorical with proper order
df["age_group"] = pd.Categorical(df["age_group"], categories=age_groups, ordered=True)

# Create pyramid chart
plot = (
    ggplot(df, aes(x="age_group", y="population", fill="gender"))
    + geom_col(width=0.85)
    + scale_fill_manual(values={"Male": "#306998", "Female": "#FFD43B"})
    + labs(
        x="Age Group",
        y="Population (thousands)",
        title="Population by Age & Gender · pyramid-basic · plotnine · pyplots.ai",
        fill="Gender",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=14),
        plot_title=element_text(size=22),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        panel_grid_minor=element_blank(),
    )
    + coord_flip()
)

# Save the plot
plot.save("plot.png", dpi=300, verbose=False)
