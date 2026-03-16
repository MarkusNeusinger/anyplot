"""pyplots.ai
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

# Base retention curve with realistic monotonic decay
base_decay = np.array([100.0, 62, 48, 40, 35, 31, 28, 26, 24, 23])

# Generate retention data with triangular shape and per-cohort variation
# Ensure monotonically decreasing retention within each cohort
rows = []
for i in range(n_cohorts):
    available_periods = n_periods - i
    cohort_variation = np.random.uniform(0.92, 1.08)
    prev_retention = 100.0
    for j in range(available_periods):
        if j == 0:
            retention = 100.0
        else:
            noise = np.random.uniform(-2, 2)
            retention = np.clip(base_decay[j] * cohort_variation + noise, 5, 100)
            # Ensure monotonic decrease
            retention = min(retention, prev_retention - 0.5)
        prev_retention = retention
        rows.append(
            {
                "cohort": f"{cohort_labels[i]} (n={cohort_sizes[i]})",
                "period": f"Month {j}",
                "period_num": j,
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
df["text_color"] = df["retention"].apply(lambda v: "white" if v > 50 else "#1a1a1a")

df_light = df[df["text_color"] == "white"].copy()
df_dark = df[df["text_color"] != "white"].copy()

# Identify critical drop zone (Month 0->1) for storytelling emphasis
df["is_critical_drop"] = (df["period_num"] == 1).astype(int)
df_drop = df[df["period_num"] == 1].copy()

# Custom tooltips for lets-plot distinctive interactivity
tile_tooltips = (
    layer_tooltips().format("retention", ".1f").line("@cohort").line("@period").line("Retention: @retention%")
)

# Plot with storytelling: highlight the critical first-month churn
plot = (
    ggplot(df, aes(x="period", y="cohort", fill="retention"))
    + geom_tile(tooltips=tile_tooltips, color="white", size=1.2)
    # Highlight critical Month 1 drop with border emphasis
    + geom_tile(
        aes(x="period", y="cohort"), data=df_drop, fill="rgba(0,0,0,0)", color="#FF6F00", size=2.5, tooltips="none"
    )
    + geom_text(aes(x="period", y="cohort", label="label"), data=df_light, color="white", size=12, fontface="bold")
    + geom_text(aes(x="period", y="cohort", label="label"), data=df_dark, color="#1a1a1a", size=12, fontface="bold")
    + scale_fill_viridis(option="viridis", limits=[0, 100], name="Retention %", direction=-1)
    + labs(
        x="Months Since Signup",
        y="Signup Cohort",
        title="heatmap-cohort-retention · letsplot · pyplots.ai",
        subtitle="Orange borders highlight critical Month 1 churn — the largest retention drop across all cohorts",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        plot_subtitle=element_text(size=16, color="#555555"),
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
