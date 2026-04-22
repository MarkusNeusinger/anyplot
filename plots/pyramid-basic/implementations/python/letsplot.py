""" pyplots.ai
pyramid-basic: Basic Pyramid Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Population pyramid showing age distribution by gender
age_groups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
male_population = [45, 52, 68, 72, 65, 58, 48, 32, 18]  # in thousands
female_population = [43, 50, 71, 75, 68, 62, 55, 42, 28]  # in thousands

# Create dataframe with negative values for left side (male)
df = pd.DataFrame(
    {
        "age": age_groups * 2,
        "population": [-x for x in male_population] + female_population,
        "gender": ["Male"] * len(age_groups) + ["Female"] * len(age_groups),
    }
)

# Convert age to categorical with ordered levels
df["age"] = pd.Categorical(df["age"], categories=age_groups, ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="age", y="population", fill="gender"))
    + geom_bar(stat="identity", width=0.8)
    + coord_flip()
    + scale_fill_manual(values=["#306998", "#FFD43B"])  # Python Blue, Python Yellow
    + scale_y_continuous(
        breaks=[-80, -60, -40, -20, 0, 20, 40, 60, 80], labels=["80", "60", "40", "20", "0", "20", "40", "60", "80"]
    )
    + labs(x="Age Group", y="Population (thousands)", title="pyramid-basic · letsplot · pyplots.ai", fill="Gender")
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major_y=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x for 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML
ggsave(plot, "plot.html", path=".")
