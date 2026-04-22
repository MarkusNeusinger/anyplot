""" pyplots.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_jitter, geom_violin, ggplot, labs, position_jitter, theme, theme_minimal


# Data - Reaction times (ms) across 4 experimental conditions
np.random.seed(42)

conditions = ["Control", "Treatment A", "Treatment B", "Treatment C"]
n_per_group = 50

data = []
for condition in conditions:
    if condition == "Control":
        values = np.random.normal(450, 80, n_per_group)
    elif condition == "Treatment A":
        values = np.random.normal(380, 60, n_per_group)
    elif condition == "Treatment B":
        values = np.concatenate(
            [np.random.normal(420, 40, n_per_group // 2), np.random.normal(520, 50, n_per_group // 2)]
        )
    else:  # Treatment C
        values = np.random.normal(350, 90, n_per_group)

    for v in values:
        data.append({"condition": condition, "reaction_time": v})

df = pd.DataFrame(data)
df["condition"] = pd.Categorical(df["condition"], categories=conditions, ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="condition", y="reaction_time"))
    + geom_violin(fill="#306998", alpha=0.4, color="#306998", size=0.8)
    + geom_jitter(position=position_jitter(width=0.15), color="#FFD43B", size=2.5, alpha=0.8, stroke=0.3)
    + labs(x="Experimental Condition", y="Reaction Time (ms)", title="violin-swarm · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        axis_text_x=element_text(size=16),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
