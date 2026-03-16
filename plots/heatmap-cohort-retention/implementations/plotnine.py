""" pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-16
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_gradient,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Data
np.random.seed(42)
cohorts = [
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
n_cohorts = len(cohorts)
cohort_sizes = [1200, 1350, 980, 1100, 1450, 1280, 1050, 1380, 1150, 1020]

rows = []
for i, cohort in enumerate(cohorts):
    max_periods = n_cohorts - i
    for period in range(max_periods):
        if period == 0:
            retention = 100.0
        else:
            base_decay = 100 * np.exp(-0.25 * period)
            noise = np.random.uniform(-3, 3)
            trend_bonus = i * 0.4
            retention = np.clip(base_decay + noise + trend_bonus, 5, 100)
        rows.append(
            {"cohort": cohort, "period": period, "retention_rate": round(retention, 1), "cohort_size": cohort_sizes[i]}
        )

df = pd.DataFrame(rows)

# Create y-axis labels with cohort size
df["cohort_label"] = df.apply(lambda r: f"{r['cohort']} (n={r['cohort_size']})", axis=1)

# Preserve ordering
cohort_labels = [f"{c} (n={s})" for c, s in zip(cohorts, cohort_sizes, strict=True)]
df["cohort_label"] = pd.Categorical(df["cohort_label"], categories=cohort_labels[::-1], ordered=True)

# Text color: white on dark cells, dark on light cells
df["text_color"] = df["retention_rate"].apply(lambda v: "white" if v > 60 else "#333333")

# Format retention text
df["label"] = df["retention_rate"].apply(lambda v: f"{v:.0f}%")

# Plot
plot = (
    ggplot(df, aes(x="period", y="cohort_label", fill="retention_rate"))
    + geom_tile(color="white", size=0.8)
    + geom_text(aes(label="label", color="text_color"), size=10)
    + scale_fill_gradient(low="#e8f5e9", high="#1b5e20", limits=(0, 100), name="Retention %")
    + scale_color_identity()
    + scale_x_continuous(breaks=range(n_cohorts), labels=[f"Month {i}" for i in range(n_cohorts)])
    + labs(x="Months Since Signup", y="", title="heatmap-cohort-retention · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=22, ha="center"),
        axis_title_x=element_text(size=18),
        axis_text_x=element_text(size=13, rotation=45, ha="right"),
        axis_text_y=element_text(size=13),
        legend_title=element_text(size=15),
        legend_text=element_text(size=13),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, width=16, height=9)
