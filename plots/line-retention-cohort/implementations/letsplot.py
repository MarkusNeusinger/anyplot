""" pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-16
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

# Endpoint labels: last data point per cohort, with nudge to avoid overlap
endpoints = df[df["Week"] == 12].copy()
endpoints["label"] = endpoints["Retention"].apply(lambda x: f"{x:.0f}%")
# Adjust y positions to prevent label overlap (spread close values apart)
sorted_ep = endpoints.sort_values("Retention").reset_index(drop=True)
min_gap = 3.5
for i in range(1, len(sorted_ep)):
    if sorted_ep.loc[i, "Retention"] - sorted_ep.loc[i - 1, "Retention"] < min_gap:
        sorted_ep.loc[i, "Retention"] = sorted_ep.loc[i - 1, "Retention"] + min_gap
endpoints = sorted_ep

# Colorblind-friendly palette with distinct hues (oldest=lightest, newest=boldest)
colors = ["#A6CEE3", "#B2DF8A", "#FDBF6F", "#E31A1C", "#306998"]

# Line widths: older cohorts thinner, newer cohorts bolder
line_widths = [1.5, 1.8, 2.0, 2.5, 3.0]

# Build plot with per-cohort layers for varying line widths
cohort_labels = df["Cohort"].unique().tolist()

plot = ggplot()

# Add lines and points per cohort with distinct widths
for i, cohort_label in enumerate(cohort_labels):
    cdf = df[df["Cohort"] == cohort_label]
    plot = plot + geom_line(
        aes(x="Week", y="Retention", color="Cohort"),
        data=cdf,
        size=line_widths[i],
        alpha=0.9,
        tooltips=layer_tooltips().line("@Cohort").line("Week @Week").line("Retention @Retention{.1f}%"),
    )

plot = (
    plot
    + geom_point(aes(x="Week", y="Retention", color="Cohort"), data=df, size=4, alpha=0.85)
    + geom_hline(yintercept=20, linetype="dashed", color="#999999", size=0.8)
    + geom_text(
        aes(x="Week", y="Retention", label="label", color="Cohort"), data=endpoints, size=14, nudge_x=0.6, hjust=0
    )
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=pd.DataFrame({"x": [0.2], "y": [20], "label": ["20% threshold"]}),
        size=12,
        color="#999999",
        hjust=0,
        vjust=-1.2,
    )
    + scale_color_manual(values=colors)
    + scale_x_continuous(breaks=list(range(0, 13, 2)), limits=[0, 14.5])
    + scale_y_continuous(breaks=list(range(0, 101, 20)), limits=[0, 105])
    + labs(title="line-retention-cohort · letsplot · pyplots.ai", x="Weeks Since Signup", y="Retained Users (%)")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, hjust=0.5, face="bold"),
        axis_title=element_text(size=22),
        axis_text=element_text(size=18),
        legend_title=element_blank(),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major=element_line(color="#EBEBEB", size=0.4),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(color="white", fill="white"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
