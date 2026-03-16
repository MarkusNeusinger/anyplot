""" pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-16
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

# Distinct per-cohort base curves for more visible variation
cohort_profiles = [
    np.array([100.0, 68, 55, 48, 43, 39, 36, 34, 32, 31]),  # Jan - strong retention
    np.array([100.0, 58, 42, 34, 29, 25, 22, 20, 19, 18]),  # Feb - weak
    np.array([100.0, 72, 60, 52, 46, 42, 39, 37, 35, 34]),  # Mar - best cohort
    np.array([100.0, 55, 38, 30, 25, 22, 20, 18, 17, 16]),  # Apr - poor
    np.array([100.0, 65, 50, 42, 37, 33, 30, 28, 26, 25]),  # May - average
    np.array([100.0, 60, 45, 36, 31, 27, 24, 22, 21, 20]),  # Jun - below avg
    np.array([100.0, 70, 56, 47, 41, 37, 34, 32, 30, 29]),  # Jul - improving
    np.array([100.0, 50, 35, 27, 23, 20, 18, 16, 15, 14]),  # Aug - worst
    np.array([100.0, 66, 52, 44, 38, 34, 31, 29, 27, 26]),  # Sep - recovery
    np.array([100.0, 63, 48, 40, 35, 31, 28, 26, 24, 23]),  # Oct - steady
]

# Generate retention data with triangular shape and per-cohort variation
rows = []
for i in range(n_cohorts):
    available_periods = n_periods - i
    prev_retention = 100.0
    for j in range(available_periods):
        if j == 0:
            retention = 100.0
        else:
            noise = np.random.uniform(-1.5, 1.5)
            retention = np.clip(cohort_profiles[i][j] + noise, 5, 100)
            retention = min(retention, prev_retention - 0.5)
        prev_retention = retention
        rows.append(
            {
                "cohort": f"{cohort_labels[i]} (n={cohort_sizes[i]:,})",
                "period": f"Month {j}",
                "period_num": j,
                "retention": round(retention, 1),
            }
        )

df = pd.DataFrame(rows)

# Set category ordering for proper display
cohort_order = [f"{c} (n={s:,})" for c, s in zip(cohort_labels, cohort_sizes)]
period_order = [f"Month {j}" for j in range(n_periods)]
df["cohort"] = pd.Categorical(df["cohort"], categories=cohort_order[::-1], ordered=True)
df["period"] = pd.Categorical(df["period"], categories=period_order, ordered=True)

# Text labels and contrast colors
df["label"] = df["retention"].apply(lambda v: f"{v:.0f}%")
df["text_color"] = df["retention"].apply(lambda v: "white" if v > 50 else "#1a1a1a")

df_light = df[df["text_color"] == "white"].copy()
df_dark = df[df["text_color"] != "white"].copy()

# Identify critical drop zone (Month 0->1) for storytelling emphasis
df_drop = df[df["period_num"] == 1].copy()

# Rich tooltips with formatted retention and cohort context
tile_tooltips = (
    layer_tooltips().format("retention", ".1f").line("@cohort").line("@period | Retention: @retention%").min_width(220)
)

# Plot with storytelling: highlight the critical first-month churn
plot = (
    ggplot(df, aes(x="period", y="cohort", fill="retention"))
    + geom_tile(tooltips=tile_tooltips, color="#f0f0f0", size=0.5, width=0.98, height=0.98)
    # Highlight critical Month 1 drop with border emphasis
    + geom_tile(
        aes(x="period", y="cohort"),
        data=df_drop,
        fill="rgba(0,0,0,0)",
        color="#FF6F00",
        size=2.8,
        width=0.98,
        height=0.98,
        tooltips="none",
    )
    + geom_text(
        aes(x="period", y="cohort", label="label"),
        data=df_light,
        color="white",
        size=11,
        fontface="bold",
        label_format="{.0f}",
    )
    + geom_text(
        aes(x="period", y="cohort", label="label"),
        data=df_dark,
        color="#2a2a2a",
        size=11,
        fontface="bold",
        label_format="{.0f}",
    )
    + scale_fill_viridis(
        option="viridis",
        limits=[0, 100],
        name="Retention %",
        direction=-1,
        breaks=[0, 20, 40, 60, 80, 100],
        labels=["0%", "20%", "40%", "60%", "80%", "100%"],
    )
    + coord_fixed(ratio=0.85)
    + labs(
        x="Months Since Signup",
        y="Signup Cohort",
        title="heatmap-cohort-retention · letsplot · pyplots.ai",
        subtitle="Orange borders highlight critical Month 1 churn — the largest retention drop across all cohorts",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold", color="#1a1a1a"),
        plot_subtitle=element_text(size=15, color="#666666", face="italic"),
        axis_title_x=element_text(size=20, color="#333333"),
        axis_title_y=element_text(size=20, color="#333333"),
        axis_text_x=element_text(size=15, angle=0),
        axis_text_y=element_text(size=14),
        legend_title=element_text(size=16, face="bold"),
        legend_text=element_text(size=13),
        panel_grid=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
        legend_background=element_rect(fill="white", color="white"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
