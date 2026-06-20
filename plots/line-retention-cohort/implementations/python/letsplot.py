"""
line-retention-cohort: User Retention Curve by Cohort
Library: letsplot | Python
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")

# Imprint palette (canonical order, 5 cohorts)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Theme-adaptive chrome tokens
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data: monthly signup cohorts tracked weekly for 12 weeks
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
    for w, r in zip(weeks, retention, strict=False):
        rows.append({"Week": w, "Retention": r, "Cohort": label})

df = pd.DataFrame(rows)

# Endpoint labels at week 12 with overlap prevention
endpoints = df[df["Week"] == 12].copy()
endpoints["label"] = endpoints["Retention"].apply(lambda x: f"{x:.0f}%")
sorted_ep = endpoints.sort_values("Retention").reset_index(drop=True)
min_gap = 5.0  # larger gap to ensure labels don't crowd at lower retention values
for i in range(1, len(sorted_ep)):
    if sorted_ep.loc[i, "Retention"] - sorted_ep.loc[i - 1, "Retention"] < min_gap:
        sorted_ep.loc[i, "Retention"] = sorted_ep.loc[i - 1, "Retention"] + min_gap
endpoints = sorted_ep

# Line widths: older cohorts thinner, newer cohorts bolder for visual hierarchy
line_widths = [1.0, 1.5, 2.0, 2.5, 3.0]
cohort_labels = [f"{k} (n={v['size']:,})" for k, v in cohorts.items()]

plot = ggplot()

# Per-cohort lines with progressive widths
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
    + geom_point(aes(x="Week", y="Retention", color="Cohort"), data=df, size=2.5, alpha=0.85)
    + geom_hline(yintercept=20, linetype="dashed", color=INK_MUTED, size=0.7)
    + geom_text(
        aes(x="Week", y="Retention", label="label", color="Cohort"), data=endpoints, size=4, nudge_x=0.55, hjust=0
    )
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=pd.DataFrame({"x": [0.2], "y": [20], "label": ["20% target"]}),
        size=3.5,
        color=INK_MUTED,
        hjust=0,
        vjust=-1.2,
    )
    + scale_color_manual(values=IMPRINT_PALETTE)
    + scale_x_continuous(breaks=list(range(0, 13, 2)), limits=[0, 15.5])
    + scale_y_continuous(breaks=list(range(0, 101, 20)), limits=[0, 105])
    + labs(title="line-retention-cohort · letsplot · anyplot.ai", x="Weeks Since Signup", y="Retained Users (%)")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=16, hjust=0.5, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_blank(),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
        panel_grid_major=element_line(color=INK, size=0.3),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT),
    )
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
