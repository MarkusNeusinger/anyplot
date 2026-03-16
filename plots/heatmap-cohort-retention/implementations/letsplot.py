""" pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-16
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Monthly cohort retention over 10 months
np.random.seed(42)
cohort_labels = [
    "Jan 2024",
    "Feb 2024",
    "Mar 2024",
    "Apr 2024",
    "May 2024",
    "Jun 2024",
    "Jul 2024",
    "Aug 2024",
    "Sep 2024",
    "Oct 2024",
]
n_cohorts = len(cohort_labels)
n_periods = 10
cohort_sizes = np.random.randint(800, 2500, n_cohorts)

# Base retention curve with realistic decay
base_decay = np.array([100.0, 62, 48, 40, 35, 31, 28, 26, 24, 23])

# Generate retention data with triangular shape and per-cohort variation
rows = []
for i in range(n_cohorts):
    available_periods = n_periods - i
    cohort_variation = np.random.uniform(0.9, 1.1)
    for j in range(available_periods):
        if j == 0:
            retention = 100.0
        else:
            noise = np.random.uniform(-3, 3)
            retention = np.clip(base_decay[j] * cohort_variation + noise, 5, 100)
        rows.append(
            {
                "cohort": f"{cohort_labels[i]} (n={cohort_sizes[i]})",
                "period": f"Month {j}",
                "retention": round(retention, 1),
            }
        )

df = pd.DataFrame(rows)

# Set category ordering for proper display
cohort_order = [f"{c} (n={s})" for c, s in zip(cohort_labels, cohort_sizes)]
period_order = [f"Month {j}" for j in range(n_periods)]
df["cohort"] = pd.Categorical(df["cohort"], categories=cohort_order[::-1], ordered=True)
df["period"] = pd.Categorical(df["period"], categories=period_order, ordered=True)

# Text labels and contrast colors
df["label"] = df["retention"].apply(lambda v: f"{v:.0f}%")
df["text_color"] = df["retention"].apply(lambda v: "white" if v > 55 else "#1a1a1a")

df_light = df[df["text_color"] == "white"].copy()
df_dark = df[df["text_color"] != "white"].copy()

# Plot
plot = (
    ggplot(df, aes(x="period", y="cohort", fill="retention"))
    + geom_tile(color="white", size=1.0)
    + geom_text(aes(x="period", y="cohort", label="label"), data=df_light, color="white", size=11)
    + geom_text(aes(x="period", y="cohort", label="label"), data=df_dark, color="#1a1a1a", size=11)
    + scale_fill_gradient(low="#E8F5E9", high="#1B5E20", limits=[0, 100], name="Retention %")
    + labs(x="Months Since Signup", y="Signup Cohort", title="heatmap-cohort-retention · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text_x=element_text(size=15),
        axis_text_y=element_text(size=14),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        panel_grid=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
