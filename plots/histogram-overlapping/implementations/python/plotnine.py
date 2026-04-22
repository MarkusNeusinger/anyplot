""" pyplots.ai
histogram-overlapping: Overlapping Histograms
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_histogram, ggplot, labs, scale_fill_manual, theme, theme_minimal


# Data - Response times (ms) for three user groups
np.random.seed(42)

# New users: higher response times, more spread
new_users = np.random.normal(loc=450, scale=120, size=150)

# Regular users: moderate response times
regular_users = np.random.normal(loc=320, scale=80, size=200)

# Power users: faster response times, tighter distribution
power_users = np.random.normal(loc=220, scale=50, size=180)

# Combine into a DataFrame
df = pd.DataFrame(
    {
        "response_time": np.concatenate([new_users, regular_users, power_users]),
        "user_group": (
            ["New Users"] * len(new_users) + ["Regular Users"] * len(regular_users) + ["Power Users"] * len(power_users)
        ),
    }
)

# Plot
plot = (
    ggplot(df, aes(x="response_time", fill="user_group"))
    + geom_histogram(alpha=0.5, bins=30, position="identity")
    + labs(
        x="Response Time (ms)", y="Frequency", title="histogram-overlapping · plotnine · pyplots.ai", fill="User Group"
    )
    + scale_fill_manual(values=["#306998", "#FFD43B", "#E74C3C"])
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
