""" pyplots.ai
line-growth-percentile: Pediatric Growth Chart with Percentile Curves
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-19
"""
# ruff: noqa: F405

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Data - WHO-style weight-for-age reference for boys (0-36 months)
np.random.seed(42)
age_months = np.arange(0, 37, 1)

# WHO-approximated weight-for-age 50th percentile for boys 0-36 months (kg)
percentile_50 = 3.3 + 3.8 * np.log1p(age_months * 0.6)

# Spread increases with age (SD widens)
spread = 0.25 + 0.03 * age_months
percentile_3 = percentile_50 - 1.88 * spread
percentile_10 = percentile_50 - 1.28 * spread
percentile_25 = percentile_50 - 0.67 * spread
percentile_75 = percentile_50 + 0.67 * spread
percentile_90 = percentile_50 + 1.28 * spread
percentile_97 = percentile_50 + 1.88 * spread

# Individual patient data - boy with growth faltering episode then catch-up
patient_ages = np.array([0, 1, 2, 4, 6, 9, 12, 15, 18, 24, 30, 36])
patient_weights = np.array([3.5, 4.6, 5.8, 7.2, 8.1, 9.0, 9.6, 10.1, 10.8, 12.4, 14.0, 15.2])

# Build percentile band dataframe
df_bands = pd.DataFrame(
    {
        "age": age_months,
        "p3": percentile_3,
        "p10": percentile_10,
        "p25": percentile_25,
        "p50": percentile_50,
        "p75": percentile_75,
        "p90": percentile_90,
        "p97": percentile_97,
    }
)

# Patient data with percentile context for tooltips
p50_at_patient = np.interp(patient_ages, age_months, percentile_50)
p25_at_patient = np.interp(patient_ages, age_months, percentile_25)
p75_at_patient = np.interp(patient_ages, age_months, percentile_75)
df_patient = pd.DataFrame(
    {
        "age": patient_ages,
        "weight": patient_weights,
        "p50_ref": np.round(p50_at_patient, 1),
        "p25_ref": np.round(p25_at_patient, 1),
        "p75_ref": np.round(p75_at_patient, 1),
    }
)

# Percentile label data (at right edge)
label_x = 36.3
df_labels = pd.DataFrame(
    {
        "age": [label_x] * 7,
        "weight": [
            percentile_3[-1],
            percentile_10[-1],
            percentile_25[-1],
            percentile_50[-1],
            percentile_75[-1],
            percentile_90[-1],
            percentile_97[-1],
        ],
        "label": ["P3", "P10", "P25", "P50", "P75", "P90", "P97"],
    }
)

# Blue-toned palette for boys (graduated: darker at extremes, lighter near median)
blue_outer = "#1A4C7A"
blue_mid = "#4A8DBF"
blue_inner = "#A3C9E8"

# Lets-plot specific: configure tooltips for patient trajectory
patient_tooltips = (
    layer_tooltips()
    .title("Patient Visit")
    .line("Age|@age months")
    .line("Weight|@weight kg")
    .line("P50 ref|@p50_ref kg")
    .line("P25-P75|@p25_ref - @p75_ref kg")
)

# Plot
plot = (
    ggplot()
    # Outermost band: P3-P10 and P90-P97
    + geom_ribbon(aes(x="age", ymin="p3", ymax="p10"), data=df_bands, fill=blue_outer, alpha=0.35, tooltips="none")
    + geom_ribbon(aes(x="age", ymin="p90", ymax="p97"), data=df_bands, fill=blue_outer, alpha=0.35, tooltips="none")
    # Middle band: P10-P25 and P75-P90
    + geom_ribbon(aes(x="age", ymin="p10", ymax="p25"), data=df_bands, fill=blue_mid, alpha=0.3, tooltips="none")
    + geom_ribbon(aes(x="age", ymin="p75", ymax="p90"), data=df_bands, fill=blue_mid, alpha=0.3, tooltips="none")
    # Inner band: P25-P75
    + geom_ribbon(aes(x="age", ymin="p25", ymax="p75"), data=df_bands, fill=blue_inner, alpha=0.3, tooltips="none")
    # Percentile lines
    + geom_line(aes(x="age", y="p3"), data=df_bands, color=blue_outer, size=0.5, alpha=0.5)
    + geom_line(aes(x="age", y="p10"), data=df_bands, color=blue_mid, size=0.5, alpha=0.5)
    + geom_line(aes(x="age", y="p25"), data=df_bands, color=blue_inner, size=0.5, alpha=0.5)
    + geom_line(aes(x="age", y="p50"), data=df_bands, color="#306998", size=1.8)
    + geom_line(aes(x="age", y="p75"), data=df_bands, color=blue_inner, size=0.5, alpha=0.5)
    + geom_line(aes(x="age", y="p90"), data=df_bands, color=blue_mid, size=0.5, alpha=0.5)
    + geom_line(aes(x="age", y="p97"), data=df_bands, color=blue_outer, size=0.5, alpha=0.5)
    # Patient trajectory with lets-plot tooltips
    + geom_line(aes(x="age", y="weight"), data=df_patient, color="#E63946", size=1.5, tooltips="none")
    + geom_point(
        aes(x="age", y="weight"),
        data=df_patient,
        color="#E63946",
        size=4,
        fill="white",
        shape=21,
        stroke=2,
        tooltips=patient_tooltips,
    )
    # Percentile labels on right margin
    + geom_text(
        aes(x="age", y="weight", label="label"), data=df_labels, size=10, color="#666666", hjust=0, tooltips="none"
    )
    # Lets-plot specific: format axis tick labels
    + scale_x_continuous(breaks=list(range(0, 37, 6)), limits=[0, 38], format="{d}")
    + scale_y_continuous(format=".1f")
    + coord_cartesian(ylim=[1, 18])
    + labs(
        title="Boys Weight-for-Age · line-growth-percentile · letsplot · pyplots.ai", x="Age (months)", y="Weight (kg)"
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_position="none",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.5),
        plot_margin=[40, 60, 20, 20],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
