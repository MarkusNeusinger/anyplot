""" pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-16
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data: Monthly signup cohorts tracked weekly for 12 weeks
np.random.seed(42)
weeks = np.arange(0, 13)

cohorts = {
    "Jan 2025": {"size": 1245, "decay": 0.18},
    "Feb 2025": {"size": 1102, "decay": 0.16},
    "Mar 2025": {"size": 1380, "decay": 0.14},
    "Apr 2025": {"size": 1510, "decay": 0.12},
    "May 2025": {"size": 1425, "decay": 0.10},
}

rows = []
for cohort_name, params in cohorts.items():
    retention = 100 * np.exp(-params["decay"] * weeks)
    noise = np.random.normal(0, 1.5, len(weeks))
    noise[0] = 0
    retention = np.clip(retention + noise, 0, 100)
    retention[0] = 100.0
    label = f"{cohort_name} (n={params['size']:,})"
    for w, r in zip(weeks, retention):
        rows.append({"Week": w, "Retention": r, "Cohort": label})

df = pd.DataFrame(rows)

# Colors: cohesive palette starting with Python Blue, older cohorts lighter
colors = ["#93B5C9", "#7EAAB8", "#5590A3", "#306998", "#1B4965"]

# Plot
plot = (
    ggplot(df, aes(x="Week", y="Retention", color="Cohort"))
    + geom_line(size=2.5, alpha=0.9)
    + geom_point(size=4, alpha=0.85)
    + geom_hline(yintercept=20, linetype="dashed", color="#888888", size=1)
    + scale_color_manual(values=colors)
    + scale_x_continuous(breaks=list(range(0, 13, 2)))
    + scale_y_continuous(breaks=list(range(0, 101, 20)), limits=[0, 105])
    + labs(title="line-retention-cohort · letsplot · pyplots.ai", x="Weeks Since Signup", y="Retained Users (%)")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, hjust=0.5),
        axis_title=element_text(size=22),
        axis_text=element_text(size=18),
        legend_title=element_blank(),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major=element_line(color="#E0E0E0", size=0.5),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
