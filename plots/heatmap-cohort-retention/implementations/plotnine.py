"""pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-16
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_discrete,
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
            trend_bonus = i * 1.5
            retention = np.clip(base_decay + noise + trend_bonus, 5, 100)
        rows.append(
            {"cohort": cohort, "period": period, "retention_rate": round(retention, 1), "cohort_size": cohort_sizes[i]}
        )

df = pd.DataFrame(rows)

# Create y-axis labels with cohort size
df["cohort_label"] = df.apply(lambda r: f"{r['cohort']} (n={r['cohort_size']:,})", axis=1)

# Preserve ordering
cohort_labels = [f"{c} (n={s:,})" for c, s in zip(cohorts, cohort_sizes, strict=True)]
df["cohort_label"] = pd.Categorical(df["cohort_label"], categories=cohort_labels[::-1], ordered=True)

# Text color: white on dark cells (viridis dark end), dark on light cells
df["text_color"] = df["retention_rate"].apply(lambda v: "#ffffff" if v < 60 else "#1a1a2e")

# Format retention text
df["label"] = df["retention_rate"].apply(lambda v: f"{v:.0f}%")

# Compare earliest vs latest cohort at same period for storytelling
compare_period = 4
earliest = df[(df["cohort"] == "Jan 2024") & (df["period"] == compare_period)]["retention_rate"].values[0]
latest = df[(df["cohort"] == "Jun 2024") & (df["period"] == compare_period)]["retention_rate"].values[0]
improvement = latest - earliest

# Perceptually uniform sequential palette (viridis-inspired: dark purple → teal → yellow)
colors = ["#440154", "#31688e", "#35b779", "#fde725"]

# Plot
plot = (
    ggplot(df, aes(x="period", y="cohort_label", fill="retention_rate"))
    + geom_tile(color="#f8f9fa", size=0.6)
    + geom_text(aes(label="label", color="text_color"), size=13, fontweight="bold")
    + scale_fill_gradientn(colors=colors, limits=(0, 100), name="Retention %")
    + scale_color_identity()
    + scale_x_continuous(breaks=range(n_cohorts), labels=[f"M{i}" for i in range(n_cohorts)])
    + scale_y_discrete(expand=(0.05, 0))
    + annotate(
        "text",
        x=n_cohorts - 2,
        y=3,
        label=f"Month {compare_period} retention improved\n+{improvement:.0f}pp from Jan→Jun 2024",
        size=11,
        color="#2d2d2d",
        ha="center",
        fontweight="bold",
    )
    + labs(
        x="Months Since Signup",
        y="",
        title="heatmap-cohort-retention · plotnine · pyplots.ai",
        subtitle="Monthly cohort retention — newer cohorts retain significantly better over time",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=26, ha="center", weight="bold", color="#0d1b2a"),
        plot_subtitle=element_text(size=18, ha="center", color="#555555", style="italic"),
        axis_title_x=element_text(size=20, color="#333333"),
        axis_text_x=element_text(size=16, color="#444444"),
        axis_text_y=element_text(size=16, color="#444444"),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="#fafafa", color="none"),
        panel_background=element_rect(fill="#fafafa", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, width=16, height=9)
