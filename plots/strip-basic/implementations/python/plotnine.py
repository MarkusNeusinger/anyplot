""" pyplots.ai
strip-basic: Basic Strip Plot
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
    theme,
    theme_minimal,
)


# Data - Patient response times (seconds) across different drug treatments
np.random.seed(42)

treatments = ["Placebo", "Drug A", "Drug B", "Drug C"]
data = []

# Generate varied distributions for each treatment group
distributions = {
    "Placebo": {"mean": 45, "std": 12, "n": 40},
    "Drug A": {"mean": 32, "std": 8, "n": 45},
    "Drug B": {"mean": 28, "std": 10, "n": 42},
    "Drug C": {"mean": 25, "std": 6, "n": 38},
}

for treatment, params in distributions.items():
    times = np.random.normal(params["mean"], params["std"], params["n"])
    # Clip to realistic response times (minimum 5 seconds)
    times = np.clip(times, 5, 80)
    data.extend([(treatment, time) for time in times])

df = pd.DataFrame(data, columns=["treatment", "response_time"])

# Create strip plot with jittered points
plot = (
    ggplot(df, aes(x="treatment", y="response_time", color="treatment"))
    + geom_point(position=position_jitter(width=0.25, height=0, random_state=42), size=4, alpha=0.65)
    + scale_color_manual(values=["#306998", "#FFD43B", "#4B8BBE", "#FFE873"])
    + labs(x="Treatment Group", y="Response Time (seconds)", title="strip-basic · plotnine · pyplots.ai")
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
plot.save("plot.png", dpi=300, verbose=False)
