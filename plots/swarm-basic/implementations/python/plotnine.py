""" pyplots.ai
swarm-basic: Basic Swarm Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_text,
    geom_point,
    ggplot,
    labs,
    position_jitter,
    scale_color_manual,
    stat_summary,
    theme,
    theme_minimal,
)


# Data - Patient biomarker levels across treatment groups
np.random.seed(42)

treatment_groups = ["Placebo", "Low Dose", "Medium Dose", "High Dose"]
data = []

# Generate varied distributions for each treatment group
distributions = {
    "Placebo": {"mean": 45, "std": 12, "n": 50},
    "Low Dose": {"mean": 55, "std": 10, "n": 45},
    "Medium Dose": {"mean": 68, "std": 8, "n": 55},
    "High Dose": {"mean": 75, "std": 6, "n": 40},
}

for group, params in distributions.items():
    values = np.random.normal(params["mean"], params["std"], params["n"])
    # Clip to realistic biomarker range
    values = np.clip(values, 20, 100)
    data.extend([(group, value) for value in values])

df = pd.DataFrame(data, columns=["treatment", "biomarker"])

# Preserve order of treatment groups
df["treatment"] = pd.Categorical(df["treatment"], categories=treatment_groups, ordered=True)

# Create swarm plot using jittered points
plot = (
    ggplot(df, aes(x="treatment", y="biomarker", color="treatment"))
    + geom_point(position=position_jitter(width=0.3, height=0, random_state=42), size=3.5, alpha=0.75)
    # Add median markers for each category
    + stat_summary(fun_y=np.median, geom="point", size=8, shape="D", color="#2C3E50")
    + scale_color_manual(values=["#1B9E77", "#D95F02", "#7570B3", "#E7298A"])
    + labs(x="Treatment Group", y="Biomarker Level (ng/mL)", title="swarm-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_position="none",
    )
)

# Save
plot.save("plot.png", dpi=300)
